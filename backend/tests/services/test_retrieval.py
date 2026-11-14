import math
import uuid
from collections.abc import Generator

import pytest
from sqlmodel import Session, select

from app.models import (
    AudienceLevel,
    Course,
    DocumentChunk,
    DocumentStatus,
    Niche,
    SourceDocument,
    User,
)
from app.services.retrieval import CourseNotFoundError, search_chunks

MODEL = "gemini-embedding-2"


def unit(*positions: int) -> list[float]:
    vector = [0.0] * 768
    for position in positions:
        vector[position] = 1.0
    return vector


E0, E1, E0_E1 = unit(0), unit(1), unit(0, 1)


@pytest.fixture(autouse=True)
def rollback(db: Session) -> Generator[None]:
    yield
    db.rollback()


def make_user(db: Session) -> User:
    user = User(email=f"{uuid.uuid4()}@example.com", hashed_password="hash")
    db.add(user)
    db.flush()
    return user


def make_course(db: Session, owner: User) -> Course:
    niche = db.exec(select(Niche).where(Niche.slug == "geral")).one()
    assert niche.id is not None
    course = Course(
        owner_id=owner.id,
        niche_id=niche.id,
        title="Course",
        audience_level=AudienceLevel.non_technical,
    )
    db.add(course)
    db.flush()
    return course


def make_document(
    db: Session,
    course: Course,
    embeddings: list[list[float]],
    *,
    status: DocumentStatus = DocumentStatus.indexed,
    embedding_model: str = MODEL,
) -> list[DocumentChunk]:
    document = SourceDocument(
        course_id=course.id,
        title="Document",
        original_filename="a.md",
        mime_type="text/markdown",
        size_bytes=1,
        sha256=uuid.uuid4().hex * 2,
        oci_object_key=str(uuid.uuid4()),
        status=status,
        embedding_model=embedding_model,
    )
    db.add(document)
    db.flush()
    chunks = [
        DocumentChunk(
            document_id=document.id,
            course_id=course.id,
            chunk_index=index,
            text=f"Text {index}",
            page_number=index + 1,
            embedding=embedding,
        )
        for index, embedding in enumerate(embeddings)
    ]
    db.add_all(chunks)
    db.flush()
    return chunks


def search(
    db: Session, course: Course, owner: User, limit: int | None = None
) -> list[uuid.UUID]:
    kwargs = {} if limit is None else {"limit": limit}
    return [
        chunk.chunk_id
        for chunk in search_chunks(
            session=db,
            course_id=course.id,
            owner_id=owner.id,
            query_embedding=E0,
            embedding_model=MODEL,
            **kwargs,
        )
    ]


def test_orders_by_similarity(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)
    a, b, c = make_document(db, course, [E0, E1, E0_E1])

    result = search_chunks(
        session=db,
        course_id=course.id,
        owner_id=user.id,
        query_embedding=E0,
        embedding_model=MODEL,
    )

    assert [chunk.chunk_id for chunk in result] == [a.id, c.id, b.id]
    assert [chunk.similarity for chunk in result] == [
        1.0,
        round(1 / math.sqrt(2), 3),
        0.0,
    ]
    first = result[0]
    assert (first.document_id, first.chunk_index, first.text, first.page_number) == (
        a.document_id,
        0,
        "Text 0",
        1,
    )


def test_ties_follow_chunk_index_then_chunk_id(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)
    first = make_document(db, course, [E1, E0, E0])
    second = make_document(db, course, [E0])

    assert search(db, course, user, limit=2) == [second[0].id, first[1].id]
    assert search(db, course, user) == [
        second[0].id,
        first[1].id,
        first[2].id,
        first[0].id,
    ]

    tied = make_course(db, user)
    left = make_document(db, tied, [E0])
    right = make_document(db, tied, [E0])
    same_index = sorted([left[0].id, right[0].id])
    assert search(db, tied, user) == same_index


def test_limit(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)
    make_document(db, course, [E0] * 9)

    assert len(search(db, course, user)) == 8
    assert len(search(db, course, user, limit=2)) == 2


@pytest.mark.parametrize(
    "status",
    [DocumentStatus.uploaded, DocumentStatus.processing, DocumentStatus.failed],
)
def test_skips_document_not_indexed(db: Session, status: DocumentStatus) -> None:
    user = make_user(db)
    course = make_course(db, user)
    (indexed,) = make_document(db, course, [E1])
    make_document(db, course, [E0], status=status)

    assert search(db, course, user) == [indexed.id]


def test_skips_other_embedding_model(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)
    (same_model,) = make_document(db, course, [E1])
    make_document(db, course, [E0], embedding_model="other-model")

    assert search(db, course, user) == [same_model.id]


def test_skips_other_course_of_same_owner(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)
    (own,) = make_document(db, course, [E1])
    make_document(db, make_course(db, user), [E0])

    assert search(db, course, user) == [own.id]


def test_other_owner_and_unknown_course_raise(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)
    make_document(db, course, [E0])

    with pytest.raises(CourseNotFoundError):
        search(db, course, make_user(db))
    with pytest.raises(CourseNotFoundError):
        search_chunks(
            session=db,
            course_id=uuid.uuid4(),
            owner_id=user.id,
            query_embedding=E0,
            embedding_model=MODEL,
        )


def test_wrong_dimension_raises(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)

    with pytest.raises(ValueError):
        search_chunks(
            session=db,
            course_id=course.id,
            owner_id=user.id,
            query_embedding=[1.0] * 767,
            embedding_model=MODEL,
        )


def test_course_without_indexed_documents_returns_empty(db: Session) -> None:
    user = make_user(db)
    course = make_course(db, user)
    make_document(db, course, [E0], status=DocumentStatus.uploaded)

    assert search(db, course, user) == []
