import uuid
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import oci
import pytest

from app.core.config import settings
from app.core.storage import (
    InMemoryStorage,
    ObjectNotFoundError,
    OCIStorage,
    Storage,
    StorageError,
    StorageNotConfiguredError,
    content_key,
    course_prefix,
    document_key,
    get_storage,
)

SECRET = "conteudo-secreto"


def service_error(
    status: int, code: str, message: str = "mensagem do serviço"
) -> oci.exceptions.ServiceError:
    return oci.exceptions.ServiceError(status, code, {}, message)


class FakeObjectStorageClient:
    """Imita as quatro chamadas do `ObjectStorageClient` que o módulo usa."""

    def __init__(self, page_size: int = 1000) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}
        self.page_size = page_size
        self.list_calls = 0
        self.fail_with: Exception | None = None

    def _check(self, namespace: str, bucket: str) -> None:
        assert (namespace, bucket) == ("ns", "bucket")
        if self.fail_with is not None:
            raise self.fail_with

    def put_object(
        self, namespace: str, bucket: str, key: str, body: bytes, *, content_type: str
    ) -> None:
        self._check(namespace, bucket)
        self.objects[key] = body
        self.content_types[key] = content_type

    def get_object(self, namespace: str, bucket: str, key: str) -> Any:
        self._check(namespace, bucket)
        if key not in self.objects:
            raise service_error(404, "ObjectNotFound")
        return SimpleNamespace(data=SimpleNamespace(content=self.objects[key]))

    def delete_object(self, namespace: str, bucket: str, key: str) -> None:
        self._check(namespace, bucket)
        if key not in self.objects:
            raise service_error(404, "ObjectNotFound")
        del self.objects[key]

    def list_objects(
        self,
        namespace: str,
        bucket: str,
        *,
        prefix: str,
        start: str | None,
        fields: str,
    ) -> Any:
        self._check(namespace, bucket)
        assert fields == "name"
        self.list_calls += 1
        names = sorted(
            name
            for name in self.objects
            if name.startswith(prefix) and (start is None or name >= start)
        )
        page, rest = names[: self.page_size], names[self.page_size :]
        return SimpleNamespace(
            data=SimpleNamespace(
                objects=[SimpleNamespace(name=name) for name in page],
                next_start_with=rest[0] if rest else None,
            )
        )


@pytest.fixture
def fake_client() -> FakeObjectStorageClient:
    return FakeObjectStorageClient()


@pytest.fixture(params=["oci", "memory"])
def any_storage(
    request: pytest.FixtureRequest, fake_client: FakeObjectStorageClient
) -> Storage:
    if request.param == "oci":
        return OCIStorage(fake_client, "ns", "bucket")
    return InMemoryStorage()


@pytest.fixture
def clean_get_storage() -> Iterator[None]:
    get_storage.cache_clear()
    yield
    get_storage.cache_clear()


def test_put_then_get_returns_bytes_and_put_replaces(any_storage: Storage) -> None:
    any_storage.put("a/1.txt", b"primeiro", "text/plain")
    assert any_storage.get("a/1.txt") == b"primeiro"

    any_storage.put("a/1.txt", b"segundo", "text/plain")
    assert any_storage.get("a/1.txt") == b"segundo"


def test_get_missing_key_raises_not_found(any_storage: Storage) -> None:
    with pytest.raises(ObjectNotFoundError):
        any_storage.get("nao/existe")


def test_delete_removes_object_and_is_idempotent(any_storage: Storage) -> None:
    any_storage.put("a/1.txt", b"x", "text/plain")

    any_storage.delete("a/1.txt")
    any_storage.delete("a/1.txt")

    with pytest.raises(ObjectNotFoundError):
        any_storage.get("a/1.txt")


def test_list_returns_only_prefix_keys_in_order(any_storage: Storage) -> None:
    for key in ("courses/1/b", "courses/1/a", "courses/10/a", "other/a"):
        any_storage.put(key, b"x", "text/plain")

    assert any_storage.list("courses/1/") == ["courses/1/a", "courses/1/b"]
    assert any_storage.list("nada/") == []


def test_oci_put_sends_content_type(fake_client: FakeObjectStorageClient) -> None:
    OCIStorage(fake_client, "ns", "bucket").put("a.json", b"{}", "application/json")

    assert fake_client.content_types["a.json"] == "application/json"


def test_oci_list_joins_pages() -> None:
    client = FakeObjectStorageClient(page_size=2)
    oci_storage = OCIStorage(client, "ns", "bucket")
    for key in ("p/c", "p/a", "p/b"):
        oci_storage.put(key, b"x", "text/plain")

    assert oci_storage.list("p/") == ["p/a", "p/b", "p/c"]
    assert client.list_calls == 2


def test_oci_404_becomes_not_found(fake_client: FakeObjectStorageClient) -> None:
    fake_client.fail_with = service_error(404, "ObjectNotFound")

    with pytest.raises(ObjectNotFoundError):
        OCIStorage(fake_client, "ns", "bucket").get("a/1.txt")


@pytest.mark.parametrize(
    "error",
    [
        service_error(500, "InternalServerError"),
        service_error(404, "BucketNotFound"),
        ConnectionError("sem rede"),
        # Erros do SDK que trazem o conteúdo do objeto na própria mensagem.
        service_error(500, "InternalServerError", f"corpo recusado: {SECRET}"),
        RuntimeError(f"corpo recusado: {SECRET}"),
    ],
)
@pytest.mark.parametrize("operation", ["put", "get", "delete", "list"])
def test_oci_other_failures_become_storage_error(
    fake_client: FakeObjectStorageClient, error: Exception, operation: str
) -> None:
    fake_client.fail_with = error
    oci_storage = OCIStorage(fake_client, "ns", "bucket")
    calls = {
        "put": lambda: oci_storage.put("a/1.txt", SECRET.encode(), "text/plain"),
        "get": lambda: oci_storage.get("a/1.txt"),
        "delete": lambda: oci_storage.delete("a/1.txt"),
        "list": lambda: oci_storage.list("a/1.txt"),
    }

    with pytest.raises(StorageError) as raised:
        calls[operation]()

    assert not isinstance(raised.value, ObjectNotFoundError)
    message = str(raised.value)
    assert operation in message
    assert "a/1.txt" in message
    assert SECRET not in message


@pytest.mark.usefixtures("clean_get_storage")
@pytest.mark.parametrize(
    ("bucket", "namespace"), [(None, None), ("bucket", None), (None, "ns")]
)
def test_get_storage_without_configuration_raises(
    monkeypatch: pytest.MonkeyPatch, bucket: str | None, namespace: str | None
) -> None:
    monkeypatch.setattr(settings, "OCI_BUCKET", bucket)
    monkeypatch.setattr(settings, "OCI_NAMESPACE", namespace)

    with pytest.raises(StorageNotConfiguredError):
        get_storage()


@pytest.mark.usefixtures("clean_get_storage")
def test_get_storage_with_api_key_reads_config_file_and_reuses_instance(
    monkeypatch: pytest.MonkeyPatch, fake_client: FakeObjectStorageClient
) -> None:
    seen: dict[str, Any] = {}

    def from_file(file_location: str, profile_name: str) -> dict[str, str]:
        seen["file"] = (file_location, profile_name)
        return {"region": "sa-saopaulo-1"}

    def build(config: dict[str, str]) -> FakeObjectStorageClient:
        seen["config"] = config
        return fake_client

    monkeypatch.setattr(settings, "OCI_BUCKET", "bucket")
    monkeypatch.setattr(settings, "OCI_NAMESPACE", "ns")
    monkeypatch.setattr(settings, "OCI_AUTH", "api_key")
    monkeypatch.setattr(settings, "OCI_CONFIG_FILE", "/fora/do/repo/config")
    monkeypatch.setattr(settings, "OCI_CONFIG_PROFILE", "DEV")
    monkeypatch.setattr(oci.config, "from_file", from_file)
    monkeypatch.setattr(oci.object_storage, "ObjectStorageClient", build)

    first = get_storage()
    first.put("a", b"x", "text/plain")

    assert seen == {
        "file": ("/fora/do/repo/config", "DEV"),
        "config": {"region": "sa-saopaulo-1"},
    }
    assert fake_client.objects == {"a": b"x"}
    assert get_storage() is first


@pytest.mark.usefixtures("clean_get_storage")
def test_get_storage_with_instance_principal_uses_signer(
    monkeypatch: pytest.MonkeyPatch, fake_client: FakeObjectStorageClient
) -> None:
    signer = object()
    seen: dict[str, Any] = {}

    def build(config: dict[str, str], signer: object) -> FakeObjectStorageClient:
        seen.update(config=config, signer=signer)
        return fake_client

    monkeypatch.setattr(settings, "OCI_BUCKET", "bucket")
    monkeypatch.setattr(settings, "OCI_NAMESPACE", "ns")
    monkeypatch.setattr(settings, "OCI_AUTH", "instance_principal")
    monkeypatch.setattr(
        oci.auth.signers,
        "InstancePrincipalsSecurityTokenSigner",
        lambda: signer,
    )
    monkeypatch.setattr(oci.object_storage, "ObjectStorageClient", build)

    assert isinstance(get_storage(), OCIStorage)
    assert seen == {"config": {}, "signer": signer}


@pytest.mark.usefixtures("clean_get_storage")
def test_get_storage_with_missing_config_file_raises_storage_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    monkeypatch.setattr(settings, "OCI_BUCKET", "bucket")
    monkeypatch.setattr(settings, "OCI_NAMESPACE", "ns")
    monkeypatch.setattr(settings, "OCI_AUTH", "api_key")
    monkeypatch.setattr(settings, "OCI_CONFIG_FILE", str(tmp_path / "ausente"))

    with pytest.raises(StorageError, match="ConfigFileNotFound"):
        get_storage()


def test_key_functions_follow_the_architecture_format() -> None:
    course_id, document_id, content_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    assert course_prefix(course_id) == f"courses/{course_id}/"
    assert (
        document_key(course_id, document_id, "md")
        == f"courses/{course_id}/documents/{document_id}.md"
    )
    assert document_key(course_id, document_id, ".pdf").endswith(f"{document_id}.pdf")

    first = content_key(course_id, content_id)
    second = content_key(course_id, content_id)
    prefix = f"courses/{course_id}/contents/{content_id}/"
    assert first != second
    for key in (first, second):
        assert key.startswith(prefix)
        assert key.endswith(".json")
        uuid.UUID(key.removeprefix(prefix).removesuffix(".json"))
