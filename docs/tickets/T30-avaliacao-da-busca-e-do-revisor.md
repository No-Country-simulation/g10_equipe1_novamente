---
id: T30
title: Crie a avaliação da busca, do revisor e da geração, que mede as falsas reprovações com o modelo real
blocked_by: [T03, T24, T28, T37]
touches:
  - backend/scripts/evaluate.py
  - backend/tests/scripts/test_evaluate.py
  - examples/evals/README.md
  - docs/ARCHITECTURE.md
  - docs/product-specs/fidelidade-e-qualidade.md
executor: agente
size: 3
---

# T30 - Crie a avaliação da busca, do revisor e da geração, que mede as falsas reprovações com o modelo real

## Contexto

`docs/product-specs/fidelidade-e-qualidade.md` define metas para a busca e para o revisor, e nenhuma foi medida. Desde T40, o produto só publica um conteúdo sem nenhuma afirmação sem apoio. Um único alarme falso do revisor reprova um conteúdo fiel. A equipe precisa saber quantas vezes isso acontece e por quê.

Uma afirmação fiel pode ser reprovada por dois motivos:

- a busca não trouxe o trecho que a sustenta, entre os 8 que `escreve` e `revisa` recebem;
- o trecho estava entre os 8, e o revisor não o reconheceu.

Este ticket cria um script que roda à mão, fora do CI, com o Gemini real. Ele lê um arquivo de casos, indexa o documento, mede a busca, o revisor e a geração completa e imprime um relatório em Markdown. Para diagnosticar reprovações, o script busca o trecho mais próximo da afirmação sem apoio e diz se ele estava entre os 8. Uma pessoa confere o conteúdo e o documento antes de atribuir a causa.

Este ticket entrega a ferramenta e o formato dos casos. T41 escreve os casos sobre os documentos de T13 e registra a primeira medição.

T30 espera T28 para usar `retrieve_chunks` e `PROMPT_VERSION`. Assim a avaliação busca os trechos pelo mesmo caminho da tarefa de fundo. O suporte a PDF usa a leitura por página de T37.

Leia antes: `docs/product-specs/fidelidade-e-qualidade.md`, `docs/ARCHITECTURE.md`, seções "A criação de um curso segue doze passos" e "Testes", e `docs/tickets/T28-tarefa-de-fundo.md`, seção "Contrato".

## Escopo

- O script `backend/scripts/evaluate.py`, com três medições: busca, revisor e geração.
- O formato do arquivo de casos e sua validação, que roda sem chamar o Gemini.
- Um teste no CI que valida todo arquivo de casos do repositório.
- O guia `examples/evals/README.md`, para quem escreve casos.
- Uma verificação com o Gemini real, com casos temporários.

## Fora do escopo

- Escrever os casos sobre os documentos da demonstração e registrar a primeira medição (T41).
- Medir a concordância da clareza com uma pessoa e a adaptação ao público. O relatório só lista a clareza dada pelo revisor, para T41 comparar.
- Mudar a busca, os agentes, o grafo ou as regras de publicação. Este ticket só mede.
- Rodar a avaliação no CI. Ela chama o Gemini e gasta a cota diária.

## Contrato

### Módulos que este ticket usa

O código deste ticket chama estes módulos sem alterá-los.

```python
# app.services.course_generation (T28)
def retrieve_chunks(
    *, session: Session, course: Course, query: str
) -> list[RetrievedChunk]: ...


# app.services.generation_graph (T24 e T28)
PROMPT_VERSION: str


def generate_content(request: WriteRequest) -> GenerationResult: ...


# app.services.indexing (T19)
def split_text(
    text: str, *, paged: bool = False, chunk_size: int = CHUNK_SIZE
) -> list[TextChunk]: ...


def index_document(
    *, session: Session, storage: Storage, document_id: uuid.UUID
) -> int: ...


# app.services.reviewer (T40)
def review_content(
    *,
    generated: GeneratedBase,
    audience_level: AudienceLevel,
    focus: str,
    chunks: Sequence[RetrievedChunk],
) -> ReviewResult: ...


# app.services.grounding (T40)
def evaluate(
    review: ReviewResult, valid_chunk_ids: Set[uuid.UUID]
) -> GroundingReport: ...


# app.services.documents (T16 e T37)
def read_document(filename: str, data: bytes) -> ExtractedDocument: ...
```

### Como rodar

Na pasta `backend/`, com o banco de desenvolvimento no ar e com as migrations aplicadas, configure `GEMINI_API_KEY` no `.env`. Para avaliar a revisão ou a geração, configure também `GEMINI_GENERATION_MODEL`.

```bash
uv run python scripts/evaluate.py ../examples/evals/<arquivo>.json > relatorio.md
```

O script usa `InMemoryStorage` para os arquivos e dispensa as variáveis `OCI_*`.

Com `--check`, o script só valida o arquivo de casos. O import de `split_text` ainda lê as configurações de desenvolvimento do `.env`, incluindo `DATABASE_URL`. O servidor PostgreSQL pode estar desligado e a chave do Gemini pode estar vazia.

```bash
uv run python scripts/evaluate.py --check ../examples/evals/<arquivo>.json
```

O script devolve 0 quando termina as medições, mesmo com metas não atingidas. Ele devolve 1, com uma mensagem em português na saída de erro, se as medições não podem começar ou terminar, por exemplo por um arquivo inválido, um nicho inexistente, falta de configuração do Gemini ou falha na indexação. Com `--check`, devolve 0 para um arquivo válido. O relatório mostra os números e as metas sem decidir se a meta foi atingida.

### Arquivo de casos

Um arquivo JSON por documento. Todos os campos são obrigatórios, e um campo a mais é um erro.

```json
{
  "document": "examples/sources/kubernetes-conceitos.md",
  "niche": "geral",
  "retrieval": [
    {
      "question": "Qual é a menor unidade que o Kubernetes implanta?",
      "expected": "Pods are the smallest deployable units of computing"
    }
  ],
  "review": [
    {
      "id": "pods-fiel",
      "focus": "Pods no Kubernetes",
      "audience_level": "technical_basic",
      "format": "tutorial",
      "planted_error": null,
      "content": {
        "summary": "...",
        "sections": [{ "title": "...", "body": "..." }],
        "takeaways": ["..."]
      }
    }
  ],
  "generation": [
    {
      "focus": "Pods e Deployments",
      "audience_level": "non_technical",
      "format": "quiz"
    }
  ]
}
```

- `document`: resolva um caminho relativo a partir da raiz do repositório. Aceite caminho absoluto para os testes e a verificação com arquivos temporários. O script lê o arquivo com `read_document`.
- `niche`: `slug` de um nicho da tabela `niche`.
- `retrieval`: perguntas para a busca. `expected` é um trecho literal do documento que responde à pergunta.
- `review`: conteúdos escritos à mão para o revisor. `content` segue o formato de `content_schemas.py` para `format`. `planted_error` é `null` em um conteúdo fiel. Em um conteúdo com erro plantado, é o texto exato do fato errado.
- `generation`: pedidos de geração completa.

### Validação do arquivo de casos

`load_cases(path: Path) -> CaseFile` valida o arquivo sem chamar o Gemini nem o banco. Em erro, levanta `CaseError` com uma mensagem que diz o problema e o caso. A validação confere:

1. o JSON segue o formato acima, com modelos Pydantic `extra="forbid"`;
2. pelo menos uma das três listas tem um caso;
3. o documento existe e `read_document` o aceita;
4. cada `expected` aparece inteiro dentro de um só chunk de `split_text` do documento, com `paged` verdadeiro para PDF, como na indexação. Um trecho que cruza dois chunks nunca seria achado;
5. cada `content` valida no modelo de `GENERATED_MODELS[format]`, com metadados fixos (`title` igual ao foco, `estimated_minutes` 5, `key_concepts` `["avaliação"]` e `prerequisites` vazio). `revisa` só lê `content`;
6. cada `planted_error` preenchido aparece em um campo de texto de `content`;
7. os `id` de `review` são únicos;
8. depois de tirar espaços nas pontas, `document`, `niche`, `question`, `expected`, `focus`, `id` e `planted_error` quando preenchido não ficam vazios. Use o mesmo limite de 255 caracteres de `title` para `focus`.

As comparações de texto ignoram diferenças de espaços e de quebras de linha: `" ".join(texto.split())` dos dois lados. A comparação diferencia maiúsculas e acentos.

### O que o script faz

1. Valida o arquivo de casos.
2. Confere a configuração do Gemini e se o nicho existe antes de gravar qualquer linha. No banco, cria um usuário inativo com e-mail aleatório e senha aleatória com hash, um curso de avaliação com o nicho do arquivo e um `source_document` com o arquivo no `InMemoryStorage`. Grava essas linhas, guarda o `id` do usuário e indexa com `index_document`. Nenhum caso publica conteúdo.
3. **Busca.** Para cada pergunta, chama `retrieve_chunks(query=question)` e registra a posição, de 1 a 8, do primeiro chunk que contém `expected`. Fora dos 8, a posição fica vazia.
4. **Revisor.** Para cada caso, chama `retrieve_chunks(query=focus)`, monta o conteúdo como na validação e chama `review_content` e `evaluate`. O caso é aprovado se `report.passed` é verdadeiro. Conte os casos com erro plantado que foram reprovados. Em T41, uma pessoa confere se o revisor marcou o erro plantado como uma afirmação sem apoio, mesmo com outras palavras. Um caso fiel reprovado conta como alarme falso.
5. **Geração.** Para cada caso, chama `retrieve_chunks(query=focus)`, monta o `WriteRequest` com o nicho do arquivo e chama `generate_content`.
6. **Pistas.** Para cada afirmação sem apoio de um caso fiel do revisor ou de uma geração que falhou e tem relatório, chama `retrieve_chunks(query=afirmação)` e pega o primeiro chunk. Identifica o caso e mostra o `chunk_index`, a similaridade, os primeiros 300 caracteres do chunk e se o `chunk_id` estava entre os 8 que o caso usou. Se a busca da pista falhar ou não devolver chunks, registre o motivo e preserve o resultado do caso.
7. No `finally`, encerra a sessão de trabalho e apaga o usuário pelo `id` em uma nova sessão e transação, se ele foi criado. As chaves estrangeiras apagam o curso, o documento e os chunks em cascata. Se a exclusão falhar, a execução sai com erro.

Um `LLMError` em um caso entra no relatório como erro daquele caso, e o script segue para o próximo.

### Relatório

O relatório em Markdown traz, nesta ordem:

1. Cabeçalho: data, arquivo de casos, documento, número de chunks, `GEMINI_GENERATION_MODEL`, `GEMINI_EMBEDDING_MODEL` e `generation_graph.PROMPT_VERSION`.
2. **Busca**: uma tabela com a pergunta e a posição, e a linha "Trecho esperado entre os 8: N de M (P%). Meta inicial: 80%."
3. **Revisor**. Uma tabela com o `id`, o texto do erro plantado quando houver, `focus_covered`, aprovação, clareza e afirmações sem apoio. Depois, mostre quantos casos com erro plantado foram reprovados. Em T41, uma pessoa aplica a meta de 4 de 5 aos erros que confirmar que o revisor encontrou. Mostre também os alarmes falsos entre os casos fiéis e a meta inicial de no máximo 1 em 5.
4. **Geração**. Uma tabela com foco, formato, público, decisão, tentativas e mensagem de falha. Conte os casos aprovados para publicação. Para cada falha, inclua os índices dos chunks usados e o último `generated.content` se houver. Esses dados permitem que uma pessoa confira se o material cobria o foco e tinha apoio no documento.
5. **Pistas**: as afirmações sem apoio, cada uma com o trecho mais próximo. O relatório explica em uma frase como ler a pista: "Fora dos 8" indica que a busca pode ter deixado de trazer o trecho. "Entre os 8" indica que o revisor pode ter deixado de reconhecer o trecho. Nos dois casos, a afirmação também pode não ter apoio no documento. Uma pessoa lê o trecho e decide.

Uma pista é só um ponto de partida para uma pessoa. O script não classifica a reprovação sozinho.

Use os casos com resultado válido como denominador. Liste os erros de execução à parte. No grafo, uma falha do modelo pode chegar como `Decision.fail` com a mensagem do modelo. Identifique esses casos no relatório. Se o denominador for zero, escreva "Sem casos medidos".

## Detalhes técnicos

- O script fica em `backend/scripts/`, como `verify_storage.py`. Ele não entra na cobertura de `backend/app`, e o `mypy` e o `ty` não o conferem. Use tipos mesmo assim.
- Separe em funções a validação (`load_cases`), a posição de um trecho na busca (`retrieval_rank(expected: str, chunks: Sequence[RetrievedChunk]) -> int | None`), as contagens do resumo e a montagem do relatório. `main(argv: list[str]) -> int` liga tudo.
- Os testes importam o script com `from scripts import evaluate`. `backend/` não tem `__init__.py`, e o pytest põe essa pasta no `sys.path`.
- O teste do item 7 dos cenários procura arquivos com `Path(__file__).parents[3] / "examples" / "evals"`. Sem arquivos, ele passa.
- O ritmo das chamadas fica com `llm.py` (T39). O script não espera por conta própria.
- A geração completa usa até quatro chamadas de texto por caso, ou até cinco com `planeja` (T29). O guia apresenta esse limite por caso e conta os embeddings da indexação, da busca por caso e das pistas à parte.
- Não edite código em `backend/app/`.
- Nenhum teste chama o Gemini.

## Guia para quem escreve casos

Em `examples/evals/README.md`, em português simples, para uma pessoa que não programa:

- para que serve cada lista do arquivo e um exemplo curto de cada uma;
- como escolher `expected`: uma frase curta copiada do documento, de um só parágrafo;
- como plantar um erro: copie um conteúdo fiel, troque um fato por um fato errado e copie o fato errado em `planted_error`. No quiz, use um fato do enunciado, da resposta correta ou da justificativa.
- que os conteúdos do revisor tratam do foco do caso e só trazem fatos do documento, exceto o erro plantado;
- quantas chamadas ao Gemini cada caso gasta;
- o comando para validar o arquivo sem gastar cota: `uv run python scripts/evaluate.py --check <arquivo>`;
- o comando para rodar a avaliação.

## Documentação

- Em `docs/ARCHITECTURE.md`, seção "Testes", troque o item "Revisor" por um item "Avaliação": `backend/scripts/evaluate.py` mede a busca, o revisor e a geração com o modelo real, a partir dos casos de `examples/evals/`. Roda à mão, fora do CI. Não mude outras seções: T29 edita o fluxo, as regras e os modelos de IA.
- Em `docs/product-specs/fidelidade-e-qualidade.md`, na seção "Como a equipe mede a qualidade", troque o primeiro parágrafo. Diga que o script mede a busca, registra as decisões do revisor e da geração e mostra pistas para a conferência em T41. Aponte para `examples/evals/README.md`.

## Verificação com o Gemini real

Rode uma vez antes de abrir o PR. Use um arquivo de casos temporário, fora do repositório, e não faça commit dele.

1. Use um documento técnico público, de 10 mil a 30 mil caracteres.
2. Escreva 3 perguntas, 2 casos do revisor (um fiel e um com erro plantado) e 1 caso de geração.
3. Rode o script e anexe o relatório ao PR.
4. Confira no banco que o usuário da avaliação foi apagado.

Sem acesso ao Gemini, registre no PR que pulou a verificação.

## Critérios de aceite

- [ ] O script cumpre o contrato e imprime o relatório na ordem descrita.
- [ ] Um arquivo de casos inválido para o script antes de qualquer chamada ao Gemini, com uma mensagem que diz o problema e o caso. `--check` valida o arquivo sem banco e sem Gemini.
- [ ] A busca, o revisor e a geração usam `retrieve_chunks`, o mesmo caminho da tarefa de fundo.
- [ ] Cada afirmação sem apoio de um caso fiel reprovado ou de uma geração que falhou traz a pista do trecho mais próximo ou explica por que ela ficou indisponível.
- [ ] O script apaga o usuário da avaliação no fim, mesmo depois de um erro.
- [ ] O CI valida todo arquivo de `examples/evals/*.json`.
- [ ] `examples/evals/README.md` explica como escrever e validar os casos.
- [ ] Os documentos de `docs/` estão atualizados como descrito.
- [ ] O PR traz o relatório da verificação manual ou diz que ela foi pulada.
- [ ] Nenhum teste chama o Gemini.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Em `backend/tests/scripts/test_evaluate.py`. Os cenários 1 a 6 usam um documento `.md` e um arquivo de casos criados em `tmp_path`.

1. Um arquivo válido carrega, com os três tipos de caso.
2. Um `expected` que não está no documento levanta `CaseError` com a pergunta na mensagem.
3. Um `expected` que cruza o limite entre dois chunks levanta `CaseError`. Use um documento com mais de 1.000 caracteres.
4. Um `content` que não segue o formato levanta `CaseError` com o `id` do caso. Um `planted_error` ausente do conteúdo também. Dois casos com o mesmo `id` também.
5. Um campo a mais, um nicho em branco ou as três listas vazias levantam `CaseError`.
6. `retrieval_rank` devolve a posição do primeiro chunk que contém o trecho, ignora diferenças de espaços e devolve `None` fora da lista.
7. Todo arquivo de `examples/evals/*.json` carrega sem erro.
8. `main` roda de ponta a ponta com a configuração do Gemini preenchida por valores de teste e as chamadas aos serviços trocadas por funções falsas. O revisor aprova o caso fiel e reprova o caso com erro plantado. O grafo devolve uma geração reprovada com uma afirmação sem apoio. O relatório traz as quatro seções, as contagens e a pista da afirmação da geração.
9. `main` com um arquivo inválido devolve 1. Com `--check`, um arquivo válido devolve 0 mesmo sem chave do Gemini. Faça o teste falhar se o script tentar abrir uma sessão ou chamar um serviço do Gemini nesses dois casos.
10. Sem a configuração do Gemini exigida pelo caso, ou com um nicho que não existe, `main` devolve 1 com uma mensagem e não cria linhas.
11. Depois de `main`, confira por `id` que o usuário e as linhas filhas da avaliação foram apagados. Repita com erro de indexação depois de criar as linhas.
12. Uma lista vazia ou composta apenas de erros do Gemini mostra "Sem casos medidos". Um erro na busca de uma pista é registrado e mantém o resultado do caso.
