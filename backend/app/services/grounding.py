import uuid
from collections.abc import Set
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from enum import StrEnum

from pydantic import BaseModel

from app.models import ClarityLevel

MIN_GROUNDING_SCORE = Decimal("0.80")
MAX_ATTEMPTS = 2


class ClaimReview(BaseModel):
    claim: str
    supported: bool
    chunk_id: uuid.UUID | None = None


class ReviewResult(BaseModel):
    claims: list[ClaimReview]
    clarity: ClarityLevel
    review_notes: str


class Decision(StrEnum):
    publish = "publish"
    rewrite = "rewrite"
    fail = "fail"


@dataclass(frozen=True, slots=True)
class GroundingReport:
    score: Decimal
    passed: bool
    supported: list[ClaimReview]
    unsupported: list[ClaimReview]
    cited_chunk_ids: list[uuid.UUID]


def evaluate(
    review: ReviewResult,
    valid_chunk_ids: Set[uuid.UUID],
    *,
    min_score: Decimal = MIN_GROUNDING_SCORE,
) -> GroundingReport:
    supported = []
    unsupported = []
    citations: dict[uuid.UUID, None] = {}
    for claim in review.claims:
        if claim.supported and claim.chunk_id in valid_chunk_ids:
            supported.append(claim)
            if claim.chunk_id is not None:
                citations[claim.chunk_id] = None
        else:
            unsupported.append(claim)

    total = len(review.claims)
    score = Decimal(len(supported)) / Decimal(total) if total else Decimal(0)
    # Compare por multiplicação para não arredondar a fração na decisão.
    passed = bool(total) and Decimal(len(supported)) >= min_score * total
    return GroundingReport(
        score=score.quantize(Decimal("0.01"), rounding=ROUND_FLOOR),
        passed=passed,
        supported=supported,
        unsupported=unsupported,
        cited_chunk_ids=list(citations),
    )


def decide(report: GroundingReport, *, attempt: int) -> Decision:
    if attempt < 1:
        raise ValueError("A tentativa deve começar em 1.")
    if report.passed:
        return Decision.publish
    return Decision.rewrite if attempt < MAX_ATTEMPTS else Decision.fail


def failure_message(report: GroundingReport) -> str:
    if not report.supported and not report.unsupported:
        return "O documento não trata do assunto pedido."
    return "\n".join(
        ["Afirmações sem apoio no documento:"]
        + [claim.claim for claim in report.unsupported]
    )
