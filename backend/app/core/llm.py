"""Acesso à API Gemini. Só este módulo importa o SDK."""

import logging
import math
import time
from collections import deque
from collections.abc import Callable, Sequence
from functools import partial
from threading import Lock
from typing import Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 768
EMBED_BATCH_SIZE = 20

_WINDOW_SECONDS = 60.0
_MAX_RATE_LIMIT_RETRIES = 2
_RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0)

_sleep: Callable[[float], None] = time.sleep
_now: Callable[[], float] = time.monotonic
_client: genai.Client | None = None


def _wait(kind: str, reason: str, seconds: float) -> None:
    if seconds >= 1:
        logger.info("Gemini %s: espera de %.2fs por %s", kind, seconds, reason)
    _sleep(seconds)


class _RateLimiter:
    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._lock = Lock()
        self._window: deque[tuple[float, int, int]] = deque()

    def acquire(self, *, requests: int, tokens: int, rpm: int, tpm: int | None) -> None:
        window = self._window
        while True:
            with self._lock:
                now = _now()
                while window and window[0][0] + _WINDOW_SECONDS <= now:
                    window.popleft()
                # Um lote acima do limite precisa da janela vazia para sair.
                if not window or (
                    requests + sum(count for _, count, _ in window) <= rpm
                    and (
                        tpm is None
                        or tokens + sum(cost for _, _, cost in window) <= tpm
                    )
                ):
                    window.append((now, requests, tokens))
                    return
                delay = window[0][0] + _WINDOW_SECONDS - now
            _wait(self.kind, "cota local", delay)


_embedding_limiter = _RateLimiter("embeddings")
_generation_limiter = _RateLimiter("texto")


class LLMError(Exception): ...


class LLMNotConfiguredError(LLMError): ...


class LLMInvalidResponseError(LLMError): ...


def _get_client() -> genai.Client:
    global _client
    if not settings.GEMINI_API_KEY:
        raise LLMNotConfiguredError("GEMINI_API_KEY não está definida.")
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _rate_limit_delay(error: errors.APIError) -> float:
    # O SDK guarda o corpo JSON em `details`.
    body = error.details
    if isinstance(body, dict):
        body = body.get("error", body)
    details = body.get("details") if isinstance(body, dict) else None
    if isinstance(details, list):
        for detail in details:
            if not isinstance(detail, dict) or detail.get("@type") != (
                "type.googleapis.com/google.rpc.RetryInfo"
            ):
                continue
            duration = detail.get("retryDelay")
            if isinstance(duration, str) and duration.endswith("s"):
                try:
                    seconds = float(duration[:-1])
                except ValueError:
                    continue
                if math.isfinite(seconds) and seconds >= 0:
                    return seconds
    return _WINDOW_SECONDS


def _call_api[R](
    call: Callable[[], R],
    *,
    limiter: _RateLimiter,
    rpm: int,
    tpm: int | None = None,
    requests: int = 1,
    tokens: int = 0,
) -> R:
    """Chama a API e tenta de novo em erro temporário.

    As exceções saem sem causa encadeada, porque o erro do SDK pode trazer
    o texto enviado ou a resposta do modelo.
    """
    rate_limit_retries = 0
    unavailable_delays = iter(_RETRY_DELAYS_SECONDS)
    while True:
        limiter.acquire(requests=requests, tokens=tokens, rpm=rpm, tpm=tpm)
        try:
            return call()
        except errors.APIError as error:
            failure = f"A API Gemini respondeu {error.code} {error.status}."
            if error.code == 429:
                failure = (
                    "A API Gemini recusou o pedido por limite de uso (429). "
                    "Tente de novo mais tarde."
                )
                if rate_limit_retries == _MAX_RATE_LIMIT_RETRIES:
                    break
                rate_limit_retries += 1
                delay = _rate_limit_delay(error)
            elif error.code == 503:
                next_delay = next(unavailable_delays, None)
                if next_delay is None:
                    break
                delay = next_delay
            else:
                break
            reason = f"HTTP {error.code}"
        except Exception as error:
            failure = f"A chamada à API Gemini falhou: {type(error).__name__}."
            break
        _wait(limiter.kind, reason, delay)
    raise LLMError(failure) from None


def _embedding_request(
    model: str, text: str, task: Literal["document", "query"]
) -> tuple[str, str | None]:
    """Devolve o texto a enviar e o `task_type` da API.

    `gemini-embedding-2` não aceita `task_type`: a tarefa vai como prefixo
    do texto. Os modelos anteriores recebem `task_type`.
    """
    if "gemini-embedding-2" in model:
        if task == "document":
            return f"title: none | text: {text}", None
        return f"task: search result | query: {text}", None
    task_type = "RETRIEVAL_DOCUMENT" if task == "document" else "RETRIEVAL_QUERY"
    return text, task_type


def embed_texts(
    texts: Sequence[str],
    *,
    task: Literal["document", "query"],
) -> list[list[float]]:
    if not texts:
        return []
    client = _get_client()
    model = settings.GEMINI_EMBEDDING_MODEL
    started = time.monotonic()

    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        requests = [_embedding_request(model, text, task) for text in batch]
        # Um `Content` por texto: o `gemini-embedding-2` junta em um só vetor
        # os textos enviados soltos em `contents`.
        contents: list[types.ContentOrDict] = [
            types.Content(parts=[types.Part.from_text(text=text)])
            for text, _ in requests
        ]
        config = types.EmbedContentConfig(
            task_type=requests[0][1],
            output_dimensionality=EMBEDDING_DIMENSIONS,
        )
        response = _call_api(
            partial(
                client.models.embed_content,
                model=model,
                contents=contents,
                config=config,
            ),
            limiter=_embedding_limiter,
            rpm=settings.GEMINI_EMBEDDING_RPM,
            tpm=settings.GEMINI_EMBEDDING_TPM,
            requests=len(batch),
            tokens=sum(math.ceil(len(text) / 3) for text in batch),
        )
        embeddings = response.embeddings or []
        if len(embeddings) != len(batch):
            raise LLMInvalidResponseError(
                f"A API devolveu {len(embeddings)} vetores para {len(batch)} textos."
            )
        for embedding in embeddings:
            values = embedding.values or []
            if len(values) != EMBEDDING_DIMENSIONS:
                raise LLMInvalidResponseError(
                    f"A API devolveu um vetor de {len(values)} valores. "
                    f"O esperado é {EMBEDDING_DIMENSIONS}."
                )
            vectors.append(values)

    logger.info(
        "Gemini embeddings: modelo=%s textos=%d tempo=%.2fs",
        model,
        len(texts),
        time.monotonic() - started,
    )
    return vectors


def generate_structured[T: BaseModel](
    *,
    system_instruction: str,
    prompt: str,
    response_model: type[T],
    temperature: float = 0.2,
) -> T:
    client = _get_client()
    model = settings.GEMINI_GENERATION_MODEL
    if not model:
        raise LLMNotConfiguredError("GEMINI_GENERATION_MODEL não está definida.")
    started = time.monotonic()

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        response_mime_type="application/json",
        response_json_schema=response_model.model_json_schema(),
    )
    text = _call_api(
        lambda: (
            client.models.generate_content(
                model=model, contents=prompt, config=config
            ).text
        ),
        limiter=_generation_limiter,
        rpm=settings.GEMINI_GENERATION_RPM,
    )
    logger.info(
        "Gemini texto: modelo=%s textos=1 tempo=%.2fs",
        model,
        time.monotonic() - started,
    )

    if not text:
        raise LLMInvalidResponseError("A API devolveu uma resposta vazia.")
    try:
        return response_model.model_validate_json(text)
    except ValidationError as error:
        # Sem causa encadeada: o erro do pydantic traz a resposta do modelo.
        raise LLMInvalidResponseError(
            f"A resposta não segue o schema de {response_model.__name__}: "
            f"{error.error_count()} erro(s) de validação."
        ) from None
