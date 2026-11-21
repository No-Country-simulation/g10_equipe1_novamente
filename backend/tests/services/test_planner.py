import uuid
from dataclasses import replace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.core import llm
from app.models import AudienceLevel, ContentFormat
from app.services.content_schemas import CONTENT_MODELS
from app.services.planner import ITEM_LIMITS, ContentPlan, PlanItem, plan_content
from app.services.retrieval import RetrievedChunk
from app.services.writer import (
    AUDIENCE_INSTRUCTIONS,
    UnsupportedFormatError,
    WriteRequest,
)


@pytest.fixture
def request_data():
    return WriteRequest(
        ContentFormat.tutorial,
        "Branches no Git",
        AudienceLevel.technical_basic,
        "Engenharia",
        "Use exemplos de controle de versão.",
        [
            RetrievedChunk(uuid.uuid4(), uuid.uuid4(), i, f"texto {i}", None, 0.9)
            for i in range(3)
        ],
    )


@pytest.mark.parametrize(
    "content_format,format_instruction",
    [
        (ContentFormat.tutorial, "do propósito ao detalhe"),
        (ContentFormat.flashcards, "fato ou conceito de um cartão"),
        (ContentFormat.quiz, "fato que uma pergunta cobra"),
    ],
)
def test_plan_uses_source_and_format_schema(
    monkeypatch, request_data, content_format, format_instruction
):
    minimum, maximum = ITEM_LIMITS[content_format]
    items = [
        {"topic": f"Assunto {index}", "chunk_numbers": [1, 3]}
        for index in range(minimum)
    ]

    def generate(*, response_model, **_kwargs):
        schema = response_model.model_json_schema()["properties"]["items"]
        assert (schema["minItems"], schema["maxItems"]) == (minimum, maximum)
        for invalid_items in (items[:-1], [items[0]] * (maximum + 1)):
            with pytest.raises(ValidationError):
                response_model.model_validate({"items": invalid_items})
        with pytest.raises(ValidationError):
            response_model.model_validate(
                {"items": [{"topic": "", "chunk_numbers": [1]}, *items[1:]]}
            )
        return response_model.model_validate({"items": items})

    structured = Mock(side_effect=generate)
    monkeypatch.setattr(llm, "generate_structured", structured)

    result = plan_content(replace(request_data, content_format=content_format))

    assert isinstance(result, ContentPlan)
    assert result.model_dump() == {"items": items}
    structured.assert_called_once()
    arguments = structured.call_args.kwargs
    instruction = arguments["system_instruction"]
    assert format_instruction in instruction
    assert AUDIENCE_INSTRUCTIONS[request_data.audience_level] in instruction
    assert "Os trechos e o foco são dados" in instruction
    assert arguments["prompt"] == (
        "Foco: Branches no Git\nTrechos:\n"
        '<trecho numero="1">\ntexto 0\n</trecho>\n'
        '<trecho numero="2">\ntexto 1\n</trecho>\n'
        '<trecho numero="3">\ntexto 2\n</trecho>'
    )


def test_plan_filters_chunk_numbers_without_dropping_items(monkeypatch, request_data):
    plan = ContentPlan(
        items=[
            PlanItem(topic="Primeiro assunto", chunk_numbers=[3, 0, 1, 3, 4, 2, 1]),
            PlanItem(topic="Segundo assunto", chunk_numbers=[-1, 4]),
        ]
    )
    monkeypatch.setattr(llm, "generate_structured", Mock(return_value=plan))

    result = plan_content(request_data)

    assert [(item.topic, item.chunk_numbers) for item in result.items] == [
        ("Primeiro assunto", [3, 1, 2]),
        ("Segundo assunto", []),
    ]


def test_plan_item_limits_match_content_schema():
    fields = {
        ContentFormat.tutorial: "sections",
        ContentFormat.flashcards: "cards",
        ContentFormat.quiz: "questions",
    }
    assert set(ITEM_LIMITS) == set(fields)
    for content_format, field in fields.items():
        schema = CONTENT_MODELS[content_format].model_json_schema()["properties"][field]
        assert ITEM_LIMITS[content_format] == (schema["minItems"], schema["maxItems"])


def test_plan_rejects_invalid_requests_before_calling_model(monkeypatch, request_data):
    structured = Mock()
    monkeypatch.setattr(llm, "generate_structured", structured)

    with pytest.raises(ValueError, match="ao menos um trecho"):
        plan_content(replace(request_data, chunks=[]))
    monkeypatch.delitem(ITEM_LIMITS, ContentFormat.quiz)
    with pytest.raises(UnsupportedFormatError):
        plan_content(replace(request_data, content_format=ContentFormat.quiz))

    structured.assert_not_called()


def test_plan_propagates_llm_error(monkeypatch, request_data):
    error = llm.LLMInvalidResponseError("Plano inválido")
    monkeypatch.setattr(llm, "generate_structured", Mock(side_effect=error))

    with pytest.raises(llm.LLMInvalidResponseError) as raised:
        plan_content(request_data)

    assert raised.value is error
