import uuid
from dataclasses import replace
from decimal import Decimal
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from sqlmodel import select

from app.core.config import settings
from app.core.storage import InMemoryStorage, StorageError
from app.models import ContentCitation, Course, CourseContent, DocumentChunk
from app.services.content_schemas import ContentPackage, GeneratedTutorial
from app.services.grounding import ClaimReview, ReviewResult, evaluate
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
            similarity=0.9123 + row.chunk_index * 0.02,
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
    review = ReviewResult(
        claims=[
            ClaimReview(claim=chunk.text, supported=True, chunk_id=chunk.chunk_id)
            for chunk in chunks[:2]
        ],
        clarity="high",
        review_notes="Aprovado",
        focus_covered=True,
    )
    report = evaluate(review, {chunk.chunk_id for chunk in chunks})
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
    before = args["session"].get(CourseContent, args["content_id"])
    before.error_message = "Erro anterior"
    old_content_updated = before.updated_at
    course_before = args["session"].get(Course, course_id)
    old_course_updated = course_before.updated_at
    args["session"].commit()
    content = publish_content(**args)
    args["session"].refresh(content)
    key = content.oci_object_key
    package = ContentPackage.model_validate_json(args["storage"].get(key))
    assert package.model_dump(mode="json") == {
        "format": "tutorial",
        "audience_level": "technical_basic",
        "niche": "geral",
        "title": "Tutorial",
        "content": args["generated"].content.model_dump(mode="json"),
        "estimated_minutes": 5,
        "key_concepts": ["conceito"],
        "prerequisites": [],
        "grounding_score": 1.0,
        "clarity": "high",
        "review_notes": "Aprovado",
    }
    assert content.content == args["generated"].content.model_dump(mode="json")
    assert content.error_message is None
    assert content.updated_at > old_content_updated
    assert package.niche == "geral"
    course = args["session"].get(Course, course_id)
    assert course.updated_at > old_course_updated
    generated = args["generated"]
    assert package.format == content.format
    assert package.audience_level == course.audience_level
    assert content.status == "succeeded"
    assert content.title == generated.title
    assert content.estimated_minutes == generated.estimated_minutes
    assert content.key_concepts == generated.key_concepts
    assert content.prerequisites == generated.prerequisites
    assert content.grounding_score == Decimal("1.00")
    assert content.clarity == args["review"].clarity
    assert content.review_notes == args["review"].review_notes
    prefix = f"courses/{course_id}/contents/{content.id}/"
    assert key.startswith(prefix) and key.endswith(".json")
    uuid.UUID(key[len(prefix) : -5])
    assert args["session"].get(Course, course_id).status == "ready"
    citations = (
        args["session"]
        .exec(select(ContentCitation).where(ContentCitation.content_id == content.id))
        .all()
    )
    assert {c.chunk_id: c.similarity for c in citations} == {
        args["chunks"][0].chunk_id: Decimal("0.912"),
        args["chunks"][1].chunk_id: Decimal("0.932"),
    }
    response = client.get(
        f"/api/v1/courses/{course_id}", headers=normal_user_token_headers
    )
    assert response.status_code == 200
    assert {
        uuid.UUID(c["chunk_id"]) for c in response.json()["contents"][0]["citations"]
    } == {args["chunks"][0].chunk_id, args["chunks"][1].chunk_id}
    chunk = args["chunks"][2]
    args["review"] = args["review"].model_copy(
        update={
            "claims": [
                ClaimReview(claim=chunk.text, supported=True, chunk_id=chunk.chunk_id)
            ]
        }
    )
    args["report"] = evaluate(args["review"], {c.chunk_id for c in args["chunks"]})
    args["generated"].content.summary = "Novo resumo"
    content = publish_content(**args)
    assert content.content["summary"] == "Novo resumo"
    package = ContentPackage.model_validate_json(
        args["storage"].get(content.oci_object_key)
    )
    assert package.content["summary"] == "Novo resumo"
    assert package.grounding_score == 1.0
    assert content.grounding_score == Decimal("1.00")
    assert args["session"].get(Course, course_id).status == "ready"
    assert content.oci_object_key != key
    assert key not in args["storage"].list("")
    citations = (
        args["session"]
        .exec(select(ContentCitation).where(ContentCitation.content_id == content.id))
        .all()
    )
    assert {citation.chunk_id for citation in citations} == {args["chunks"][2].chunk_id}


def assert_unpublished(args):
    args["session"].expire_all()
    content = args["session"].get(CourseContent, args["content_id"])
    assert content.status == "pending"
    assert content.content is None and content.oci_object_key is None
    assert not args["storage"].list("")
    assert (
        not args["session"]
        .exec(select(ContentCitation).where(ContentCitation.content_id == content.id))
        .all()
    )


def test_validation_failures(publication):
    args, _ = publication
    report = args["report"]
    empty_review = args["review"].model_copy(update={"claims": []})
    args["report"] = evaluate(empty_review, {c.chunk_id for c in args["chunks"]})
    with pytest.raises(ValueError):
        publish_content(**args)
    assert_unpublished(args)
    args["report"] = replace(report, cited_chunk_ids=[uuid.uuid4()])
    with pytest.raises(ValueError):
        publish_content(**args)
    assert_unpublished(args)
    args["report"] = report
    args["review"].review_notes = ""
    with pytest.raises(ValidationError):
        publish_content(**args)
    assert_unpublished(args)


def test_storage_and_commit_failures(publication):
    args, _ = publication
    with patch.object(args["storage"], "put", side_effect=StorageError):
        with pytest.raises(PublishError, match="armazenamento"):
            publish_content(**args)
    assert_unpublished(args)
    with patch.object(args["session"], "commit", side_effect=RuntimeError):
        with pytest.raises(PublishError, match="publicar"):
            publish_content(**args)
    assert_unpublished(args)


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
    assert_unpublished(args)
    content = args["session"].get(CourseContent, args["content_id"])
    content.format = "tutorial"
    course = args["session"].get(Course, course_id)
    course.status = "failed"
    args["session"].commit()
    publish_content(**args)
    assert course.status == "ready"


def test_old_object_delete_failure(publication, caplog):
    args, course_id = publication
    old = publish_content(**args).oci_object_key
    with patch.object(args["storage"], "delete", side_effect=StorageError) as delete:
        content = publish_content(**args)
    assert content.status == "succeeded"
    assert content.oci_object_key != old
    assert delete.call_count == 2
    assert str(course_id) in caplog.text
