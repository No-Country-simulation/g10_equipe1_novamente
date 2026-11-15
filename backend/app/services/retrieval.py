import uuid
from collections.abc import Sequence
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.orm import defer
from sqlmodel import Session, select

from app.models import Course, DocumentChunk, DocumentStatus, SourceDocument

EMBEDDING_DIMENSIONS = 768


class CourseNotFoundError(LookupError): ...


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    page_number: int | None
    similarity: float


def search_chunks(
    *,
    session: Session,
    course_id: uuid.UUID,
    owner_id: uuid.UUID,
    query_embedding: Sequence[float],
    embedding_model: str,
    limit: int = 8,
) -> list[RetrievedChunk]:
    if len(query_embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"query_embedding tem {len(query_embedding)} valores, "
            f"esperado {EMBEDDING_DIMENSIONS}"
        )

    chunk = sa.inspect(DocumentChunk).columns
    document = sa.inspect(SourceDocument).columns
    course = sa.inspect(Course).columns

    distance = chunk.embedding.cosine_distance(list(query_embedding))
    # A ordem usa o valor arredondado, o mesmo que quem chama recebe. Assim o
    # desempate por chunk_index vale para similaridades iguais no resultado.
    similarity = sa.func.greatest(
        -1, sa.func.least(1, sa.func.round(sa.cast(1 - distance, sa.Numeric), 3))
    )
    eligible = sa.join(
        DocumentChunk,
        SourceDocument,
        sa.and_(
            document.id == chunk.document_id,
            document.status == DocumentStatus.indexed,
            document.embedding_model == embedding_model,
        ),
    )
    # O LEFT JOIN separa os dois casos em uma consulta: nenhuma linha quer
    # dizer curso inexistente ou de outro dono, e uma linha sem chunk quer
    # dizer curso sem chunk elegível.
    statement = (
        select(DocumentChunk, similarity)
        .select_from(sa.outerjoin(Course, eligible, chunk.course_id == course.id))
        .where(course.id == course_id, course.owner_id == owner_id)
        .options(defer(sa.inspect(DocumentChunk).attrs.embedding.class_attribute))
        .order_by(similarity.desc(), chunk.chunk_index, chunk.id)
        .limit(limit)
    )
    rows = session.exec(statement).all()
    if not rows:
        raise CourseNotFoundError(f"Curso {course_id} não encontrado")
    return [
        RetrievedChunk(
            chunk_id=found.id,
            document_id=found.document_id,
            chunk_index=found.chunk_index,
            text=found.text,
            page_number=found.page_number,
            similarity=float(value),
        )
        for found, value in rows
        if found is not None
    ]
