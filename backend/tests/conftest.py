from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine
from app.core.storage import InMemoryStorage, Storage, get_storage
from app.main import app
from app.models import CourseObjectCleanup, User
from app.services import course_deletion
from tests.utils.user import authentication_token_from_email


@pytest.fixture(scope="session", autouse=True)
def isolate_cleanup_storage() -> Generator[None]:
    def resolve_storage(app: FastAPI) -> Storage:
        return app.dependency_overrides.get(get_storage, InMemoryStorage)()

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(course_deletion, "_resolve_storage", resolve_storage)
        yield


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
