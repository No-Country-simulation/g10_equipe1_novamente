from typing import Any, cast

from fastapi.testclient import TestClient


def create_course(
    *,
    client: TestClient,
    owner_email: str,
    title: str = "Curso de teste",
    status: str = "ready",
    documents: list[dict[str, Any]] | None = None,
    contents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "owner_email": owner_email,
        "title": title,
        "audience_level": "technical_basic",
        "status": status,
        "documents": documents
        if documents is not None
        else [{"original_filename": "documento.md", "chunks": ["chunk de teste"]}],
        "contents": contents
        if contents is not None
        else [
            {
                "format": "tutorial",
                "title": "Tutorial de teste",
                "content": {"body": "Conteúdo de teste"},
                "cited_chunks": [0],
            }
        ],
    }
    response = client.post("/api/v1/private/courses/", json=payload)
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())
