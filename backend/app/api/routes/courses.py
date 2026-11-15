import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, col, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CitationPublic,
    ContentCitation,
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
def read_courses(
    *, session: SessionDep, current_user: CurrentUser
) -> CoursesPublic:
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
            select(SourceDocument)
            .where(col(SourceDocument.course_id) == course.id)
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
        contents=[
            _content_public(session, course.id, content) for content in contents
        ],
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
