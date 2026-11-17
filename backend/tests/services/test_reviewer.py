import uuid

import pytest

from app.core import llm
from app.models import AudienceLevel, ClarityLevel
from app.services.content_schemas import GeneratedBase
from app.services.grounding import evaluate
from app.services.retrieval import RetrievedChunk
from app.services.reviewer import PROMPT_VERSION, _ClaimOut, _ReviewOut, review_content


@pytest.fixture
def inputs():
    generated = GeneratedBase(
        title="Título", estimated_minutes=1, key_concepts=["conceito"], prerequisites=[]
    )
    chunks = [
        RetrievedChunk(uuid.uuid4(), uuid.uuid4(), i, f"texto {i}", None, 0.5)
        for i in range(3)
    ]
    return generated, chunks


def test_review(monkeypatch, inputs):
    generated, chunks = inputs
    calls = []

    def fake(**kwargs):
        calls.append(kwargs)
        return _ReviewOut(
            claims=[
                _ClaimOut(claim=str(n), supported=True, chunk_number=n)
                for n in (2, 0, 4, None)
            ],
            clarity=ClarityLevel.high,
            review_notes="Adequado",
        )

    monkeypatch.setattr(llm, "generate_structured", fake)
    result = review_content(
        generated=generated, audience_level=AudienceLevel.technical_basic, chunks=chunks
    )
    assert len(calls) == 1
    call = calls[0]
    assert call["temperature"] == 0.0 and call["response_model"] is _ReviewOut
    assert "Título" in call["prompt"] and "technical_basic" in call["prompt"]
    for i, chunk in enumerate(chunks, 1):
        assert f'<trecho numero="{i}">\n{chunk.text}' in call["prompt"]
        assert str(chunk.chunk_id) not in call["prompt"] + call["system_instruction"]
    assert (
        "dados" in call["system_instruction"]
        and "Analogias" in call["system_instruction"]
    )
    assert [c.chunk_id for c in result.claims] == [chunks[1].chunk_id, None, None, None]
    assert all(c.supported for c in result.claims)
    assert [c.claim for c in result.claims] == ["2", "0", "4", "None"]
    assert result.clarity == ClarityLevel.high and result.review_notes == "Adequado"
    assert len(evaluate(result, {c.chunk_id for c in chunks}).supported) == 1
    assert len(PROMPT_VERSION) <= 20


def test_empty(monkeypatch, inputs):
    def fail(**_kwargs):
        pytest.fail("modelo chamado")

    monkeypatch.setattr(llm, "generate_structured", fail)
    with pytest.raises(ValueError):
        review_content(
            generated=inputs[0], audience_level=AudienceLevel.non_technical, chunks=[]
        )


@pytest.mark.parametrize("error", [llm.LLMError, llm.LLMInvalidResponseError])
def test_error_propagates(monkeypatch, inputs, error):
    def fail(**_kwargs):
        raise error("falha")

    monkeypatch.setattr(llm, "generate_structured", fail)
    with pytest.raises(error, match="falha"):
        review_content(
            generated=inputs[0],
            audience_level=AudienceLevel.non_technical,
            chunks=inputs[1],
        )
