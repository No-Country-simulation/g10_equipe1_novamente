import logging
from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.llm import LLMError
from app.services import reviewer, writer
from app.services.content_schemas import GeneratedBase
from app.services.grounding import (
    Decision,
    GroundingReport,
    ReviewResult,
    decide,
    evaluate,
    failure_message,
)
from app.services.writer import Rewrite, WriteRequest

PROMPT_VERSION = f"{writer.PROMPT_VERSION}+{reviewer.PROMPT_VERSION}"

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GenerationResult:
    decision: Decision
    attempts: int
    generated: GeneratedBase | None
    review: ReviewResult | None
    report: GroundingReport | None
    error_message: str | None


class _GenerationState(TypedDict):
    request: WriteRequest
    attempt: int
    generated: GeneratedBase | None
    review: ReviewResult | None
    report: GroundingReport | None
    decision: Decision | None
    error_message: str | None


def _escreve(state: _GenerationState) -> _GenerationState:
    request = state["request"]
    attempt = state["attempt"] + 1
    try:
        if attempt == 1:
            generated = writer.write_content(request)
        else:
            previous, report = state["generated"], state["report"]
            assert previous is not None and report is not None
            generated = writer.write_content(
                request,
                rewrite=Rewrite(
                    previous, [claim.claim for claim in report.unsupported]
                ),
            )
    except LLMError as error:
        return {
            **state,
            "attempt": attempt,
            "decision": Decision.fail,
            "error_message": f"Não foi possível gerar o conteúdo. {error}",
        }

    return {
        **state,
        "attempt": attempt,
        "generated": generated,
        "review": None,
        "report": None,
        "decision": None,
    }


def _revisa(state: _GenerationState) -> _GenerationState:
    request, generated = state["request"], state["generated"]
    assert generated is not None
    try:
        review = reviewer.review_content(
            generated=generated,
            audience_level=request.audience_level,
            focus=request.focus,
            chunks=request.chunks,
        )
    except LLMError as error:
        return {
            **state,
            "decision": Decision.fail,
            "error_message": f"Não foi possível gerar o conteúdo. {error}",
        }

    report = evaluate(review, {chunk.chunk_id for chunk in request.chunks})
    decision = decide(report, attempt=state["attempt"])
    return {
        **state,
        "review": review,
        "report": report,
        "decision": decision,
        "error_message": failure_message(report) if decision is Decision.fail else None,
    }


_graph = (
    # O ty não reconhece TypedDict no limite genérico de StateGraph.
    StateGraph(_GenerationState)  # ty: ignore[invalid-argument-type]
    .add_node("escreve", _escreve)
    .add_node("revisa", _revisa)
    .add_edge(START, "escreve")
    .add_conditional_edges(
        "escreve",
        lambda state: END if state["decision"] is Decision.fail else "revisa",
        [END, "revisa"],
    )
    .add_conditional_edges(
        "revisa",
        lambda state: "escreve" if state["decision"] is Decision.rewrite else END,
        ["escreve", END],
    )
    .compile()
)


def generate_content(request: WriteRequest) -> GenerationResult:
    state = _graph.invoke(
        {
            "request": request,
            "attempt": 0,
            "generated": None,
            "review": None,
            "report": None,
            "decision": None,
            "error_message": None,
        },
        version="v2",
    ).value
    decision = state["decision"]
    assert decision in (Decision.publish, Decision.fail)
    result = GenerationResult(
        decision=decision,
        attempts=state["attempt"],
        generated=state["generated"],
        review=state["review"],
        report=state["report"],
        error_message=state["error_message"],
    )
    if result.report is None:
        logger.info("decisão=%s tentativas=%d", result.decision, result.attempts)
    else:
        logger.info(
            "decisão=%s tentativas=%d sustentadas=%d sem_apoio=%d",
            result.decision,
            result.attempts,
            len(result.report.supported),
            len(result.report.unsupported),
        )
    return result
