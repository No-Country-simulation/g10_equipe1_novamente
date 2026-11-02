import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from pydantic import EmailStr
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(
        default=True, sa_column_kwargs={"server_default": sa.true()}
    )
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    courses: list[Course] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class AudienceLevel(StrEnum):
    non_technical = "non_technical"
    technical_basic = "technical_basic"
    technical_advanced = "technical_advanced"


class ContentFormat(StrEnum):
    tutorial = "tutorial"
    flashcards = "flashcards"
    quiz = "quiz"


class DocumentStatus(StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class GenerationStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class ClarityLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class CourseStatus(StrEnum):
    initializing = "initializing"
    ready = "ready"
    failed = "failed"


class Niche(SQLModel, table=True):
    __tablename__ = "niche"
    id: int | None = Field(
        default=None,
        sa_column=sa.Column(sa.SmallInteger, primary_key=True, autoincrement=True),
    )
    slug: str = Field(max_length=50, unique=True)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, sa_type=sa.Text)
    prompt_hint: str = Field(sa_type=sa.Text)


class Course(SQLModel, table=True):
    __tablename__ = "course"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    niche_id: int = Field(
        sa_column=sa.Column(
            sa.SmallInteger,
            sa.ForeignKey("niche.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_type=sa.Text)
    audience_level: AudienceLevel = Field(
        sa_column=sa.Column(
            sa.Enum(
                AudienceLevel,
                name="audience_level",
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
        )
    )
    status: CourseStatus = Field(
        default=CourseStatus.initializing,
        sa_column=sa.Column(
            sa.Enum(
                CourseStatus,
                name="course_status",
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
            server_default="initializing",
        ),
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    owner: User | None = Relationship(back_populates="courses")
    documents: list[SourceDocument] = Relationship(
        back_populates="course", cascade_delete=True
    )
    contents: list[CourseContent] = Relationship(
        back_populates="course", cascade_delete=True
    )


class SourceDocument(SQLModel, table=True):
    __tablename__ = "source_document"
    __table_args__ = (
        sa.UniqueConstraint("course_id", "sha256"),
        sa.UniqueConstraint("id", "course_id"),
        sa.CheckConstraint("size_bytes > 0", name="ck_source_document_size_positive"),
        sa.CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_source_document_sha256_hex"
        ),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", ondelete="CASCADE")
    title: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    mime_type: str = Field(max_length=100)
    size_bytes: int = Field(sa_type=sa.BigInteger)
    sha256: str = Field(sa_type=sa.CHAR(64))
    oci_object_key: str = Field(max_length=512, unique=True)
    status: DocumentStatus = Field(
        default=DocumentStatus.uploaded,
        sa_column=sa.Column(
            sa.Enum(
                DocumentStatus,
                name="document_status",
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
            server_default="uploaded",
        ),
    )
    embedding_model: str = Field(
        default="gemini-embedding-2",
        max_length=100,
        sa_column_kwargs={"server_default": "gemini-embedding-2"},
    )
    error_message: str | None = Field(default=None, sa_type=sa.Text)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    course: Course | None = Relationship(back_populates="documents")


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunk"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["document_id", "course_id"],
            ["source_document.id", "source_document.course_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("document_id", "chunk_index"),
        sa.UniqueConstraint("id", "course_id"),
        sa.CheckConstraint("chunk_index >= 0", name="ck_document_chunk_position"),
        sa.CheckConstraint(
            "length(btrim(text)) > 0", name="ck_document_chunk_text_nonempty"
        ),
        sa.CheckConstraint(
            "page_number IS NULL OR page_number >= 1", name="ck_document_chunk_page"
        ),
        sa.CheckConstraint(
            "token_count IS NULL OR token_count > 0", name="ck_document_chunk_tokens"
        ),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID
    course_id: uuid.UUID = Field(index=True)
    chunk_index: int
    text: str = Field(sa_type=sa.Text)
    page_number: int | None = None
    token_count: int | None = None
    embedding: list[float] = Field(sa_column=sa.Column(Vector(768), nullable=False))


class CourseContent(SQLModel, table=True):
    __tablename__ = "course_content"
    __table_args__ = (
        sa.UniqueConstraint("id", "course_id"),
        sa.Index("ix_course_content_course_id_position", "course_id", "position"),
        sa.CheckConstraint("position >= 0", name="ck_course_content_position"),
        sa.CheckConstraint(
            "length(btrim(focus)) > 0", name="ck_course_content_focus_nonempty"
        ),
        sa.CheckConstraint(
            "estimated_minutes IS NULL OR estimated_minutes > 0",
            name="ck_course_content_minutes",
        ),
        sa.CheckConstraint(
            "grounding_score IS NULL OR grounding_score BETWEEN 0 AND 1",
            name="ck_course_content_grounding",
        ),
        sa.CheckConstraint(
            "content IS NULL OR jsonb_typeof(content) = 'object'",
            name="ck_course_content_body_json",
        ),
        sa.CheckConstraint(
            "key_concepts IS NULL OR jsonb_typeof(key_concepts) = 'array'",
            name="ck_course_content_key_concepts_array",
        ),
        sa.CheckConstraint(
            "prerequisites IS NULL OR jsonb_typeof(prerequisites) = 'array'",
            name="ck_course_content_prerequisites_array",
        ),
        sa.CheckConstraint(
            "(content IS NULL) = (oci_object_key IS NULL)",
            name="ck_course_content_published_pair",
        ),
        sa.CheckConstraint(
            "status <> 'succeeded' OR (content IS NOT NULL AND oci_object_key IS NOT NULL)",
            name="ck_course_content_successful_published",
        ),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", ondelete="CASCADE")
    format: ContentFormat = Field(
        sa_column=sa.Column(
            sa.Enum(
                ContentFormat,
                name="content_format",
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
        )
    )
    position: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
    focus: str = Field(sa_type=sa.Text)
    title: str | None = Field(default=None, max_length=255)
    status: GenerationStatus = Field(
        default=GenerationStatus.pending,
        sa_column=sa.Column(
            sa.Enum(
                GenerationStatus,
                name="generation_status",
                values_callable=lambda e: [m.value for m in e],
            ),
            nullable=False,
            server_default="pending",
        ),
    )
    error_message: str | None = Field(default=None, sa_type=sa.Text)
    llm_model: str | None = Field(default=None, max_length=100)
    prompt_version: str | None = Field(default=None, max_length=50)
    content: dict[str, Any] | None = Field(
        default=None, sa_column=sa.Column(JSONB(none_as_null=True))
    )
    estimated_minutes: int | None = None
    key_concepts: list[str] | None = Field(
        default=None, sa_column=sa.Column(JSONB(none_as_null=True))
    )
    prerequisites: list[str] | None = Field(
        default=None, sa_column=sa.Column(JSONB(none_as_null=True))
    )
    grounding_score: Decimal | None = Field(
        default=None, sa_column=sa.Column(sa.Numeric(3, 2))
    )
    clarity: ClarityLevel | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.Enum(
                ClarityLevel,
                name="clarity_level",
                values_callable=lambda e: [m.value for m in e],
            )
        ),
    )
    review_notes: str | None = Field(default=None, sa_type=sa.Text)
    oci_object_key: str | None = Field(default=None, max_length=512, unique=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    course: Course | None = Relationship(back_populates="contents")


class ContentCitation(SQLModel, table=True):
    __tablename__ = "content_citation"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["content_id", "course_id"],
            ["course_content.id", "course_content.course_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id", "course_id"],
            ["document_chunk.id", "document_chunk.course_id"],
            ondelete="CASCADE",
        ),
        sa.Index("ix_content_citation_chunk_id_course_id", "chunk_id", "course_id"),
        sa.CheckConstraint(
            "similarity IS NULL OR similarity BETWEEN -1 AND 1",
            name="ck_content_citation_cosine_similarity",
        ),
    )
    course_id: uuid.UUID
    content_id: uuid.UUID = Field(primary_key=True)
    chunk_id: uuid.UUID = Field(primary_key=True)
    similarity: Decimal | None = Field(
        default=None, sa_column=sa.Column(sa.Numeric(4, 3))
    )
