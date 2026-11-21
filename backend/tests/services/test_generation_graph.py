import logging
import uuid
from unittest.mock import Mock, call

import pytest

from app.core import llm
from app.models import AudienceLevel, ClarityLevel, ContentFormat
from app.services import planner, reviewer, writer
from app.services.content_schemas import GeneratedTutorial
from app.services.generation_graph import PROMPT_VERSION, generate_content
from app.services.grounding import (
    ClaimReview,
    Decision,
    ReviewResult,
    evaluate,
    failure_message,
)
from app.services.retrieval import RetrievedChunk
from app.services.reviewer import _ClaimOut, _ReviewOut
from app.services.writer import Rewrite, WriteRequest


@pytest.fixture
def request_data():
    return WriteRequest(
        content_format=ContentFormat.tutorial,
        focus="Como criar branches no Git",
        audience_level=AudienceLevel.technical_basic,
        niche_name="Engenharia",
        niche_prompt_hint="Use exemplos de controle de versão.",
        chunks=[
            RetrievedChunk(
                uuid.uuid4(), uuid.uuid4(), 0, "git branch cria um branch.", None, 0.9
            )
        ],
    )


@pytest.fixture
def drafts():
    return [
        GeneratedTutorial.model_validate(
            {
                "title": title,
                "estimated_minutes": 2,
                "key_concepts": ["branch"],
                "prerequisites": [],
                "content": {
                    "summary": "Como criar um branch.",
                    "sections": [{"title": "Comando", "body": "Use `git branch`."}],
                    "takeaways": ["Crie um branch com `git branch`."],
                },
            }
        )
        for title in ("Primeira versão", "Segunda versão")
    ]


@pytest.fixture
def reviews(request_data):
    supported = ClaimReview(
        claim="git branch cria um branch.",
        supported=True,
        chunk_id=request_data.chunks[0].chunk_id,
    )

    def review(*unsupported, focus_covered=True):
        return ReviewResult(
            claims=[supported]
            + [ClaimReview(claim=fact, supported=False) for fact in unsupported],
            clarity=ClarityLevel.high,
            review_notes="Adequado ao público.",
            focus_covered=focus_covered,
        )

    return review


@pytest.fixture
def agents(monkeypatch, drafts):
    agents = Mock()
    agents.plan.return_value = planner.ContentPlan(
        items=[planner.PlanItem(topic="Criação de um branch", chunk_numbers=[1])]
    )
    agents.write.side_effect = drafts
    monkeypatch.setattr(planner, "plan_content", agents.plan)
    monkeypatch.setattr(writer, "write_content", agents.write)
    monkeypatch.setattr(reviewer, "review_content", agents.review)
    return agents


def test_publish_first_attempt(request_data, drafts, reviews, agents, caplog):
    approved = reviews()
    agents.review.side_effect = [approved]

    with caplog.at_level(logging.INFO, logger="app.services.generation_graph"):
        result = generate_content(request_data)

    assert agents.mock_calls == [
        call.plan(request_data),
        call.write(request_data, plan=agents.plan.return_value),
        call.review(
            generated=drafts[0],
            audience_level=request_data.audience_level,
            focus=request_data.focus,
            chunks=request_data.chunks,
        ),
    ]
    assert agents.plan.call_args.args[0] is request_data
    assert result.decision is Decision.publish
    assert result.attempts == 1
    assert result.generated is drafts[0]
    assert result.review is approved
    assert result.report == evaluate(approved, {request_data.chunks[0].chunk_id})
    assert result.error_message is None
    assert caplog.messages == ["decisão=publish tentativas=1 sustentadas=1 sem_apoio=0"]


def test_rewrite_passes_unsupported_claims_and_reuses_plan_and_chunks(
    request_data, drafts, reviews, agents
):
    write, review = agents.write, agents.review
    unsupported = ["Git exige acesso à internet.", "Git exige acesso de root."]
    approved = reviews()
    review.side_effect = [reviews(*unsupported), approved]

    result = generate_content(request_data)

    agents.plan.assert_called_once_with(request_data)
    plan = agents.plan.return_value
    assert write.call_args_list == [
        call(request_data, plan=plan),
        call(request_data, plan=plan, rewrite=Rewrite(drafts[0], unsupported)),
    ]
    assert all(write_call.kwargs["plan"] is plan for write_call in write.call_args_list)
    assert write.call_args.args[0] is request_data
    assert write.call_args.kwargs["rewrite"].previous is drafts[0]
    assert review.call_count == 2
    for review_call, draft in zip(review.call_args_list, drafts, strict=True):
        assert review_call.kwargs["generated"] is draft
        assert review_call.kwargs["chunks"] is request_data.chunks
        assert review_call.kwargs["focus"] == request_data.focus
        assert review_call.kwargs["audience_level"] is request_data.audience_level
    assert result.decision is Decision.publish
    assert result.attempts == 2
    assert result.generated is drafts[1]
    assert result.review is approved
    assert result.report == evaluate(approved, {request_data.chunks[0].chunk_id})
    assert result.error_message is None


def test_fail_if_rewritten_claim_is_unsupported(request_data, drafts, reviews, agents):
    write, review = agents.write, agents.review
    last_review = reviews("Git exige acesso de root.")
    review.side_effect = [reviews("Git exige acesso à internet."), last_review]

    result = generate_content(request_data)

    assert result.decision is Decision.fail
    assert result.attempts == write.call_count == review.call_count == 2
    assert result.generated is drafts[1]
    assert result.review is last_review
    expected_report = evaluate(last_review, {request_data.chunks[0].chunk_id})
    assert result.report == expected_report
    assert result.error_message == failure_message(expected_report)


def test_fail_immediately_if_focus_is_not_covered(request_data, reviews, agents):
    write, review = agents.write, agents.review
    review.side_effect = [reviews(focus_covered=False)]

    result = generate_content(request_data)

    assert result.decision is Decision.fail
    assert result.attempts == write.call_count == review.call_count == 1
    assert result.error_message == "O documento não trata do assunto pedido."


def test_plan_error_stops_before_first_write(request_data, agents):
    agents.plan.side_effect = llm.LLMError("falha P")

    result = generate_content(request_data)

    assert agents.mock_calls == [call.plan(request_data)]
    assert result.decision is Decision.fail
    assert result.attempts == 0
    assert result.error_message == "Não foi possível gerar o conteúdo. falha P"
    assert result.generated is result.review is result.report is None


def test_prompt_version_includes_all_agents():
    assert PROMPT_VERSION == "planeja-v1+escreve-v4+revisa-v3"


@pytest.mark.parametrize(
    "stage,attempt,review_count,version,error_type",
    [
        ("write", 1, 0, None, llm.LLMError),
        ("review", 1, 1, 0, llm.LLMError),
        ("review", 2, 2, 1, llm.LLMInvalidResponseError),
        ("write", 2, 1, 0, llm.LLMError),
    ],
)
def test_model_error_keeps_data_for_last_written_version(
    request_data,
    drafts,
    reviews,
    agents,
    caplog,
    stage,
    attempt,
    review_count,
    version,
    error_type,
):
    write, review = agents.write, agents.review
    first_review = reviews("Git exige acesso à internet.")
    error = error_type("falha X")
    if stage == "write":
        write.side_effect = [*drafts[: attempt - 1], error]
        review.side_effect = [first_review]
    else:
        review.side_effect = [*([first_review] if attempt == 2 else []), error]

    with caplog.at_level(logging.INFO, logger="app.services.generation_graph"):
        result = generate_content(request_data)

    assert result.decision is Decision.fail
    assert result.attempts == write.call_count == attempt
    assert review.call_count == review_count
    assert result.error_message == "Não foi possível gerar o conteúdo. falha X"
    assert result.generated is (drafts[version] if version is not None else None)
    if stage == "write" and attempt == 2:
        assert result.review is first_review
        assert result.report == evaluate(
            first_review, {request_data.chunks[0].chunk_id}
        )
        assert caplog.messages == [
            "decisão=fail tentativas=2 sustentadas=1 sem_apoio=1"
        ]
    else:
        assert result.review is None
        assert result.report is None
        assert caplog.messages == [f"decisão=fail tentativas={attempt}"]


def test_caller_error_propagates(request_data, agents):
    write, review = agents.write, agents.review
    error = ValueError("Pedido inválido.")
    write.side_effect = error

    with pytest.raises(ValueError) as raised:
        generate_content(request_data)

    assert raised.value is error
    write.assert_called_once_with(request_data, plan=agents.plan.return_value)
    review.assert_not_called()


def test_rewrite_reaches_writer_prompt(monkeypatch, request_data, drafts):
    unsupported = "Git exige acesso à internet."
    reviews = iter(
        _ReviewOut(
            focus_covered=True,
            claims=[claim],
            clarity=ClarityLevel.high,
            review_notes="Adequado ao público.",
        )
        for claim in (
            _ClaimOut(claim=unsupported, supported=False),
            _ClaimOut(
                claim=request_data.chunks[0].text, supported=True, chunk_number=1
            ),
        )
    )
    versions = iter(drafts)
    calls = []
    topic = "Criação de um branch"

    def generate_structured(*, response_model, prompt, **_kwargs):
        calls.append((response_model, prompt))
        if issubclass(response_model, planner.ContentPlan):
            return response_model.model_validate(
                {"items": [{"topic": topic, "chunk_numbers": [1]}]}
            )
        if response_model is GeneratedTutorial:
            return next(versions)
        assert response_model is _ReviewOut
        return next(reviews)

    monkeypatch.setattr(llm, "generate_structured", generate_structured)

    result = generate_content(request_data)

    assert result.decision is Decision.publish
    assert result.attempts == 2
    assert result.generated is drafts[1]
    assert issubclass(calls[0][0], planner.ContentPlan)
    assert [model for model, _ in calls[1:]] == [
        GeneratedTutorial,
        _ReviewOut,
        GeneratedTutorial,
        _ReviewOut,
    ]
    for _, prompt in (calls[1], calls[3]):
        assert f"Plano:\n1. {topic} (trechos 1)" in prompt
    assert unsupported in calls[3][1]
