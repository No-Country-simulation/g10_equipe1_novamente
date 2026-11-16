import hashlib
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import col, select

from app.api.deps import SessionDep
from app.api.routes.courses import read_course
from app.core.security import get_password_hash
from app.models import (
    AudienceLevel,
    ClarityLevel,
    ContentCitation,
    ContentFormat,
    Course,
    CourseContent,
    CourseDetail,
    CourseStatus,
    DocumentChunk,
    DocumentStatus,
    GenerationStatus,
    Niche,
    SourceDocument,
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


class PrivateDocumentCreate(BaseModel):
    original_filename: str = "documento.md"
    status: DocumentStatus = DocumentStatus.indexed
    chunks: list[str] = Field(default_factory=list)


class PrivateContentCreate(BaseModel):
    format: ContentFormat
    status: GenerationStatus = GenerationStatus.succeeded
    title: str | None = None
    content: dict[str, Any] | None = None
    estimated_minutes: int | None = None
    key_concepts: list[str] | None = None
    prerequisites: list[str] | None = None
    grounding_score: float | None = None
    clarity: ClarityLevel | None = None
    review_notes: str | None = None
    error_message: str | None = None
    cited_chunks: list[int] = Field(default_factory=list)


class PrivateCourseCreate(BaseModel):
    owner_email: str
    title: str
    niche_slug: str = "geral"
    audience_level: AudienceLevel
    status: CourseStatus = CourseStatus.ready
    documents: list[PrivateDocumentCreate]
    contents: list[PrivateContentCreate]


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> User:
    """
    Create a new user.
    """

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()

    return user


@router.post("/courses/", response_model=CourseDetail)
def create_course(course_in: PrivateCourseCreate, session: SessionDep) -> CourseDetail:
    owner = session.exec(
        select(User).where(col(User.email) == course_in.owner_email)
    ).first()
    if owner is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    niche = session.exec(
        select(Niche).where(col(Niche.slug) == course_in.niche_slug)
    ).first()
    if niche is None or niche.id is None:
        raise HTTPException(status_code=404, detail="Setor não encontrado.")

    if not course_in.documents:
        raise HTTPException(status_code=422, detail="documents não pode ser vazio.")
    if not course_in.contents:
        raise HTTPException(status_code=422, detail="contents não pode ser vazio.")
    if any(
        content.status == GenerationStatus.succeeded and content.content is None
        for content in course_in.contents
    ):
        raise HTTPException(
            status_code=422,
            detail="Conteúdo succeeded precisa ter content.",
        )

    total_chunks = sum(len(document.chunks) for document in course_in.documents)
    invalid_indices = {
        chunk_index
        for content in course_in.contents
        for chunk_index in content.cited_chunks
        if chunk_index < 0 or chunk_index >= total_chunks
    }
    if invalid_indices:
        raise HTTPException(
            status_code=422,
            detail="cited_chunks contém um índice inexistente.",
        )
    if any(
        not chunk.strip()
        for document in course_in.documents
        for chunk in document.chunks
    ):
        raise HTTPException(
            status_code=422,
            detail="chunks não pode conter texto vazio.",
        )

    document_hashes = [
        hashlib.sha256("\n".join(document.chunks).encode("utf-8")).hexdigest()
        if document.chunks
        else hashlib.sha256(str(uuid.uuid4()).encode("utf-8")).hexdigest()
        for document in course_in.documents
    ]
    if len(set(document_hashes)) != len(document_hashes):
        raise HTTPException(
            status_code=422,
            detail="documents contém documentos com texto repetido.",
        )

    course = Course(
        owner_id=owner.id,
        niche_id=niche.id,
        title=course_in.title,
        audience_level=course_in.audience_level,
        status=course_in.status,
    )
    session.add(course)

    all_chunks: list[DocumentChunk] = []
    for document_in, document_hash in zip(
        course_in.documents, document_hashes, strict=True
    ):
        document_id = uuid.uuid4()
        document_text = "\n".join(document_in.chunks).encode("utf-8")
        document = SourceDocument(
            id=document_id,
            course_id=course.id,
            title=document_in.original_filename,
            original_filename=document_in.original_filename,
            mime_type="text/markdown",
            size_bytes=max(1, len(document_text)),
            sha256=document_hash,
            oci_object_key=(f"courses/{course.id}/documents/{document_id}.md"),
            status=document_in.status,
        )
        session.add(document)
        session.flush()

        for chunk_index, text in enumerate(document_in.chunks):
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=document.id,
                course_id=course.id,
                chunk_index=chunk_index,
                text=text,
                embedding=[1.0] + [0.0] * 767,
            )
            all_chunks.append(chunk)
            session.add(chunk)
        session.flush()

    for position, content_in in enumerate(course_in.contents):
        content_id = uuid.uuid4()
        content = CourseContent(
            id=content_id,
            course_id=course.id,
            format=content_in.format,
            position=position,
            focus=course.title,
            title=content_in.title,
            status=content_in.status,
            content=content_in.content,
            estimated_minutes=content_in.estimated_minutes,
            key_concepts=content_in.key_concepts,
            prerequisites=content_in.prerequisites,
            grounding_score=(
                Decimal(str(content_in.grounding_score))
                if content_in.grounding_score is not None
                else None
            ),
            clarity=content_in.clarity,
            review_notes=content_in.review_notes,
            oci_object_key=(
                f"courses/{course.id}/contents/{content_id}/{uuid.uuid4()}.json"
                if content_in.content is not None
                else None
            ),
            error_message=content_in.error_message,
        )
        session.add(content)
        session.flush()

        for chunk_index in dict.fromkeys(content_in.cited_chunks):
            cited_chunk = all_chunks[chunk_index]
            session.add(
                ContentCitation(
                    course_id=course.id,
                    content_id=content.id,
                    chunk_id=cited_chunk.id,
                    similarity=Decimal("0.9"),
                )
            )

    session.commit()
    return read_course(
        session=session,
        current_user=owner,
        course_id=course.id,
    )
