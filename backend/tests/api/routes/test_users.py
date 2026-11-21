from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic, sleep
from unittest.mock import Mock

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import event, text
from sqlmodel import Session, col, select

from app import crud
from app.api.deps import SessionDep, TokenDep, get_current_user
from app.core.config import settings
from app.core.db import engine
from app.core.security import verify_password
from app.core.storage import InMemoryStorage, get_storage
from app.main import app
from app.models import (
    AudienceLevel,
    ContentFormat,
    Course,
    CourseContent,
    CourseObjectCleanup,
    GenerationStatus,
    Niche,
    User,
    UserCreate,
    UserUpdate,
)
from app.services import course_generation
from tests.utils.user import create_random_user, user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_update_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    full_name = "Updated Name"
    email = random_email()
    data = {"full_name": full_name, "email": email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name

    user_query = select(User).where(User.email == email)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == email
    assert user_db.full_name == full_name


def test_update_password_me(client: TestClient, db: Session) -> None:
    user = create_random_user(db)
    password = random_lower_string()
    crud.update_user(session=db, db_user=user, user_in=UserUpdate(password=password))
    headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    new_password = random_lower_string()
    data = {"current_password": password, "new_password": new_password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password updated successfully"

    db.refresh(user)
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified


def test_update_password_me_incorrect_password(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    new_password = random_lower_string()
    data = {"current_password": new_password, "new_password": new_password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"


def test_update_user_me_email_exists(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    data = {"email": user.email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


def test_update_password_me_same_password_error(
    client: TestClient, db: Session
) -> None:
    user = create_random_user(db)
    password = random_lower_string()
    crud.update_user(session=db, db_user=user, user_in=UserUpdate(password=password))
    headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    data = {"current_password": password, "new_password": password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "New password cannot be the same as the current one"


def test_register_user(client: TestClient, db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    data = {"email": username, "password": password, "full_name": full_name}
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == username
    assert created_user["full_name"] == full_name

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == username
    assert user_db.full_name == full_name
    verified, _ = verify_password(password, user_db.hashed_password)
    assert verified


def test_register_user_already_exists_error(client: TestClient, db: Session) -> None:
    user = create_random_user(db)
    password = random_lower_string()
    full_name = random_lower_string()
    data = {
        "email": user.email,
        "password": password,
        "full_name": full_name,
    }
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "The user with this email already exists in the system"


def test_delete_user_me(client: TestClient, db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    user_id = user.id
    niche_id = db.exec(select(Niche.id).where(col(Niche.slug) == "geral")).one()
    courses = [
        Course(
            owner_id=user_id,
            niche_id=niche_id,
            title=title,
            audience_level=AudienceLevel.non_technical,
        )
        for title in ("Curso A", "Curso B")
    ]
    course_ids = [course.id for course in courses]
    active = CourseContent(
        course_id=course_ids[1], format=ContentFormat.tutorial, focus="Foco"
    )
    db.add_all(courses)
    db.flush()
    db.add(active)
    db.commit()

    login_data = {
        "username": username,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    url = f"{settings.API_V1_STR}/users/me"
    r = client.delete(url, headers=headers)
    assert r.status_code == 409
    assert (
        r.json()["detail"]
        == "Espere a geração dos seus cursos terminar para excluir a conta."
    )
    assert client.get(url, headers=headers).status_code == 200
    for course_id in course_ids:
        assert (
            client.get(
                f"{settings.API_V1_STR}/courses/{course_id}", headers=headers
            ).status_code
            == 200
        )
        assert db.get(CourseObjectCleanup, course_id) is None

    active.status = GenerationStatus.failed
    db.commit()
    active_id = active.id
    r = client.delete(url, headers=headers)
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted successfully"
    db.expire_all()
    assert db.get(User, user_id) is None
    assert db.get(CourseContent, active_id) is None
    for course_id in course_ids:
        assert db.get(Course, course_id) is None
        assert db.get(CourseObjectCleanup, course_id) is not None


def test_account_deletion_waits_for_upload_and_sees_new_course(client, db, monkeypatch):
    password = random_lower_string()
    owner = crud.create_user(
        session=db, user_create=UserCreate(email=random_email(), password=password)
    )
    headers = user_authentication_headers(
        client=client, email=owner.email, password=password
    )
    niche_id = db.exec(select(Niche.id).where(col(Niche.slug) == "geral")).one()
    uploading, finish_upload = Event(), Event()
    deleting_pid: Queue[int] = Queue()

    class PausedStorage(InMemoryStorage):
        def put(self, key, data, content_type):
            uploading.set()
            assert finish_upload.wait(10)
            super().put(key, data, content_type)

    def observe_owner_lock(connection, _cursor, statement, *_args):
        if 'FROM "user"' in statement and "FOR UPDATE" in statement:
            deleting_pid.put(connection.connection.driver_connection.info.backend_pid)

    monkeypatch.setitem(app.dependency_overrides, get_storage, PausedStorage)
    monkeypatch.setattr(course_generation, "run_course_generation", Mock())
    with ThreadPoolExecutor(max_workers=2) as pool:
        creation = pool.submit(_post_course, client, headers, niche_id)
        try:
            assert uploading.wait(5)
            event.listen(engine, "before_cursor_execute", observe_owner_lock)
            try:
                deletion = pool.submit(
                    client.delete, f"{settings.API_V1_STR}/users/me", headers=headers
                )
                pid = deleting_pid.get(timeout=5)
                deadline = monotonic() + 5
                while not db.execute(
                    text("SELECT pg_blocking_pids(:pid)"), {"pid": pid}
                ).scalar_one():
                    assert monotonic() < deadline, (
                        "A exclusão deveria esperar o lock da criação."
                    )
                    sleep(0.01)
            finally:
                event.remove(engine, "before_cursor_execute", observe_owner_lock)
        finally:
            finish_upload.set()

        created = creation.result(timeout=5)
        assert created.status_code == 201, created.text
        assert deletion.result(timeout=5).status_code == 409

    assert (
        client.get(
            f"{settings.API_V1_STR}/courses/{created.json()['id']}", headers=headers
        ).status_code
        == 200
    )


def _post_course(client, headers, niche_id):
    return client.post(
        f"{settings.API_V1_STR}/courses/",
        headers=headers,
        data={
            "title": "Curso novo",
            "niche_id": niche_id,
            "audience_level": "non_technical",
            "formats": "tutorial",
        },
        files={"files": ("guia.md", b"Texto do curso", "text/markdown")},
    )


@pytest.mark.parametrize("operation", ["create_course", "delete_account"])
def test_account_deletion_wins_after_authentication(client, db, monkeypatch, operation):
    password = random_lower_string()
    email = random_email()
    crud.create_user(session=db, user_create=UserCreate(email=email, password=password))
    headers = user_authentication_headers(client=client, email=email, password=password)
    niche_id = db.exec(select(Niche.id).where(col(Niche.slug) == "geral")).one()
    delete_url = f"{settings.API_V1_STR}/users/me"
    authenticated, resume = Event(), Event()
    storage = InMemoryStorage()
    put = Mock(wraps=storage.put)
    generation = Mock()

    def pause_after_auth(
        request: Request, session: SessionDep, token: TokenDep
    ) -> User:
        user = get_current_user(session=session, token=token)
        if request.headers.get("x-pause-after-auth") == "1":
            authenticated.set()
            assert resume.wait(10)
        return user

    monkeypatch.setitem(app.dependency_overrides, get_current_user, pause_after_auth)
    monkeypatch.setitem(app.dependency_overrides, get_storage, lambda: storage)
    monkeypatch.setattr(storage, "put", put)
    monkeypatch.setattr(course_generation, "run_course_generation", generation)
    paused_headers = {**headers, "x-pause-after-auth": "1"}
    with ThreadPoolExecutor(max_workers=1) as pool:
        if operation == "create_course":
            pending = pool.submit(_post_course, client, paused_headers, niche_id)
        else:
            pending = pool.submit(client.delete, delete_url, headers=paused_headers)
        try:
            assert authenticated.wait(5)
            assert client.delete(delete_url, headers=headers).status_code == 200
        finally:
            resume.set()
        response = pending.result(timeout=5)

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
    put.assert_not_called()
    assert storage.list("courses/") == []
    generation.assert_not_called()
