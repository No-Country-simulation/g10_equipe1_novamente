import uuid
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core import llm
from app.core.config import settings
from app.core.storage import InMemoryStorage
from app.models import DocumentChunk, DocumentStatus, SourceDocument
from app.services import documents
from app.services.indexing import (
    DocumentNotFoundError,
    IndexingError,
    index_document,
    split_text,
)
from tests.utils.course import create_course
from tests.utils.user import create_random_user


def test_split_text() -> None:
    assert [(c.index, c.text, c.page_number) for c in split_text("a" * 300)] == [
        (0, "a" * 300, None)
    ]
    assert [len(c.text) for c in split_text("a" * 2500)] == [1000, 1000, 500]
    text = "\n\n".join(["a" * 400] * 6)
    chunks = split_text(text)
    assert [c.text for c in chunks] == ["\n\n".join(["a" * 400] * 2)] * 3
    assert [c.index for c in chunks] == [0, 1, 2]
    assert all(len(c.text) <= 1000 for c in chunks)
    assert "".join("".join(c.text.split()) for c in chunks) == "".join(text.split())
    assert [c.text for c in split_text("A. B. C. D.", chunk_size=6)] == [
        "A. B.",
        "C. D.",
    ]
    sentence = "Uma frase curta. "
    long_text = sentence * 90
    sentence_chunks = split_text(long_text)
    assert len(sentence_chunks) > 1
    assert all(c.text.endswith(".") and len(c.text) <= 1000 for c in sentence_chunks)
    assert "".join("".join(c.text.split()) for c in sentence_chunks) == "".join(
        long_text.split()
    )
    assert split_text("") == []
    assert split_text(" \n ") == []
    assert [(c.text, c.page_number) for c in split_text("A\fB", paged=True)] == [
        ("A", 1),
        ("B", 2),
    ]
    assert [(c.text, c.page_number) for c in split_text("A\f\fC", paged=True)] == [
        ("A", 1),
        ("C", 3),
    ]
    assert split_text("A\fB")[0].text == "A B"
    assert [len(c.text) for c in split_text("x" * 101, chunk_size=50)] == [50, 50, 1]
    with pytest.raises(ValueError):
        split_text("x", chunk_size=0)


@pytest.fixture
def setup_document(
    client: TestClient, db: Session
) -> tuple[SourceDocument, InMemoryStorage]:
    user = create_random_user(db)
    course = create_course(
        client=client,
        owner_email=user.email,
        documents=[
            {"original_filename": "guia.md", "status": "uploaded", "chunks": []}
        ],
        contents=[{"format": "tutorial", "status": "pending"}],
    )
    doc = db.get(SourceDocument, uuid.UUID(course["documents"][0]["id"]))
    assert doc is not None
    storage = InMemoryStorage()
    storage.put(
        doc.oci_object_key, b"a" * 1000 + b"b" * 1000 + b"c" * 500, "text/markdown"
    )
    return doc, storage


def rows(db: Session, doc: SourceDocument) -> list[DocumentChunk]:
    return list(
        db.exec(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == doc.id)
            .order_by(DocumentChunk.chunk_index)
        ).all()
    )


def test_index_and_retry(
    db: Session,
    setup_document: tuple[SourceDocument, InMemoryStorage],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc, storage = setup_document
    calls = []

    def embed(texts, *, task):
        calls.append((texts, task))
        return [[float(i + 1)] * 768 for i, _ in enumerate(texts)]

    monkeypatch.setattr(llm, "embed_texts", embed)
    assert index_document(session=db, storage=storage, document_id=doc.id) == 3
    assert calls == [(["a" * 1000, "b" * 1000, "c" * 500], "document")]
    assert [(c.text, list(c.embedding)) for c in rows(db, doc)] == [
        ("a" * 1000, [1.0] * 768),
        ("b" * 1000, [2.0] * 768),
        ("c" * 500, [3.0] * 768),
    ]
    old_ids = {c.id for c in rows(db, doc)}
    assert [c.chunk_index for c in rows(db, doc)] == [0, 1, 2]
    assert all(
        c.course_id == doc.course_id and len(c.embedding) == 768 for c in rows(db, doc)
    )
    assert (
        doc.status == DocumentStatus.indexed
        and doc.embedding_model == settings.GEMINI_EMBEDDING_MODEL
    )
    storage.delete(doc.oci_object_key)
    assert index_document(session=db, storage=storage, document_id=doc.id) == 3
    assert len(calls) == 1
    doc.status = DocumentStatus.failed
    doc.error_message = "erro"
    db.add(doc)
    db.commit()
    storage.put(doc.oci_object_key, b"novo documento", "text/markdown")
    assert index_document(session=db, storage=storage, document_id=doc.id) == 1
    assert doc.status == DocumentStatus.indexed and doc.error_message is None
    assert [c.text for c in rows(db, doc)] == ["novo documento"]
    assert old_ids.isdisjoint({c.id for c in rows(db, doc)})


@pytest.mark.parametrize(
    "failure, expected",
    [
        ("storage", "Não foi possível ler o documento guia.md no armazenamento."),
        ("utf8", "guia.md: Não foi possível ler o arquivo como texto."),
        (
            "key",
            "Não foi possível indexar o documento guia.md: a chave do Gemini não está configurada.",
        ),
        (
            "llm",
            "Não foi possível indexar o documento guia.md: o modelo de embeddings falhou.",
        ),
        (
            "rate_limit",
            "Não foi possível indexar o documento guia.md. "
            "A API Gemini recusou o pedido por limite de uso (429). "
            "Tente de novo mais tarde.",
        ),
        ("other", "Não foi possível indexar o documento guia.md."),
        ("empty", "guia.md: O arquivo não tem texto."),
    ],
)
def test_failures(
    db: Session,
    setup_document: tuple[SourceDocument, InMemoryStorage],
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    expected: str,
) -> None:
    doc, storage = setup_document
    db.add(
        DocumentChunk(
            document_id=doc.id,
            course_id=doc.course_id,
            chunk_index=0,
            text="antigo",
            embedding=[0.0] * 768,
        )
    )
    db.commit()
    if failure == "storage":
        storage.delete(doc.oci_object_key)
    elif failure == "utf8":
        storage.put(doc.oci_object_key, b"\xff", "text/markdown")
    elif failure == "empty":
        original = documents.read_document
        monkeypatch.setattr(
            documents,
            "read_document",
            lambda name, data: replace(original(name, data), text=" "),
        )
    else:
        exc = {
            "key": llm.LLMNotConfiguredError("segredo"),
            "llm": llm.LLMError("segredo"),
            "rate_limit": llm.LLMRateLimitError(
                "A API Gemini recusou o pedido por limite de uso (429). "
                "Tente de novo mais tarde."
            ),
            "other": RuntimeError("segredo"),
        }[failure]

        def fail(*_args, **_kwargs):
            raise exc

        monkeypatch.setattr(llm, "embed_texts", fail)
    with pytest.raises(IndexingError) as raised:
        index_document(session=db, storage=storage, document_id=doc.id)
    db.refresh(doc)
    assert expected == str(raised.value) == doc.error_message
    assert "segredo" not in str(raised.value)
    assert doc.status == DocumentStatus.failed and rows(db, doc) == []


def test_pdf_and_missing(
    db: Session,
    setup_document: tuple[SourceDocument, InMemoryStorage],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc, storage = setup_document
    original = documents.read_document
    monkeypatch.setattr(
        documents,
        "read_document",
        lambda name, data: replace(
            original(name, data), text="A\fB", mime_type="application/pdf"
        ),
    )
    monkeypatch.setattr(
        llm, "embed_texts", lambda texts, *, task: [[0.0] * 768 for _ in texts]
    )
    assert index_document(session=db, storage=storage, document_id=doc.id) == 2
    assert [c.page_number for c in rows(db, doc)] == [1, 2]
    with pytest.raises(DocumentNotFoundError):
        index_document(session=db, storage=storage, document_id=uuid.uuid4())


def test_commit_failure(
    db: Session,
    setup_document: tuple[SourceDocument, InMemoryStorage],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc, storage = setup_document
    monkeypatch.setattr(
        llm, "embed_texts", lambda texts, *, task: [[0.0] * 768 for _ in texts]
    )
    commit = db.commit
    calls = 0

    def flaky_commit():
        nonlocal calls
        calls += 1
        if calls == 2:
            db.flush()
            raise RuntimeError("falha")
        commit()

    monkeypatch.setattr(db, "commit", flaky_commit)
    with pytest.raises(IndexingError) as raised:
        index_document(session=db, storage=storage, document_id=doc.id)
    db.refresh(doc)
    assert (
        str(raised.value)
        == doc.error_message
        == "Não foi possível indexar o documento guia.md."
    )
    assert doc.status == DocumentStatus.failed and rows(db, doc) == []
