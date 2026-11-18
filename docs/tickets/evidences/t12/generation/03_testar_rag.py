"""T12 NovaMente: simulação lexical local de recuperação + 1 geração Gemini por comando.

Não usa embeddings, pgvector, OCI ou banco. Sem chamadas externas com --dry-run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

ROOT = Path(__file__).resolve().parent
RESULTADOS = ROOT / "t12_resultados"
COLUNAS = ["data_utc", "modelo", "cenario", "status", "duracao_s", "tokens_entrada",
           "tokens_saida", "tokens_pensamento", "tokens_total", "tokens_cache",
           "finish_reason", "erro_codigo", "erro_tipo", "validacao", "arquivo_saida"]

Text = str

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class TutorialSection(StrictModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)

class TutorialContent(StrictModel):
    summary: str = Field(min_length=1)
    sections: list[TutorialSection] = Field(min_length=1, max_length=8)
    takeaways: list[str] = Field(min_length=1, max_length=5)

class Flashcard(StrictModel):
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)
    hint: str | None = Field(default=None, min_length=1)

class FlashcardsContent(StrictModel):
    introduction: str = Field(min_length=1)
    cards: list[Flashcard] = Field(min_length=8, max_length=12)

class QuizQuestion(StrictModel):
    prompt: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=1)

    @field_validator("options")
    @classmethod
    def options_are_unique(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values):
            raise ValueError("Opções não podem se repetir")
        return values

class QuizContent(StrictModel):
    questions: list[QuizQuestion] = Field(min_length=5, max_length=5)

class GeneratedBase(StrictModel):
    title: str = Field(min_length=1, max_length=255)
    estimated_minutes: int = Field(ge=1, le=600)
    key_concepts: list[str] = Field(min_length=1, max_length=10)
    prerequisites: list[str] = Field(max_length=10)

class GeneratedTutorial(GeneratedBase):
    content: TutorialContent

class GeneratedFlashcards(GeneratedBase):
    content: FlashcardsContent

class GeneratedQuiz(GeneratedBase):
    content: QuizContent

SCHEMAS = {"tutorial": GeneratedTutorial, "flashcards": GeneratedFlashcards, "quiz": GeneratedQuiz}


def estrutural(obj):
    """Fallback explícito, apenas se schema completo for rejeitado (não automático)."""
    ignorar = {"minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum"}
    if isinstance(obj, list):
        return [estrutural(x) for x in obj]
    if isinstance(obj, dict):
        return {k: estrutural(v) for k, v in obj.items() if k not in ignorar}
    return obj


def palavras(s):
    s = unicodedata.normalize("NFKD", s.casefold())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    stop = {"para", "como", "com", "uma", "uns", "das", "dos", "que", "por", "sobre", "nos", "nas", "nao", "mais", "isso", "esse", "esta", "este", "seu", "sua", "sao", "entre", "quando", "pela", "pelo", "the", "and", "http", "api"}
    return {x for x in re.findall(r"[a-z0-9]{3,}", s) if x not in stop}


def chunk_text(texto: str, tamanho: int) -> list[dict]:
    """Segmentação determinística, sem perda de caracteres. Não é busca vetorial."""
    if not texto.strip():
        raise ValueError("Documento vazio")
    partes = []
    for i, inicio in enumerate(range(0, len(texto), tamanho), 1):
        trecho = texto[inicio:inicio+tamanho]
        partes.append({"chunk_id": f"C{i:03d}", "inicio": inicio, "fim": inicio + len(trecho), "texto": trecho})
    return partes


def selecionar(chunks: list[dict], foco: str, top_k: int) -> list[dict]:
    query = palavras(foco)
    classificados = []
    for c in chunks:
        score = len(query & palavras(c["texto"]))
        classificados.append({**c, "score_lexical": score})
    classificados.sort(key=lambda c: (-c["score_lexical"], c["inicio"]))
    return classificados[:top_k]


def prompt_para(cenario: str, foco: str, nivel: str, setor: str, recuperados: list[dict]) -> str:
    tarefa = {
        "tutorial": "Escreva resumo, de 2 a 4 seções e 3 a 5 itens 'Para levar'.",
        "flashcards": "Escreva exatamente 8 flashcards diferentes, com frente, verso e dica opcional.",
        "quiz": "Escreva exatamente 5 perguntas, cada uma com 4 opções diferentes, índice correto (0-3) e explicação.",
    }[cenario]
    contexto = "\n\n".join(f"[{c['chunk_id']}] {c['texto']}" for c in recuperados)
    return (
        f"Foco: {foco}\nNível: {nivel}\nSetor: {setor}\nFormato: {cenario}\n"
        "Use EXCLUSIVAMENTE os trechos numerados como fonte factual. Não invente fatos. "
        "Escreva em português brasileiro. Use exemplos do setor apenas se sustentados pelos trechos. "
        "Se faltar informação, reduza o detalhamento sem inventar. "
        "Preencha title, estimated_minutes, key_concepts, prerequisites e content. "
        f"{tarefa}\n\nTRECHOS RECUPERADOS (simulação local de RAG):\n{contexto}"
    )


def adicionar_csv(linha: dict) -> Path:
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    destino = RESULTADOS / "medicoes.csv"
    novo = not destino.exists() or destino.stat().st_size == 0
    if not novo:
        with destino.open("r", encoding="utf-8-sig", newline="") as f:
            cabecalho = next(csv.reader(f), [])
        if cabecalho != COLUNAS:
            raise ValueError("Cabeçalho incompatível: medições existentes não foram alteradas")
    with destino.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        if novo:
            w.writeheader()
        w.writerow(linha)
    return destino


def gravar_json(path: Path, value: dict):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def executar(args, client_factory=None):
    fonte_path = Path(args.fonte).resolve()
    fonte = fonte_path.read_text(encoding="utf-8")
    if len(fonte) > 150_000:
        raise SystemExit("Documento excede 150.000 caracteres; nenhuma chamada executada")
    chunks = chunk_text(fonte, args.chunk_chars)
    recuperados = selecionar(chunks, args.foco, args.top_k)
    prompt = prompt_para(args.cenario, args.foco, args.nivel, args.setor, recuperados)
    schema = SCHEMAS[args.cenario]
    esquema_json = schema.model_json_schema()
    if args.schema_mode == "compat":
        esquema_json = estrutural(esquema_json)

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    ident = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    tag = f"{ident}_{args.modelo}_{args.cenario}_rag"
    caminho_contexto = RESULTADOS / f"{tag}_contexto.json"
    contexto = {
        "experimento": "simulacao_rag_lexical_nao_vetorial", "fonte_nome": fonte_path.name,
        "fonte_sha256": hashlib.sha256(fonte.encode("utf-8")).hexdigest(),
        "foco": args.foco, "nivel": args.nivel, "setor": args.setor,
        "cenario": args.cenario, "modelo": args.modelo, "schema_mode": args.schema_mode,
        "chunk_chars": args.chunk_chars, "top_k": args.top_k,
        "chunks_documento": len(chunks), "chunks_selecionados": len(recuperados),
        "caracteres_contexto": sum(len(x["texto"]) for x in recuperados),
        "chunks": recuperados,
    }
    gravar_json(caminho_contexto, contexto)

    if args.dry_run:
        caminho_prompt = RESULTADOS / f"{tag}_prompt.txt"
        with caminho_prompt.open("x", encoding="utf-8") as f:
            f.write(prompt)
        print(json.dumps({"modo": "dry-run", "chamadas_api": 0, "chunks": len(chunks),
                          "selecionados": [x["chunk_id"] for x in recuperados],
                          "contexto": str(caminho_contexto), "prompt": str(caminho_prompt)},
                         ensure_ascii=False, indent=2))
        return {"modo": "dry-run"}

    key = os.getenv("GEMINI_API_KEY")
    if not key and client_factory is None:
        raise SystemExit("Defina GEMINI_API_KEY. Nenhuma chamada executada.")
    linha = dict.fromkeys(COLUNAS, "")
    linha.update(data_utc=datetime.now(timezone.utc).isoformat(), modelo=args.modelo,
                 cenario=f"rag_{args.cenario}", status="erro", validacao="nao_avaliado")
    inicio = time.monotonic()
    etapa = "chamada_api"
    cliente = None
    try:
        if client_factory is None:
            from google import genai
            from google.genai import types
            client_factory = lambda: genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120_000))
            config = types.GenerateContentConfig(temperature=0.2, max_output_tokens=args.max_output_tokens,
                response_mime_type="application/json", response_json_schema=esquema_json)
        else:
            config = {"temperature": 0.2, "max_output_tokens": args.max_output_tokens,
                      "response_mime_type": "application/json", "response_json_schema": esquema_json}
        cliente = client_factory()
        resposta = cliente.models.generate_content(model=args.modelo, contents=prompt, config=config)
        etapa = "processamento_resposta"
        u = getattr(resposta, "usage_metadata", None)
        linha.update(tokens_entrada=getattr(u, "prompt_token_count", None),
                     tokens_saida=getattr(u, "candidates_token_count", None),
                     tokens_pensamento=getattr(u, "thoughts_token_count", None),
                     tokens_total=getattr(u, "total_token_count", None),
                     tokens_cache=getattr(u, "cached_content_token_count", None))
        candidatos = getattr(resposta, "candidates", None) or []
        linha["finish_reason"] = str(candidatos[0].finish_reason) if candidatos else ""
        texto = resposta.text or ""
        if not texto.strip():
            linha["validacao"] = "resposta_vazia"
        else:
            try:
                schema.model_validate_json(texto)
                linha["validacao"] = "valido"
            except ValidationError as exc:
                linha["validacao"] = f"invalido_{exc.error_count()}_erros"
            except ValueError:
                linha["validacao"] = "json_invalido"
        etapa = "gravacao_resposta"
        destino = RESULTADOS / f"{tag}_resposta.json"
        with destino.open("x", encoding="utf-8") as f:
            f.write(texto)
        linha["arquivo_saida"] = str(destino)
        linha["status"] = "ok" if linha["validacao"] == "valido" else "resposta_invalida"
    except Exception as exc:
        linha["status"] = "erro"
        linha["erro_tipo"] = type(exc).__name__
        linha["erro_codigo"] = getattr(exc, "code", "") or ""
        print(f"Falha em {etapa}: {linha['erro_tipo']} (HTTP {linha['erro_codigo'] or 'n/d'})", file=sys.stderr)
    finally:
        linha["duracao_s"] = round(time.monotonic() - inicio, 3)
        if cliente is not None:
            try:
                cliente.close()
            except Exception:
                pass
        try:
            destino_csv = adicionar_csv(linha)
            print(json.dumps({"medicao": linha, "contexto": str(caminho_contexto), "csv": str(destino_csv)},
                             ensure_ascii=False, indent=2))
        except (OSError, ValueError) as exc:
            print(f"Falha ao registrar CSV: {type(exc).__name__}. Os dados existentes foram preservados.", file=sys.stderr)
            raise
    return linha


def main():
    p = argparse.ArgumentParser(description="T12: simular RAG local e gerar 1 conteúdo estruturado")
    p.add_argument("--cenario", required=True, choices=tuple(SCHEMAS))
    p.add_argument("--modelo", default="gemini-3.5-flash-lite")
    p.add_argument("--fonte", default=str(ROOT / "fonte_rag_exemplo.md"))
    p.add_argument("--foco", default="HTTP requisições respostas códigos de status autenticação autorização JSON")
    p.add_argument("--nivel", default="tecnico_basico", choices=("nao_tecnico", "tecnico_basico", "tecnico_avancado"))
    p.add_argument("--setor", default="geral")
    p.add_argument("--chunk-chars", type=int, default=850)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--schema-mode", default="full", choices=("full", "compat"))
    p.add_argument("--max-output-tokens", type=int, default=4096)
    p.add_argument("--dry-run", action="store_true", help="Gera prompt e contexto sem chamada API nem linha CSV")
    args = p.parse_args()
    if not 300 <= args.chunk_chars <= 1500:
        p.error("--chunk-chars deve estar entre 300 e 1500")
    if not 1 <= args.top_k <= 15:
        p.error("--top-k deve estar entre 1 e 15")
    if not 512 <= args.max_output_tokens <= 16384:
        p.error("--max-output-tokens deve estar entre 512 e 16384")
    executar(args)

if __name__ == "__main__":
    main()
