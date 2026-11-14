import builtins
import uuid
from functools import lru_cache
from typing import Annotated, Any, Protocol

import oci  # type: ignore[import-untyped]
from fastapi import Depends

from app.core.config import settings


class StorageError(Exception): ...


class StorageNotConfiguredError(StorageError): ...


class ObjectNotFoundError(StorageError): ...


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def list(self, prefix: str) -> builtins.list[str]: ...


def _is_object_not_found(exc: Exception) -> bool:
    # Um bucket errado ou sem permissão também responde 404, com outro código.
    # Esse caso é erro de configuração e não pode passar por objeto ausente.
    return (
        isinstance(exc, oci.exceptions.ServiceError)
        and exc.status == 404
        and exc.code == "ObjectNotFound"
    )


def _storage_error(operation: str, key: str, exc: Exception) -> StorageError:
    # A mensagem leva só o tipo e os códigos do erro, nunca o conteúdo do objeto.
    detail = type(exc).__name__
    if isinstance(exc, oci.exceptions.ServiceError):
        detail = f"{detail} {exc.status} {exc.code}"
    return StorageError(f"{operation} falhou para a chave {key!r}: {detail}")


class OCIStorage:
    def __init__(self, client: Any, namespace: str, bucket: str) -> None:
        self._client = client
        self._namespace = namespace
        self._bucket = bucket

    def put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self._client.put_object(
                self._namespace, self._bucket, key, data, content_type=content_type
            )
        except Exception as exc:
            raise _storage_error("put", key, exc) from exc

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(self._namespace, self._bucket, key)
            content: bytes = response.data.content
        except Exception as exc:
            if _is_object_not_found(exc):
                raise ObjectNotFoundError(key) from exc
            raise _storage_error("get", key, exc) from exc
        return content

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(self._namespace, self._bucket, key)
        except Exception as exc:
            if _is_object_not_found(exc):
                return
            raise _storage_error("delete", key, exc) from exc

    def list(self, prefix: str) -> builtins.list[str]:
        keys: builtins.list[str] = []
        start: str | None = None
        try:
            while True:
                response = self._client.list_objects(
                    self._namespace,
                    self._bucket,
                    prefix=prefix,
                    start=start,
                    fields="name",
                )
                keys.extend(item.name for item in response.data.objects)
                start = response.data.next_start_with
                if start is None:
                    break
        except Exception as exc:
            raise _storage_error("list", prefix, exc) from exc
        return sorted(keys)


class InMemoryStorage:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put(self, key: str, data: bytes, content_type: str) -> None:  # noqa: ARG002
        self._objects[key] = data

    def get(self, key: str) -> bytes:
        try:
            return self._objects[key]
        except KeyError:
            raise ObjectNotFoundError(key) from None

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)

    def list(self, prefix: str) -> builtins.list[str]:
        return sorted(key for key in self._objects if key.startswith(prefix))


def _build_client() -> Any:
    if settings.OCI_AUTH == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    config = oci.config.from_file(
        file_location=settings.OCI_CONFIG_FILE,
        profile_name=settings.OCI_CONFIG_PROFILE,
    )
    return oci.object_storage.ObjectStorageClient(config)


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    if not settings.OCI_BUCKET or not settings.OCI_NAMESPACE:
        raise StorageNotConfiguredError("Defina OCI_BUCKET e OCI_NAMESPACE no .env.")
    try:
        client = _build_client()
    except Exception as exc:
        raise StorageError(
            f"Não foi possível criar o cliente da OCI: {type(exc).__name__}"
        ) from exc
    return OCIStorage(client, settings.OCI_NAMESPACE, settings.OCI_BUCKET)


StorageDep = Annotated[Storage, Depends(get_storage)]


def document_key(course_id: uuid.UUID, document_id: uuid.UUID, extension: str) -> str:
    return f"courses/{course_id}/documents/{document_id}.{extension.lstrip('.')}"


def content_key(course_id: uuid.UUID, content_id: uuid.UUID) -> str:
    return f"courses/{course_id}/contents/{content_id}/{uuid.uuid4()}.json"


def course_prefix(course_id: uuid.UUID) -> str:
    return f"courses/{course_id}/"
