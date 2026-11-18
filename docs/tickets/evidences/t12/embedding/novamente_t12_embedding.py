"""NovaMente T12: teste isolado do Gemini Embedding 2 (etapas A e B).

Nao acessa o repositorio, nao grava arquivos e nao imprime a chave nem vetores.
Uso: python novamente_t12_embedding.py --etapa a
     python novamente_t12_embedding.py --etapa b
"""

import argparse
import os
import sys
import time
from getpass import getpass

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("Pacote ausente. Execute: python -m pip install -U google-genai")

MODELO = "gemini-embedding-2"
DIMENSOES = 768


def solicitar_chave() -> str:
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave:
        chave = getpass("Cole sua GEMINI_API_KEY (entrada oculta): ").strip()
    if not chave:
        raise ValueError("Chave de API nao informada.")
    return chave


def medir(cliente, conteudos):
    inicio = time.perf_counter()
    resposta = cliente.models.embed_content(
        model=MODELO,
        contents=conteudos,
        config=types.EmbedContentConfig(output_dimensionality=DIMENSOES),
    )
    duracao = time.perf_counter() - inicio
    vetores = [item.values for item in (resposta.embeddings or [])]
    return vetores, duracao


def etapa_a(cliente) -> None:
    print("\nETAPA A - Um texto, um embedding\n")
    texto = (
        "title: APIs REST | text: Uma API REST permite que sistemas "
        "troquem informacoes por meio de requisicoes HTTP."
    )
    vetores, duracao = medir(cliente, texto)
    ok = len(vetores) == 1 and len(vetores[0]) == DIMENSOES
    print(f"Modelo solicitado: {MODELO}")
    print(f"Requisicoes ao endpoint embed_content: 1")
    print(f"Embeddings recebidos: {len(vetores)}")
    print(f"Dimensoes: {[len(v) for v in vetores]}")
    print(f"Latencia: {duracao:.2f} s")
    print(f"Resultado: {'APROVADO' if ok else 'REPROVADO'}")
    if not ok:
        sys.exit(2)


def etapa_b(cliente) -> None:
    print("\nETAPA B - Tres textos independentes, uma requisicao\n")
    textos = [
        "title: REST | text: Uma API REST utiliza recursos identificados por URLs e metodos HTTP.",
        "title: Banco de dados | text: PostgreSQL armazena dados relacionais em tabelas.",
        "title: Nuvem | text: Armazenamento de objetos guarda arquivos e metadados em buckets.",
    ]
    conteudos = [
        types.Content(parts=[types.Part.from_text(text=texto)])
        for texto in textos
    ]
    vetores, duracao = medir(cliente, conteudos)
    dimensoes = [len(v) for v in vetores]
    distintos = (
        len(vetores) == len(textos)
        and all(vetores[i] != vetores[j]
                for i in range(len(vetores)) for j in range(i + 1, len(vetores)))
    )
    ok = len(vetores) == 3 and all(d == DIMENSOES for d in dimensoes) and distintos
    print(f"Modelo solicitado: {MODELO}")
    print(f"Requisicoes ao endpoint embed_content: 1")
    print(f"Textos enviados: {len(textos)}")
    print(f"Embeddings recebidos: {len(vetores)}")
    print(f"Dimensoes: {dimensoes}")
    print(f"Vetores diferentes entre si: {'sim' if distintos else 'nao'}")
    print(f"Latencia: {duracao:.2f} s")
    print(f"Resultado: {'APROVADO' if ok else 'REPROVADO'}")
    if not ok:
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Teste controlado de embeddings do NovaMente")
    parser.add_argument("--etapa", required=True, choices=["a", "b"])
    args = parser.parse_args()

    try:
        chave = solicitar_chave()
        cliente = genai.Client(api_key=chave)
        try:
            if args.etapa == "a":
                etapa_a(cliente)
            else:
                etapa_b(cliente)
        finally:
            cliente.close()
    except Exception as erro:
        print(f"Falha: {type(erro).__name__}", file=sys.stderr)
        print("Confira a chave, o identificador do modelo, as quotas e a conexao."
              " Nao compartilhe sua chave nem rastreamentos com credenciais.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
