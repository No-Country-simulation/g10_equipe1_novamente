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


def review(claims: list[ClaimReview]) -> ReviewResult:
    return ReviewResult(claims=claims, clarity=ClarityLevel.high, review_notes="Claro")


@pytest.mark.parametrize(
    "supported,total,score,passed",
    [
        (8, 10, "0.80", True),
        (7, 10, "0.70", False),
        (159, 200, "0.79", False),
        (0, 0, "0.00", False),
        (1, 3, "0.33", False),
        (3, 3, "1.00", True),
    ],
)
def test_evaluate_and_decide(
    supported: int, total: int, score: str, passed: bool
) -> None:
    chunk = uuid.uuid4()
    claims = [
        ClaimReview(claim=str(i), supported=i < supported, chunk_id=chunk)
        for i in range(total)
    ]
    result = evaluate(review(claims), {chunk})
    assert result.score == Decimal(score)
    assert result.score.as_tuple().exponent == -2
    assert result.passed is passed
    assert result.supported == claims[:supported]
    assert result.unsupported == claims[supported:]
    for attempt in (1, 2, 3):
        expected = (
            Decision.publish
            if passed
            else (Decision.rewrite if attempt == 1 else Decision.fail)
        )
        assert decide(result, attempt=attempt) == expected


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
    assert failure_message(result) == (
        "Afirmações sem apoio no documento:\nSem trecho\nTrecho desconhecido\nReprovada"
    )


def test_empty_review_never_passes() -> None:
    result = evaluate(review([]), set(), min_score=Decimal("0"))
    assert not result.passed
    assert result.cited_chunk_ids == []
    assert failure_message(result) == "O documento não trata do assunto pedido."


def test_custom_threshold_uses_fraction_before_rounding() -> None:
    chunk = uuid.uuid4()
    result = evaluate(
        review(
            [
                ClaimReview(claim=str(i), supported=i < 2, chunk_id=chunk)
                for i in range(3)
            ]
        ),
        {chunk},
        min_score=Decimal("0.665"),
    )
    assert result.score == Decimal("0.66")
    assert result.passed


@pytest.mark.parametrize("attempt", [0, -1])
@pytest.mark.parametrize("passed", [True, False])
def test_invalid_attempt(attempt: int, passed: bool) -> None:
    chunk = uuid.uuid4()
    result = evaluate(
        review([ClaimReview(claim="Fato", supported=passed, chunk_id=chunk)]), {chunk}
    )
    with pytest.raises(ValueError):
        decide(result, attempt=attempt)


def test_review_validates_model_response() -> None:
    with pytest.raises(ValidationError):
        ReviewResult.model_validate(
            {"claims": [], "clarity": "invalid", "review_notes": ""}
        )
    with pytest.raises(ValidationError):
        ClaimReview.model_validate(
            {"claim": "Fato", "supported": True, "chunk_id": "invalid"}
        )
