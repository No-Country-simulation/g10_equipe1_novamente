from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine
from app.main import app
from app.models import CourseObjectCleanup, User
from tests.utils.user import authentication_token_from_email


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    with Session(engine) as session:
        yield session
        session.exec(delete(CourseObjectCleanup))
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> TestClient:
    # Os testes de rotas inspecionam as pendências com o limpador parado.
    return TestClient(app)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
