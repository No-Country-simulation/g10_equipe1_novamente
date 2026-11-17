import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from sqlmodel import Session, col, select

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
    CourseSummary,
    DocumentChunk,
    DocumentPublic,
    Niche,
    NichePublic,
    SourceDocument,
)
from app.services.documents import MAX_FILE_BYTES, DocumentError, read_documents

router = APIRouter(prefix="/courses", tags=["courses"])


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


@router.post("/", status_code=201, response_model=CourseDetail)
def create_course(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request: Request,
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
    storage = request.app.dependency_overrides.get(get_storage, get_storage)()
    course = Course(
        owner_id=current_user.id,
        niche_id=niche_id,
        title=title,
        audience_level=audience_level,
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
    return read_course(session=session, current_user=current_user, course_id=course.id)
