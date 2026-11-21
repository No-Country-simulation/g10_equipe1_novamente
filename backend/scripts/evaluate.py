"""Mede a busca, o revisor e a geração com casos escritos à mão."""

import argparse
import json
import secrets
import sys
import uuid
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import escape
from itertools import chain
from pathlib import Path
from textwrap import indent
from typing import Any

from pydantic import PrivateAttr, ValidationError
from pydantic_core import ErrorDetails
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlmodel import Session, col, delete, select

from app.core.config import settings
from app.core.db import engine
from app.core.llm import LLMError
from app.core.security import get_password_hash
from app.core.storage import InMemoryStorage, document_key
from app.models import (
    AudienceLevel,
    ClarityLevel,
    ContentFormat,
    Course,
    Niche,
    SourceDocument,
    User,
)
from app.services import (
    course_generation,
    generation_graph,
    grounding,
    indexing,
    reviewer,
)
from app.services.content_schemas import (
    GENERATED_MODELS,
    GeneratedBase,
    StrictModel,
    Text,
    Title,
)
from app.services.documents import DocumentError, ExtractedDocument, read_document
from app.services.retrieval import RetrievedChunk
from app.services.writer import WriteRequest

REPO_ROOT = Path(__file__).resolve().parents[2]


class CaseError(ValueError): ...


class RetrievalCase(StrictModel):
    question: Text
    expected: Text


class GenerationCase(StrictModel):
    focus: Title
    audience_level: AudienceLevel
    format: ContentFormat


class ReviewCase(GenerationCase):
    id: Text
    planted_error: Text | None
    content: Any

    def generated(self) -> GeneratedBase:
        return GENERATED_MODELS[self.format].model_validate(
            {
                "title": self.focus,
                "estimated_minutes": 5,
                "key_concepts": ["avaliação"],
                "prerequisites": [],
                "content": self.content,
            }
        )


class CaseFile(StrictModel):
    document: Text
    niche: Text
    retrieval: list[RetrievalCase]
    review: list[ReviewCase]
    generation: list[GenerationCase]
    _source: tuple[ExtractedDocument, bytes] = PrivateAttr()


def _issue_location(parts: tuple[str | int, ...], raw: Any) -> str:
    locations = []
    if isinstance(raw, dict) and len(parts) >= 2:
        list_name, index = parts[:2]
        items = raw.get(list_name)
        name_field = {
            "review": "id",
            "retrieval": "question",
            "generation": "focus",
        }.get(list_name)
        if (
            name_field is not None
            and isinstance(items, list)
            and isinstance(index, int)
            and index < len(items)
        ):
            item = items[index]
            name = item.get(name_field) if isinstance(item, dict) else None
            label = f"{list_name} {index + 1}"
            if isinstance(name, str) and name.strip():
                label += f" ({name.strip()!r})"
            locations.append(label)
            parts = parts[2:]
    locations.extend(str(part + 1) if isinstance(part, int) else part for part in parts)
    return " / ".join(locations) or "arquivo"


def _issue_message(issue: ErrorDetails) -> str:
    message = issue["msg"]
    context = issue.get("ctx", {})
    match issue["type"]:
        case "enum":
            return "use " + message.removeprefix("Input should be ").replace(
                " or ", " ou "
            )
        case "missing":
            return "preencha este campo"
        case "extra_forbidden":
            return "remova este campo"
        case "string_type" | "string_too_short":
            return "preencha com texto entre aspas"
        case "string_too_long":
            return f"use até {context['max_length']} caracteres"
        case "list_type":
            return "use uma lista entre colchetes"
        case "too_short":
            return f"inclua pelo menos {context['min_length']} itens"
        case "too_long":
            return f"mantenha no máximo {context['max_length']} itens"
        case "model_type" | "model_attributes_type":
            return "use um objeto entre chaves, como no guia"
        case "int_type" | "int_parsing" | "int_from_float":
            return "use um número inteiro"
        case "greater_than_equal" | "less_than_equal":
            return "use um número de 0 a 3 para indicar a opção correta"
        case _:
            return message.removeprefix("Value error, ")


def _validation_details(error: ValidationError, raw: Any = None) -> str:
    return "\n".join(
        f"- {_issue_location(issue['loc'], raw)}: {_issue_message(issue)}"
        for issue in error.errors(include_input=False, include_url=False)
    )


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _text_fields(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _text_fields(item)
    elif isinstance(value, list):
        for item in value:
            yield from _text_fields(item)


def load_cases(path: Path) -> CaseFile:
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise CaseError(
            f"JSON inválido na linha {exc.lineno}, coluna {exc.colno}. "
            "Confira as aspas, vírgulas e chaves nesse ponto."
        ) from exc
    except UnicodeDecodeError as exc:
        raise CaseError(
            f"Salve o arquivo de casos {path} com codificação UTF-8."
        ) from exc
    except OSError as exc:
        raise CaseError(
            f"Não foi possível ler o arquivo de casos {path}. Confira o caminho e a permissão de leitura."
        ) from exc
    try:
        cases = CaseFile.model_validate(raw)
    except ValidationError as exc:
        raise CaseError(
            f"Corrija os campos do arquivo de casos.\n{_validation_details(exc, raw)}"
        ) from exc

    if not (cases.retrieval or cases.review or cases.generation):
        raise CaseError("Inclua pelo menos um caso em retrieval, review ou generation.")
    source_path = REPO_ROOT / cases.document
    try:
        data = source_path.read_bytes()
        document = read_document(source_path.name, data)
    except (OSError, ValueError) as exc:
        detail = (
            exc.message
            if isinstance(exc, DocumentError)
            else "Confira o caminho em document e a permissão de leitura."
        )
        raise CaseError(
            f"Não foi possível ler o documento {cases.document}. {detail}"
        ) from exc
    cases._source = (document, data)

    document_text = _normalized(document.text)
    chunks = [
        _normalized(chunk.text)
        for chunk in indexing.split_text(
            document.text, paged=document.mime_type == "application/pdf"
        )
    ]
    for case in cases.retrieval:
        expected = _normalized(case.expected)
        if expected not in document_text:
            raise CaseError(
                f"Busca {case.question!r}: a frase de expected não está no documento. Copie a frase exata do arquivo."
            )
        if not any(expected in chunk for chunk in chunks):
            raise CaseError(
                f"Busca {case.question!r}: a frase de expected cruza o limite entre dois trechos. "
                "Escolha uma frase mais curta de um único parágrafo."
            )

    seen: set[str] = set()
    for position, case in enumerate(cases.review, 1):
        label = f"Revisor {position} ({case.id!r})"
        if case.id in seen:
            raise CaseError(
                f"{label}: id repetido. Use um id diferente para cada caso."
            )
        seen.add(case.id)
        try:
            content = case.generated().model_dump()["content"]
        except ValidationError as exc:
            raise CaseError(
                f"{label}: conteúdo inválido para {case.format}. "
                f"Confira o exemplo desse formato em examples/evals/README.md.\n{_validation_details(exc)}"
            ) from exc
        if case.planted_error is not None and not any(
            _normalized(case.planted_error) in _normalized(value)
            for value in _text_fields(content)
        ):
            raise CaseError(
                f"{label}: copie o texto exato do fato errado de content para planted_error."
            )
    return cases


def retrieval_rank(expected: str, chunks: Sequence[RetrievedChunk]) -> int | None:
    expected = _normalized(expected)
    return next(
        (
            rank
            for rank, chunk in enumerate(chunks, 1)
            if expected in _normalized(chunk.text)
        ),
        None,
    )


@dataclass
class Measurements:
    ranks: list[tuple[str, int | None]] = field(default_factory=list)
    reviews: list[tuple[ReviewCase, ClarityLevel, grounding.GroundingReport]] = field(
        default_factory=list
    )
    generations: list[
        tuple[GenerationCase, generation_graph.GenerationResult, list[RetrievedChunk]]
    ] = field(default_factory=list)
    clues: list[tuple[str, str, str]] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)


def _retrieve(session: Session, course: Course, query: str) -> list[RetrievedChunk]:
    chunks = course_generation.retrieve_chunks(
        session=session, course=course, query=query
    )
    session.commit()
    return chunks


def _clue(
    session: Session, course: Course, claim: str, used_ids: set[uuid.UUID]
) -> str:
    try:
        chunks = _retrieve(session, course, claim)
    except Exception as exc:
        session.rollback()
        reason = str(exc) if isinstance(exc, LLMError) else type(exc).__name__
        return f"Pista indisponível. A busca falhou: {reason.rstrip('.')}. Confira a conexão com o banco e o Gemini antes de tentar de novo."
    if not chunks:
        return "Pista indisponível. A busca não devolveu trechos. Confira se o documento tem texto sobre a afirmação."
    nearest = chunks[0]
    position = "Entre os 8" if nearest.chunk_id in used_ids else "Fora dos 8"
    return f"{position}. Chunk {nearest.chunk_index}, similaridade {nearest.similarity:.3f}. {nearest.text[:300]}"


def _model_failure(result: generation_graph.GenerationResult) -> bool:
    # Se a reescrita falha, o grafo mantém o relatório da primeira tentativa.
    return result.decision == grounding.Decision.fail and (
        result.report is None
        or result.error_message != grounding.failure_message(result.report)
    )


def _measure(
    session: Session, course: Course, niche: Niche, cases: CaseFile
) -> Measurements:
    measured = Measurements()
    for case in chain(cases.retrieval, cases.review, cases.generation):
        if isinstance(case, RetrievalCase):
            label, query = f"Busca: {case.question}", case.question
        elif isinstance(case, ReviewCase):
            label, query = f"Revisor: {case.id}", case.focus
        else:
            label, query = (
                f"Geração: {case.focus} ({case.format}, {case.audience_level})",
                case.focus,
            )

        try:
            chunks = _retrieve(session, course, query)
            if isinstance(case, RetrievalCase):
                measured.ranks.append(
                    (case.question, retrieval_rank(case.expected, chunks))
                )
                continue
            if not chunks:
                measured.errors.append(
                    (
                        label,
                        "A busca não devolveu trechos. Confira o documento e o modelo de embeddings.",
                    )
                )
                continue

            used_ids = {chunk.chunk_id for chunk in chunks}
            if isinstance(case, ReviewCase):
                review = reviewer.review_content(
                    generated=case.generated(),
                    audience_level=case.audience_level,
                    focus=case.focus,
                    chunks=chunks,
                )
                report = grounding.evaluate(review, used_ids)
                measured.reviews.append((case, review.clarity, report))
                diagnose = case.planted_error is None and not report.passed
            else:
                result = generation_graph.generate_content(
                    WriteRequest(
                        content_format=case.format,
                        focus=case.focus,
                        audience_level=case.audience_level,
                        niche_name=niche.name,
                        niche_prompt_hint=niche.prompt_hint,
                        chunks=chunks,
                    )
                )
                measured.generations.append((case, result, chunks))
                if _model_failure(result):
                    measured.errors.append(
                        (label, result.error_message or "O modelo falhou.")
                    )
                report = result.report
                diagnose = result.decision == grounding.Decision.fail
        except LLMError as exc:
            session.rollback()
            measured.errors.append((label, str(exc)))
            continue

        if diagnose and report is not None:
            for claim in report.unsupported:
                clue = _clue(session, course, claim.claim, used_ids)
                measured.clues.append((label, claim.claim, clue))
    return measured


def _run(cases: CaseFile) -> tuple[int, Measurements]:
    if not (settings.GEMINI_API_KEY or "").strip():
        raise CaseError("Defina GEMINI_API_KEY no .env da raiz do repositório.")
    if (cases.review or cases.generation) and not (
        settings.GEMINI_GENERATION_MODEL or ""
    ).strip():
        raise CaseError(
            "Defina GEMINI_GENERATION_MODEL no .env da raiz para avaliar o revisor ou a geração."
        )
    if not settings.GEMINI_EMBEDDING_MODEL.strip():
        raise CaseError(
            "Defina GEMINI_EMBEDDING_MODEL no .env da raiz ou remova a linha para usar o modelo padrão."
        )

    extracted, data = cases._source
    storage = InMemoryStorage()
    owner_id = None
    try:
        with Session(engine, expire_on_commit=False) as session:
            niche = session.exec(
                select(Niche).where(Niche.slug == cases.niche)
            ).one_or_none()
            if niche is None:
                raise CaseError(
                    f"Nicho {cases.niche!r} não encontrado. Em niche, use geral, fintech, saude ou e-commerce."
                )
            assert niche.id is not None
            owner = User(
                email=f"avaliacao-{uuid.uuid4()}@example.com",
                is_active=False,
                hashed_password=get_password_hash(secrets.token_urlsafe()),
            )
            course = Course(
                owner_id=owner.id,
                niche_id=niche.id,
                title="Avaliação",
                audience_level=AudienceLevel.technical_basic,
            )
            document_id = uuid.uuid4()
            key = document_key(course.id, document_id, extracted.extension)
            storage.put(key, data, extracted.mime_type)
            document = SourceDocument(
                id=document_id,
                course_id=course.id,
                title=extracted.filename,
                original_filename=extracted.filename,
                oci_object_key=key,
                mime_type=extracted.mime_type,
                size_bytes=extracted.size_bytes,
                sha256=extracted.sha256,
            )
            document.course = course
            course.owner = owner
            session.add(document)
            owner_id = owner.id
            session.commit()
            count = indexing.index_document(
                session=session, storage=storage, document_id=document_id
            )
            return count, _measure(session, course, niche, cases)
    finally:
        if owner_id is not None:
            try:
                with Session(engine) as cleanup, cleanup.begin():
                    cleanup.exec(delete(User).where(col(User.id) == owner_id))
            except SQLAlchemyError as exc:
                raise CaseError(
                    f"Não foi possível apagar o usuário da avaliação {owner_id} ({type(exc).__name__}). "
                    "Peça à equipe para remover esse usuário do banco antes de repetir a avaliação."
                ) from exc


def _count(
    label: str, success: int, total: int, *, percent: bool = False, note: str = ""
) -> str:
    result = f"{success} de {total}" if total else "Sem casos medidos"
    if total and percent:
        result += f" ({success / total:.0%})"
    return f"{label}: {result}. {note}".rstrip()


def _summary(measured: Measurements) -> tuple[str, str, str, str]:
    hits = sum(rank is not None for _, rank in measured.ranks)
    total = len(measured.ranks)
    planted = [
        report.passed
        for case, _, report in measured.reviews
        if case.planted_error is not None
    ]
    faithful = [
        report.passed
        for case, _, report in measured.reviews
        if case.planted_error is None
    ]
    generations = [
        result for _, result, _ in measured.generations if not _model_failure(result)
    ]
    return (
        _count(
            "Trecho esperado entre os 8",
            hits,
            total,
            percent=True,
            note="Meta inicial: 80%.",
        ),
        _count(
            "Casos com erro plantado reprovados",
            planted.count(False),
            len(planted),
            note="T41 confere quais erros o revisor encontrou. Meta inicial: 4 de 5 erros confirmados.",
        ),
        _count(
            "Alarmes falsos entre os casos fiéis",
            faithful.count(False),
            len(faithful),
            note="Meta inicial: no máximo 1 em 5.",
        ),
        _count(
            "Casos aprovados para publicação",
            sum(
                result.decision == grounding.Decision.publish for result in generations
            ),
            len(generations),
        ),
    )


def _cell(value: object) -> str:
    if value is None:
        return ""
    return escape(_normalized(str(value)), quote=False).replace("|", "&#124;")


def _row(*cells: object) -> str:
    return "| " + " | ".join(map(_cell, cells)) + " |"


def _table(headers: tuple[str, ...], rows: Iterable[Sequence[object]]) -> str:
    return "\n".join(
        [_row(*headers), _row(*["---"] * len(headers)), *(_row(*row) for row in rows)]
    )


def _yes_no(value: bool) -> str:
    return "Sim" if value else "Não"


def _markdown(path: Path, cases: CaseFile, count: int, measured: Measurements) -> str:
    retrieval_summary, planted_summary, faithful_summary, generation_summary = _summary(
        measured
    )
    retrieval_table = _table(("Pergunta", "Posição"), measured.ranks)
    review_table = _table(
        (
            "ID",
            "Erro plantado",
            "focus_covered",
            "Aprovado",
            "Clareza",
            "Afirmações sem apoio",
        ),
        (
            (
                case.id,
                case.planted_error,
                _yes_no(report.focus_covered),
                _yes_no(report.passed),
                clarity,
                " / ".join(claim.claim for claim in report.unsupported),
            )
            for case, clarity, report in measured.reviews
        ),
    )
    generation_table = _table(
        ("Foco", "Formato", "Público", "Decisão", "Tentativas", "Mensagem de falha"),
        (
            (
                case.focus,
                case.format,
                case.audience_level,
                "fail (erro do modelo)" if _model_failure(result) else result.decision,
                result.attempts,
                result.error_message,
            )
            for case, result, _ in measured.generations
        ),
    )
    sections = [
        f"""# Avaliação da busca, do revisor e da geração

- Data (UTC): {datetime.now(UTC).date()}
- Arquivo de casos: {_cell(path)}
- Documento: {_cell(cases.document)}
- Chunks: {count}
- GEMINI_GENERATION_MODEL: {_cell(settings.GEMINI_GENERATION_MODEL) or "Sem configuração"}
- GEMINI_EMBEDDING_MODEL: {_cell(settings.GEMINI_EMBEDDING_MODEL)}
- PROMPT_VERSION: {_cell(generation_graph.PROMPT_VERSION)}

## Busca

{retrieval_table}

{retrieval_summary}

## Revisor

{review_table}

{planted_summary}

{faithful_summary}

## Geração

{generation_table}

{generation_summary}"""
    ]
    for case, result, chunks in measured.generations:
        if result.decision != grounding.Decision.fail:
            continue
        indices = ", ".join(str(chunk.chunk_index) for chunk in chunks)
        sections.extend(
            [
                f"**{_cell(case.focus)} ({case.format}, {case.audience_level})**",
                f"Chunks usados: {indices}",
            ]
        )
        if result.generated is not None:
            content = result.generated.model_dump(mode="json")["content"]
            sections.extend(
                [
                    "Último conteúdo gerado",
                    indent(json.dumps(content, ensure_ascii=False, indent=2), "    "),
                ]
            )

    sections.extend(
        [
            "## Pistas",
            '"Fora dos 8" indica que a busca pode ter deixado de trazer o trecho. '
            '"Entre os 8" indica que o revisor pode ter deixado de reconhecer o trecho. '
            "Nos dois casos, a afirmação também pode não ter apoio no documento. Uma pessoa lê o trecho e decide.",
            _table(
                ("Caso", "Afirmação sem apoio", "Trecho mais próximo"), measured.clues
            ),
        ]
    )
    if measured.errors:
        sections.extend(
            [
                "### Erros de execução",
                "Para erros do modelo, confira a chave, os modelos e a cota do Gemini antes de tentar de novo.",
                _table(("Caso", "Erro"), measured.errors),
            ]
        )
    return "\n\n".join(sections)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, exit_on_error=False)
    parser.add_argument(
        "--check", action="store_true", help="Só valida o arquivo de casos."
    )
    parser.add_argument("path", type=Path, help="Caminho do arquivo JSON de casos.")
    try:
        try:
            args = parser.parse_args(argv)
        except argparse.ArgumentError as exc:
            raise CaseError(
                "Informe um arquivo JSON de casos. Use --help para ver o comando."
            ) from exc
        cases = load_cases(args.path)
        if not args.check:
            count, measured = _run(cases)
            print(_markdown(args.path, cases, count, measured))
    except CaseError as exc:
        print(f"Erro na avaliação: {exc}", file=sys.stderr)
        return 1
    except OperationalError:
        print(
            "Não foi possível conectar ao banco. Suba o banco e aplique as migrations "
            "(veja examples/evals/README.md).",
            file=sys.stderr,
        )
        return 1
    except indexing.IndexingError as exc:
        print(
            f"Erro na avaliação: {exc} Confira o documento e as configurações do Gemini antes de tentar de novo.",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(
            f"Não foi possível terminar a avaliação ({type(exc).__name__}). "
            "Confira a configuração em examples/evals/README.md. Se o erro continuar, envie esta mensagem à equipe.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
