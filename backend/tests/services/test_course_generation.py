import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from threading import Barrier
from unittest.mock import Mock

import pytest
from sqlalchemy import text
from sqlalchemy.sql.dml import Update
from sqlmodel import Session, select

from app.core import llm
from app.core.config import settings
from app.core.db import engine
from app.core.security import create_access_token
from app.core.storage import InMemoryStorage, StorageError, get_storage
from app.main import app
from app.models import (
    ContentCitation,
    Course,
    CourseContent,
    DocumentChunk,
    Niche,
    SourceDocument,
    get_datetime_utc,
)
from app.services import course_generation, generation_graph, indexing, publishing
from app.services.content_schemas import GENERATED_MODELS
from app.services.generation_graph import GenerationResult
from app.services.grounding import ClaimReview, Decision, ReviewResult, evaluate
from tests.services.test_content_schemas import generated
from tests.utils.course import create_course
from tests.utils.user import create_random_user

FORMATS = ["quiz", "tutorial", "flashcards"]
TEXTS = ["VCNs são redes virtuais privadas.", "Sub-redes dividem uma VCN."]
REJECTED = "O documento não trata do assunto pedido."


@dataclass
class CourseSetup:
    course_id: uuid.UUID
    document_ids: list[uuid.UUID]
    content_ids: list[uuid.UUID]
    storage: InMemoryStorage
    generation_id: uuid.UUID
    headers: dict[str, str]

    def run(self):
        course_generation.run_course_generation(
            storage=self.storage,
            course_id=self.course_id,
            generation_id=self.generation_id,
        )

    def retry(self, client, position):
        return client.post(
            f"/api/v1/courses/{self.course_id}/contents/{self.content_ids[position]}/retry",
            headers=self.headers,
        )

    def contents(self, session):
        return [
            session.get_one(CourseContent, content_id)
            for content_id in self.content_ids
        ]


@pytest.fixture
def setup(client, db, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_GENERATION_MODEL", "modelo-de-teste")
    owner = create_random_user(db)
    data = create_course(
        client=client,
        owner_email=owner.email,
        title="Redes na OCI",
        status="initializing",
        documents=[
            {"original_filename": name, "status": "uploaded"}
            for name in ("a.md", "b.md")
        ],
        contents=[{"format": fmt, "status": "pending"} for fmt in FORMATS],
    )
    storage = InMemoryStorage()
    monkeypatch.setitem(app.dependency_overrides, get_storage, lambda: storage)
    course_id = uuid.UUID(data["id"])
    generation_id = uuid.uuid4()
    db.get_one(Course, course_id).generation_id = generation_id
    token = create_access_token(owner.id, timedelta(minutes=5))
    documents = sorted(data["documents"], key=lambda doc: doc["original_filename"])
    document_ids = [uuid.UUID(doc["id"]) for doc in documents]
    for document_id, document_text in zip(document_ids, TEXTS, strict=True):
        document = db.get_one(SourceDocument, document_id)
        storage.put(document.oci_object_key, document_text.encode(), document.mime_type)
    content_ids = [uuid.UUID(content["id"]) for content in data["contents"]]
    for content_id, fmt in zip(content_ids, FORMATS, strict=True):
        db.get_one(CourseContent, content_id).focus = f"Redes na OCI para {fmt}"
    db.commit()
    return CourseSetup(
        course_id,
        document_ids,
        content_ids,
        storage,
        generation_id,
        {"Authorization": f"Bearer {token}"},
    )


def _embedding(texts, *, task):  # noqa: ARG001
    return [[1.0] + [0.0] * 767 for _ in texts]


def _approve(request):
    fmt = request.content_format
    review = ReviewResult(
        claims=[
            ClaimReview(claim=chunk.text, chunk_id=chunk.chunk_id, supported=True)
            for chunk in request.chunks
        ],
        clarity="high",
        review_notes="A versão cobre o foco.",
        focus_covered=True,
    )
    report = evaluate(review, {chunk.chunk_id for chunk in request.chunks})
    return GenerationResult(
        Decision.publish,
        1,
        GENERATED_MODELS[fmt].model_validate(generated(fmt)),
        review,
        report,
        None,
    )


def _reject():
    return GenerationResult(Decision.fail, 1, None, None, None, REJECTED)


@pytest.fixture(autouse=True)
def agents(monkeypatch):
    embed = Mock(side_effect=_embedding)
    graph = Mock(side_effect=_approve)
    monkeypatch.setattr(llm, "embed_texts", embed)
    monkeypatch.setattr(generation_graph, "generate_content", graph)
    return embed, graph


def test_generates_and_publishes_three_formats_in_order(setup, agents, caplog):
    embed, graph = agents

    def generate(request):
        if request.content_format == "tutorial":
            with Session(engine) as observer:
                quiz, tutorial, flashcards = setup.contents(observer)
                assert quiz.status == "succeeded"
                assert observer.get_one(Course, setup.course_id).status == "ready"
                assert tutorial.status == "running"
                assert tutorial.llm_model == settings.GEMINI_GENERATION_MODEL
                assert tutorial.prompt_version == generation_graph.PROMPT_VERSION
                assert flashcards.status == "pending"
        return _approve(request)

    graph.side_effect = generate
    with caplog.at_level(logging.INFO, logger=course_generation.logger.name):
        setup.run()

    with Session(engine) as db:
        course = db.get_one(Course, setup.course_id)
        niche = db.get_one(Niche, course.niche_id)
        assert course.status == "ready"
        assert all(
            db.get_one(SourceDocument, id).status == "indexed"
            for id in setup.document_ids
        )
        for content in setup.contents(db):
            assert content.status == "succeeded"
            assert content.llm_model == settings.GEMINI_GENERATION_MODEL
            assert content.prompt_version == generation_graph.PROMPT_VERSION
    assert len(setup.storage.list(f"courses/{setup.course_id}/contents/")) == 3
    requests = [call.args[0] for call in graph.call_args_list]
    assert [request.content_format for request in requests] == FORMATS
    assert [request.focus for request in requests] == [
        f"Redes na OCI para {fmt}" for fmt in FORMATS
    ]
    for request in requests:
        assert request.audience_level == "technical_basic"
        assert request.niche_name == niche.name
        assert request.niche_prompt_hint == niche.prompt_hint
        assert {chunk.document_id for chunk in request.chunks} == set(
            setup.document_ids
        )
    assert [(call.args[0], call.kwargs["task"]) for call in embed.call_args_list] == [
        *(([text], "document") for text in TEXTS),
        *(([request.focus], "query") for request in requests),
    ]
    assert "formato=tutorial estado=succeeded tentativas=1 segundos=" in caplog.text
    assert f"course_id={setup.course_id} estado=ready segundos=" in caplog.text


def test_ends_transaction_before_generation(setup, agents):
    _, graph = agents
    idle_transactions = []

    def generate(request):
        with Session(engine) as observer:
            idle_transactions.append(
                observer.execute(
                    text("""
                        SELECT pid FROM pg_stat_activity
                        WHERE datname = current_database()
                          AND pid <> pg_backend_pid()
                          AND state = 'idle in transaction'
                    """)
                )
                .scalars()
                .all()
            )
        return _approve(request)

    graph.side_effect = generate
    setup.run()
    assert idle_transactions == [[], [], []]


@pytest.mark.parametrize("unexpected", [False, True])
def test_indexing_failure_stops_generation(
    setup, db, agents, monkeypatch, caplog, unexpected
):
    _, graph = agents
    first_id, second_id = setup.document_ids
    second = db.get_one(SourceDocument, second_id)
    if unexpected:
        index = indexing.index_document

        def index_or_raise(*, document_id, **kwargs):
            if document_id == second_id:
                raise RuntimeError("falha inesperada")
            return index(document_id=document_id, **kwargs)

        monkeypatch.setattr(indexing, "index_document", index_or_raise)
        error = "Não foi possível indexar o documento b.md."
    else:
        setup.storage.delete(second.oci_object_key)
        error = "Não foi possível ler o documento b.md no armazenamento."
    setup.run()
    db.expire_all()
    graph.assert_not_called()
    assert db.get_one(SourceDocument, first_id).status == "indexed"
    assert (second.status, second.error_message) == ("failed", error)
    assert db.get_one(Course, setup.course_id).status == "failed"
    for content in setup.contents(db):
        assert content.status == "failed"
        assert (
            content.error_message
            == "O conteúdo não foi gerado, porque um documento do curso falhou."
        )
        assert content.llm_model is None
    if unexpected:
        assert any(
            record.levelno == logging.ERROR
            and str(setup.course_id) in record.message
            and str(second_id) in record.message
            for record in caplog.records
        )


@pytest.mark.parametrize("failure", ["review", "embedding", "storage", "unexpected"])
def test_content_failure_continues_with_next(
    setup, db, agents, monkeypatch, caplog, failure
):
    embed, graph = agents
    first_id = setup.content_ids[0]
    if failure == "review":
        graph.side_effect = lambda request: (
            _reject() if request.content_format == "quiz" else _approve(request)
        )
        message = REJECTED
    elif failure == "embedding":

        def embed_or_raise(texts, *, task):
            if task == "query" and texts == ["Redes na OCI para quiz"]:
                raise llm.LLMError("cota")
            return _embedding(texts, task=task)

        embed.side_effect = embed_or_raise
        message = "Não foi possível gerar o conteúdo. cota"
    elif failure == "storage":
        put = setup.storage.put

        def fail_first_write(key, data, content_type):
            if f"/contents/{first_id}/" in key:
                raise StorageError()
            put(key, data, content_type)

        monkeypatch.setattr(setup.storage, "put", fail_first_write)
        message = "Não foi possível guardar o conteúdo no armazenamento."
    else:

        def generate(request):
            if request.content_format == "quiz":
                raise RuntimeError("falha inesperada")
            return _approve(request)

        graph.side_effect = generate
        message = "Não foi possível gerar o conteúdo."
    setup.run()
    db.expire_all()
    first, second, third = setup.contents(db)
    assert (first.status, second.status, third.status) == (
        "failed",
        "succeeded",
        "succeeded",
    )
    assert first.error_message == message
    assert first.content is None and first.oci_object_key is None
    assert first.llm_model == settings.GEMINI_GENERATION_MODEL
    assert first.prompt_version == generation_graph.PROMPT_VERSION
    assert db.get_one(Course, setup.course_id).status == "ready"
    if failure == "unexpected":
        assert any(
            record.levelno == logging.ERROR
            and str(setup.course_id) in record.message
            and str(first_id) in record.message
            for record in caplog.records
        )


def test_all_rejected_marks_course_failed(setup, db, agents):
    _, graph = agents
    graph.side_effect = lambda _request: _reject()
    before = db.get_one(Course, setup.course_id).updated_at
    setup.run()
    db.expire_all()
    course = db.get_one(Course, setup.course_id)
    assert course.status == "failed"
    assert course.updated_at > before
    assert all(content.status == "failed" for content in setup.contents(db))
    assert setup.storage.list(f"courses/{setup.course_id}/contents/") == []


def test_skips_content_reserved_by_another_session(setup, db, agents, monkeypatch):
    _, graph = agents
    graph.side_effect = lambda _request: _reject()
    exec_statement = Session.exec
    raced = False

    def reserve_elsewhere(session, statement, *args, **kwargs):
        nonlocal raced
        if (
            isinstance(statement, Update)
            and statement.entity_description["entity"] is CourseContent
            and not raced
        ):
            raced = True
            with Session(engine) as other:
                other.get_one(CourseContent, setup.content_ids[0]).status = "running"
                other.commit()
        return exec_statement(session, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "exec", reserve_elsewhere)
    setup.run()
    db.expire_all()
    assert [call.args[0].content_format for call in graph.call_args_list] == FORMATS[1:]
    assert [c.status for c in setup.contents(db)] == ["running", "failed", "failed"]
    assert db.get_one(Course, setup.course_id).status == "initializing"


def test_reservation_commit_failure_recovers_pending_content(
    setup, db, agents, monkeypatch
):
    for document_id in setup.document_ids:
        indexing.index_document(
            session=db, storage=setup.storage, document_id=document_id
        )

    commit = Session.commit
    sessions = []

    def fail_first_commit(session):
        sessions.append(session)
        if len(sessions) == 1:
            raise RuntimeError("falha ao confirmar a reserva")
        commit(session)

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", fail_first_commit)
        setup.run()
    db.expire_all()
    first, second, third = setup.contents(db)
    assert sessions[1] is not sessions[0]
    assert (first.status, second.status, third.status) == (
        "failed",
        "succeeded",
        "succeeded",
    )
    assert first.error_message == "Não foi possível gerar o conteúdo."
    assert first.llm_model is None and first.prompt_version is None
    _, graph = agents
    assert [call.args[0].content_format for call in graph.call_args_list] == FORMATS[1:]


def test_recovery_write_failure_stops_task_without_raising(
    setup, agents, caplog, monkeypatch
):
    _, graph = agents
    graph.side_effect = RuntimeError("falha na geração")
    recover = Mock(side_effect=RuntimeError("falha ao gravar a recuperação"))
    monkeypatch.setattr(course_generation, "_fail_content", recover)

    setup.run()

    graph.assert_called_once()
    recover.assert_called_once()
    with Session(engine) as db:
        assert [content.status for content in setup.contents(db)] == [
            "running",
            "pending",
            "pending",
        ]
        assert db.get_one(Course, setup.course_id).status == "initializing"
    assert any(
        record.levelno == logging.ERROR
        and record.message == f"Falha na tarefa de fundo course_id={setup.course_id}"
        and record.exc_info is not None
        and str(record.exc_info[1]) == "falha ao gravar a recuperação"
        for record in caplog.records
    )


def test_rejected_retry_preserves_publication(setup, db, agents, client):
    _, second, third = setup.contents(db)
    second.status = third.status = "failed"
    db.commit()
    setup.run()
    db.expire_all()
    content = setup.contents(db)[0]
    citations = select(ContentCitation).where(ContentCitation.content_id == content.id)
    before = content.model_dump(exclude={"status", "error_message", "updated_at"})
    before_citations = [row.model_dump() for row in db.exec(citations)]
    key = content.oci_object_key
    old_object = setup.storage.get(key)
    content.status = "failed"
    db.commit()
    _, graph = agents
    graph.side_effect = lambda _request: _reject()
    assert setup.retry(client, 0).status_code == 202
    db.expire_all()
    assert (content.status, content.error_message) == ("failed", REJECTED)
    assert (
        content.model_dump(exclude={"status", "error_message", "updated_at"}) == before
    )
    assert [row.model_dump() for row in db.exec(citations)] == before_citations
    assert setup.storage.get(key) == old_object
    assert db.get_one(Course, setup.course_id).status == "ready"


def test_missing_course_logs_warning(caplog, agents):
    course_id = uuid.uuid4()
    course_generation.run_course_generation(
        storage=InMemoryStorage(), course_id=course_id, generation_id=uuid.uuid4()
    )
    assert f"Curso não encontrado course_id={course_id}" in caplog.text
    for mock in agents:
        mock.assert_not_called()


def test_no_chunks_for_current_model(setup, db, agents, monkeypatch):
    for document_id in setup.document_ids:
        indexing.index_document(
            session=db, storage=setup.storage, document_id=document_id
        )
    monkeypatch.setattr(settings, "GEMINI_EMBEDDING_MODEL", "outro-modelo")
    setup.run()
    db.expire_all()
    agents[1].assert_not_called()
    assert db.get_one(Course, setup.course_id).status == "failed"
    for content in setup.contents(db):
        assert content.status == "failed"
        assert (
            content.error_message
            == "Não foi possível gerar o conteúdo, porque o curso não tem trechos indexados."
        )


def test_retry_joins_active_queue_once(setup, agents, client, monkeypatch):
    _, graph = agents
    run = course_generation.run_course_generation
    task = Mock()
    monkeypatch.setattr(course_generation, "run_course_generation", task)
    barrier = Barrier(2, timeout=5)
    calls = []

    def retry():
        barrier.wait()
        return setup.retry(client, 0)

    def generate(request):
        calls.append(request.content_format)
        if calls == ["quiz"]:
            return _reject()
        if request.content_format == "tutorial":
            with ThreadPoolExecutor(max_workers=2) as workers:
                replies = list(workers.map(lambda _: retry(), range(2)))
            assert sorted(reply.status_code for reply in replies) == [202, 409]
            with Session(engine) as other:
                assert (
                    other.get_one(Course, setup.course_id).generation_id
                    == setup.generation_id
                )
        return _approve(request)

    graph.side_effect = generate
    run(
        storage=setup.storage,
        course_id=setup.course_id,
        generation_id=setup.generation_id,
    )
    assert calls == ["quiz", "tutorial", "quiz", "flashcards"]
    task.assert_not_called()
    with Session(engine) as db:
        assert [c.status for c in setup.contents(db)] == ["succeeded"] * 3
        assert db.get_one(Course, setup.course_id).generation_id is None


@pytest.mark.parametrize(
    ("second_document_minutes", "content_status", "second_document_status"),
    [(6, "succeeded", "indexed"), (11, "failed", "failed")],
)
def test_indexing_deadline_tracks_each_document(
    client,
    db,
    agents,
    monkeypatch,
    second_document_minutes,
    content_status,
    second_document_status,
):
    owner = create_random_user(db)
    token = create_access_token(owner.id, timedelta(minutes=5))
    headers = {"Authorization": f"Bearer {token}"}
    niche = db.exec(select(Niche).where(Niche.slug == "geral")).one()
    monkeypatch.setitem(app.dependency_overrides, get_storage, InMemoryStorage)
    monkeypatch.setattr(settings, "GEMINI_GENERATION_MODEL", "modelo-de-teste")
    now = get_datetime_utc()
    monkeypatch.setattr(course_generation, "get_datetime_utc", lambda: now)
    monkeypatch.setattr(publishing, "datetime", Mock(now=lambda _tz: now))
    document_times = iter((6, second_document_minutes))

    def embed(texts, *, task):
        nonlocal now
        if task == "document":
            now += timedelta(minutes=next(document_times))
            course_generation.expire_stalled_courses()
        return _embedding(texts, task=task)

    agents[0].side_effect = embed
    created = client.post(
        "/api/v1/courses/",
        headers=headers,
        data={
            "title": "Redes na OCI",
            "niche_id": niche.id,
            "audience_level": "technical_basic",
            "formats": "tutorial",
        },
        files=[
            ("files", (f"{name}.md", content.encode(), "text/markdown"))
            for name, content in zip(("a", "b"), TEXTS, strict=True)
        ],
    )
    assert created.status_code == 201
    course_id = uuid.UUID(created.json()["id"])
    result = client.get(f"/api/v1/courses/{course_id}", headers=headers)
    assert result.status_code == 200
    course = result.json()
    assert course["contents"][0]["status"] == content_status
    assert {doc["original_filename"]: doc["status"] for doc in course["documents"]} == {
        "a.md": "indexed",
        "b.md": second_document_status,
    }
    with Session(engine) as observer:
        assert observer.get_one(Course, course_id).generation_id is None
    if content_status == "failed":
        assert course["contents"][0]["error_message"] == (
            course_generation.GENERATION_INTERRUPTED
        )
        agents[1].assert_not_called()


@pytest.fixture
def stalled_clock(monkeypatch):
    now = get_datetime_utc()
    monkeypatch.setattr(course_generation, "get_datetime_utc", lambda: now)

    def advance():
        nonlocal now
        now = get_datetime_utc() + timedelta(minutes=10)

    return advance


@pytest.mark.parametrize("late_error", [False, True])
def test_stalled_indexing_cannot_write_into_retry(
    setup, db, agents, client, monkeypatch, stalled_clock, late_error
):
    run = course_generation.run_course_generation
    task = Mock()
    monkeypatch.setattr(course_generation, "run_course_generation", task)
    doc_id = setup.document_ids[0]

    def embed(texts, *, task):
        assert task == "document"
        stalled_clock()
        course_generation.expire_stalled_courses()
        with Session(engine) as other:
            document = other.get_one(SourceDocument, doc_id)
            assert (document.status, document.error_message) == (
                "failed",
                course_generation.GENERATION_INTERRUPTED,
            )
            assert [c.status for c in setup.contents(other)] == ["failed"] * 3
            assert other.get_one(Course, setup.course_id).status == "failed"
        assert setup.retry(client, 0).status_code == 202
        if late_error:
            raise llm.LLMError("erro da tarefa que expirou")
        return _embedding(texts, task=task)

    agents[0].side_effect = embed
    run(
        storage=setup.storage,
        course_id=setup.course_id,
        generation_id=setup.generation_id,
    )
    db.expire_all()
    assert (
        db.exec(select(DocumentChunk).where(DocumentChunk.document_id == doc_id)).all()
        == []
    )
    assert setup.contents(db)[0].error_message is None
    assert (
        db.get_one(SourceDocument, doc_id).error_message
        == course_generation.GENERATION_INTERRUPTED
    )
    next_generation = task.call_args.kwargs["generation_id"]
    assert next_generation != setup.generation_id
    assert db.get_one(Course, setup.course_id).generation_id == next_generation

    db.rollback()
    agents[0].side_effect = _embedding
    monkeypatch.setattr(course_generation, "get_datetime_utc", get_datetime_utc)
    run(**task.call_args.kwargs)
    db.expire_all()
    assert db.get_one(SourceDocument, doc_id).status == "indexed"
    assert setup.contents(db)[0].status == "succeeded"


@pytest.mark.parametrize("late_error", [False, True])
def test_stalled_generation_preserves_publication_and_retry(
    setup, agents, client, monkeypatch, stalled_clock, late_error
):
    run = course_generation.run_course_generation
    task = Mock()
    monkeypatch.setattr(course_generation, "run_course_generation", task)
    _, graph = agents
    prefix = f"courses/{setup.course_id}/contents/"
    published = []

    def generate(request):
        if request.content_format == "quiz":
            return _approve(request)
        with Session(engine) as other:
            first = setup.contents(other)[0]
            published.extend((first.content, first.oci_object_key))
        stalled_clock()
        course_generation.expire_stalled_courses()
        with Session(engine) as other:
            assert other.get_one(Course, setup.course_id).status == "ready"
            assert [c.status for c in setup.contents(other)] == [
                "succeeded",
                "failed",
                "failed",
            ]
            assert (
                setup.contents(other)[1].error_message
                == course_generation.GENERATION_INTERRUPTED
            )
        assert setup.retry(client, 1).status_code == 202
        if late_error:
            raise RuntimeError("erro da tarefa que expirou")
        return _approve(request)

    graph.side_effect = generate
    run(
        storage=setup.storage,
        course_id=setup.course_id,
        generation_id=setup.generation_id,
    )
    task.assert_called_once()
    with Session(engine) as db:
        first, second, third = setup.contents(db)
        assert (second.status, second.error_message) == ("pending", None)
        assert third.error_message == course_generation.GENERATION_INTERRUPTED
        assert [first.content, first.oci_object_key] == published
        assert db.exec(
            select(ContentCitation.content_id).where(
                ContentCitation.course_id == setup.course_id
            )
        ).all() == [first.id, first.id]
        assert setup.storage.list(prefix) == [first.oci_object_key]


def test_recovery_keeps_old_pending_while_course_makes_progress(setup, db):
    first, second, third = setup.contents(db)
    first.updated_at = third.updated_at = get_datetime_utc() - timedelta(minutes=10)
    second.status = "running"
    db.commit()
    course_generation.expire_stalled_courses()
    db.expire_all()
    assert [c.status for c in setup.contents(db)] == ["pending", "running", "pending"]
    assert db.get_one(Course, setup.course_id).generation_id == setup.generation_id


def test_recovery_skips_locked_course(setup, db):
    expired = get_datetime_utc() - timedelta(minutes=10)
    for content in setup.contents(db):
        content.updated_at = expired
    db.commit()
    db.get_one(Course, setup.course_id, with_for_update=True)
    try:
        course_generation.expire_stalled_courses()
        assert [c.status for c in setup.contents(db)] == ["pending"] * 3
    finally:
        db.rollback()
    course_generation.expire_stalled_courses()
    assert [c.status for c in setup.contents(db)] == ["failed"] * 3


def test_retry_after_indexing_failure_reuses_indexed_documents(
    setup, db, agents, client
):
    second = db.get_one(SourceDocument, setup.document_ids[1])
    key = second.oci_object_key
    mime_type = second.mime_type
    setup.storage.delete(key)
    db.rollback()
    setup.run()
    setup.storage.put(key, TEXTS[1].encode(), mime_type)
    agents[0].reset_mock()
    assert setup.retry(client, 0).status_code == 202
    documents = [
        call.args[0]
        for call in agents[0].call_args_list
        if call.kwargs["task"] == "document"
    ]
    assert documents == [[TEXTS[1]]]
    db.expire_all()
    assert [c.status for c in setup.contents(db)] == ["succeeded", "failed", "failed"]


def test_worker_cannot_publish_after_deadline_before_recovery(
    setup, agents, stalled_clock
):
    def generate(request):
        stalled_clock()
        return _approve(request)

    agents[1].side_effect = generate
    setup.run()
    with Session(engine) as db:
        assert db.get_one(Course, setup.course_id).generation_id == setup.generation_id
        assert [c.status for c in setup.contents(db)] == [
            "running",
            "pending",
            "pending",
        ]
    assert setup.storage.list(f"courses/{setup.course_id}/contents/") == []
