from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from tests.utils.course import create_course
from tests.utils.user import create_random_user


def test_create_user(client: TestClient, db: Session) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": "pollo@listo.com",
            "password": "password123",
            "full_name": "Pollo Listo",
        },
    )

    assert r.status_code == 200

    data = r.json()

    user = db.exec(select(User).where(User.id == data["id"])).first()

    assert user
    assert user.email == "pollo@listo.com"
    assert user.full_name == "Pollo Listo"


def test_seed_creates_initializing_course_with_pending_content(
    client: TestClient, db: Session
) -> None:
    user = create_random_user(db)

    response = client.post(
        f"{settings.API_V1_STR}/private/courses/",
        json={
            "owner_email": user.email,
            "title": "Curso inicializando",
            "audience_level": "non_technical",
            "status": "initializing",
            "documents": [{"chunks": []}],
            "contents": [{"format": "tutorial", "status": "pending"}],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "initializing"
    assert data["contents"][0]["status"] == "pending"
    assert data["contents"][0]["content"] is None


def test_seed_creates_ready_course_with_citations(
    client: TestClient, db: Session
) -> None:
    user = create_random_user(db)

    course = create_course(client=client, owner_email=user.email)

    assert course["status"] == "ready"
    assert course["contents"][0]["status"] == "succeeded"
    assert course["contents"][0]["content"] == {"body": "Conteúdo de teste"}
    assert course["contents"][0]["citations"][0]["similarity"] == 0.9


def test_seed_returns_404_for_unknown_owner_or_niche(
    client: TestClient, db: Session
) -> None:
    user = create_random_user(db)
    payload = {
        "owner_email": user.email,
        "title": "Curso inválido",
        "audience_level": "technical_basic",
        "documents": [{"chunks": ["chunk"]}],
        "contents": [{"format": "tutorial", "content": {"body": "ok"}}],
    }

    owner_response = client.post(
        f"{settings.API_V1_STR}/private/courses/",
        json={**payload, "owner_email": "missing@example.com"},
    )
    niche_response = client.post(
        f"{settings.API_V1_STR}/private/courses/",
        json={**payload, "niche_slug": "missing"},
    )

    assert owner_response.status_code == 404
    assert niche_response.status_code == 404


def test_seed_returns_422_for_invalid_payloads(
    client: TestClient, db: Session
) -> None:
    user = create_random_user(db)
    base_payload = {
        "owner_email": user.email,
        "title": "Curso inválido",
        "audience_level": "technical_basic",
        "documents": [{"chunks": ["chunk"]}],
        "contents": [{"format": "tutorial", "content": {"body": "ok"}}],
    }
    invalid_payloads = [
        {**base_payload, "documents": []},
        {**base_payload, "contents": []},
        {
            **base_payload,
            "contents": [{"format": "tutorial", "status": "succeeded"}],
        },
        {
            **base_payload,
            "contents": [
                {
                    "format": "tutorial",
                    "content": {"body": "ok"},
                    "cited_chunks": [1],
                }
            ],
        },
    ]

    responses = [
        client.post(
            f"{settings.API_V1_STR}/private/courses/",
            json=payload,
        )
        for payload in invalid_payloads
    ]

    assert [response.status_code for response in responses] == [422, 422, 422, 422]
