"""T12: um teste controlado por execucao, sem retry automatico.

Exemplos:
  python 02_testar_geracao.py --modelo gemini-3.5-flash-lite --cenario tutorial
  python 02_testar_geracao.py --modelo gemini-3.8-flash --cenario quiz

Resultados: pasta t12_resultados, ao lado deste script. O CSV e acumulativo.
"""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

MODELOS = ("gemini-3.5-flash-lite", "gemini-3.8-flash")
# Caminho fixo, independente de onde o comando Python for executado.
PASTA_RESULTADOS = Path(__file__).resolve().parent / "t12_resultados"
COLUNAS = ["data_utc", "modelo", "cenario", "status", "duracao_s", "tokens_entrada",
           "tokens_saida", "tokens_pensamento", "tokens_total", "tokens_cache",
           "finish_reason", "erro_codigo", "erro_tipo", "validacao", "arquivo_saida"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Secao(StrictModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)


class Tutorial(StrictModel):
    summary: str = Field(min_length=1)
    sections: list[Secao] = Field(min_length=1, max_length=8)
    takeaways: list[str] = Field(min_length=1, max_length=5)


class Flashcard(StrictModel):
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)
    hint: str | None = None


class Flashcards(StrictModel):
    introduction: str = Field(min_length=1)
    cards: list[Flashcard] = Field(min_length=8, max_length=12)


class Questao(StrictModel):
    prompt: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def opcoes_sem_repeticao(self):
        if len({v.strip().casefold() for v in self.options}) != len(self.options):
            raise ValueError("Opcoes duplicadas")
        return self


class Quiz(StrictModel):
    questions: list[Questao] = Field(min_length=5, max_length=5)


FORMATOS = {"tutorial": Tutorial, "flashcards": Flashcards, "quiz": Quiz}


def apenas_schema_estrutural(schema: dict) -> dict:
    """Remove restricoes locais; a validacao Pydantic completa continua ativa."""
    ignorar = {"minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum"}

    def limpar(value):
        if isinstance(value, list):
            return [limpar(x) for x in value]
        if isinstance(value, dict):
            return {k: limpar(v) for k, v in value.items() if k not in ignorar}
        return value

    return limpar(schema)


def obter_prompt(cenario: str, texto_fonte: str) -> str:
    instrucao = {
        "simples": "Explique o funcionamento de HTTP para iniciantes em 2 paragrafos curtos. Cite os codigos mencionados na fonte.",
        "tutorial": "Crie um tutorial com resumo, 2 a 4 secoes e 3 pontos principais.",
        "flashcards": "Crie exatamente 8 flashcards diferentes, com pergunta e resposta, podendo incluir dica.",
        "quiz": "Crie exatamente 5 questoes com 4 alternativas cada, indice correto de 0 a 3 e justificativa.",
    }[cenario]
    return (
        "Use EXCLUSIVAMENTE as informacoes da FONTE. Nao invente fatos. "
        "Publico: tecnico basico. Idioma: portugues brasileiro. "
        "Se a fonte nao sustentar algum detalhe, nao o acrescente.\n\n"
        f"TAREFA: {instrucao}\n\nFONTE:\n{texto_fonte}"
    )


def garantir_pasta_resultados() -> Path:
    """Cria t12_resultados se ausente; preserva seu conteudo se existir."""
    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    return PASTA_RESULTADOS


def registrar_medicao(pasta: Path, linha: dict) -> Path:
    """Adiciona exatamente uma linha ao CSV; escreve cabecalho so no inicio."""
    arquivo = pasta / "medicoes.csv"
    existe_com_conteudo = arquivo.is_file() and arquivo.stat().st_size > 0

    # Evita adicionar linhas a um CSV com formato incompativel.
    if existe_com_conteudo:
        with arquivo.open("r", encoding="utf-8", newline="") as entrada:
            cabecalho = next(csv.reader(entrada), [])
        if cabecalho != COLUNAS:
            raise ValueError(
                f"Cabecalho incompativel em {arquivo}. "
                "O arquivo existente foi preservado, sem novas linhas."
            )

    with arquivo.open("a", encoding="utf-8", newline="") as saida:
        writer = csv.DictWriter(saida, fieldnames=COLUNAS)
        if not existe_com_conteudo:
            writer.writeheader()
        writer.writerow(linha)
    return arquivo


def executar(args):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY nao definida; nenhuma chamada executada.")

    fonte = Path(args.fonte).read_text(encoding="utf-8")
    if len(fonte) > 150_000:
        raise SystemExit("Fonte excede 150000 caracteres.")

    modelo = args.modelo
    cenario = args.cenario
    prompt = obter_prompt(cenario, fonte)
    schema = FORMATOS.get(cenario)
    config_kwargs = {"temperature": 0.2, "max_output_tokens": args.max_output_tokens}
    if schema:
        config_kwargs.update(
            response_mime_type="application/json",
            response_json_schema=apenas_schema_estrutural(schema.model_json_schema()),
        )
    config = types.GenerateContentConfig(**config_kwargs)

    # Cria a pasta somente se for necessario. Nao apaga nem recria arquivos.
    pasta = garantir_pasta_resultados()
    agora = datetime.now(timezone.utc)
    identificador = agora.strftime("%Y%m%dT%H%M%S%fZ")
    linha = dict.fromkeys(COLUNAS, "")
    linha.update(data_utc=agora.isoformat(), modelo=modelo, cenario=cenario, status="erro")

    cliente = None
    etapa = "criacao_cliente"
    inicio = time.monotonic()
    try:
        cliente = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120_000))

        etapa = "chamada_api"
        resposta = cliente.models.generate_content(model=modelo, contents=prompt, config=config)

        etapa = "processamento_resposta"
        uso = resposta.usage_metadata
        linha.update(
            tokens_entrada=getattr(uso, "prompt_token_count", None),
            tokens_saida=getattr(uso, "candidates_token_count", None),
            tokens_pensamento=getattr(uso, "thoughts_token_count", None),
            tokens_total=getattr(uso, "total_token_count", None),
            tokens_cache=getattr(uso, "cached_content_token_count", None),
        )
        candidatos = resposta.candidates or []
        linha["finish_reason"] = str(candidatos[0].finish_reason) if candidatos else ""
        texto = resposta.text or ""
        if not texto.strip():
            linha["validacao"] = "resposta_vazia"
        elif schema:
            try:
                schema.model_validate_json(texto)
                linha["validacao"] = "valido"
            except ValidationError as exc:
                linha["validacao"] = f"invalido_{exc.error_count()}_erros"
            except ValueError:
                linha["validacao"] = "json_invalido"
        else:
            linha["validacao"] = "texto_nao_estruturado"

        etapa = "gravacao_resposta"
        caminho_saida = pasta / f"{identificador}_{modelo}_{cenario}.txt"
        # 'x' impede sobrescrever uma resposta anterior por colisao de nomes.
        with caminho_saida.open("x", encoding="utf-8") as arquivo_txt:
            arquivo_txt.write(texto)
        linha["arquivo_saida"] = str(caminho_saida)
        linha["status"] = "ok"

    except Exception as exc:
        # Nao imprimir exc: erros do SDK podem conter prompt ou informacoes sensiveis.
        linha["status"] = "erro"
        linha["erro_tipo"] = type(exc).__name__
        linha["erro_codigo"] = getattr(exc, "code", "") or ""
        if etapa in ("criacao_cliente", "chamada_api"):
            linha["validacao"] = "nao_avaliado"
        print(
            f"Erro na etapa '{etapa}': {type(exc).__name__}"
            + (f" (HTTP {linha['erro_codigo']})" if linha["erro_codigo"] else ""),
            file=sys.stderr,
        )
    finally:
        linha["duracao_s"] = round(time.monotonic() - inicio, 3)
        if cliente is not None:
            try:
                cliente.close()
            except Exception:
                # Falha no fechamento nao impede registrar a medicao.
                print("Aviso: nao foi possivel fechar o cliente Gemini.", file=sys.stderr)

        # Registra inclusive as tentativas que resultaram em erro na API.
        try:
            caminho_csv = registrar_medicao(pasta, linha)
        except (OSError, ValueError) as exc:
            print(
                f"Falha ao gravar medicoes.csv: {type(exc).__name__}. "
                "Nenhuma confirmacao de gravacao sera emitida.",
                file=sys.stderr,
            )
            raise

        print(json.dumps(linha, ensure_ascii=False, indent=2))
        print(f"Medicoes registradas em {caminho_csv}")


def main():
    parser = argparse.ArgumentParser(description="T12 - uma geracao por comando")
    parser.add_argument("--modelo", choices=MODELOS, required=True)
    parser.add_argument("--cenario", choices=("simples", *FORMATOS), required=True)
    parser.add_argument("--fonte", default="fonte_exemplo.md")
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    args = parser.parse_args()
    if not 128 <= args.max_output_tokens <= 8192:
        parser.error("--max-output-tokens deve estar entre 128 e 8192")
    executar(args)


if __name__ == "__main__":
    main()
