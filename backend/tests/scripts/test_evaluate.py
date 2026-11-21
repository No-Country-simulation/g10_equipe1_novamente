import json
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlmodel import Session, col, delete, select

from app.core import llm
from app.models import Course, CourseContent, DocumentChunk, SourceDocument, User
from app.services import grounding
from app.services.generation_graph import GenerationResult
from app.services.retrieval import RetrievedChunk
from scripts import evaluate
from tests.services.test_documents import pdf_bytes

FACT = "Um Pod pode conter vários contêineres."
ERROR = "Um Pod exige dez contêineres."
UNSUPPORTED = "Pods usam somente IPv6."


@pytest.fixture
def cases(tmp_path):
    document = tmp_path / "pods.md"
    document.write_text(FACT, encoding="utf-8")
    request = {
        "focus": "Pods",
        "format": "tutorial",
        "audience_level": "technical_basic",
    }
    return {
        "document": str(document),
        "niche": "geral",
        "retrieval": [{"question": "Quantos contêineres cabem?", "expected": FACT}],
        "review": [
            {
                **request,
                "id": id_,
                "planted_error": planted,
                "content": {
                    "summary": statement,
                    "sections": [{"title": "Contêineres", "body": statement}],
                    "takeaways": [statement],
                },
            }
            for id_, statement, planted in (
                ("fiel", FACT, None),
                ("plantado", ERROR, ERROR),
            )
        ],
        "generation": [request.copy()],
    }


@pytest.fixture
def write_cases(tmp_path):
    def write(cases):
        path = tmp_path / "cases.json"
        path.write_text(json.dumps(cases), encoding="utf-8")
        return path

    return write


@pytest.fixture(autouse=True)
def block_gemini(monkeypatch):
    def unexpected():
        pytest.fail("O teste tentou chamar o Gemini.")

    monkeypatch.setattr(llm, "_get_client", unexpected)


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(evaluate.settings, "GEMINI_API_KEY", "teste")
    monkeypatch.setattr(evaluate.settings, "GEMINI_GENERATION_MODEL", "modelo-de-teste")


def test_load_cases(cases, write_cases, tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate, "REPO_ROOT", tmp_path)
    cases["document"] = "  pods.md  "
    cases["niche"] = " geral "
    cases["retrieval"][0]["expected"] = " Um Pod\n pode conter vários contêineres. "
    loaded = evaluate.load_cases(write_cases(cases))
    assert loaded.document == "pods.md"
    assert loaded.niche == "geral"
    assert len(loaded.retrieval) == len(loaded.generation) == 1
    assert [case.id for case in loaded.review] == ["fiel", "plantado"]
    assert loaded.review[0].generated().model_dump()["content"]["summary"] == FACT


@pytest.mark.parametrize(
    ("document", "fix"),
    [
        ("Pods existem.", "Copie a frase exata do arquivo"),
        (
            "x" * 990 + "\n\nAntes\n\nDepois",
            "Escolha uma frase mais curta de um único parágrafo",
        ),
    ],
)
def test_expected_must_fit_in_one_chunk(cases, write_cases, document, fix):
    Path(cases["document"]).write_text(document, encoding="utf-8")
    cases["retrieval"][0]["expected"] = "Antes Depois"
    with pytest.raises(evaluate.CaseError, match=f"Quantos contêineres cabem.*{fix}"):
        evaluate.load_cases(write_cases(cases))


def test_pdf_expected_must_fit_on_one_page(cases, write_cases, tmp_path):
    path = tmp_path / "pods.pdf"
    path.write_bytes(pdf_bytes("Primeira pagina", "Segunda pagina"))
    cases["document"] = str(path)
    cases["retrieval"][0]["expected"] = "Segunda pagina"
    evaluate.load_cases(write_cases(cases))
    cases["retrieval"][0]["expected"] = "pagina Segunda"
    with pytest.raises(evaluate.CaseError, match="cruza o limite entre dois trechos"):
        evaluate.load_cases(write_cases(cases))


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"content": {"summary": "Incompleto"}}, "plantado.*conteúdo inválido"),
        ({"planted_error": "Fato ausente"}, "plantado.*planted_error"),
        ({"id": " fiel "}, "fiel.*id repetido"),
        ({"planted_error": " "}, "review 2.*plantado.*planted_error.*preencha"),
        ({"focus": "x" * 256}, "review 2.*plantado.*focus.*até 255 caracteres"),
    ],
)
def test_invalid_review(cases, write_cases, update, message):
    cases["review"][1].update(update)
    with pytest.raises(evaluate.CaseError, match=message):
        evaluate.load_cases(write_cases(cases))


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"extra": True}, "extra"),
        ({"niche": "  "}, "niche"),
        ({"retrieval": [], "review": [], "generation": []}, "pelo menos um caso"),
        ({"document": "inexistente.md"}, "inexistente.md"),
    ],
)
def test_invalid_file(cases, write_cases, update, message):
    cases.update(update)
    with pytest.raises(evaluate.CaseError, match=message):
        evaluate.load_cases(write_cases(cases))


def chunk(text, index=0):
    return RetrievedChunk(uuid.uuid4(), uuid.uuid4(), index, text, None, 0.82)


def test_retrieval_rank():
    chunks = [
        chunk("Outro trecho."),
        chunk(" Um Pod\n pode conter "),
        chunk("Um Pod pode conter."),
    ]
    assert evaluate.retrieval_rank("Um Pod  pode conter", chunks) == 2
    assert evaluate.retrieval_rank("um Pod pode conter", chunks) is None
    assert evaluate.retrieval_rank(FACT, []) is None


def test_repository_cases():
    folder = Path(__file__).parents[3] / "examples" / "evals"
    for path in sorted(folder.glob("*.json")):
        try:
            evaluate.load_cases(path)
        except evaluate.CaseError as exc:
            pytest.fail(f"{path.name}: {exc}")


def test_main_check_and_invalid_file(cases, write_cases, monkeypatch, capsys):
    monkeypatch.setattr(evaluate.settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(
        evaluate, "Session", Mock(side_effect=AssertionError("Abriu uma sessão"))
    )
    assert evaluate.main(["--check", str(write_cases(cases))]) == 0
    cases["retrieval"][0]["expected"] = "Ausente"
    assert evaluate.main([str(write_cases(cases))]) == 1
    output = capsys.readouterr()
    assert "Quantos contêineres cabem" in output.err
    assert not output.out
    evaluate.Session.assert_not_called()


def test_main_reports_json_error_location(tmp_path, capsys):
    path = tmp_path / "cases.json"
    path.write_text('{\n  "document": "pods.md",\n}', encoding="utf-8")

    assert evaluate.main(["--check", str(path)]) == 1
    assert (
        "JSON inválido na linha 2, coluna 24. Confira as aspas, vírgulas e chaves"
        in capsys.readouterr().err
    )


def test_main_reports_case_names_and_allowed_values(cases, write_cases, capsys):
    cases["review"][1]["audience_level"] = "outro"
    del cases["retrieval"][0]["expected"]
    cases["generation"][0]["format"] = "outro"

    assert evaluate.main(["--check", str(write_cases(cases))]) == 1
    error = capsys.readouterr().err
    assert "retrieval 1 ('Quantos contêineres cabem?') / expected: preencha" in error
    assert (
        "review 2 ('plantado') / audience_level: "
        "use 'non_technical', 'technical_basic' ou 'technical_advanced'"
    ) in error
    assert (
        "generation 1 ('Pods') / format: use 'tutorial', 'flashcards' ou 'quiz'"
    ) in error


def owner_ids():
    with Session(evaluate.engine) as session:
        return set(
            session.exec(
                select(User.id).where(col(User.email).startswith("avaliacao-"))
            )
        )


@pytest.mark.parametrize(
    ("key", "model", "embedding_model", "niche", "message"),
    [
        (None, "teste", "teste", "geral", "GEMINI_API_KEY"),
        ("teste", None, "teste", "geral", "GEMINI_GENERATION_MODEL"),
        ("teste", "teste", "", "geral", "GEMINI_EMBEDDING_MODEL"),
        (
            "teste",
            "teste",
            "teste",
            "inexistente",
            "Nicho 'inexistente' não encontrado",
        ),
    ],
)
def test_main_rejects_missing_configuration_or_niche(
    cases, write_cases, monkeypatch, capsys, key, model, embedding_model, niche, message
):
    monkeypatch.setattr(evaluate.settings, "GEMINI_API_KEY", key)
    monkeypatch.setattr(evaluate.settings, "GEMINI_GENERATION_MODEL", model)
    monkeypatch.setattr(evaluate.settings, "GEMINI_EMBEDDING_MODEL", embedding_model)
    index = Mock()
    monkeypatch.setattr(evaluate.indexing, "index_document", index)
    cases["niche"] = niche
    before = owner_ids()
    assert evaluate.main([str(write_cases(cases))]) == 1
    assert message in capsys.readouterr().err
    assert owner_ids() == before
    index.assert_not_called()


@pytest.mark.usefixtures("configured")
def test_main_explains_how_to_recover_when_database_is_unavailable(
    cases, write_cases, monkeypatch, capsys
):
    monkeypatch.setattr(
        evaluate, "Session", Mock(side_effect=OperationalError(None, None, OSError()))
    )

    assert evaluate.main([str(write_cases(cases))]) == 1
    output = capsys.readouterr()
    assert not output.out
    assert output.err == (
        "Não foi possível conectar ao banco. Suba o banco e aplique as migrations "
        "(veja examples/evals/README.md).\n"
    )


@pytest.mark.usefixtures("configured")
def test_main_measures_all_cases(cases, write_cases, monkeypatch, capsys):
    indexed = Mock(return_value=2)
    monkeypatch.setattr(evaluate.indexing, "index_document", indexed)
    original = chunk(FACT)
    nearest = chunk("Um Pod tem seu próprio IP.", index=3)

    def retrieve(*, session, course, query):
        assert session.get(User, course.owner_id).is_active is False
        return [nearest] if query == UNSUPPORTED else [original]

    def review(*, generated, audience_level, focus, chunks):
        assert (audience_level, focus, chunks) == (
            "technical_basic",
            "Pods",
            [original],
        )
        claim = generated.model_dump()["content"]["summary"]
        supported = claim == FACT
        return grounding.ReviewResult(
            claims=[
                grounding.ClaimReview(
                    claim=claim,
                    supported=supported,
                    chunk_id=original.chunk_id if supported else None,
                )
            ],
            clarity="high",
            focus_covered=True,
            review_notes="",
        )

    result = grounding.ReviewResult(
        claims=[grounding.ClaimReview(claim=UNSUPPORTED, supported=False)],
        clarity="high",
        focus_covered=True,
        review_notes="",
    )
    report = grounding.evaluate(result, {original.chunk_id})

    def generate(request):
        assert request.chunks == [original]
        assert request.niche_name == "Geral"
        assert request.niche_prompt_hint
        generated = evaluate.load_cases(path).review[0].generated()
        return GenerationResult(
            grounding.Decision.fail,
            2,
            generated,
            result,
            report,
            grounding.failure_message(report),
        )

    monkeypatch.setattr(
        evaluate.course_generation, "retrieve_chunks", Mock(side_effect=retrieve)
    )
    monkeypatch.setattr(evaluate.reviewer, "review_content", review)
    monkeypatch.setattr(evaluate.generation_graph, "generate_content", generate)
    path = write_cases(cases)

    assert evaluate.main([str(path)]) == 0
    output = capsys.readouterr().out
    assert [line for line in output.splitlines() if line.startswith("## ")] == [
        "## Busca",
        "## Revisor",
        "## Geração",
        "## Pistas",
    ]
    assert "Trecho esperado entre os 8: 1 de 1 (100%). Meta inicial: 80%." in output
    assert "Casos com erro plantado reprovados: 1 de 1." in output
    assert "Alarmes falsos entre os casos fiéis: 0 de 1." in output
    assert "Casos aprovados para publicação: 0 de 1." in output
    assert "Chunks usados: 0" in output
    assert f'"summary": "{FACT}"' in output
    assert f"{UNSUPPORTED} | Fora dos 8. Chunk 3, similaridade 0.820." in output
    indexed.assert_called_once()
    queries = [
        call.kwargs["query"]
        for call in evaluate.course_generation.retrieve_chunks.call_args_list
    ]
    assert queries == [
        "Quantos contêineres cabem?",
        "Pods",
        "Pods",
        "Pods",
        UNSUPPORTED,
    ]


@pytest.mark.parametrize("failure", [None, "index", "cleanup"])
@pytest.mark.usefixtures("configured")
def test_main_cascades_cleanup(cases, write_cases, monkeypatch, capsys, failure):
    cases["review"] = []
    cases["generation"] = []
    ids = {}
    index_document = evaluate.indexing.index_document
    monkeypatch.setattr(llm, "embed_texts", Mock(return_value=[[1.0] + [0.0] * 767]))

    def index(*, session, storage, document_id):
        assert (
            index_document(session=session, storage=storage, document_id=document_id)
            == 1
        )
        document = session.get_one(SourceDocument, document_id)
        course = session.get_one(Course, document.course_id)
        chunk_id = session.exec(
            select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        ).one()
        ids.update(
            {
                User: course.owner_id,
                Course: course.id,
                SourceDocument: document_id,
                DocumentChunk: chunk_id,
            }
        )
        assert not session.exec(
            select(CourseContent).where(CourseContent.course_id == course.id)
        ).all()
        if failure == "index":
            raise evaluate.indexing.IndexingError("Falha de indexação de teste.")
        return 1

    monkeypatch.setattr(evaluate.indexing, "index_document", index)
    if failure == "cleanup":
        work = Session(evaluate.engine, expire_on_commit=False)
        cleanup = Session(evaluate.engine)
        fail_delete = Mock(side_effect=SQLAlchemyError())
        monkeypatch.setattr(cleanup, "exec", fail_delete)
        monkeypatch.setattr(evaluate, "Session", Mock(side_effect=[work, cleanup]))
    try:
        assert evaluate.main([str(write_cases(cases))]) == int(failure is not None)
        captured = capsys.readouterr()
        assert len(ids) == 4
        if failure == "cleanup":
            fail_delete.assert_called_once()
            assert (
                f"Não foi possível apagar o usuário da avaliação {ids[User]}"
                in captured.err
            )
            assert not captured.out
            return
        if failure == "index":
            assert "Falha de indexação de teste" in captured.err
        else:
            assert "1 de 1 (100%)" in captured.out
        with Session(evaluate.engine) as session:
            for model, row_id in ids.items():
                assert session.get(model, row_id) is None
    finally:
        if failure == "cleanup" and User in ids:
            with Session(evaluate.engine) as session, session.begin():
                session.exec(delete(User).where(col(User.id) == ids[User]))


@pytest.mark.usefixtures("configured")
def test_model_and_clue_errors(cases, write_cases, monkeypatch, capsys):
    cases["review"].pop()
    monkeypatch.setattr(evaluate.indexing, "index_document", Mock(return_value=1))
    source = chunk(FACT)

    def retrieve(*, session, course, query):  # noqa: ARG001
        if query != "Pods":
            raise llm.LLMError("Modelo indisponível")
        return [source]

    review = grounding.ReviewResult(
        claims=[grounding.ClaimReview(claim=UNSUPPORTED, supported=False)],
        clarity="medium",
        focus_covered=True,
        review_notes="",
    )
    report = grounding.evaluate(review, {source.chunk_id})
    result = GenerationResult(
        grounding.Decision.fail,
        2,
        None,
        review,
        report,
        "Serviço de texto indisponível.",
    )

    monkeypatch.setattr(evaluate.course_generation, "retrieve_chunks", retrieve)
    monkeypatch.setattr(evaluate.reviewer, "review_content", Mock(return_value=review))
    monkeypatch.setattr(
        evaluate.generation_graph, "generate_content", Mock(return_value=result)
    )

    assert evaluate.main([str(write_cases(cases))]) == 0
    output = capsys.readouterr().out
    assert "Trecho esperado entre os 8: Sem casos medidos" in output
    assert "Casos com erro plantado reprovados: Sem casos medidos" in output
    assert "Casos aprovados para publicação: Sem casos medidos" in output
    assert "Alarmes falsos entre os casos fiéis: 1 de 1." in output
    assert "| fail (erro do modelo) | 2 |" in output
    assert "### Erros de execução" in output
    assert "Revisor: fiel | Pods usam somente IPv6. | Pista indisponível." in output
