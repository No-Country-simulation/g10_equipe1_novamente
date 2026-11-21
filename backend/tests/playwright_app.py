from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel

from app.core import llm
from app.core.storage import InMemoryStorage, get_storage
from app.main import app
from app.models import ContentFormat
from app.services import planner, retrieval, reviewer
from app.services.content_schemas import GENERATED_MODELS

_COMMANDS = [
    ("git status", "mostra o estado da árvore de trabalho"),
    ("git add", "prepara alterações para o próximo commit"),
    ("git commit", "registra as alterações preparadas"),
    ("git log", "mostra o histórico de commits"),
    ("git diff", "mostra diferenças entre versões"),
    ("git branch", "lista as branches locais"),
    ("git switch", "troca a branch atual"),
    ("git fetch", "busca referências de um repositório remoto"),
]
_TUTORIAL_TOPIC = "Estado da árvore de trabalho"
_PLAN_TOPICS = {
    ContentFormat.tutorial: [_TUTORIAL_TOPIC],
    ContentFormat.flashcards: [f"Uso de {command}" for command, _ in _COMMANDS],
    ContentFormat.quiz: [f"Uso de {command}" for command, _ in _COMMANDS[:5]],
}
_PLAN_FORMATS = {model: fmt for fmt, model in planner._RESPONSE_MODELS.items()}
_GENERATED_FORMATS = {model: fmt for fmt, model in GENERATED_MODELS.items()}
_TITLES = {
    ContentFormat.tutorial: "Guia de comandos Git",
    ContentFormat.flashcards: "Cartões de comandos Git",
    ContentFormat.quiz: "Quiz de comandos Git",
}
_CONTENTS = {
    ContentFormat.tutorial: {
        "summary": "Conheça os comandos básicos do Git.",
        "sections": [
            {
                "title": _TUTORIAL_TOPIC,
                "body": "O comando `git status` mostra o estado da árvore de trabalho.",
            }
        ],
        "takeaways": ["Use git status para conferir a árvore de trabalho."],
    },
    ContentFormat.flashcards: {
        "introduction": "Revise a função de cada comando Git.",
        "cards": [
            {"front": f"O que faz {command}?", "back": f"{purpose.capitalize()}."}
            for command, purpose in _COMMANDS
        ],
    },
    ContentFormat.quiz: {
        "questions": [
            {
                "prompt": f"Qual comando {purpose}?",
                "options": [option for option, _ in _COMMANDS[index : index + 4]],
                "correct_index": 0,
                "explanation": f"O comando {command} {purpose}.",
            }
            for index, (command, purpose) in enumerate(_COMMANDS[:5])
        ],
    },
}


def _embed_texts(
    texts: Sequence[str], *, task: Literal["document", "query"]
) -> list[list[float]]:
    if task not in ("document", "query"):
        raise ValueError(f"Tarefa de embedding inesperada no Playwright: {task}")
    return [[1.0] * retrieval.EMBEDDING_DIMENSIONS for _ in texts]


def _generate_structured[T: BaseModel](
    *,
    system_instruction: str,  # noqa: ARG001
    prompt: str,
    response_model: type[T],
    temperature: float = 0.2,  # noqa: ARG001
) -> T:
    if response_model in _PLAN_FORMATS:
        topics = _PLAN_TOPICS[_PLAN_FORMATS[response_model]]
        return response_model.model_validate(
            {"items": [{"topic": topic, "chunk_numbers": [1]} for topic in topics]}
        )

    if response_model in _GENERATED_FORMATS:
        content_format = _GENERATED_FORMATS[response_model]
        first_topic = _PLAN_TOPICS[content_format][0]
        if f"1. {first_topic} (trechos 1)" not in prompt.splitlines():
            raise ValueError(
                f"O prompt de escrita não recebeu o plano de {content_format}"
            )
        return response_model.model_validate(
            {
                "title": _TITLES[content_format],
                "estimated_minutes": 5,
                "key_concepts": ["Git"],
                "prerequisites": [],
                "content": _CONTENTS[content_format],
            }
        )

    if response_model is reviewer._ReviewOut:
        return response_model.model_validate(
            {
                "focus_covered": not prompt.startswith("Foco: [falha]"),
                "claims": [
                    {
                        "claim": "O comando git status mostra o estado da árvore de trabalho.",
                        "supported": True,
                        "chunk_number": 1,
                    }
                ],
                "clarity": "high",
                "review_notes": "O exemplo explica a função do comando.",
            }
        )

    raise ValueError(f"Modelo de resposta inesperado no Playwright: {response_model}")


_storage = InMemoryStorage()
app.dependency_overrides[get_storage] = lambda: _storage
llm.embed_texts = _embed_texts
llm.generate_structured = _generate_structured
