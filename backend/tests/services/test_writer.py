import uuid
from dataclasses import replace

import pytest

from app.core import llm
from app.models import AudienceLevel, ContentFormat
from app.services import writer
from app.services.content_schemas import (
    GeneratedFlashcards,
    GeneratedQuiz,
    GeneratedTutorial,
)
from app.services.retrieval import RetrievedChunk
from app.services.writer import (
    FLASHCARDS_INSTRUCTION,
    PROMPT_VERSION,
    TUTORIAL_INSTRUCTION,
    Rewrite,
    UnsupportedFormatError,
    WriteRequest,
    write_content,
)


def tutorial_result():
    return GeneratedTutorial.model_validate(
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


def test_writer(monkeypatch):
    tutorial = tutorial_result()
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return tutorial

    monkeypatch.setattr(llm, "generate_structured", generate)
    chunks = [
        RetrievedChunk(uuid.uuid4(), uuid.uuid4(), i, f"texto {i}", None, 0.9)
        for i in range(3)
    ]

    def request(level=AudienceLevel.non_technical, chunks=chunks):
        return WriteRequest(
            ContentFormat.tutorial, "foco", level, "setor", "dica", chunks
        )

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
    with pytest.raises(ValueError):
        write_content(request(chunks=[]))
    with pytest.raises(ValueError):
        write_content(request(), rewrite=Rewrite(flashcards_result(), []))
    assert len(calls) == count

    def fail(**_kwargs):
        raise llm.LLMInvalidResponseError("inválido")

    monkeypatch.setattr(llm, "generate_structured", fail)
    with pytest.raises(llm.LLMInvalidResponseError):
        write_content(request())
    assert len(PROMPT_VERSION) <= 20


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


def test_writer_combines_common_and_format_instructions(monkeypatch):
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        if kwargs["response_model"] is GeneratedFlashcards:
            return flashcards_result()
        return tutorial_result()

    monkeypatch.setattr(llm, "generate_structured", generate)

    request = flashcards_request()
    write_content(request)
    write_content(replace(request, content_format=ContentFormat.tutorial))

    flashcards_instruction = calls[0]["system_instruction"]
    tutorial_instruction = calls[1]["system_instruction"]
    assert flashcards_instruction.endswith(FLASHCARDS_INSTRUCTION)
    assert tutorial_instruction.endswith(TUTORIAL_INSTRUCTION)
    assert "8 a 12 cartões" in flashcards_instruction
    assert "dica é opcional" in flashcards_instruction
    assert "fato técnico novo" in flashcards_instruction

    common_instruction = flashcards_instruction.removesuffix(FLASHCARDS_INSTRUCTION)
    assert common_instruction == tutorial_instruction.removesuffix(TUTORIAL_INSTRUCTION)
    assert "Use um título que descreva o material" in common_instruction
    assert "fatos técnicos em content" in common_instruction
    assert "conceitos-chave que aparecem nos trechos" in common_instruction
    assert "que o conteúdo ensina" in common_instruction
    assert "pré-requisitos" in common_instruction
    assert "tempo estimado em minutos" in common_instruction
    assert "conceitos-chave" not in TUTORIAL_INSTRUCTION
    assert "pré-requisitos" not in TUTORIAL_INSTRUCTION


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
    assert flashcards.model_dump_json() in prompt
    assert "afirmação sem apoio A" in prompt
    assert "afirmação sem apoio B" in prompt
    assert "Retire ou corrija cada afirmação sem apoio" in prompt


def test_flashcards_rewrite_rejects_tutorial(monkeypatch):
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(llm, "generate_structured", generate)

    with pytest.raises(ValueError, match="formato da versão anterior") as error:
        write_content(
            flashcards_request(),
            rewrite=Rewrite(previous=tutorial_result(), unsupported_claims=[]),
        )

    assert not isinstance(error.value, UnsupportedFormatError)
    assert calls == []


def quiz_result(prompt="Pergunta do quiz"):
    return GeneratedQuiz.model_validate(
        {
            "title": "Quiz",
            "estimated_minutes": 5,
            "key_concepts": ["conceito"],
            "prerequisites": [],
            "content": {
                "questions": [
                    {
                        "prompt": f"{prompt} {index + 1}",
                        "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
                        "correct_index": index % 4,
                        "explanation": "Justificativa",
                    }
                    for index in range(5)
                ],
            },
        }
    )


@pytest.fixture
def quiz_request():
    return replace(
        flashcards_request(), content_format=ContentFormat.quiz, focus="foco do quiz"
    )


@pytest.fixture
def quiz_generation(monkeypatch):
    quiz = quiz_result()
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        return quiz

    monkeypatch.setattr(llm, "generate_structured", generate)
    return quiz, calls


def test_first_quiz_write(quiz_request, quiz_generation):
    quiz, calls = quiz_generation

    assert write_content(quiz_request) is quiz
    assert len(calls) == 1
    assert calls[0]["response_model"] is GeneratedQuiz

    instruction = calls[0]["system_instruction"]
    assert "exatamente 5 perguntas" in instruction
    assert "exatamente 4 opções distintas por pergunta" in instruction
    assert "uma única resposta correta" in instruction
    assert "correct_index de 0 a 3" in instruction
    assert "varie a posição da resposta correta" in instruction
    assert "plausíveis para o nível de público" in instruction
    assert "distinguir a resposta correta das demais" in instruction
    assert "justificativa com fatos dos trechos" in instruction
    assert "fato no enunciado ou na justificativa deve ter apoio" in instruction
    assert "Perguntas diferentes devem tratar de fatos distintos" in instruction
    assert "Use um título que descreva o material" in instruction
    assert "fatos técnicos em content" in instruction
    assert (
        "conceitos-chave que aparecem nos trechos e que o conteúdo ensina"
        in instruction
    )
    assert "pré-requisitos" in instruction
    assert "tempo estimado em minutos" in instruction


def test_writer_supports_all_formats_with_prompt_version_v3():
    assert set(writer.FORMAT_INSTRUCTIONS) == set(ContentFormat)
    assert PROMPT_VERSION == "escreve-v3"


def test_quiz_rewrite_contains_previous_and_claims(quiz_request, quiz_generation):
    quiz, calls = quiz_generation
    previous = quiz_result("Enunciado da versão anterior")
    claims = ["afirmação sem apoio A", "afirmação sem apoio B"]

    assert write_content(quiz_request, rewrite=Rewrite(previous, claims)) is quiz
    assert len(calls) == 1
    assert calls[0]["response_model"] is GeneratedQuiz
    prompt = calls[0]["prompt"]
    assert previous.model_dump_json() in prompt
    assert all(claim in prompt for claim in claims)
    assert "Retire ou corrija cada afirmação sem apoio" in prompt


def test_quiz_rewrite_rejects_flashcards(quiz_request, quiz_generation):
    _, calls = quiz_generation

    with pytest.raises(ValueError, match="formato da versão anterior"):
        write_content(quiz_request, rewrite=Rewrite(flashcards_result(), []))

    assert calls == []


def test_quiz_without_format_instruction(quiz_request, quiz_generation, monkeypatch):
    _, calls = quiz_generation
    monkeypatch.delitem(writer.FORMAT_INSTRUCTIONS, ContentFormat.quiz)

    with pytest.raises(UnsupportedFormatError):
        write_content(quiz_request)

    assert calls == []
