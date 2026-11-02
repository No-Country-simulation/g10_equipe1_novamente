import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import (
    AudienceLevel,
    ContentCitation,
    ContentFormat,
    Course,
    CourseContent,
    DocumentChunk,
    GenerationStatus,
    Niche,
    SourceDocument,
    User,
)


def graph(
    db: Session,
) -> tuple[User, Course, SourceDocument, DocumentChunk, CourseContent, ContentCitation]:
    user = User(email=f"{uuid.uuid4()}@example.com", hashed_password="hash")
    db.add(user)
    db.flush()
    niche = db.exec(select(Niche).where(Niche.slug == "geral")).one()
    assert niche.id is not None
    course = Course(
        owner_id=user.id,
        niche_id=niche.id,
        title="Course",
        audience_level=AudienceLevel.non_technical,
    )
    db.add(course)
    db.flush()
    document = SourceDocument(
        course_id=course.id,
        title="Document",
        original_filename="a.txt",
        mime_type="text/plain",
        size_bytes=1,
        sha256="a" * 64,
        oci_object_key=str(uuid.uuid4()),
    )
    db.add(document)
    db.flush()
    chunk = DocumentChunk(
        document_id=document.id,
        course_id=course.id,
        chunk_index=0,
        text="Text",
        embedding=[0.1] * 768,
    )
    content = CourseContent(
        course_id=course.id, format=ContentFormat.tutorial, focus="Focus"
    )
    db.add_all([chunk, content])
    db.flush()
    citation = ContentCitation(
        course_id=course.id, content_id=content.id, chunk_id=chunk.id
    )
    db.add(citation)
    db.flush()
    return user, course, document, chunk, content, citation


def test_niche_seed(db: Session) -> None:
    assert set(db.exec(select(Niche.slug)).all()) >= {
        "fintech",
        "saude",
        "e-commerce",
        "geral",
    }


def test_course_graph_round_trip(db: Session) -> None:
    records = graph(db)
    db.expire_all()
    for record in records[:5]:
        assert db.get(type(record), record.id) is not None
    chunk = db.get(DocumentChunk, records[3].id)
    assert chunk is not None
    assert chunk.text == "Text"
    assert len(chunk.embedding) == 768
    assert db.get(ContentCitation, (records[4].id, records[3].id)) is not None
    db.rollback()


def test_chunk_rejects_other_course(db: Session) -> None:
    _, _, document, _, _, _ = graph(db)
    _, other, _, _, _, _ = graph(db)
    db.add(
        DocumentChunk(
            document_id=document.id,
            course_id=other.id,
            chunk_index=1,
            text="Text",
            embedding=[0.1] * 768,
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_citation_rejects_other_course(db: Session) -> None:
    _, course, _, _, content, _ = graph(db)
    _, _, _, chunk, _, _ = graph(db)
    db.add(
        ContentCitation(course_id=course.id, content_id=content.id, chunk_id=chunk.id)
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_succeeded_content_requires_published(db: Session) -> None:
    _, course, _, _, _, _ = graph(db)
    db.add(
        CourseContent(
            course_id=course.id,
            format=ContentFormat.tutorial,
            focus="Focus",
            status=GenerationStatus.succeeded,
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_delete_user_cascades(db: Session) -> None:
    user, course, document, chunk, content, citation = graph(db)
    ids = (
        course.id,
        document.id,
        chunk.id,
        content.id,
        (citation.content_id, citation.chunk_id),
    )
    db.execute(text('DELETE FROM "user" WHERE id = :id'), {"id": user.id})
    db.expire_all()
    for model, key in zip(
        (Course, SourceDocument, DocumentChunk, CourseContent, ContentCitation),
        ids,
        strict=True,
    ):
        assert db.get(model, key) is None
    db.rollback()


def test_niche_in_use_cannot_be_deleted(db: Session) -> None:
    graph(db)
    niche = db.exec(select(Niche).where(Niche.slug == "geral")).one()
    with pytest.raises(IntegrityError):
        db.delete(niche)
        db.flush()
    db.rollback()


def test_schema_matches_erd(db: Session) -> None:
    checks = dict(
        db.execute(
            text(
                "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE contype = 'c' AND connamespace = 'public'::regnamespace"
            )
        ).all()
    )
    assert checks == {
        "ck_content_citation_cosine_similarity": "CHECK (((similarity IS NULL) OR ((similarity >= ('-1'::integer)::numeric) AND (similarity <= (1)::numeric))))",
        "ck_course_content_body_json": "CHECK (((content IS NULL) OR (jsonb_typeof(content) = 'object'::text)))",
        "ck_course_content_focus_nonempty": "CHECK ((length(btrim(focus)) > 0))",
        "ck_course_content_grounding": "CHECK (((grounding_score IS NULL) OR ((grounding_score >= (0)::numeric) AND (grounding_score <= (1)::numeric))))",
        "ck_course_content_key_concepts_array": "CHECK (((key_concepts IS NULL) OR (jsonb_typeof(key_concepts) = 'array'::text)))",
        "ck_course_content_minutes": "CHECK (((estimated_minutes IS NULL) OR (estimated_minutes > 0)))",
        "ck_course_content_position": 'CHECK (("position" >= 0))',
        "ck_course_content_prerequisites_array": "CHECK (((prerequisites IS NULL) OR (jsonb_typeof(prerequisites) = 'array'::text)))",
        "ck_course_content_published_pair": "CHECK (((content IS NULL) = (oci_object_key IS NULL)))",
        "ck_course_content_successful_published": "CHECK (((status <> 'succeeded'::generation_status) OR ((content IS NOT NULL) AND (oci_object_key IS NOT NULL))))",
        "ck_document_chunk_page": "CHECK (((page_number IS NULL) OR (page_number >= 1)))",
        "ck_document_chunk_position": "CHECK ((chunk_index >= 0))",
        "ck_document_chunk_text_nonempty": "CHECK ((length(btrim(text)) > 0))",
        "ck_document_chunk_tokens": "CHECK (((token_count IS NULL) OR (token_count > 0)))",
        "ck_source_document_sha256_hex": "CHECK ((sha256 ~ '^[0-9a-f]{64}$'::text))",
        "ck_source_document_size_positive": "CHECK ((size_bytes > 0))",
    }
    enums: dict[str, list[str]] = {}
    for name, value in db.execute(
        text(
            "SELECT t.typname, e.enumlabel FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid WHERE t.typnamespace = 'public'::regnamespace ORDER BY t.typname, e.enumsortorder"
        )
    ):
        enums.setdefault(name, []).append(value)
    assert enums == {
        "audience_level": ["non_technical", "technical_basic", "technical_advanced"],
        "content_format": ["tutorial", "flashcards", "quiz"],
        "document_status": ["uploaded", "processing", "indexed", "failed"],
        "generation_status": ["pending", "running", "succeeded", "failed"],
        "clarity_level": ["low", "medium", "high"],
        "course_status": ["initializing", "ready", "failed"],
    }
    defaults = {
        (table, column): default
        for table, column, default in db.execute(
            text(
                "SELECT table_name, column_name, column_default FROM information_schema.columns WHERE table_schema='public'"
            )
        )
    }
    for key, expected in {
        ("user", "is_active"): "true",
        ("course", "status"): "initializing",
        ("source_document", "status"): "uploaded",
        ("source_document", "embedding_model"): "gemini-embedding-2",
        ("course_content", "status"): "pending",
        ("course_content", "position"): "0",
        **{
            (table, column): "now()"
            for table, columns in {
                "course": ("created_at", "updated_at"),
                "source_document": ("created_at",),
                "course_content": ("created_at", "updated_at"),
            }.items()
            for column in columns
        },
    }.items():
        assert expected in defaults[key]
    indexes = {
        (table, definition)
        for table, definition in db.execute(
            text("SELECT tablename, indexdef FROM pg_indexes WHERE schemaname='public'")
        )
    }
    for table, columns in [
        ("source_document", "id, course_id"),
        ("document_chunk", "id, course_id"),
        ("course_content", "id, course_id"),
        ("source_document", "course_id, sha256"),
        ("document_chunk", "document_id, chunk_index"),
    ]:
        assert any(
            t == table and "UNIQUE INDEX" in definition and f"({columns})" in definition
            for t, definition in indexes
        )
