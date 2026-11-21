import hashlib
import uuid
from collections.abc import Iterator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.storage import InMemoryStorage, StorageError, document_key, get_storage
from app.main import app
from app.models import Course, CourseContent, Niche, SourceDocument
from app.services import course_generation
from tests.utils.user import authentication_token_from_email, create_random_user

URL = f"{settings.API_V1_STR}/courses/"


@pytest.fixture(autouse=True)
def generation(monkeypatch):
    task = Mock()
    monkeypatch.setattr(course_generation, "run_course_generation", task)
    return task


@pytest.fixture
def storage() -> Iterator[InMemoryStorage]:
    result = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: result
    yield result
    app.dependency_overrides.pop(get_storage, None)


@pytest.fixture
def headers(client: TestClient, db: Session) -> dict[str, str]:
    user = create_random_user(db)
    return authentication_token_from_email(client=client, email=user.email, db=db)


def send(
    client,
    headers,
    *,
    title="Curso",
    niche="1",
    level="non_technical",
    formats=("tutorial",),
    files=(("guia.md", b"conteudo"),),
):
    fields = [("niche_id", (None, niche)), ("audience_level", (None, level))]
    if title is not None:
        fields.append(("title", (None, title)))
    fields.extend(("formats", (None, fmt)) for fmt in formats)
    fields.extend(("files", (name, data, "text/markdown")) for name, data in files)
    return client.post(URL, headers=headers, files=fields)


def assert_empty(client, headers, storage):
    assert storage.list("courses/") == []
    assert client.get(URL, headers=headers).json()["count"] == 0


def test_create_course(client: TestClient, db: Session, headers, storage, generation):
    niche = db.exec(select(Niche)).first()
    response = send(client, headers, title=" Curso ", niche=str(niche.id))
    assert response.status_code == 201, response.text
    course = response.json()
    course_id = uuid.UUID(course["id"])
    generation_id = db.get_one(Course, course_id).generation_id
    assert isinstance(generation_id, uuid.UUID)
    generation.assert_called_once_with(
        storage=storage, course_id=course_id, generation_id=generation_id
    )
    assert "generation_id" not in course
    assert course["title"] == "Curso"
    assert course["status"] == "initializing"
    assert course["niche"]["id"] == niche.id
    assert course["audience_level"] == "non_technical"
    doc = course["documents"][0]
    assert (
        doc["title"],
        doc["original_filename"],
        doc["mime_type"],
        doc["size_bytes"],
        doc["status"],
    ) == ("guia.md", "guia.md", "text/markdown", 8, "uploaded")
    content = course["contents"][0]
    assert (content["format"], content["position"], content["status"]) == (
        "tutorial",
        0,
        "pending",
    )
    row = db.get(SourceDocument, uuid.UUID(doc["id"]))
    key = document_key(uuid.UUID(course["id"]), row.id, "md")
    assert row.sha256 == hashlib.sha256(b"conteudo").hexdigest()
    assert row.oci_object_key == key
    assert storage.get(key) == b"conteudo"
    assert db.get(CourseContent, uuid.UUID(content["id"])).focus == "Curso"
    assert client.get(URL + course["id"], headers=headers).json() == course
    assert any(
        item["id"] == course["id"]
        for item in client.get(URL, headers=headers).json()["data"]
    )
    other = create_random_user(db)
    other_headers = authentication_token_from_email(
        client=client, email=other.email, db=db
    )
    assert client.get(URL + course["id"], headers=other_headers).status_code == 404


def test_three_files_and_order(client, headers, storage):
    response = send(
        client,
        headers,
        formats=("quiz", "tutorial", "flashcards"),
        files=(("a.md", b"a"), ("b.md", b"b"), ("c.md", b"c")),
    )
    assert response.status_code == 201, response.text
    assert [(c["format"], c["position"]) for c in response.json()["contents"]] == [
        ("quiz", 0),
        ("tutorial", 1),
        ("flashcards", 2),
    ]
    assert len(storage.list("courses/")) == 3


@pytest.mark.parametrize(
    ("kwargs", "status", "detail"),
    [
        ({"title": None}, 422, "Informe um título."),
        ({"title": "   "}, 422, "Informe um título."),
        ({"title": "a" * 256}, 422, "O título passa de 255 caracteres."),
        (
            {"files": (), "formats": ()},
            422,
            "Envie pelo menos um documento e escolha pelo menos uma saída.",
        ),
        (
            {"files": ()},
            422,
            "Envie pelo menos um documento e escolha pelo menos uma saída.",
        ),
        (
            {"formats": ()},
            422,
            "Envie pelo menos um documento e escolha pelo menos uma saída.",
        ),
        (
            {"files": (("a.md", b"a"),) * 4},
            422,
            "Envie até 3 documentos e escolha até 3 saídas.",
        ),
        (
            {"formats": ("tutorial",) * 4},
            422,
            "Envie até 3 documentos e escolha até 3 saídas.",
        ),
        (
            {"formats": ("tutorial", "tutorial")},
            422,
            "Escolha só uma saída de cada formato.",
        ),
        (
            {"files": (("notas.txt", b"a"),)},
            422,
            "notas.txt: Envie um arquivo .md ou PDF, ou digite o texto.",
        ),
        ({"files": (("a.md", b""),)}, 422, "a.md: O arquivo não tem texto."),
        (
            {"files": (("a.md", b"a" * (5 * 1024 * 1024 + 1)),)},
            422,
            "a.md: O arquivo passa de 5 MiB.",
        ),
        (
            {"files": (("a.md", b"a"), ("b.md", b"a"))},
            422,
            "b.md: Este arquivo já está no curso.",
        ),
        ({"niche": "32767"}, 404, "Setor não encontrado."),
    ],
)
def test_invalid_input(client, headers, storage, generation, kwargs, status, detail):
    response = send(client, headers, **kwargs)
    assert response.status_code == status
    assert response.json()["detail"] == detail
    assert_empty(client, headers, storage)
    generation.assert_not_called()


def test_max_title_and_invalid_types(client, headers, storage, generation):
    assert send(client, headers, level="invalido").status_code == 422
    assert send(client, headers, formats=("invalido",)).status_code == 422
    assert send(client, headers, niche="invalido").status_code == 422
    assert_empty(client, headers, storage)
    generation.assert_not_called()
    assert send(client, headers, title="a" * 255).status_code == 201


def test_anonymous(client, generation):
    assert send(client, {}).status_code == client.get(URL).status_code
    generation.assert_not_called()


def test_second_put_failure(client, headers, storage, monkeypatch, generation):
    original = storage.put

    def put(key, data, content_type):
        if storage.list("courses/"):
            raise StorageError()
        original(key, data, content_type)

    monkeypatch.setattr(storage, "put", put)
    response = send(client, headers, files=(("a.md", b"a"), ("b.md", b"b")))
    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "O armazenamento de arquivos não está disponível. Tente novamente mais tarde."
    )
    assert_empty(client, headers, storage)
    generation.assert_not_called()


def test_commit_failure(client, headers, storage, generation):
    with patch.object(Session, "commit", side_effect=RuntimeError("commit")):
        with pytest.raises(RuntimeError, match="commit"):
            send(client, headers)
    assert_empty(client, headers, storage)
    generation.assert_not_called()


def test_unconfigured_storage(client, headers, monkeypatch, generation):
    monkeypatch.setattr(settings, "OCI_BUCKET", None)
    monkeypatch.setattr(settings, "OCI_NAMESPACE", None)
    get_storage.cache_clear()
    assert send(client, headers, title=" ").json()["detail"] == "Informe um título."
    assert send(client, headers, niche="32767").status_code == 404
    response = send(client, headers)
    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "O armazenamento de arquivos não está disponível. Tente novamente mais tarde."
    )
    generation.assert_not_called()
    get_storage.cache_clear()
