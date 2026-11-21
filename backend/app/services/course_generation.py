import logging
import uuid
from datetime import timedelta
from time import monotonic

from sqlalchemy import func, or_, update
from sqlalchemy.sql.dml import Update
from sqlmodel import Session, col, select

from app.core import llm
from app.core.config import settings
from app.core.db import engine
from app.core.storage import Storage
from app.models import (
    ContentFormat,
    Course,
    CourseContent,
    CourseStatus,
    DocumentStatus,
    GenerationStatus,
    Niche,
    SourceDocument,
    get_datetime_utc,
)
from app.services import generation_graph, indexing, publishing
from app.services.grounding import Decision
from app.services.retrieval import RetrievedChunk, search_chunks
from app.services.writer import WriteRequest

logger = logging.getLogger(__name__)

GENERATION_FAILED = "Não foi possível gerar o conteúdo."
INDEXING_FAILED = "O conteúdo não foi gerado, porque um documento do curso falhou."
NO_CHUNKS = (
    "Não foi possível gerar o conteúdo, porque o curso não tem trechos indexados."
)
GENERATION_INTERRUPTED = "A geração foi interrompida. Tente novamente."
GENERATION_TIMEOUT = timedelta(minutes=10)
ACTIVE_STATUSES = (GenerationStatus.pending, GenerationStatus.running)


def _last_progress():
    return func.max(col(CourseContent.updated_at))


def _has_active_contents():
    return func.bool_or(col(CourseContent.status).in_(ACTIVE_STATUSES))


def generation_activity(session: Session, course_id: uuid.UUID) -> tuple[bool, bool]:
    last_progress, active = session.exec(
        select(_last_progress(), _has_active_contents()).where(
            col(CourseContent.course_id) == course_id
        )
    ).one()
    stalled = (
        last_progress is not None
        and last_progress <= get_datetime_utc() - GENERATION_TIMEOUT
    )
    return bool(active), stalled


def _lock_generation(
    session: Session, course_id: uuid.UUID, generation_id: uuid.UUID
) -> Course | None:
    course = session.get(
        Course, course_id, with_for_update=True, populate_existing=True
    )
    if course is None or course.generation_id != generation_id:
        return None
    _, stalled = generation_activity(session, course_id)
    return None if stalled else course


def expire_stalled_courses() -> None:
    with Session(engine) as session:
        course_ids = session.exec(
            select(col(CourseContent.course_id))
            .group_by(col(CourseContent.course_id))
            .having(
                _has_active_contents(),
                _last_progress() <= get_datetime_utc() - GENERATION_TIMEOUT,
            )
        ).all()
        session.rollback()
        for course_id in course_ids:
            with session.begin():
                course = session.get(
                    Course, course_id, with_for_update={"skip_locked": True}
                )
                if course is None:
                    continue
                active, stalled = generation_activity(session, course_id)
                if not (active and stalled):
                    continue
                session.exec(
                    _fail_content_update(GENERATION_INTERRUPTED).where(
                        col(CourseContent.course_id) == course_id,
                        col(CourseContent.status).in_(ACTIVE_STATUSES),
                    )
                )
                session.exec(
                    update(SourceDocument)
                    .where(
                        col(SourceDocument.course_id) == course_id,
                        col(SourceDocument.status) == DocumentStatus.processing,
                    )
                    .values(
                        status=DocumentStatus.failed,
                        error_message=GENERATION_INTERRUPTED,
                    )
                )
                _finish_course(session, course)


def retrieve_chunks(
    *, session: Session, course: Course, query: str
) -> list[RetrievedChunk]:
    (embedding,) = llm.embed_texts([query], task="query")
    return search_chunks(
        session=session,
        course_id=course.id,
        owner_id=course.owner_id,
        query_embedding=embedding,
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )


def _fail_content_update(message: str | None) -> Update:
    return update(CourseContent).values(
        status=GenerationStatus.failed,
        error_message=message,
        updated_at=get_datetime_utc(),
    )


def _log_content(
    course_id: uuid.UUID,
    content_id: uuid.UUID,
    content_format: ContentFormat,
    status: GenerationStatus,
    attempts: int | None,
    seconds: float,
) -> None:
    logger.info(
        "course_id=%s content_id=%s formato=%s estado=%s tentativas=%s segundos=%.3f",
        course_id,
        content_id,
        content_format,
        status,
        attempts,
        seconds,
    )


def _fail_pending_contents(session: Session, course_id: uuid.UUID) -> None:
    contents = session.exec(
        _fail_content_update(INDEXING_FAILED)
        .where(
            col(CourseContent.course_id) == course_id,
            col(CourseContent.status) == GenerationStatus.pending,
        )
        .returning(col(CourseContent.id), col(CourseContent.format))
    ).all()
    for content_id, content_format in contents:
        _log_content(
            course_id, content_id, content_format, GenerationStatus.failed, None, 0
        )


def _index_documents(
    session: Session, storage: Storage, course_id: uuid.UUID, generation_id: uuid.UUID
) -> bool:
    documents = session.exec(
        select(col(SourceDocument.id), col(SourceDocument.original_filename))
        .where(
            col(SourceDocument.course_id) == course_id,
            col(SourceDocument.status) != DocumentStatus.indexed,
        )
        .order_by(col(SourceDocument.created_at), col(SourceDocument.id))
    ).all()
    session.rollback()

    def validate_generation(session: Session) -> None:
        if _lock_generation(session, course_id, generation_id) is None:
            raise indexing.IndexingInterrupted

    def record_indexing_progress(session: Session) -> None:
        session.exec(
            update(CourseContent)
            .where(
                col(CourseContent.course_id) == course_id,
                col(CourseContent.status) == GenerationStatus.pending,
            )
            .values(updated_at=get_datetime_utc())
        )

    for document_id, name in documents:
        try:
            indexing.index_document(
                session=session,
                storage=storage,
                document_id=document_id,
                validate_generation=validate_generation,
                on_indexed=record_indexing_progress,
            )
        except indexing.IndexingInterrupted:
            return False
        except indexing.IndexingError:
            unexpected = False
        except Exception:
            logger.exception(
                "Falha na indexação course_id=%s document_id=%s", course_id, document_id
            )
            unexpected = True
        else:
            continue
        session.rollback()
        with Session(engine) as recovery:
            course = _lock_generation(recovery, course_id, generation_id)
            if course is None:
                return False
            if unexpected:
                recovery.exec(
                    update(SourceDocument)
                    .where(
                        col(SourceDocument.id) == document_id,
                        col(SourceDocument.status) != DocumentStatus.indexed,
                    )
                    .values(
                        status=DocumentStatus.failed,
                        error_message=f"Não foi possível indexar o documento {name}.",
                    )
                )
            _fail_pending_contents(recovery, course_id)
            _finish_course(recovery, course)
            recovery.commit()
        return False
    return True


def _write_request(
    session: Session, course: Course, content: CourseContent
) -> tuple[WriteRequest | None, str | None]:
    try:
        chunks = retrieve_chunks(session=session, course=course, query=content.focus)
    except llm.LLMError as error:
        return None, f"{GENERATION_FAILED} {error}"
    if not chunks:
        return None, NO_CHUNKS

    niche = session.get_one(Niche, course.niche_id)
    return WriteRequest(
        content_format=content.format,
        focus=content.focus,
        audience_level=course.audience_level,
        niche_name=niche.name,
        niche_prompt_hint=niche.prompt_hint,
        chunks=chunks,
    ), None


def _publish(
    session: Session,
    storage: Storage,
    content_id: uuid.UUID,
    result: generation_graph.GenerationResult,
    request: WriteRequest,
) -> str | None:
    assert (
        result.generated is not None
        and result.review is not None
        and result.report is not None
    )
    try:
        publishing.publish_content(
            session=session,
            storage=storage,
            content_id=content_id,
            generated=result.generated,
            review=result.review,
            report=result.report,
            chunks=request.chunks,
        )
    except publishing.PublishError as error:
        return str(error)
    return None


def _process_content(
    session: Session,
    storage: Storage,
    course: Course,
    content: CourseContent,
    generation_id: uuid.UUID,
) -> None:
    course_id, content_id, content_format = course.id, content.id, content.format
    started = monotonic()
    expected_status = GenerationStatus.pending
    status = GenerationStatus.failed
    attempts = None
    try:
        reserved = session.exec(
            update(CourseContent)
            .where(
                col(CourseContent.id) == content_id,
                col(CourseContent.status) == expected_status,
            )
            .values(
                status=GenerationStatus.running,
                llm_model=settings.GEMINI_GENERATION_MODEL,
                prompt_version=generation_graph.PROMPT_VERSION,
                error_message=None,
                updated_at=get_datetime_utc(),
            )
            .returning(col(CourseContent.id))
        ).first()
        session.commit()
        if reserved is None:
            return
        expected_status = GenerationStatus.running
        request, error_message = _write_request(session, course, content)
        if request is not None:
            # A chamada ao Gemini pode levar dezenas de segundos.
            session.rollback()
            result = generation_graph.generate_content(request)
            attempts = result.attempts
            error_message = result.error_message
            if result.decision == Decision.publish:
                if _lock_generation(session, course_id, generation_id) is None or (
                    session.exec(
                        select(col(CourseContent.status)).where(
                            col(CourseContent.id) == content_id
                        )
                    ).one()
                    != GenerationStatus.running
                ):
                    return
                error_message = _publish(session, storage, content_id, result, request)
                if error_message is None:
                    status = GenerationStatus.succeeded
    except Exception:
        logger.exception(
            "Falha na geração course_id=%s content_id=%s", course_id, content_id
        )
        session.rollback()
        with Session(engine) as recovery:
            if not _fail_content(
                recovery,
                course_id,
                generation_id,
                content_id,
                expected_status,
                GENERATION_FAILED,
            ):
                return
    else:
        if status == GenerationStatus.failed and not _fail_content(
            session,
            course_id,
            generation_id,
            content_id,
            expected_status,
            error_message,
        ):
            return

    _log_content(
        course_id, content_id, content_format, status, attempts, monotonic() - started
    )


def _fail_content(
    session: Session,
    course_id: uuid.UUID,
    generation_id: uuid.UUID,
    content_id: uuid.UUID,
    expected_status: GenerationStatus,
    message: str | None,
) -> bool:
    if _lock_generation(session, course_id, generation_id) is None:
        return False
    failed = session.exec(
        _fail_content_update(message)
        .where(
            col(CourseContent.id) == content_id,
            col(CourseContent.status) == expected_status,
        )
        .returning(col(CourseContent.id))
    ).first()
    session.commit()
    return failed is not None


def _finish_course(session: Session, course: Course) -> CourseStatus:
    active_or_published = select(col(CourseContent.id)).where(
        col(CourseContent.course_id) == course.id,
        or_(
            col(CourseContent.status).in_(ACTIVE_STATUSES),
            col(CourseContent.content).is_not(None)
            & col(CourseContent.oci_object_key).is_not(None),
        ),
    )
    if (
        course.status == CourseStatus.initializing
        and not session.exec(select(active_or_published.exists())).one()
    ):
        course.status = CourseStatus.failed
        course.updated_at = get_datetime_utc()
    course.generation_id = None
    return course.status


def run_course_generation(
    *, storage: Storage, course_id: uuid.UUID, generation_id: uuid.UUID
) -> None:
    started = monotonic()
    status: CourseStatus | None
    try:
        with Session(engine, expire_on_commit=False) as session:
            if session.get(Course, course_id) is None:
                logger.warning("Curso não encontrado course_id=%s", course_id)
                return
            if _index_documents(session, storage, course_id, generation_id):
                while True:
                    course = _lock_generation(session, course_id, generation_id)
                    if course is None:
                        return
                    content = session.exec(
                        select(CourseContent)
                        .where(
                            col(CourseContent.course_id) == course_id,
                            col(CourseContent.status) == GenerationStatus.pending,
                        )
                        .order_by(col(CourseContent.position))
                        .limit(1)
                    ).first()
                    if content is None:
                        status = _finish_course(session, course)
                        session.commit()
                        break
                    _process_content(session, storage, course, content, generation_id)
                    session.rollback()
            else:
                session.rollback()
                status = session.exec(
                    select(col(Course.status)).where(col(Course.id) == course_id)
                ).first()
        logger.info(
            "course_id=%s estado=%s segundos=%.3f",
            course_id,
            status,
            monotonic() - started,
        )
    except Exception:
        logger.exception("Falha na tarefa de fundo course_id=%s", course_id)
