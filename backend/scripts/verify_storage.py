"""Envia, lê, lista e apaga um objeto no bucket configurado.

Rode de `backend/`, com as variáveis `OCI_*` no `.env`:

    uv run python scripts/verify_storage.py
"""

import sys
import uuid

from app.core.storage import ObjectNotFoundError, StorageError, get_storage


def main() -> int:
    key = f"verify/{uuid.uuid4()}.txt"
    data = b"novamente verify_storage"
    try:
        storage = get_storage()
        print(f"chave: {key}")
        storage.put(key, data, "text/plain")
        print("put: ok")
        if storage.get(key) != data:
            print("get: falhou, os bytes lidos diferem dos enviados")
            return 1
        print("get: ok")
        if key not in storage.list("verify/"):
            print("list: falhou, a chave não apareceu")
            return 1
        print("list: ok")
        storage.delete(key)
        try:
            storage.get(key)
        except ObjectNotFoundError:
            print("delete: ok")
        else:
            print("delete: falhou, o objeto ainda existe")
            return 1
    except StorageError as exc:
        print(f"falhou: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
