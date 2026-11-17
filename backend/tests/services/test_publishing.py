import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from sqlmodel import select

from app.core.config import settings
from app.core.storage import InMemoryStorage, StorageError
from app.models import ContentCitation, Course, CourseContent, DocumentChunk
from app.services.content_schemas import ContentPackage, GeneratedTutorial
from app.services.grounding import GroundingReport, ReviewResult
from app.services.publishing import ContentNotFoundError, PublishError, publish_content
from app.services.retrieval import RetrievedChunk
from tests.utils.course import create_course


@pytest.fixture
def publication(client, db, normal_user_token_headers):  # noqa: ARG001
    data = create_course(
        client=client,
        owner_email=settings.EMAIL_TEST_USER,
        status="initializing",
        documents=[{"chunks": ["um", "dois", "três"]}],
        contents=[{"format": "tutorial", "status": "pending"}],
    )
    course_id = uuid.UUID(data["id"])
    content_id = uuid.UUID(data["contents"][0]["id"])
    rows = db.exec(
        select(DocumentChunk)
        .where(DocumentChunk.course_id == course_id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    chunks = [
        RetrievedChunk(
            chunk_id=row.id,
            document_id=row.document_id,
            chunk_index=row.chunk_index,
            text=row.text,
            page_number=row.page_number,
            similarity=0.9123,
        )
        for row in rows
    ]
    generated = GeneratedTutorial.model_validate(
        {
            "title": "Tutorial",
            "estimated_minutes": 5,
            "key_concepts": ["conceito"],
            "prerequisites": [],
            "content": {
                "summary": "Resumo",
                "sections": [{"title": "Seção", "body": "Texto"}],
                "takeaways": ["Item"],
            },
        }
    )
    review = ReviewResult(claims=[], clarity="high", review_notes="Aprovado")
    report = GroundingReport(
        score=Decimal("0.90"),
        passed=True,
        supported=[],
        unsupported=[],
        cited_chunk_ids=[chunks[0].chunk_id, chunks[1].chunk_id],
    )
    return {
        "session": db,
        "storage": InMemoryStorage(),
        "content_id": content_id,
        "generated": generated,
        "review": review,
        "report": report,
        "chunks": chunks,
    }, course_id


def test_publish_and_regenerate(publication, client, normal_user_token_headers):
    args, course_id = publication
    content = publish_content(**args)
    key = content.oci_object_key
    package = ContentPackage.model_validate_json(args["storage"].get(key))
    assert package.content == content.content
    assert package.niche == "geral"
    assert key.startswith(f"courses/{course_id}/contents/{content.id}/")
    assert args["session"].get(Course, course_id).status == "ready"
    citations = (
        args["session"]
        .exec(select(ContentCitation).where(ContentCitation.content_id == content.id))
        .all()
    )
    assert len(citations) == 2
    assert all(c.similarity == Decimal("0.912") for c in citations)
    response = client.get(
        f"/api/v1/courses/{course_id}", headers=normal_user_token_headers
    )
    assert response.status_code == 200
    assert len(response.json()["contents"][0]["citations"]) == 2
    args["report"] = GroundingReport(
        score=Decimal("1"),
        passed=True,
        supported=[],
        unsupported=[],
        cited_chunk_ids=[args["chunks"][2].chunk_id],
    )
    content = publish_content(**args)
    assert content.oci_object_key != key
    assert key not in args["storage"].list("")
    assert (
        len(
            args["session"]
            .exec(
                select(ContentCitation).where(ContentCitation.content_id == content.id)
            )
            .all()
        )
        == 1
    )


def test_validation_failures(publication):
    args, _ = publication
    report = args["report"]
    args["report"] = GroundingReport(
        score=Decimal("0"),
        passed=False,
        supported=[],
        unsupported=[],
        cited_chunk_ids=[],
    )
    with pytest.raises(ValueError):
        publish_content(**args)
    args["report"] = GroundingReport(
        score=report.score,
        passed=True,
        supported=[],
        unsupported=[],
        cited_chunk_ids=[uuid.uuid4()],
    )
    with pytest.raises(ValueError):
        publish_content(**args)
    args["report"] = report
    args["review"].review_notes = ""
    with pytest.raises(ValidationError):
        publish_content(**args)
    assert not args["storage"].list("")
    assert args["session"].get(CourseContent, args["content_id"]).status == "pending"


def test_storage_and_commit_failures(publication):
    args, _ = publication
    with patch.object(args["storage"], "put", side_effect=StorageError):
        with pytest.raises(PublishError, match="armazenamento"):
            publish_content(**args)
    with patch.object(args["session"], "commit", side_effect=RuntimeError):
        with pytest.raises(PublishError, match="publicar"):
            publish_content(**args)
    assert not args["storage"].list("")
    assert args["session"].get(CourseContent, args["content_id"]).status == "pending"


def test_missing_content(publication):
    args, _ = publication
    args["content_id"] = uuid.uuid4()
    with pytest.raises(ContentNotFoundError):
        publish_content(**args)


def test_wrong_format_and_failed_course(publication):
    args, course_id = publication
    content = args["session"].get(CourseContent, args["content_id"])
    content.format = "quiz"
    args["session"].commit()
    with pytest.raises(ValueError):
        publish_content(**args)
    assert not args["storage"].list("")
    content.format = "tutorial"
    course = args["session"].get(Course, course_id)
    course.status = "failed"
    args["session"].commit()
    publish_content(**args)
    assert course.status == "ready"


def test_old_object_delete_failure(publication, caplog):
    args, course_id = publication
    publish_content(**args)
    with patch.object(args["storage"], "delete", side_effect=StorageError) as delete:
        publish_content(**args)
    assert delete.call_count == 2
    assert str(course_id) in caplog.text
