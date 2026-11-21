import uuid
from dataclasses import dataclass
from datetime import timedelta
from threading import Event
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.routes import courses
from app.core.security import create_access_token
from app.core.storage import InMemoryStorage, StorageError, get_storage
from app.main import app
from app.models import Course, CourseContent, get_datetime_utc
from app.services import course_generation
from tests.utils.course import create_course
from tests.utils.user import create_random_user


@dataclass
class RetryCase:
    course_id: uuid.UUID
    content_id: uuid.UUID
    headers: dict[str, str]

    @property
    def url(self):
        return f"/api/v1/courses/{self.course_id}/contents/{self.content_id}/retry"


@pytest.fixture
def case(client, db):
    owner = create_random_user(db)
    data = create_course(
        client=client,
        owner_email=owner.email,
        status="failed",
        contents=[{"format": "quiz", "status": "failed", "error_message": "Falhou."}],
    )
    token = create_access_token(owner.id, timedelta(minutes=5))
    return RetryCase(
        uuid.UUID(data["id"]),
        uuid.UUID(data["contents"][0]["id"]),
        {"Authorization": f"Bearer {token}"},
    )


@pytest.fixture(autouse=True)
def task(monkeypatch):
    storage = InMemoryStorage()
    generation = Mock()
    monkeypatch.setitem(app.dependency_overrides, get_storage, lambda: storage)
    monkeypatch.setattr(course_generation, "run_course_generation", generation)
    return generation, storage


@pytest.mark.parametrize("ready", [False, True])
def test_retry_returns_pending_and_starts_one_task(client, db, case, task, ready):
    course = db.get_one(Course, case.course_id)
    if ready:
        course.status = "ready"
    content = db.get_one(CourseContent, case.content_id)
    content.llm_model = "modelo anterior"
    content.prompt_version = "versão anterior"
    db.commit()
    before = content.updated_at
    response = client.post(case.url, headers=case.headers)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ("ready" if ready else "initializing")
    assert (data["contents"][0]["status"], data["contents"][0]["error_message"]) == (
        "pending",
        None,
    )
    db.expire_all()
    assert content.updated_at > before
    assert (content.llm_model, content.prompt_version) == (
        "modelo anterior",
        "versão anterior",
    )
    generation, storage = task
    assert isinstance(course.generation_id, uuid.UUID)
    generation.assert_called_once_with(
        storage=storage, course_id=case.course_id, generation_id=course.generation_id
    )


@pytest.mark.parametrize(
    ("scenario", "http_status", "detail"),
    [
        ("pending", 409, "Só um conteúdo que falhou pode ser gerado de novo."),
        ("running", 409, "Só um conteúdo que falhou pode ser gerado de novo."),
        ("succeeded", 409, "Só um conteúdo que falhou pode ser gerado de novo."),
        ("absent_course", 404, "Curso não encontrado."),
        ("foreign_course", 404, "Curso não encontrado."),
        ("absent_content", 404, "Conteúdo não encontrado."),
        ("foreign_content", 404, "Conteúdo não encontrado."),
        ("no_token", 401, None),
        (
            "no_storage",
            503,
            "O armazenamento de arquivos não está disponível. Tente novamente mais tarde.",
        ),
        ("broken_commit", 500, None),
    ],
)
def test_retry_error_preserves_states_and_schedules_nothing(
    client, db, case, task, monkeypatch, scenario, http_status, detail
):
    course = db.get_one(Course, case.course_id)
    content = db.get_one(CourseContent, case.content_id)
    url, headers = case.url, case.headers
    if scenario in ("pending", "running", "succeeded"):
        content.status = scenario
        if scenario == "succeeded":
            content.content = {"body": "Publicado"}
            content.oci_object_key = "teste.json"
    if scenario in ("absent_course", "foreign_course"):
        other = uuid.uuid4()
        if scenario == "foreign_course":
            course.owner_id = create_random_user(db).id
            other = case.course_id
        url = url.replace(str(case.course_id), str(other))
    if scenario in ("absent_content", "foreign_content"):
        other = uuid.uuid4()
        if scenario == "foreign_content":
            other_course = create_course(
                client=client,
                owner_email=db.get_one(Course, case.course_id).owner.email,
            )
            other = other_course["contents"][0]["id"]
        url = url.replace(str(case.content_id), str(other))
    if scenario == "no_token":
        headers = {}
    if scenario == "no_storage":
        monkeypatch.setitem(
            app.dependency_overrides,
            get_storage,
            Mock(side_effect=StorageError("indisponível")),
        )
    db.commit()
    before = (
        content.status,
        content.error_message,
        content.updated_at,
        course.status,
        course.generation_id,
    )
    if scenario == "broken_commit":
        with monkeypatch.context() as patch:
            patch.setattr(
                Session, "commit", Mock(side_effect=RuntimeError("commit falhou"))
            )
            response = TestClient(app, raise_server_exceptions=False).post(
                url, headers=headers
            )
    else:
        response = client.post(url, headers=headers)
    assert response.status_code == http_status
    if detail:
        assert response.json()["detail"] == detail
    db.expire_all()
    assert (
        content.status,
        content.error_message,
        content.updated_at,
        course.status,
        course.generation_id,
    ) == before
    task[0].assert_not_called()


@pytest.mark.parametrize("legacy", [False, True])
def test_stalled_retry_waits_for_lifespan_recovery(client, db, case, task, legacy):
    course = db.get_one(Course, case.course_id)
    course.status = "initializing"
    course.generation_id = None if legacy else uuid.uuid4()
    running = CourseContent(
        course_id=course.id,
        format="tutorial",
        position=1,
        focus=course.title,
        status="running",
    )
    content = db.get_one(CourseContent, case.content_id)
    db.add(running)
    if legacy:
        db.commit()
        response = client.post(case.url, headers=case.headers)
        assert response.status_code == 409
        assert response.json()["detail"] == course_generation.GENERATION_INTERRUPTED

    content.updated_at = running.updated_at = get_datetime_utc() - timedelta(minutes=10)
    db.commit()

    response = client.post(case.url, headers=case.headers)
    assert response.status_code == 409
    assert response.json()["detail"] == course_generation.GENERATION_INTERRUPTED
    task[0].assert_not_called()
    for url in ("/api/v1/courses/", f"/api/v1/courses/{case.course_id}"):
        data = client.get(url, headers=case.headers).json()
        if "data" in data:
            data = next(row for row in data["data"] if row["id"] == str(case.course_id))
        assert [row["status"] for row in data["contents"]] == ["failed", "running"]
    db.expire_all()
    assert running.status == "running"

    with TestClient(app) as restarted:
        db.expire_all()
        assert (course.status, course.generation_id) == ("failed", None)
        assert (running.status, running.error_message) == (
            "failed",
            course_generation.GENERATION_INTERRUPTED,
        )
        response = restarted.post(case.url, headers=case.headers)
        assert response.status_code == 202
    task[0].assert_called_once()


def test_periodic_recovery_retries_after_error(monkeypatch, caplog):
    cycle = Event()

    def recover():
        if recovery.call_count == 1:
            raise RuntimeError("banco indisponível")
        cycle.set()

    recovery = Mock(side_effect=recover)
    monkeypatch.setattr(course_generation, "expire_stalled_courses", recovery)
    monkeypatch.setattr(courses, "RECOVERY_INTERVAL_SECONDS", 0.01)
    with TestClient(app):
        assert cycle.wait(2)
    assert recovery.call_count >= 2
    assert "Falha ao recuperar gerações interrompidas" in caplog.text
