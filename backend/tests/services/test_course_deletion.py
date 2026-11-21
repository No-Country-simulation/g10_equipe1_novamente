from datetime import timedelta
from itertools import chain, repeat
from threading import Event
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.storage import InMemoryStorage, StorageError, course_prefix, get_storage
from app.main import app
from app.models import CourseObjectCleanup, get_datetime_utc
from app.services import course_deletion


@pytest.fixture
def seed(db):
    storage = InMemoryStorage()

    def create(course_id=None):
        course_id = course_id or uuid4()
        db.add(
            CourseObjectCleanup(
                course_id=course_id,
                next_attempt_at=get_datetime_utc() - timedelta(days=1),
            )
        )
        db.commit()
        for filename in ("documents/guia.md", "contents/curso.json"):
            storage.put(course_prefix(course_id) + filename, b"dados", "text/plain")
        return course_id

    return storage, create


@pytest.mark.parametrize("operation", ["get_storage", "list", "delete"])
def test_cleanup_retries_and_continues_batch(db, seed, monkeypatch, caplog, operation):
    storage, create = seed
    failing, healthy = create(), create()
    failing_prefix = course_prefix(failing)
    unrelated = course_prefix(uuid4()) + "keep"
    storage.put(unrelated, b"outro curso", "text/plain")
    error = StorageError("conteúdo privado")
    provider = Mock(return_value=storage)

    with monkeypatch.context() as scoped:
        if operation == "get_storage":
            provider.side_effect = chain([error], repeat(storage))
        else:
            original = getattr(storage, operation)

            def fail_on_course(key):
                if key.startswith(failing_prefix):
                    raise error
                return original(key)

            scoped.setattr(storage, operation, fail_on_course)
        before = get_datetime_utc()
        course_deletion.process_pending_cleanups(provider)

    job = db.get_one(CourseObjectCleanup, failing)
    assert job.next_attempt_at >= before + timedelta(minutes=1)
    assert db.get(CourseObjectCleanup, healthy) is None
    assert storage.list(course_prefix(healthy)) == []
    assert (
        f"course_id={failing} operation={operation} error=StorageError" in caplog.text
    )
    assert "conteúdo privado" not in caplog.text
    if operation == "delete":
        assert f"key={failing_prefix}contents/curso.json" in caplog.text

    course_deletion.process_pending_cleanups(lambda: storage)
    assert storage.list(failing_prefix)
    job.next_attempt_at = before
    db.commit()
    course_deletion.process_pending_cleanups(lambda: storage)
    assert db.get(CourseObjectCleanup, failing) is None
    assert storage.list("courses/") == [unrelated]


def test_cleanup_can_repeat_after_transaction_failure(db, seed, caplog):
    storage, create = seed
    course_id = create()
    with patch.object(Session, "commit", side_effect=RuntimeError("commit")):
        course_deletion.process_pending_cleanups(lambda: storage)

    assert db.get(CourseObjectCleanup, course_id) is not None
    assert storage.list(course_prefix(course_id)) == []
    assert (
        f"course_id={course_id} operation=transaction error=RuntimeError" in caplog.text
    )

    course_deletion.process_pending_cleanups(lambda: storage)
    db.expire_all()
    assert db.get(CourseObjectCleanup, course_id) is None


def test_cleanup_lifespan_processes_at_startup_and_after_restart(db, seed, monkeypatch):
    storage, create = seed
    first = create()
    expected = course_prefix(first)
    listed = Event()
    original = storage.list

    def notify(prefix):
        if prefix == expected:
            listed.set()
        return original(prefix)

    monkeypatch.setattr(storage, "list", notify)
    monkeypatch.setattr(course_deletion, "CLEANUP_INTERVAL_SECONDS", 0.01)
    monkeypatch.setitem(app.dependency_overrides, get_storage, lambda: storage)
    with TestClient(app):
        assert listed.wait(5)
        second = uuid4()
        expected = course_prefix(second)
        listed.clear()
        create(second)
        assert listed.wait(5)
    assert original("courses/") == []

    after_restart = create()
    expected = course_prefix(after_restart)
    listed.clear()
    monkeypatch.setattr(course_deletion, "CLEANUP_INTERVAL_SECONDS", 30)
    with TestClient(app):
        assert listed.wait(5)
    assert original(expected) == []
    assert db.get(CourseObjectCleanup, after_restart) is None
