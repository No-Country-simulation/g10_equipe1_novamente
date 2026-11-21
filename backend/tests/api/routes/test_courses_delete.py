from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import Session, col, select

from app.core.config import settings
from app.core.storage import InMemoryStorage, course_prefix, document_key, get_storage
from app.main import app
from app.models import (
    ContentCitation,
    Course,
    CourseContent,
    CourseObjectCleanup,
    DocumentChunk,
    SourceDocument,
)
from tests.utils.user import authentication_token_from_email, create_random_user

URL = f"{settings.API_V1_STR}/courses"


@pytest.fixture
def seed(client, db):
    owner = create_random_user(db)
    headers = authentication_token_from_email(client=client, email=owner.email, db=db)

    def create(status="succeeded"):
        response = client.post(
            f"{settings.API_V1_STR}/private/courses/",
            json={
                "owner_email": owner.email,
                "title": "Curso",
                "audience_level": "non_technical",
                "documents": [{"chunks": ["Trecho da fonte"]}],
                "contents": [
                    {
                        "format": "tutorial",
                        "status": status,
                        "content": {"summary": "Introdução"}
                        if status == "succeeded"
                        else None,
                        "cited_chunks": [0],
                    }
                ],
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    return create, headers


def test_delete_course_cascades_and_records_cleanup_without_storage(
    client, db, seed, monkeypatch
):
    create, headers = seed
    course = create()
    course_id = UUID(course["id"])
    monkeypatch.setattr(settings, "OCI_BUCKET", None)
    monkeypatch.setattr(settings, "OCI_NAMESPACE", None)

    response = client.delete(f"{URL}/{course_id}", headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{URL}/{course_id}", headers=headers).status_code == 404
    assert db.get(CourseObjectCleanup, course_id) is not None
    for model in (SourceDocument, DocumentChunk, CourseContent, ContentCitation):
        assert (
            db.exec(select(model).where(col(model.course_id) == course_id)).first()
            is None
        )


def test_delete_course_requires_owner_and_authentication(client, db, seed):
    create, headers = seed
    course_id = create()["id"]
    other = create_random_user(db)
    other_headers = authentication_token_from_email(
        client=client, email=other.email, db=db
    )
    assert client.delete(f"{URL}/{course_id}").status_code == 401
    for identifier, token in [(course_id, other_headers), (uuid4(), headers)]:
        response = client.delete(f"{URL}/{identifier}", headers=token)
        assert response.status_code == 404
        assert response.json()["detail"] == "Curso não encontrado."


@pytest.mark.parametrize("status", ["pending", "running"])
def test_delete_course_refuses_active_content(client, db, seed, status):
    create, headers = seed
    course_id = UUID(create(status)["id"])

    response = client.delete(f"{URL}/{course_id}", headers=headers)

    assert response.status_code == 409
    assert (
        response.json()["detail"] == "Espere a geração terminar para excluir o curso."
    )
    assert (
        client.get(f"{URL}/{course_id}", headers=headers).json()["contents"][0][
            "status"
        ]
        == status
    )
    assert db.get(CourseObjectCleanup, course_id) is None


def test_delete_course_rolls_back_after_commit_failure(client, db, seed, monkeypatch):
    create, headers = seed
    course = create()
    course_id = UUID(course["id"])
    key = document_key(course_id, UUID(course["documents"][0]["id"]), "md")
    storage = InMemoryStorage()
    storage.put(key, b"Trecho da fonte", "text/markdown")
    monkeypatch.setitem(app.dependency_overrides, get_storage, lambda: storage)

    def fail_commit(session):
        session.flush()
        raise RuntimeError("commit")

    with (
        patch.object(Session, "commit", fail_commit),
        pytest.raises(RuntimeError, match="commit"),
    ):
        client.delete(f"{URL}/{course_id}", headers=headers)

    assert db.get(Course, course_id) is not None
    assert db.get(CourseObjectCleanup, course_id) is None
    assert storage.list(course_prefix(course_id)) == [key]
