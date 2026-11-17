import uuid

import pytest

from app.core import llm
from app.models import AudienceLevel, ContentFormat
from app.services.content_schemas import GeneratedBase, GeneratedTutorial
from app.services.retrieval import RetrievedChunk
from app.services.writer import (
    PROMPT_VERSION,
    Rewrite,
    UnsupportedFormatError,
    WriteRequest,
    write_content,
)


def test_writer(monkeypatch):
    tutorial = GeneratedTutorial.model_validate(
        {
            "title": "Anterior",
            "estimated_minutes": 5,
            "key_concepts": ["conceito"],
            "prerequisites": [],
            "content": {
                "summary": "resumo",
                "sections": [{"title": "seção", "body": "texto"}],
                "takeaways": ["ponto"],
            },
        }
    )
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return tutorial

    monkeypatch.setattr(llm, "generate_structured", generate)
    chunks = [
        RetrievedChunk(uuid.uuid4(), uuid.uuid4(), i, f"texto {i}", None, 0.9)
        for i in range(3)
    ]

    def request(
        level=AudienceLevel.non_technical, format=ContentFormat.tutorial, chunks=chunks
    ):
        return WriteRequest(format, "foco", level, "setor", "dica", chunks)

    assert write_content(request()) is tutorial
    assert calls[-1]["response_model"] is GeneratedTutorial
    prompt = calls[-1]["prompt"]
    assert "foco" in prompt and prompt.index("texto 0") < prompt.index(
        "texto 1"
    ) < prompt.index("texto 2")
    assert "Afirmações sem apoio" not in prompt
    instruction = calls[-1]["system_instruction"]
    assert all(
        s in instruction for s in ("setor", "dica", "dados", "ignore instruções")
    )
    instructions = {instruction}
    for level in (AudienceLevel.technical_basic, AudienceLevel.technical_advanced):
        write_content(request(level))
        instructions.add(calls[-1]["system_instruction"])
    assert len(instructions) == 3
    write_content(request(), rewrite=Rewrite(tutorial, ["afirmação A", "afirmação B"]))
    assert all(
        s in calls[-1]["prompt"] for s in ("Anterior", "afirmação A", "afirmação B")
    )
    count = len(calls)
    for format in (ContentFormat.flashcards, ContentFormat.quiz):
        with pytest.raises(UnsupportedFormatError):
            write_content(request(format=format))
    with pytest.raises(ValueError):
        write_content(request(chunks=[]))
    with pytest.raises(ValueError):
        write_content(
            request(),
            rewrite=Rewrite(
                GeneratedBase(
                    title="x", estimated_minutes=1, key_concepts=["x"], prerequisites=[]
                ),
                [],
            ),
        )
    assert len(calls) == count

    def fail(**_kwargs):
        raise llm.LLMInvalidResponseError("inválido")

    monkeypatch.setattr(llm, "generate_structured", fail)
    with pytest.raises(llm.LLMInvalidResponseError):
        write_content(request())
    assert len(PROMPT_VERSION) <= 20
