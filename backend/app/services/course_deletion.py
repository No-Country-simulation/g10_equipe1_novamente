import logging
import uuid
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from datetime import timedelta
from functools import partial

import anyio
from fastapi import FastAPI
from sqlmodel import Session, col, select
from starlette.concurrency import run_in_threadpool

from app.core.db import engine
from app.core.storage import Storage, course_prefix, get_storage
from app.models import (
    CourseContent,
    CourseObjectCleanup,
    GenerationStatus,
    get_datetime_utc,
)

logger = logging.getLogger(__name__)
CLEANUP_INTERVAL_SECONDS = 30
BATCH_SIZE = 10


def has_active_content(session: Session, course_ids: Sequence[uuid.UUID]) -> bool:
    statement = (
        select(CourseContent.id)
        .where(
            col(CourseContent.course_id).in_(course_ids),
            col(CourseContent.status).in_(
                (GenerationStatus.pending, GenerationStatus.running)
            ),
        )
        .limit(1)
    )
    return session.exec(statement).first() is not None


def enqueue_cleanup(session: Session, course_ids: Sequence[uuid.UUID]) -> None:
    session.add_all(
        [CourseObjectCleanup(course_id=course_id) for course_id in course_ids]
    )


def _clean_course(
    session: Session, job: CourseObjectCleanup, storage_provider: Callable[[], Storage]
) -> None:
    operation = "get_storage"
    key = None
    try:
        storage = storage_provider()
        operation = "list"
        keys = storage.list(course_prefix(job.course_id))
        operation = "delete"
        for key in keys:
            storage.delete(key)
    except Exception as exc:
        logger.warning(
            "Falha na limpeza course_id=%s operation=%s error=%s key=%s",
            job.course_id,
            operation,
            type(exc).__name__,
            key,
        )
        job.next_attempt_at = get_datetime_utc() + timedelta(minutes=1)
    else:
        session.delete(job)


def process_pending_cleanups(storage_provider: Callable[[], Storage]) -> None:
    for _ in range(BATCH_SIZE):
        course_id = None
        try:
            with Session(engine) as session:
                job = session.exec(
                    select(CourseObjectCleanup)
                    .where(
                        col(CourseObjectCleanup.next_attempt_at) <= get_datetime_utc()
                    )
                    .order_by(
                        col(CourseObjectCleanup.next_attempt_at),
                        col(CourseObjectCleanup.course_id),
                    )
                    .limit(1)
                    .with_for_update(skip_locked=True)
                ).first()
                if job is None:
                    return
                course_id = job.course_id
                _clean_course(session, job, storage_provider)
                session.commit()
        except Exception as exc:
            logger.warning(
                "Falha na limpeza course_id=%s operation=transaction error=%s",
                course_id,
                type(exc).__name__,
            )
            return


def _resolve_storage(app: FastAPI) -> Storage:
    return app.dependency_overrides.get(get_storage, get_storage)()


@asynccontextmanager
async def cleanup_lifespan(app: FastAPI) -> AsyncIterator[None]:
    storage_provider = partial(_resolve_storage, app)

    async def clean_periodically() -> None:
        while True:
            await run_in_threadpool(process_pending_cleanups, storage_provider)
            await anyio.sleep(CLEANUP_INTERVAL_SECONDS)

    async with anyio.create_task_group() as tasks:
        tasks.start_soon(clean_periodically)
        try:
            yield
        finally:
            tasks.cancel_scope.cancel()
