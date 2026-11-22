import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from sqlmodel import Session, col, delete, select

from app.core import llm
from app.core.config import settings
from app.core.storage import Storage, StorageError
from app.models import DocumentChunk, DocumentStatus, SourceDocument
from app.services import documents

CHUNK_SIZE = 1000
PAGE_BREAK = "\f"


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int
    text: str
    page_number: int | None


class DocumentNotFoundError(LookupError): ...


class IndexingError(Exception):
    """A mensagem é o texto gravado em source_document.error_message."""


class IndexingInterrupted(Exception): ...


def split_text(
    text: str, *, paged: bool = False, chunk_size: int = CHUNK_SIZE
) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser positivo")
    pages = text.split(PAGE_BREAK) if paged else [text.replace(PAGE_BREAK, " ")]
    result: list[TextChunk] = []
    for page_number, page in enumerate(pages, 1):
        remaining = page.strip()
        while remaining:
            end = min(chunk_size, len(remaining))
            if len(remaining) > chunk_size:
                window = remaining[: chunk_size + 1]
                for pattern in (r"\n\n", r"\n", r"[.!?](?=\s)", r"\s"):
                    matches = list(re.finditer(pattern, window))
                    positions = [
                        m.end() if pattern == r"[.!?](?=\s)" else m.start()
                        for m in matches
                    ]
                    positions = [p for p in positions if 0 < p <= chunk_size]
                    if positions:
                        end = positions[-1]
                        break
            chunk = remaining[:end].strip()
            if chunk:
                result.append(
                    TextChunk(len(result), chunk, page_number if paged else None)
                )
            remaining = remaining[end:].strip()
    return result


def index_document(
    *,
    session: Session,
    storage: Storage,
    document_id: uuid.UUID,
    validate_generation: Callable[[Session], None] | None = None,
    on_indexed: Callable[[Session], None] | None = None,
) -> int:
    if validate_generation is not None:
        validate_generation(session)
    document = session.get(SourceDocument, document_id)
    if document is None:
        raise DocumentNotFoundError(str(document_id))
    if document.status == DocumentStatus.indexed:
        return len(
            session.exec(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            ).all()
        )
    name, key, course_id = (
        document.original_filename,
        document.oci_object_key,
        document.course_id,
    )
    document.status = DocumentStatus.processing
    document.error_message = None
    session.add(document)
    session.commit()
    try:
        data = storage.get(key)
        extracted = documents.read_document(name, data)
        chunks = split_text(
            extracted.text, paged=extracted.mime_type == "application/pdf"
        )
        if not chunks:
            raise documents.DocumentError(
                documents.DocumentErrorCode.empty, "O arquivo não tem texto."
            )
        embeddings = llm.embed_texts([chunk.text for chunk in chunks], task="document")
        if len(embeddings) != len(chunks):
            raise ValueError("Número inválido de embeddings")
        if validate_generation is not None:
            validate_generation(session)
        session.exec(
            delete(DocumentChunk).where(col(DocumentChunk.document_id) == document_id)
        )
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            session.add(
                DocumentChunk(
                    document_id=document_id,
                    course_id=course_id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    embedding=embedding,
                )
            )
        document.status = DocumentStatus.indexed
        document.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        session.add(document)
        if on_indexed is not None:
            # O progresso e os chunks ficam visíveis no mesmo commit.
            on_indexed(session)
        session.commit()
        return len(chunks)
    except IndexingInterrupted:
        raise
    except Exception as exc:
        session.rollback()
        if validate_generation is not None:
            validate_generation(session)
        if isinstance(exc, StorageError):
            message = f"Não foi possível ler o documento {name} no armazenamento."
        elif isinstance(exc, documents.DocumentError):
            message = f"{name}: {exc.message}"
        elif isinstance(exc, llm.LLMNotConfiguredError):
            message = f"Não foi possível indexar o documento {name}: a chave do Gemini não está configurada."
        elif isinstance(exc, llm.LLMRateLimitError):
            message = f"Não foi possível indexar o documento {name}. {exc}"
        elif isinstance(exc, llm.LLMError):
            message = f"Não foi possível indexar o documento {name}: o modelo de embeddings falhou."
        else:
            message = f"Não foi possível indexar o documento {name}."
        session.exec(
            delete(DocumentChunk).where(col(DocumentChunk.document_id) == document_id)
        )
        document = session.get(SourceDocument, document_id)
        assert document is not None
        document.status = DocumentStatus.failed
        document.error_message = message
        session.add(document)
        session.commit()
        raise IndexingError(message) from None
