import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import ClarityLevel
from app.services.grounding import (
    ClaimReview,
    Decision,
    ReviewResult,
    decide,
    evaluate,
    failure_message,
)


def review(claims: list[ClaimReview], *, focus_covered: bool = True) -> ReviewResult:
    return ReviewResult(
        claims=claims,
        clarity=ClarityLevel.high,
        review_notes="Claro",
        focus_covered=focus_covered,
    )


@pytest.mark.parametrize(
    "supported,total,focus_covered,score,first_decision,last_decision",
    [
        (12, 12, True, "1.00", Decision.publish, Decision.publish),
        (16, 18, True, "0.88", Decision.rewrite, Decision.fail),
        (8, 10, True, "0.80", Decision.rewrite, Decision.fail),
        (159, 200, True, "0.79", Decision.rewrite, Decision.fail),
        (10, 10, False, "1.00", Decision.fail, Decision.fail),
        (0, 0, True, "0.00", Decision.rewrite, Decision.fail),
    ],
)
def test_evaluate_and_decide(
    supported: int,
    total: int,
    focus_covered: bool,
    score: str,
    first_decision: Decision,
    last_decision: Decision,
) -> None:
    chunk = uuid.uuid4()
    claims = [
        ClaimReview(claim=str(i), supported=i < supported, chunk_id=chunk)
        for i in range(total)
    ]
    result = evaluate(review(claims, focus_covered=focus_covered), {chunk})
    assert result.score == Decimal(score)
    assert result.score.as_tuple().exponent == -2
    assert result.focus_covered is focus_covered
    assert result.passed is (first_decision == Decision.publish)
    assert result.supported == claims[:supported]
    assert result.unsupported == claims[supported:]
    assert decide(result, attempt=1) == first_decision
    assert decide(result, attempt=2) == last_decision
    assert decide(result, attempt=3) == last_decision
    if not focus_covered or not claims:
        assert failure_message(result) == "O documento não trata do assunto pedido."


def test_invalid_chunks_and_ordered_unique_citations() -> None:
    first, second, foreign = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    claims = [
        ClaimReview(claim="Primeira", supported=True, chunk_id=first),
        ClaimReview(claim="Sem trecho", supported=True),
        ClaimReview(claim="Trecho desconhecido", supported=True, chunk_id=foreign),
        ClaimReview(claim="Segunda", supported=True, chunk_id=second),
        ClaimReview(claim="Repetida", supported=True, chunk_id=first),
        ClaimReview(claim="Reprovada", supported=False, chunk_id=second),
    ]
    result = evaluate(review(claims), {first, second})
    assert result.supported == [claims[0], claims[3], claims[4]]
    assert result.unsupported == [claims[1], claims[2], claims[5]]
    assert result.cited_chunk_ids == [first, second]
    assert result.score == Decimal("0.50")
    assert not result.passed
    assert decide(result, attempt=1) == Decision.rewrite
    assert failure_message(result) == (
        "Afirmações sem apoio no documento:\nSem trecho\nTrecho desconhecido\nReprovada"
    )


@pytest.mark.parametrize(
    "invalid_chunk_id", [None, uuid.UUID(int=0)], ids=["missing", "unknown"]
)
def test_invalid_chunk_alone_blocks_publication(
    invalid_chunk_id: uuid.UUID | None,
) -> None:
    chunk = uuid.uuid4()
    claims = [
        ClaimReview(claim="Com citação válida", supported=True, chunk_id=chunk),
        ClaimReview(
            claim="Sem citação válida", supported=True, chunk_id=invalid_chunk_id
        ),
    ]
    result = evaluate(review(claims), {chunk})

    assert result.passed is False
    assert decide(result, attempt=1) == Decision.rewrite
    assert decide(result, attempt=2) == Decision.fail
    assert failure_message(result) == (
        "Afirmações sem apoio no documento:\nSem citação válida"
    )


@pytest.mark.parametrize("attempt", [0, -1])
@pytest.mark.parametrize(
    "focus_covered,supported", [(True, True), (True, False), (False, True)]
)
def test_invalid_attempt(attempt: int, focus_covered: bool, supported: bool) -> None:
    chunk = uuid.uuid4()
    result = evaluate(
        review(
            [ClaimReview(claim="Fato", supported=supported, chunk_id=chunk)],
            focus_covered=focus_covered,
        ),
        {chunk},
    )
    with pytest.raises(ValueError):
        decide(result, attempt=attempt)


def test_review_validates_model_response() -> None:
    with pytest.raises(ValidationError, match="focus_covered") as error:
        ReviewResult.model_validate(
            {"claims": [], "clarity": "high", "review_notes": "Claro"}
        )
    assert error.value.error_count() == 1
    with pytest.raises(ValidationError):
        ClaimReview.model_validate(
            {"claim": "Fato", "supported": True, "chunk_id": "invalid"}
        )
