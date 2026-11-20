import uuid

import pytest

from app.core import llm
from app.models import AudienceLevel, ContentFormat
from app.services.content_schemas import GeneratedFlashcards, GeneratedTutorial
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
    assert len(calls) == 1
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
    with pytest.raises(UnsupportedFormatError):
        write_content(request(format=ContentFormat.quiz))
    with pytest.raises(ValueError):
        write_content(request(chunks=[]))
    with pytest.raises(ValueError):
        write_content(
            request(),
            rewrite=Rewrite(
                GeneratedFlashcards.model_validate(
                    {
                        "title": "x",
                        "estimated_minutes": 1,
                        "key_concepts": ["x"],
                        "prerequisites": [],
                        "content": {
                            "introduction": "Introdução",
                            "cards": [
                                {"front": f"Pergunta {i}", "back": "Resposta"}
                                for i in range(8)
                            ],
                        },
                    }
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


def flashcards_result(introduction="Introdução dos flashcards"):
    return GeneratedFlashcards.model_validate(
        {
            "title": "Flashcards",
            "estimated_minutes": 10,
            "key_concepts": ["conceito"],
            "prerequisites": [],
            "content": {
                "introduction": introduction,
                "cards": [
                    {
                        "front": f"Pergunta {index}",
                        "back": "Resposta",
                        "hint": "Dica" if index % 2 == 0 else None,
                    }
                    for index in range(8)
                ],
            },
        }
    )


def flashcards_request():
    chunk = RetrievedChunk(
        uuid.uuid4(), uuid.uuid4(), 0, "texto do documento", None, 0.9
    )
    return WriteRequest(
        ContentFormat.flashcards,
        "foco dos flashcards",
        AudienceLevel.non_technical,
        "setor",
        "dica do setor",
        [chunk],
    )


def test_first_flashcards_write(monkeypatch):
    flashcards = flashcards_result()
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return flashcards

    monkeypatch.setattr(llm, "generate_structured", generate)

    result = write_content(flashcards_request())

    assert result is flashcards
    assert len(calls) == 1
    assert calls[0]["response_model"] is GeneratedFlashcards


def test_flashcards_instruction_is_specific(monkeypatch):
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        if kwargs["response_model"] is GeneratedFlashcards:
            return flashcards_result()
        return GeneratedTutorial.model_validate(
            {
                "title": "Tutorial",
                "estimated_minutes": 5,
                "key_concepts": ["conceito"],
                "prerequisites": [],
                "content": {
                    "summary": "Resumo",
                    "sections": [{"title": "Seção", "body": "Texto"}],
                    "takeaways": ["Ponto"],
                },
            }
        )

    monkeypatch.setattr(llm, "generate_structured", generate)

    write_content(flashcards_request())
    flashcards_instruction = calls[-1]["system_instruction"]

    tutorial_request = WriteRequest(
        ContentFormat.tutorial,
        "foco do tutorial",
        AudienceLevel.non_technical,
        "setor",
        "dica do setor",
        [RetrievedChunk(uuid.uuid4(), uuid.uuid4(), 0, "texto", None, 0.9)],
    )
    write_content(tutorial_request)
    tutorial_instruction = calls[-1]["system_instruction"]

    assert "8 a 12 cartões" in flashcards_instruction
    assert "dica é opcional" in flashcards_instruction
    assert "fato técnico novo" in flashcards_instruction
    assert flashcards_instruction != tutorial_instruction


def test_metadata_instructions_are_common(monkeypatch):
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        if kwargs["response_model"] is GeneratedFlashcards:
            return flashcards_result()
        return GeneratedTutorial.model_validate(
            {
                "title": "Tutorial",
                "estimated_minutes": 5,
                "key_concepts": ["conceito"],
                "prerequisites": [],
                "content": {
                    "summary": "Resumo",
                    "sections": [{"title": "Seção", "body": "Texto"}],
                    "takeaways": ["Ponto"],
                },
            }
        )

    monkeypatch.setattr(llm, "generate_structured", generate)

    write_content(flashcards_request())
    flashcards_instruction = calls[-1]["system_instruction"]

    tutorial_request = WriteRequest(
        ContentFormat.tutorial,
        "foco",
        AudienceLevel.non_technical,
        "setor",
        "dica",
        [RetrievedChunk(uuid.uuid4(), uuid.uuid4(), 0, "texto", None, 0.9)],
    )
    write_content(tutorial_request)
    tutorial_instruction = calls[-1]["system_instruction"]

    common_rules = (
        "Use um título que descreva o material",
        "conceitos-chave",
        "pré-requisitos",
        "tempo estimado",
    )
    assert all(rule in flashcards_instruction for rule in common_rules)
    assert all(rule in tutorial_instruction for rule in common_rules)


def test_flashcards_rewrite_contains_previous_and_claims(monkeypatch):
    flashcards = flashcards_result("Introdução anterior distinta")
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return flashcards_result("Introdução reescrita")

    monkeypatch.setattr(llm, "generate_structured", generate)

    write_content(
        flashcards_request(),
        rewrite=Rewrite(
            previous=flashcards,
            unsupported_claims=["afirmação sem apoio A", "afirmação sem apoio B"],
        ),
    )

    prompt = calls[0]["prompt"]
    assert "Introdução anterior distinta" in prompt
    assert "afirmação sem apoio A" in prompt
    assert "afirmação sem apoio B" in prompt
    assert "Retire ou corrija cada afirmação sem apoio" in prompt


def test_flashcards_rewrite_rejects_tutorial(monkeypatch):
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(llm, "generate_structured", generate)

    tutorial = GeneratedTutorial.model_validate(
        {
            "title": "Tutorial",
            "estimated_minutes": 5,
            "key_concepts": ["conceito"],
            "prerequisites": [],
            "content": {
                "summary": "Resumo",
                "sections": [{"title": "Seção", "body": "Texto"}],
                "takeaways": ["Ponto"],
            },
        }
    )

    with pytest.raises(ValueError):
        write_content(
            flashcards_request(),
            rewrite=Rewrite(previous=tutorial, unsupported_claims=[]),
        )

    assert calls == []
