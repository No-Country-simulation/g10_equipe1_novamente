import logging
import uuid
from unittest.mock import Mock, call

import pytest

from app.core import llm
from app.models import AudienceLevel, ClarityLevel, ContentFormat
from app.services import reviewer, writer
from app.services.content_schemas import GeneratedTutorial
from app.services.generation_graph import generate_content
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
    write = Mock(side_effect=drafts)
    review = Mock()
    monkeypatch.setattr(writer, "write_content", write)
    monkeypatch.setattr(reviewer, "review_content", review)
    return write, review


def test_publish_first_attempt(request_data, drafts, reviews, agents, caplog):
    write, review = agents
    approved = reviews()
    review.side_effect = [approved]

    with caplog.at_level(logging.INFO, logger="app.services.generation_graph"):
        result = generate_content(request_data)

    write.assert_called_once_with(request_data)
    review.assert_called_once_with(
        generated=drafts[0],
        audience_level=request_data.audience_level,
        focus=request_data.focus,
        chunks=request_data.chunks,
    )
    assert result.decision is Decision.publish
    assert result.attempts == 1
    assert result.generated is drafts[0]
    assert result.review is approved
    assert result.report == evaluate(approved, {request_data.chunks[0].chunk_id})
    assert result.error_message is None
    assert caplog.messages == ["decisão=publish tentativas=1 sustentadas=1 sem_apoio=0"]


def test_rewrite_passes_unsupported_claims_and_reuses_chunks(
    request_data, drafts, reviews, agents
):
    write, review = agents
    unsupported = ["Git exige acesso à internet.", "Git exige acesso de root."]
    approved = reviews()
    review.side_effect = [reviews(*unsupported), approved]

    result = generate_content(request_data)

    assert write.call_args_list == [
        call(request_data),
        call(request_data, rewrite=Rewrite(drafts[0], unsupported)),
    ]
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
    write, review = agents
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
    write, review = agents
    review.side_effect = [reviews(focus_covered=False)]

    result = generate_content(request_data)

    assert result.decision is Decision.fail
    assert result.attempts == write.call_count == review.call_count == 1
    assert result.error_message == "O documento não trata do assunto pedido."


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
    write, review = agents
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
    write, review = agents
    error = ValueError("Pedido inválido.")
    write.side_effect = error

    with pytest.raises(ValueError) as raised:
        generate_content(request_data)

    assert raised.value is error
    write.assert_called_once_with(request_data)
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

    def generate_structured(*, response_model, prompt, **_kwargs):
        calls.append((response_model, prompt))
        if response_model is GeneratedTutorial:
            return next(versions)
        assert response_model is _ReviewOut
        return next(reviews)

    monkeypatch.setattr(llm, "generate_structured", generate_structured)

    result = generate_content(request_data)

    assert result.decision is Decision.publish
    assert result.attempts == 2
    assert result.generated is drafts[1]
    assert [model for model, _ in calls] == [
        GeneratedTutorial,
        _ReviewOut,
        GeneratedTutorial,
        _ReviewOut,
    ]
    assert unsupported in calls[2][1]
