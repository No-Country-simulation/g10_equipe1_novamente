from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.user import authentication_token_from_email, create_random_user


def test_read_niches_ordered_by_id(client: TestClient, db: Session) -> None:
    user = create_random_user(db)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    response = client.get(
        f"{settings.API_V1_STR}/niches/",
        headers=headers,
    )

    assert response.status_code == 200
    niches = response.json()
    assert [niche["slug"] for niche in niches] == [
        "fintech",
        "saude",
        "e-commerce",
        "geral",
    ]
    assert [niche["id"] for niche in niches] == sorted(niche["id"] for niche in niches)


def test_read_niches_requires_authentication(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/niches/")

    assert response.status_code in (401, 403)
