import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

import sqlalchemy as sa
from anyio import create_task_group, sleep, to_thread
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from sqlmodel import Session, col, delete, select

from app.api.deps import CurrentUser, SessionDep
from app.core.storage import document_key, get_storage
from app.models import (
    AudienceLevel,
    CitationPublic,
    ContentCitation,
    ContentFormat,
    ContentPublic,
    ContentSummary,
    Course,
    CourseContent,
    CourseDetail,
    CoursesPublic,
    CourseStatus,
    CourseSummary,
    DocumentChunk,
    DocumentPublic,
    GenerationStatus,
    Niche,
    NichePublic,
    SourceDocument,
    User,
)
from app.services import course_deletion, course_generation
from app.services.documents import MAX_FILE_BYTES, DocumentError, read_documents

RECOVERY_INTERVAL_SECONDS = 30


async def _recover_stalled_courses() -> None:
    try:
        await to_thread.run_sync(course_generation.expire_stalled_courses)
    except Exception:
        logging.exception("Falha ao recuperar gerações interrompidas")


@asynccontextmanager
async def lifespan(_app: object) -> AsyncIterator[None]:
    async def recover_periodically() -> None:
        while True:
            await sleep(RECOVERY_INTERVAL_SECONDS)
            await _recover_stalled_courses()

    await _recover_stalled_courses()
    async with create_task_group() as tasks:
        tasks.start_soon(recover_periodically)
        try:
            yield
        finally:
            tasks.cancel_scope.cancel()


router = APIRouter(prefix="/courses", tags=["courses"], lifespan=lifespan)


def _content_summary(content: CourseContent) -> ContentSummary:
    return ContentSummary(
        id=content.id,
        format=content.format,
        status=content.status,
        position=content.position,
        title=content.title,
    )


def _niche_public(niche: Niche) -> NichePublic:
    if niche.id is None:
        raise RuntimeError("Persisted niche is missing its id")
    return NichePublic(
        id=niche.id,
        slug=niche.slug,
        name=niche.name,
        description=niche.description,
    )


def _course_summary(
    course: Course, niche: NichePublic, contents: list[CourseContent]
) -> CourseSummary:
    return CourseSummary(
        id=course.id,
        title=course.title,
        audience_level=course.audience_level,
        status=course.status,
        niche=niche,
        created_at=course.created_at,
        updated_at=course.updated_at,
        contents=[_content_summary(content) for content in contents],
    )


def _content_public(
    session: Session, course_id: uuid.UUID, content: CourseContent
) -> ContentPublic:
    citation_statement = (
        select(ContentCitation, DocumentChunk, SourceDocument)
        .join(
            DocumentChunk,
            (col(ContentCitation.chunk_id) == col(DocumentChunk.id))
            & (col(ContentCitation.course_id) == col(DocumentChunk.course_id)),
        )
        .join(
            SourceDocument,
            (col(DocumentChunk.document_id) == col(SourceDocument.id))
            & (col(DocumentChunk.course_id) == col(SourceDocument.course_id)),
        )
        .where(
            col(ContentCitation.course_id) == course_id,
            col(ContentCitation.content_id) == content.id,
        )
        .order_by(col(ContentCitation.similarity).desc().nullslast())
    )
    citations = [
        CitationPublic(
            chunk_id=citation.chunk_id,
            document_id=chunk.document_id,
            document_title=document.title,
            text=chunk.text,
            page_number=chunk.page_number,
            similarity=(
                float(citation.similarity) if citation.similarity is not None else None
            ),
        )
        for citation, chunk, document in session.exec(citation_statement).all()
    ]

    return ContentPublic(
        id=content.id,
        format=content.format,
        status=content.status,
        position=content.position,
        title=content.title,
        content=content.content,
        estimated_minutes=content.estimated_minutes,
        key_concepts=content.key_concepts,
        prerequisites=content.prerequisites,
        grounding_score=(
            float(content.grounding_score)
            if content.grounding_score is not None
            else None
        ),
        clarity=content.clarity,
        review_notes=content.review_notes,
        oci_object_key=content.oci_object_key,
        error_message=content.error_message,
        updated_at=content.updated_at,
        citations=citations,
    )


@router.get("/", response_model=CoursesPublic)
def read_courses(*, session: SessionDep, current_user: CurrentUser) -> CoursesPublic:
    statement = (
        select(Course, Niche)
        .join(Niche, col(Course.niche_id) == col(Niche.id))
        .where(col(Course.owner_id) == current_user.id)
        .order_by(col(Course.created_at).desc())
    )
    course_rows = session.exec(statement).all()

    data = []
    for course, niche in course_rows:
        contents = list(
            session.exec(
                select(CourseContent)
                .where(col(CourseContent.course_id) == course.id)
                .order_by(col(CourseContent.position))
            ).all()
        )
        data.append(_course_summary(course, _niche_public(niche), contents))

    return CoursesPublic(data=data, count=len(data))


@router.get("/{course_id}", response_model=CourseDetail)
def read_course(
    *, session: SessionDep, current_user: CurrentUser, course_id: uuid.UUID
) -> CourseDetail:
    statement = (
        select(Course, Niche)
        .join(Niche, col(Course.niche_id) == col(Niche.id))
        .where(
            col(Course.id) == course_id,
            col(Course.owner_id) == current_user.id,
        )
    )
    course_row = session.exec(statement).first()
    if course_row is None:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")

    course, niche = course_row
    contents = list(
        session.exec(
            select(CourseContent)
            .where(col(CourseContent.course_id) == course.id)
            .order_by(col(CourseContent.position))
        ).all()
    )
    documents = list(
        session.exec(
            select(SourceDocument).where(col(SourceDocument.course_id) == course.id)
        ).all()
    )

    return CourseDetail(
        id=course.id,
        title=course.title,
        audience_level=course.audience_level,
        status=course.status,
        niche=_niche_public(niche),
        created_at=course.created_at,
        updated_at=course.updated_at,
        contents=[_content_public(session, course.id, content) for content in contents],
        documents=[
            DocumentPublic(
                id=document.id,
                title=document.title,
                original_filename=document.original_filename,
                mime_type=document.mime_type,
                size_bytes=document.size_bytes,
                status=document.status,
                error_message=document.error_message,
            )
            for document in documents
        ],
    )


@router.delete("/{course_id}", status_code=204)
def delete_course(
    *, session: SessionDep, current_user: CurrentUser, course_id: uuid.UUID
) -> None:
    course = session.exec(
        select(Course.id)
        .where(col(Course.id) == course_id, col(Course.owner_id) == current_user.id)
        .with_for_update()
    ).first()
    if course is None:
        raise HTTPException(404, "Curso não encontrado.")
    if course_deletion.has_active_content(session, [course_id]):
        raise HTTPException(409, "Espere a geração terminar para excluir o curso.")

    course_deletion.enqueue_cleanup(session, [course_id])
    session.exec(delete(Course).where(col(Course.id) == course_id))
    session.commit()


@router.post("/", status_code=201, response_model=CourseDetail)
def create_course(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request: Request,
    background_tasks: BackgroundTasks,
    niche_id: Annotated[int, Form()],
    audience_level: Annotated[AudienceLevel, Form()],
    title: Annotated[str, Form()] = "",
    formats: Annotated[list[ContentFormat] | None, Form()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> CourseDetail:
    title = title.strip()
    if not title:
        raise HTTPException(422, "Informe um título.")
    if len(title) > 255:
        raise HTTPException(422, "O título passa de 255 caracteres.")
    if not files or not formats:
        raise HTTPException(
            422, "Envie pelo menos um documento e escolha pelo menos uma saída."
        )
    if len(files) > 3 or len(formats) > 3:
        raise HTTPException(422, "Envie até 3 documentos e escolha até 3 saídas.")
    if len(set(formats)) != len(formats):
        raise HTTPException(422, "Escolha só uma saída de cada formato.")
    data = [(f.filename or "", f.file.read(MAX_FILE_BYTES + 1)) for f in files]
    try:
        documents = read_documents(data)
    except DocumentError as exc:
        detail = f"{exc.filename}: {exc.message}" if exc.filename else exc.message
        raise HTTPException(422, detail) from exc
    if session.get(Niche, niche_id) is None:
        raise HTTPException(404, "Setor não encontrado.")
    owner_id = session.exec(
        select(User.id).where(col(User.id) == current_user.id).with_for_update()
    ).first()
    if owner_id is None:
        raise HTTPException(404, "User not found")
    storage = request.app.dependency_overrides.get(get_storage, get_storage)()
    generation_id = uuid.uuid4()
    course = Course(
        owner_id=current_user.id,
        niche_id=niche_id,
        title=title,
        audience_level=audience_level,
        generation_id=generation_id,
    )
    keys: list[str] = []
    try:
        rows = []
        for doc, (_, content) in zip(documents, data, strict=True):
            doc_id = uuid.uuid4()
            key = document_key(course.id, doc_id, doc.extension)
            storage.put(key, content, doc.mime_type)
            keys.append(key)
            rows.append(
                SourceDocument(
                    id=doc_id,
                    course_id=course.id,
                    title=doc.filename,
                    original_filename=doc.filename,
                    mime_type=doc.mime_type,
                    size_bytes=doc.size_bytes,
                    sha256=doc.sha256,
                    oci_object_key=key,
                )
            )
        session.add(course)
        session.add_all(rows)
        session.add_all(
            [
                CourseContent(course_id=course.id, format=fmt, position=i, focus=title)
                for i, fmt in enumerate(formats)
            ]
        )
        session.commit()
    except Exception:
        session.rollback()
        for key in keys:
            try:
                storage.delete(key)
            except Exception:
                logging.exception("Falha ao limpar objetos do curso %s", course.id)
        raise
    background_tasks.add_task(
        course_generation.run_course_generation,
        storage=storage,
        course_id=course.id,
        generation_id=generation_id,
    )
    return read_course(session=session, current_user=current_user, course_id=course.id)


@router.post(
    "/{course_id}/contents/{content_id}/retry",
    status_code=202,
    response_model=CourseDetail,
)
def retry_content(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request: Request,
    background_tasks: BackgroundTasks,
    course_id: uuid.UUID,
    content_id: uuid.UUID,
) -> CourseDetail:
    course = session.exec(
        select(Course)
        .where(col(Course.id) == course_id, col(Course.owner_id) == current_user.id)
        .with_for_update()
    ).first()
    if course is None:
        raise HTTPException(404, "Curso não encontrado.")
    content = session.get(CourseContent, content_id)
    if content is None or content.course_id != course_id:
        raise HTTPException(404, "Conteúdo não encontrado.")
    if content.status != GenerationStatus.failed:
        raise HTTPException(409, "Só um conteúdo que falhou pode ser gerado de novo.")

    active, stalled = course_generation.generation_activity(session, course_id)
    if active and (stalled or course.generation_id is None):
        raise HTTPException(409, course_generation.GENERATION_INTERRUPTED)
    storage = request.app.dependency_overrides.get(get_storage, get_storage)()
    now = datetime.now(UTC)
    updated = session.exec(
        sa.update(CourseContent)
        .where(
            col(CourseContent.id) == content_id,
            col(CourseContent.status) == GenerationStatus.failed,
        )
        .values(status=GenerationStatus.pending, error_message=None, updated_at=now)
        .returning(col(CourseContent.id))
    ).first()
    if updated is None:
        raise HTTPException(409, "Só um conteúdo que falhou pode ser gerado de novo.")
    if course.status == CourseStatus.failed:
        course.status = CourseStatus.initializing
        course.updated_at = now

    generation_id = None
    if course.generation_id is None or stalled:
        generation_id = course.generation_id = uuid.uuid4()
    detail = read_course(
        session=session, current_user=current_user, course_id=course_id
    )
    session.commit()
    if generation_id is not None:
        background_tasks.add_task(
            course_generation.run_course_generation,
            storage=storage,
            course_id=course_id,
            generation_id=generation_id,
        )
    return detail
