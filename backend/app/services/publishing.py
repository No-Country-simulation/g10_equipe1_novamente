import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from sqlalchemy import delete
from sqlmodel import Session, col

from app.core.storage import Storage, content_key
from app.models import (
    ContentCitation,
    Course,
    CourseContent,
    CourseStatus,
    GenerationStatus,
    Niche,
)
from app.services.content_schemas import (
    GENERATED_MODELS,
    ContentPackage,
    GeneratedBase,
    GeneratedFlashcards,
    GeneratedQuiz,
    GeneratedTutorial,
)
from app.services.grounding import GroundingReport, ReviewResult
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class ContentNotFoundError(LookupError): ...


class PublishError(Exception):
    """A mensagem é um texto para course_content.error_message."""


def publish_content(
    *,
    session: Session,
    storage: Storage,
    content_id: uuid.UUID,
    generated: GeneratedBase,
    review: ReviewResult,
    report: GroundingReport,
    chunks: Sequence[RetrievedChunk],
) -> CourseContent:
    content = session.get(CourseContent, content_id)
    if content is None:
        raise ContentNotFoundError(content_id)
    if not report.passed:
        raise ValueError("O conteúdo não foi aprovado.")
    if not isinstance(generated, GENERATED_MODELS[content.format]):
        raise ValueError("O formato do conteúdo não corresponde à geração.")
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    if any(chunk_id not in by_id for chunk_id in report.cited_chunk_ids):
        raise ValueError("Um chunk citado não foi encontrado.")
    course = session.get_one(Course, content.course_id)
    niche = session.get_one(Niche, course.niche_id)
    package = ContentPackage(
        format=content.format,
        audience_level=course.audience_level,
        niche=niche.slug,
        title=generated.title,
        content=cast(
            GeneratedTutorial | GeneratedFlashcards | GeneratedQuiz, generated
        ).content.model_dump(mode="json"),
        estimated_minutes=generated.estimated_minutes,
        key_concepts=generated.key_concepts,
        prerequisites=generated.prerequisites,
        grounding_score=float(report.score),
        clarity=review.clarity,
        review_notes=review.review_notes,
    )
    key = content_key(course.id, content.id)
    old_key = content.oci_object_key
    try:
        storage.put(key, package.model_dump_json().encode(), "application/json")
    except Exception as exc:
        raise PublishError(
            "Não foi possível guardar o conteúdo no armazenamento."
        ) from exc
    try:
        content.title = package.title
        content.content = package.content
        content.estimated_minutes = package.estimated_minutes
        content.key_concepts = package.key_concepts
        content.prerequisites = package.prerequisites
        content.grounding_score = report.score
        content.clarity = package.clarity
        content.review_notes = package.review_notes
        content.oci_object_key = key
        content.status = GenerationStatus.succeeded
        content.error_message = None
        content.updated_at = datetime.now(UTC)
        session.exec(
            delete(ContentCitation).where(col(ContentCitation.content_id) == content.id)
        )
        for chunk_id in report.cited_chunk_ids:
            session.add(
                ContentCitation(
                    course_id=course.id,
                    content_id=content.id,
                    chunk_id=chunk_id,
                    similarity=Decimal(str(by_id[chunk_id].similarity)).quantize(
                        Decimal("0.001")
                    ),
                )
            )
        if course.status != CourseStatus.ready:
            course.status = CourseStatus.ready
            course.updated_at = datetime.now(UTC)
        session.add(content)
        session.add(course)
        session.commit()
    except Exception as exc:
        session.rollback()
        try:
            storage.delete(key)
        except Exception as cleanup_error:
            logger.error(
                "Falha ao apagar objeto novo: course_id=%s key=%s erro=%s",
                content.course_id,
                key,
                type(cleanup_error).__name__,
            )
        raise PublishError("Não foi possível publicar o conteúdo.") from exc
    if old_key:
        for attempt in range(2):
            try:
                storage.delete(old_key)
                break
            except Exception as exc:
                if attempt == 1:
                    logger.error(
                        "Falha ao apagar objeto antigo: course_id=%s key=%s erro=%s",
                        course.id,
                        old_key,
                        type(exc).__name__,
                    )
    return content
