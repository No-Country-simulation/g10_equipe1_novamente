"""Acesso à API Gemini. Só este módulo importa o SDK."""

import logging
import time
from collections.abc import Callable, Sequence
from functools import partial
from typing import Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 768
EMBED_BATCH_SIZE = 20

_TEMPORARY_STATUS_CODES = {429, 503}
_RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0)

_sleep: Callable[[float], None] = time.sleep
_client: genai.Client | None = None


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


def _call_api[R](call: Callable[[], R]) -> R:
    """Chama a API e tenta de novo em erro temporário.

    As exceções saem sem causa encadeada, porque o erro do SDK pode trazer
    o texto enviado ou a resposta do modelo.
    """
    failure: str
    for delay in (*_RETRY_DELAYS_SECONDS, None):
        try:
            return call()
        except errors.APIError as error:
            failure = f"A API Gemini respondeu {error.code} {error.status}."
            temporary = error.code in _TEMPORARY_STATUS_CODES
        except Exception as error:
            failure = f"A chamada à API Gemini falhou: {type(error).__name__}."
            temporary = False
        if not temporary or delay is None:
            break
        _sleep(delay)
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
            )
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
        )
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
