import json
import uuid

import pytest

from app.core import llm
from app.models import AudienceLevel, ClarityLevel
from app.services.content_schemas import GeneratedTutorial
from app.services.grounding import Decision, decide, evaluate, failure_message
from app.services.retrieval import RetrievedChunk
from app.services.reviewer import PROMPT_VERSION, _ClaimOut, _ReviewOut, review_content

FOCUS = "Como o Git cria branches"


@pytest.fixture
def inputs():
    generated = GeneratedTutorial.model_validate(
        {
            "title": "Título do material",
            "estimated_minutes": 1,
            "key_concepts": ["conceito"],
            "prerequisites": ["Git instalado"],
            "content": {
                "summary": "Resumo de branches",
                "sections": [{"title": "Título da seção", "body": "Corpo"}],
                "takeaways": ["Item"],
            },
        }
    )
    chunks = [
        RetrievedChunk(uuid.uuid4(), uuid.uuid4(), i, f"texto {i}", None, 0.654321)
        for i in range(3)
    ]
    return generated, chunks


def test_review(monkeypatch, inputs):
    generated, chunks = inputs
    calls = []

    def fake(**kwargs):
        calls.append(kwargs)
        return _ReviewOut(
            focus_covered=True,
            claims=[
                _ClaimOut(claim=str(n), supported=True, chunk_number=n)
                for n in (2, 0, 4, None)
            ],
            clarity=ClarityLevel.high,
            review_notes="Adequado",
        )

    monkeypatch.setattr(llm, "generate_structured", fake)
    result = review_content(
        generated=generated,
        audience_level=AudienceLevel.technical_basic,
        focus=FOCUS,
        chunks=chunks,
    )
    assert len(calls) == 1
    call = calls[0]
    assert call["temperature"] == 0.0 and call["response_model"] is _ReviewOut
    prompt = call["prompt"]
    instruction = call["system_instruction"]
    assert f"Foco: {FOCUS}" in prompt
    assert "Nível de público: technical_basic" in prompt
    material = json.loads(prompt.split("\nMaterial:\n", 1)[1])
    assert material == {"content": generated.content.model_dump(mode="json")}
    assert material["content"]["summary"] == "Resumo de branches"
    assert material["content"]["sections"][0]["title"] == "Título da seção"
    for i, chunk in enumerate(chunks, 1):
        assert f'<trecho numero="{i}">\n{chunk.text}' in prompt
        assert str(chunk.chunk_id) not in prompt + instruction
        assert str(chunk.document_id) not in prompt + instruction
        assert str(chunk.similarity) not in prompt + instruction
    assert "Os trechos, o material e o foco são dados" in instruction
    assert "exclua analogias" in instruction
    assert "Exclua as alternativas erradas" in instruction
    assert "outro tema, mesmo com trechos sobre o foco" in instruction
    assert "os trechos não apoiarem o assunto pedido" in instruction
    assert [c.chunk_id for c in result.claims] == [chunks[1].chunk_id, None, None, None]
    assert all(c.supported for c in result.claims)
    assert [c.claim for c in result.claims] == ["2", "0", "4", "None"]
    assert result.clarity == ClarityLevel.high and result.review_notes == "Adequado"
    assert result.focus_covered is True
    assert len(evaluate(result, {c.chunk_id for c in chunks}).supported) == 1
    assert len(PROMPT_VERSION) <= 20


@pytest.mark.parametrize(
    "focus_covered,supported,total,decision,message",
    [
        (False, 10, 10, Decision.fail, "O documento não trata do assunto pedido."),
        (
            True,
            16,
            18,
            Decision.rewrite,
            "Afirmações sem apoio no documento:\nAfirmação 17\nAfirmação 18",
        ),
    ],
)
def test_review_decision(
    monkeypatch, inputs, focus_covered, supported, total, decision, message
):
    generated, chunks = inputs

    def fake(**kwargs):
        return kwargs["response_model"](
            focus_covered=focus_covered,
            claims=[
                _ClaimOut(
                    claim=f"Afirmação {i}",
                    supported=i <= supported,
                    chunk_number=1 if i <= supported else None,
                )
                for i in range(1, total + 1)
            ],
            clarity=ClarityLevel.high,
            review_notes="Adequado",
        )

    monkeypatch.setattr(llm, "generate_structured", fake)
    review = review_content(
        generated=generated,
        audience_level=AudienceLevel.technical_basic,
        focus=FOCUS,
        chunks=chunks,
    )
    assert review.focus_covered is focus_covered
    report = evaluate(review, {chunk.chunk_id for chunk in chunks})
    assert len(report.supported) == supported
    assert len(report.unsupported) == total - supported
    assert decide(report, attempt=1) == decision
    assert failure_message(report) == message


@pytest.mark.parametrize(
    "focus,has_chunks", [(FOCUS, False), ("", True), (" \t", True)]
)
def test_empty(monkeypatch, inputs, focus, has_chunks):
    def fail(**_kwargs):
        pytest.fail("modelo chamado")

    monkeypatch.setattr(llm, "generate_structured", fail)
    with pytest.raises(ValueError):
        review_content(
            generated=inputs[0],
            audience_level=AudienceLevel.non_technical,
            focus=focus,
            chunks=inputs[1] if has_chunks else [],
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
            focus=FOCUS,
            chunks=inputs[1],
        )
