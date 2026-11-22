import logging
import math
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel, Field

from app.core import llm
from app.core.config import settings

SECRET_TEXT = "texto-secreto-do-documento"


class Answer(BaseModel):
    title: str
    items: list[str] = Field(min_length=1)


def api_error(code: int, *, retry_delay: str | None = None) -> llm.errors.APIError:
    body: dict[str, Any] = {"status": "FALHA", "message": SECRET_TEXT}
    if retry_delay is not None:
        body["details"] = [
            {
                "@type": "type.googleapis.com/google.rpc.RetryInfo",
                "retryDelay": retry_delay,
            }
        ]
    return llm.errors.APIError(code, {"error": body}, None)


class FakeModels:
    """Responde com `outcomes` em ordem. O último vale para as chamadas seguintes."""

    def __init__(self, *outcomes: Any) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []
        self.call_times: list[float] = []

    def _next(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        self.call_times.append(llm._now())
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome(**kwargs) if callable(outcome) else outcome

    embed_content = _next
    generate_content = _next


def embeddings_for(dimensions: int = llm.EMBEDDING_DIMENSIONS) -> Callable[..., Any]:
    """Cada vetor começa com o índice global do texto, para conferir a ordem."""
    counter = iter(range(10_000))

    def respond(**kwargs: Any) -> Any:
        return SimpleNamespace(
            embeddings=[
                SimpleNamespace(values=[float(next(counter))] * dimensions)
                for _ in kwargs["contents"]
            ]
        )

    return respond


def text_response(text: str | None) -> Any:
    return SimpleNamespace(text=text, embeddings=None)


@pytest.fixture(autouse=True)
def configured(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Usa modelos falsos e avança o relógio só durante as esperas."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "chave-falsa")
    monkeypatch.setattr(settings, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
    monkeypatch.setattr(settings, "GEMINI_GENERATION_MODEL", "modelo-de-texto")
    monkeypatch.setattr(settings, "GEMINI_EMBEDDING_RPM", 100)
    monkeypatch.setattr(settings, "GEMINI_EMBEDDING_TPM", 30_000)
    monkeypatch.setattr(settings, "GEMINI_GENERATION_RPM", 15)
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.setattr(llm, "_embedding_limiter", llm._RateLimiter("embeddings"))
    monkeypatch.setattr(llm, "_generation_limiter", llm._RateLimiter("texto"))
    waits: list[float] = []
    monkeypatch.setattr(llm, "_sleep", waits.append)
    monkeypatch.setattr(llm, "_now", lambda: sum(waits, 0.0))
    return waits


def use(monkeypatch: pytest.MonkeyPatch, *outcomes: Any) -> FakeModels:
    models = FakeModels(*outcomes)
    monkeypatch.setattr(llm, "_client", SimpleNamespace(models=models))
    return models


def sent_texts(call: dict[str, Any]) -> list[str]:
    return [content.parts[0].text for content in call["contents"]]


def test_embed_texts_splits_batches_and_keeps_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models = use(monkeypatch, embeddings_for())

    texts = [f"t{i}" for i in range(45)]

    vectors = llm.embed_texts(texts, task="document")

    assert [len(call["contents"]) for call in models.calls] == [20, 20, 5]
    sent = [text for call in models.calls for text in sent_texts(call)]
    assert sent == [f"title: none | text: {text}" for text in texts]
    assert [vector[0] for vector in vectors] == [float(i) for i in range(45)]
    assert all(len(vector) == 768 for vector in vectors)
    assert models.calls[0]["model"] == "gemini-embedding-2"
    assert models.calls[0]["config"].output_dimensionality == 768


def test_embedding_limits_for_large_document(
    monkeypatch: pytest.MonkeyPatch,
    configured: list[float],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.core.llm")
    models = use(monkeypatch, embeddings_for())
    texts = [f"{i:0>1000}" for i in range(150)]

    vectors = llm.embed_texts(texts, task="document")

    assert [len(call["contents"]) for call in models.calls] == [20] * 7 + [10]
    assert [text for call in models.calls for text in sent_texts(call)] == [
        f"title: none | text: {text}" for text in texts
    ]
    assert [vector[0] for vector in vectors] == list(range(150))
    for end in models.call_times:
        window = [
            text.removeprefix("title: none | text: ")
            for sent_at, call in zip(models.call_times, models.calls, strict=True)
            if end - 60 < sent_at <= end
            for text in sent_texts(call)
        ]
        assert len(window) <= 100
        assert sum(math.ceil(len(text) / 3) for text in window) <= 30_000
    assert sum(configured) > 0
    assert "Gemini embeddings: espera de 60.00s por cota local" in caplog.text
    assert texts[0] not in caplog.text


def test_short_embedding_batch_leaves_without_waiting(
    monkeypatch: pytest.MonkeyPatch, configured: list[float]
) -> None:
    models = use(monkeypatch, embeddings_for())

    assert len(llm.embed_texts(["a"] * 20, task="document")) == 20

    assert models.call_times == [0.0]
    assert configured == []


def test_embedding_requests_share_a_window_between_calls(
    monkeypatch: pytest.MonkeyPatch, configured: list[float]
) -> None:
    models = use(monkeypatch, embeddings_for())

    llm.embed_texts(["a"] * 60, task="document")
    llm.embed_texts(["a"] * 60, task="document")

    assert models.call_times == [0.0] * 5 + [60.0]
    assert configured == [60.0]


def test_oversized_embedding_batches_wait_for_empty_window(
    monkeypatch: pytest.MonkeyPatch, configured: list[float]
) -> None:
    monkeypatch.setattr(settings, "GEMINI_EMBEDDING_RPM", 10)
    models = use(monkeypatch, embeddings_for())

    assert len(llm.embed_texts(["a"] * 40, task="document")) == 40

    assert models.call_times == [0.0, 60.0]
    assert configured == [60.0]


def test_embed_texts_empty_list_does_not_call_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models = use(monkeypatch, embeddings_for())

    assert llm.embed_texts([], task="document") == []
    assert models.calls == []


def test_embed_texts_rejects_wrong_vector_size(monkeypatch: pytest.MonkeyPatch) -> None:
    use(monkeypatch, embeddings_for(dimensions=767))

    with pytest.raises(llm.LLMInvalidResponseError, match="767"):
        llm.embed_texts(["a"], task="document")


def test_embed_texts_rejects_wrong_vector_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    use(monkeypatch, SimpleNamespace(embeddings=None))

    with pytest.raises(llm.LLMInvalidResponseError):
        llm.embed_texts(["a"], task="document")


def test_embed_texts_sends_task_as_text_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    models = use(monkeypatch, embeddings_for())

    llm.embed_texts(["a"], task="document")
    llm.embed_texts(["a"], task="query")

    document, query = models.calls
    assert sent_texts(document) == ["title: none | text: a"]
    assert sent_texts(query) == ["task: search result | query: a"]
    assert document["config"].task_type is None
    assert query["config"].task_type is None


def test_embed_texts_sends_task_type_to_older_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    models = use(monkeypatch, embeddings_for())

    llm.embed_texts(["a"], task="document")
    llm.embed_texts(["a"], task="query")

    document, query = models.calls
    assert sent_texts(document) == sent_texts(query) == ["a"]
    assert document["config"].task_type == "RETRIEVAL_DOCUMENT"
    assert query["config"].task_type == "RETRIEVAL_QUERY"


def test_generate_structured_returns_validated_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models = use(monkeypatch, text_response('{"title": "T", "items": ["a"]}'))

    answer = llm.generate_structured(
        system_instruction="sistema",
        prompt="pedido",
        response_model=Answer,
    )

    assert answer == Answer(title="T", items=["a"])
    (call,) = models.calls
    assert call["model"] == "modelo-de-texto"
    assert call["contents"] == "pedido"
    config = call["config"]
    assert config.system_instruction == "sistema"
    assert config.temperature == 0.2
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == Answer.model_json_schema()


@pytest.mark.parametrize(
    "text",
    [None, "", "isto não é JSON", '{"title": "T", "items": []}'],
)
def test_generate_structured_rejects_invalid_response_without_retry(
    monkeypatch: pytest.MonkeyPatch, text: str | None
) -> None:
    models = use(monkeypatch, text_response(text))

    with pytest.raises(llm.LLMInvalidResponseError) as raised:
        llm.generate_structured(
            system_instruction="s", prompt="p", response_model=Answer
        )

    assert len(models.calls) == 1
    assert raised.value.__cause__ is None


def test_generation_waits_after_fifteen_requests(
    monkeypatch: pytest.MonkeyPatch, configured: list[float]
) -> None:
    models = use(monkeypatch, text_response('{"title": "T", "items": ["a"]}'))

    for _ in range(16):
        llm.generate_structured(
            system_instruction="s", prompt="p", response_model=Answer
        )

    assert models.call_times == [0.0] * 15 + [60.0]
    assert configured == [60.0]


@pytest.mark.parametrize(("code", "waits"), [(429, [60.0, 60.0]), (503, [1.0, 2.0])])
def test_two_temporary_errors_then_success(
    monkeypatch: pytest.MonkeyPatch,
    configured: list[float],
    code: int,
    waits: list[float],
) -> None:
    models = use(monkeypatch, api_error(code), api_error(code), embeddings_for())

    vectors = llm.embed_texts(["a"], task="query")

    assert len(vectors) == 1
    assert len(models.calls) == 3
    assert configured == waits


@pytest.mark.parametrize(
    ("code", "retry_delay", "wait"),
    [
        (429, "37s", 37.0),
        (429, "37.5s", 37.5),
        (429, "60s", 60.0),
        (429, None, 60.0),
        (429, "invalido", 60.0),
        (503, None, 1.0),
    ],
)
def test_temporary_error_then_success(
    monkeypatch: pytest.MonkeyPatch,
    configured: list[float],
    code: int,
    retry_delay: str | None,
    wait: float,
) -> None:
    models = use(
        monkeypatch, api_error(code, retry_delay=retry_delay), embeddings_for()
    )

    assert len(llm.embed_texts(["a"], task="query")) == 1

    assert models.call_times == [0.0, wait]
    assert configured == [wait]


def test_generation_retries_after_short_rate_limit_delay(
    monkeypatch: pytest.MonkeyPatch, configured: list[float]
) -> None:
    models = use(
        monkeypatch,
        api_error(429, retry_delay="37s"),
        text_response('{"title": "T", "items": ["a"]}'),
    )

    answer = llm.generate_structured(
        system_instruction="s", prompt="p", response_model=Answer
    )

    assert answer == Answer(title="T", items=["a"])
    assert models.call_times == [0.0, 37.0]
    assert configured == [37.0]


@pytest.mark.parametrize("kind", ["embeddings", "text"])
@pytest.mark.parametrize("retry_delay", ["60.001s", "17321s"])
def test_long_rate_limit_delay_raises_without_waiting(
    monkeypatch: pytest.MonkeyPatch,
    configured: list[float],
    kind: str,
    retry_delay: str,
) -> None:
    models = use(monkeypatch, api_error(429, retry_delay=retry_delay))

    with pytest.raises(llm.LLMRateLimitError) as raised:
        if kind == "embeddings":
            llm.embed_texts([SECRET_TEXT], task="document")
        else:
            llm.generate_structured(
                system_instruction="s", prompt=SECRET_TEXT, response_model=Answer
            )

    assert str(raised.value) == (
        "A API Gemini recusou o pedido por limite de uso (429). "
        "Tente de novo mais tarde."
    )
    assert len(models.calls) == 1
    assert configured == []


def test_three_rate_limit_errors_raise_llm_rate_limit_error(
    monkeypatch: pytest.MonkeyPatch,
    configured: list[float],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.core.llm")
    models = use(monkeypatch, api_error(429, retry_delay="37s"))

    with pytest.raises(llm.LLMRateLimitError) as raised:
        llm.embed_texts([SECRET_TEXT], task="query")

    assert str(raised.value) == (
        "A API Gemini recusou o pedido por limite de uso (429). "
        "Tente de novo mais tarde."
    )
    assert raised.value.__cause__ is None
    assert len(models.calls) == 3
    assert configured == [37.0, 37.0]
    assert "Gemini embeddings: espera de 37.00s por HTTP 429" in caplog.text
    assert SECRET_TEXT not in caplog.text


def test_retry_counts_toward_quota(
    monkeypatch: pytest.MonkeyPatch, configured: list[float]
) -> None:
    monkeypatch.setattr(settings, "GEMINI_EMBEDDING_RPM", 2)
    models = use(monkeypatch, api_error(429, retry_delay="37s"), embeddings_for())

    llm.embed_texts(["a"], task="query")
    llm.embed_texts(["b"], task="query")

    assert models.call_times == [0.0, 37.0, 60.0]
    assert configured == [37.0, 23.0]


def test_four_temporary_errors_raise_llm_error(
    monkeypatch: pytest.MonkeyPatch, configured: list[float]
) -> None:
    models = use(monkeypatch, api_error(503))

    with pytest.raises(llm.LLMError) as raised:
        llm.generate_structured(
            system_instruction="s", prompt="p", response_model=Answer
        )

    assert not isinstance(raised.value, llm.LLMInvalidResponseError)
    assert len(models.calls) == 4
    assert configured == [1.0, 2.0, 4.0]


@pytest.mark.parametrize("failure", [api_error(400), RuntimeError(SECRET_TEXT)])
def test_other_failures_raise_llm_error_without_retry(
    monkeypatch: pytest.MonkeyPatch, configured: list[float], failure: Exception
) -> None:
    models = use(monkeypatch, failure)

    with pytest.raises(llm.LLMError):
        llm.embed_texts(["a"], task="document")

    assert len(models.calls) == 1
    assert configured == []


def test_without_api_key_raises_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)

    with pytest.raises(llm.LLMNotConfiguredError):
        llm.embed_texts(["a"], task="document")
    with pytest.raises(llm.LLMNotConfiguredError):
        llm.generate_structured(
            system_instruction="s", prompt="p", response_model=Answer
        )


def test_without_generation_model_raises_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models = use(monkeypatch, text_response("{}"))
    monkeypatch.setattr(settings, "GEMINI_GENERATION_MODEL", None)

    with pytest.raises(llm.LLMNotConfiguredError):
        llm.generate_structured(
            system_instruction="s", prompt="p", response_model=Answer
        )
    assert models.calls == []


def test_client_is_created_on_first_call_and_reused() -> None:
    client = llm._get_client()

    assert isinstance(client, llm.genai.Client)
    assert llm._get_client() is client


@pytest.mark.parametrize(
    "outcome",
    [
        api_error(400),
        api_error(503),
        RuntimeError(SECRET_TEXT),
        embeddings_for(dimensions=1),
        text_response(SECRET_TEXT),
        text_response(f'{{"title": "{SECRET_TEXT}", "items": []}}'),
    ],
)
def test_errors_and_logs_never_carry_document_text_or_model_response(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    outcome: Any,
) -> None:
    caplog.set_level(logging.DEBUG)

    for call in (
        lambda: llm.embed_texts([SECRET_TEXT], task="document"),
        lambda: llm.generate_structured(
            system_instruction=SECRET_TEXT, prompt=SECRET_TEXT, response_model=Answer
        ),
    ):
        use(monkeypatch, outcome)
        with pytest.raises(llm.LLMError) as raised:
            call()
        assert SECRET_TEXT not in str(raised.value)
        # Nenhuma exceção encadeada leva o texto para um traceback.
        assert raised.value.__cause__ is None
        assert raised.value.__context__ is None or raised.value.__suppress_context__

    assert SECRET_TEXT not in caplog.text


def test_successful_calls_log_model_count_and_time(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app.core.llm")

    use(monkeypatch, embeddings_for())
    llm.embed_texts([SECRET_TEXT, SECRET_TEXT], task="document")
    use(monkeypatch, text_response(f'{{"title": "{SECRET_TEXT}", "items": ["a"]}}'))
    llm.generate_structured(
        system_instruction=SECRET_TEXT, prompt=SECRET_TEXT, response_model=Answer
    )

    assert "modelo=gemini-embedding-2 textos=2 tempo=" in caplog.text
    assert "modelo=modelo-de-texto textos=1 tempo=" in caplog.text
    assert SECRET_TEXT not in caplog.text
