r"""NovaMente / T12: testes isolados do Gemini Embedding 2 (etapas A, B, C e D).

Uso no PowerShell (Windows):
    .\.venv\Scripts\python.exe .\novamente_t12_embedding_v3.py --etapa d --previsualizar
    .\.venv\Scripts\python.exe .\novamente_t12_embedding_v3.py --etapa d

O modo --previsualizar nao chama API e nao pede chave.
Os testes usam somente textos ficticios; nenhuma chave ou vetor e impresso.
A etapa C realiza UMA chamada ao metodo embed_content com 10 objetos Content.
A etapa D realiza DUAS chamadas (10 documentos + 10 consultas),
com 20 embeddings esperados de 768 dimensoes; sem gravar dados.

"""

import argparse
import math
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
    vetores = [item.values or [] for item in (resposta.embeddings or [])]
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
    print("Chamadas ao metodo embed_content: 1")
    print(f"Embeddings recebidos: {len(vetores)}")
    print(f"Dimensoes: {[len(v) for v in vetores]}")
    print(f"Latencia: {duracao:.2f} s")
    print(f"Resultado: {'APROVADO' if ok else 'REPROVADO'}")
    if not ok:
        sys.exit(2)


def etapa_b(cliente) -> None:
    print("\nETAPA B - Tres textos independentes, uma chamada ao SDK\n")
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
    print("Chamadas ao metodo embed_content: 1")
    print(f"Textos enviados: {len(textos)}")
    print(f"Embeddings recebidos: {len(vetores)}")
    print(f"Dimensoes: {dimensoes}")
    print(f"Vetores diferentes entre si: {'sim' if distintos else 'nao'}")
    print(f"Latencia: {duracao:.2f} s")
    print(f"Resultado: {'APROVADO' if ok else 'REPROVADO'}")
    if not ok:
        sys.exit(2)


# Conteudos sinteticos. O teste C mede dimensoes, quantidade e latencia,
# NAO a qualidade da busca RAG. Cada tema recebe ~1.000 caracteres.
TEMAS = [
    ("APIs REST e recursos HTTP", "Em APIs REST, cada recurso recebe um identificador de URL. Os metodos GET, POST, PUT e DELETE indicam operacoes diferentes. Respostas usam codigos HTTP para indicar sucesso, erros de validacao ou falhas do servidor. Uma boa especificacao descreve parametros, exemplos e formatos JSON de maneira consistente."),
    ("Autenticacao e JWT", "A autenticacao valida credenciais antes de emitir uma autorizacao de acesso. Um JWT possui declaracoes e assinatura que devem ser verificadas no backend. Tokens expirados nao devem autorizar chamadas. O armazenamento de segredos, a rotacao de chaves e a validacao do emissor sao medidas relevantes para proteger endpoints."),
    ("PostgreSQL e transacoes", "O PostgreSQL organiza dados relacionais em tabelas, restricoes e indices. Transacoes agrupam alteracoes que devem ser confirmadas ou revertidas juntas. Chaves estrangeiras ajudam a preservar integridade referencial. Consultas com filtros e joins devem ser avaliadas quanto a planos de execucao e indices utilizados."),
    ("Busca vetorial e pgvector", "Embeddings transformam trechos de documentos em vetores numericos. Uma busca por similaridade compara o vetor de consulta aos vetores persistidos, recuperando trechos proximos semanticamente. A extensao pgvector permite armazenar esses vetores no PostgreSQL. O backend precisa manter o mesmo modelo e a mesma dimensionalidade."),
    ("Armazenamento de objetos na OCI", "O Object Storage da OCI armazena documentos como objetos identificados por chave e associados a um bucket. Um servico pode enviar, listar, recuperar e excluir objetos com credenciais apropriadas. O controle de acesso deve privilegiar o menor privilegio. Metadados no banco podem referenciar os objetos sem copiar seus bytes."),
    ("FastAPI e validacao de dados", "O FastAPI permite definir endpoints HTTP e modelos de entrada e saida com validacao. Schemas Pydantic documentam formatos aceitos e ajudam a identificar dados invalidos antes de executar regras de negocio. A separacao entre rotas, servicos e acesso a dados facilita testes, observabilidade e evolucao dos contratos."),
    ("LangGraph e agentes", "Um grafo de agentes representa etapas de processamento e transicoes de estado. Agentes podem planejar, escrever e revisar um texto, enquanto regras deterministicas decidem quando aprovar ou reprovar. Cada etapa deve receber dados delimitados e produzir estruturas validadas. A aplicacao precisa tratar falhas, tentativas e limites de custo."),
    ("RAG e fidelidade documental", "Retrieval-Augmented Generation combina recuperacao de evidencias com geracao de respostas. Documentos sao divididos em trechos, indexados e consultados por similaridade. O modelo gerador recebe os trechos relevantes, mas suas afirmacoes ainda precisam ser avaliadas. Citacoes validas permitem rastrear a origem das informacoes publicadas."),
    ("Docker e implantacao", "Containers empacotam aplicacoes e dependencias, padronizando sua execucao. O Docker Compose descreve servicos, redes, volumes e variaveis de configuracao. Um backend pode conversar com um banco em uma rede interna, sem expor sua porta publicamente. Logs, backups e verificacoes de saude auxiliam a manutencao."),
    ("Conteudo educacional personalizado", "Um gerador de conteudo educacional recebe fontes tecnicas, perfil do publico e formato de saida. O texto deve preservar conceitos da documentacao e adaptar a linguagem ao destinatario. Objetivos de aprendizagem, exemplos e verificacoes ajudam na compreensao. A revisao tecnica deve ocorrer antes da publicacao do material."),
]


def produzir_chunks() -> list[str]:
    chunks = []
    for indice, (titulo, paragrafo) in enumerate(TEMAS, start=1):
        prefixo = f"title: {titulo} | chunk: {indice:02d} | text: "
        texto = prefixo + paragrafo
        # Complementa com frases tecnicas do proprio tema. A repeticao e
        # intencional e adequada ao teste de capacidade, nao a RAG de qualidade.
        complemento = (
            f" No contexto de {titulo.lower()}, o material de estudo precisa "
            "apresentar conceitos, cuidados de implementacao e exemplos praticos "
            "sem inserir afirmacoes que nao possam ser verificadas."
        )
        while len(texto) < 950:
            texto += complemento
        # Mantem palavras inteiras sem se preocupar com tamanho exato.
        if len(texto) > 1100:
            texto = texto[:1050].rsplit(" ", 1)[0] + "."
        chunks.append(texto)
    return chunks


def etapa_c(cliente=None, previsualizar=False) -> None:
    textos = produzir_chunks()
    tamanhos = [len(texto) for texto in textos]
    print("\nETAPA C - Dez chunks de aproximadamente 1.000 caracteres\n")
    print(f"Modelo solicitado: {MODELO}")
    print(f"Quantidade de chunks: {len(textos)}")
    print(f"Caracteres por chunk: min={min(tamanhos)}, max={max(tamanhos)}, media={sum(tamanhos)/len(tamanhos):.1f}")
    print(f"Total de caracteres: {sum(tamanhos)}")
    print("Dimensoes solicitadas por embedding: 768")
    print("Chamadas previstas ao metodo embed_content: 1")
    print("Observacao: caracteres NAO equivalem a tokens; o consumo real sera visto no AI Studio.")
    if previsualizar:
        print("Resultado: PREVISUALIZACAO CONCLUIDA - nenhuma chamada a API realizada")
        return

    conteudos = [
        types.Content(parts=[types.Part.from_text(text=texto)])
        for texto in textos
    ]
    vetores, duracao = medir(cliente, conteudos)
    dimensoes = [len(v) for v in vetores]
    todos_finitos = all(math.isfinite(valor) for vetor in vetores for valor in vetor)
    distintos = len(vetores) == len(set(tuple(v) for v in vetores))
    ok = (
        len(vetores) == len(textos)
        and all(d == DIMENSOES for d in dimensoes)
        and todos_finitos
        and distintos
    )
    print(f"Embeddings recebidos: {len(vetores)}")
    print(f"Dimensoes: {dimensoes}")
    print(f"Vetores diferentes: {'sim' if distintos else 'nao'}")
    print(f"Valores numericos finitos: {'sim' if todos_finitos else 'nao'}")
    print(f"Latencia total: {duracao:.2f} s")
    print(f"Latencia media aritmetica por texto (nao e latencia individual): {duracao/len(textos):.3f} s")
    print(f"Resultado: {'APROVADO' if ok else 'REPROVADO'}")
    if not ok:
        sys.exit(2)



# Etapa D - Recuperacao semantica com um corpus pequeno e gabarito conhecido.
# Reaproveita apenas os PARAGRAFOS originais de TEMAS (sem as repeticoes
# artificiais da etapa C), pois repeticao pode distorcer o ranking semantico.
# Prefixos documentados pelo Google para o gemini-embedding-2.
PERGUNTAS_D = [
    ("Q01", "Como URLs, metodos HTTP e codigos de resposta organizam uma API REST?", "CH01"),
    ("Q02", "Quais cuidados validar em um token JWT, como assinatura, emissor e expiracao?", "CH02"),
    ("Q03", "Como transacoes e chaves estrangeiras preservam dados consistentes no PostgreSQL?", "CH03"),
    ("Q04", "Como usar pgvector para recuperar chunks por similaridade de embeddings?", "CH04"),
    ("Q05", "Como enviar, listar e excluir arquivos em um bucket do OCI Object Storage?", "CH05"),
    ("Q06", "Como o FastAPI usa modelos Pydantic para validar dados de endpoints?", "CH06"),
    ("Q07", "Como coordenar agentes de escrita e revisao num grafo de etapas?", "CH07"),
    ("Q08", "Como usar RAG e citacoes para verificar se uma resposta respeita os documentos?", "CH08"),
    ("Q09", "Como o Docker Compose conecta servicos sem expor a porta do banco?", "CH09"),
    ("Q10", "Como adaptar um treinamento ao publico mantendo fidelidade tecnica?", "CH10"),
]


def conteudos_independentes(textos: list[str]):
    # Evita agregacao em um unico vetor: um Content por texto.
    return [
        types.Content(parts=[types.Part.from_text(text=texto)])
        for texto in textos
    ]


def validar_vetores(vetores: list[list[float]], quantidade: int, etiqueta: str) -> None:
    if len(vetores) != quantidade:
        raise ValueError(f"{etiqueta}: esperados {quantidade} vetores, recebidos {len(vetores)}")
    for indice, vetor in enumerate(vetores, start=1):
        if len(vetor) != DIMENSOES:
            raise ValueError(f"{etiqueta} {indice}: dimensao {len(vetor)}; esperado {DIMENSOES}")
        if not all(math.isfinite(float(valor)) for valor in vetor):
            raise ValueError(f"{etiqueta} {indice}: vetor contem numero invalido")
        if not any(float(valor) != 0 for valor in vetor):
            raise ValueError(f"{etiqueta} {indice}: vetor nulo")


def similaridade_cosseno(a: list[float], b: list[float]) -> float:
    # Nao depende de NumPy e tambem serve quando embeddings nao forem unitarios.
    produto = math.fsum(float(x) * float(y) for x, y in zip(a, b))
    norma_a = math.sqrt(math.fsum(float(x) * float(x) for x in a))
    norma_b = math.sqrt(math.fsum(float(y) * float(y) for y in b))
    if norma_a == 0 or norma_b == 0:
        raise ValueError("Norma zero: nao e possivel calcular similaridade")
    return produto / (norma_a * norma_b)


def etapa_d(cliente=None, previsualizar=False) -> None:
    documentos = [
        (f"CH{indice:02d}", titulo, paragrafo)
        for indice, (titulo, paragrafo) in enumerate(TEMAS, start=1)
    ]
    textos_documentos = [
        f"title: {titulo} | text: {paragrafo}"
        for _, titulo, paragrafo in documentos
    ]
    textos_perguntas = [
        f"task: question answering | query: {pergunta}"
        for _, pergunta, _ in PERGUNTAS_D
    ]

    print("\nETAPA D - Recuperacao semantica (busca RAG simulada)\n")
    print(f"Modelo solicitado: {MODELO}")
    print(f"Trechos do corpus: {len(documentos)}")
    print(f"Consultas de teste: {len(PERGUNTAS_D)}")
    print(f"Embeddings esperados: {len(documentos) + len(PERGUNTAS_D)}")
    print("Dimensoes esperadas por vetor: 768")
    print("Chamadas previstas ao metodo embed_content: 2")
    print("Busca: similaridade por cosseno, sem PostgreSQL nem geracao de texto")
    print("ATENCAO: 2 chamadas ao SDK nao significam necessariamente 2 unidades de RPD.")
    if previsualizar:
        print("\nCorpus e gabarito:")
        for (ident, titulo, _), (qid, pergunta, esperado) in zip(documentos, PERGUNTAS_D):
            print(f"  {ident}: {titulo}")
            print(f"  {qid}: {pergunta} [esperado: {esperado}]")
        print("\nResultado: PREVISUALIZACAO CONCLUIDA - nenhuma chamada a API realizada")
        return

    print("\nGerando embeddings dos documentos...")
    vetores_documentos, duracao_documentos = medir(
        cliente, conteudos_independentes(textos_documentos)
    )
    validar_vetores(vetores_documentos, len(documentos), "documento")
    print(f"  {len(vetores_documentos)} vetores em {duracao_documentos:.2f} s")

    print("Gerando embeddings das consultas...")
    vetores_perguntas, duracao_perguntas = medir(
        cliente, conteudos_independentes(textos_perguntas)
    )
    validar_vetores(vetores_perguntas, len(PERGUNTAS_D), "consulta")
    print(f"  {len(vetores_perguntas)} vetores em {duracao_perguntas:.2f} s")

    acertos_1 = 0
    acertos_3 = 0
    reciprocais_3 = []
    print("\nRanking de recuperacao (tres primeiros por consulta):")
    for (qid, pergunta, esperado), vetor_pergunta in zip(PERGUNTAS_D, vetores_perguntas):
        ranking = sorted(
            ((ident, titulo, similaridade_cosseno(vetor_pergunta, vetor_documento))
             for (ident, titulo, _), vetor_documento in zip(documentos, vetores_documentos)),
            key=lambda item: item[2],
            reverse=True,
        )
        ids = [item[0] for item in ranking]
        posicao = ids.index(esperado) + 1
        acertos_1 += posicao == 1
        acertos_3 += posicao <= 3
        reciprocais_3.append(1 / posicao if posicao <= 3 else 0.0)
        print(f"  {qid} | esperado: {esperado} | posicao: {posicao} | top3:")
        for numero, (ident, titulo, score) in enumerate(ranking[:3], start=1):
            marcador = " <-- esperado" if ident == esperado else ""
            print(f"       {numero}. {ident} ({score:.4f}) - {titulo}{marcador}")

    total = len(PERGUNTAS_D)
    hit1 = acertos_1 / total
    hit3 = acertos_3 / total
    mrr3 = sum(reciprocais_3) / total
    atende = hit1 >= 0.80 and hit3 == 1.0
    print("\nRESUMO DO TESTE D")
    print(f"HitRate@1: {acertos_1}/{total} = {hit1:.1%}")
    print(f"HitRate@3: {acertos_3}/{total} = {hit3:.1%}")
    print(f"MRR@3: {mrr3:.4f}")
    print(f"Latencia dos documentos: {duracao_documentos:.2f} s")
    print(f"Latencia das consultas: {duracao_perguntas:.2f} s")
    print(f"Latencia total de API: {duracao_documentos + duracao_perguntas:.2f} s")
    print("Criterio exploratorio sugerido: HitRate@1 >= 80% e HitRate@3 = 100%")
    print(f"Resultado: {'ATENDE CRITERIO EXPLORATORIO' if atende else 'ABAIXO DO CRITERIO EXPLORATORIO'}")
    print("Nota: este benchmark sintetico nao substitui avaliacao com documentos reais.")
    # Resultado abaixo do criterio e dado de pesquisa, nao erro de execucao.


def main():
    parser = argparse.ArgumentParser(description="Teste controlado de embeddings do NovaMente")
    parser.add_argument("--etapa", required=True, choices=["a", "b", "c", "d"])
    parser.add_argument("--previsualizar", action="store_true",
                        help="Etapas C ou D: mostra a carga de testes, sem usar API")
    args = parser.parse_args()
    if args.previsualizar and args.etapa not in {"c", "d"}:
        parser.error("--previsualizar pode ser usado somente com --etapa c ou d")
    if args.previsualizar:
        if args.etapa == "c":
            etapa_c(previsualizar=True)
        else:
            etapa_d(previsualizar=True)
        return

    try:
        chave = solicitar_chave()
        cliente = genai.Client(api_key=chave)
        try:
            if args.etapa == "a":
                etapa_a(cliente)
            elif args.etapa == "b":
                etapa_b(cliente)
            elif args.etapa == "c":
                etapa_c(cliente)
            else:
                etapa_d(cliente)
        finally:
            cliente.close()
    except Exception as erro:
        print(f"Falha: {type(erro).__name__}", file=sys.stderr)
        print("Confira a chave, o identificador do modelo, as quotas e a conexao. "
              "Nao compartilhe credenciais ou rastreamentos contendo segredos.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
