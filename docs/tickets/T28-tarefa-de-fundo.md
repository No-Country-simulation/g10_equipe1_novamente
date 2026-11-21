---
id: T28
title: Ligue a criação do curso a uma tarefa de fundo que indexa os documentos e gera cada conteúdo
blocked_by: [T03, T19, T22, T23, T24, T26, T39]
touches:
  - backend/app/services/course_generation.py
  - backend/app/services/generation_graph.py
  - backend/app/api/routes/courses.py
  - backend/tests/services/test_course_generation.py
  - backend/tests/api/routes/test_courses_create.py
  - docs/ARCHITECTURE.md
  - docs/product-specs/criar-curso.md
executor: agente
size: 3
---

# T28 - Ligue a criação do curso a uma tarefa de fundo que indexa os documentos e gera cada conteúdo

## Contexto

Hoje `POST /api/v1/courses/` (T23) grava o curso, os documentos e os conteúdos e responde HTTP 201. Nada acontece depois: o curso fica em "Gerando" e cada conteúdo fica em "Na fila" para sempre.

As peças da geração já existem separadas:

- a indexação de um documento (T19);
- a busca dos 8 chunks mais próximos (T03);
- o grafo que escreve, revisa e reescreve uma vez (T24), para os três formatos (T20, T25 e T26);
- a publicação no OCI e no banco (T22);
- o ritmo dos limites por minuto do Gemini (T39).

Este ticket liga essas peças em uma tarefa de fundo (`BackgroundTasks` do FastAPI), agendada pela rota de criação. É o primeiro ticket em que o caminho inteiro roda: a pessoa envia um documento e lê o conteúdo publicado.

T32 (nova tentativa) e T33 (exclusão) usam a função deste ticket. T29 e T30 usam `PROMPT_VERSION` e `retrieve_chunks`, descritos no contrato.

Leia antes: `docs/ARCHITECTURE.md`, seções "A criação de um curso segue doze passos", "Os estados tornam a tarefa de fundo observável", "Regras que o código mantém" e "Falhas e recuperação"; `docs/generated/db-schema.md`, seção "O backend garante as regras que o banco não expressa"; `docs/product-specs/criar-curso.md`.

## Escopo

- A função `run_course_generation`, que indexa os documentos do curso e gera os conteúdos `pending`, um por vez, na ordem de `position`.
- A função `retrieve_chunks`, que gera o embedding de um texto e busca os 8 chunks mais próximos no curso.
- A constante `PROMPT_VERSION` em `generation_graph.py`.
- O agendamento da tarefa na rota de criação.
- Os estados e as mensagens de falha de documento, conteúdo e curso.
- Uma verificação manual com o Gemini e o OCI reais.

## Fora do escopo

- Nova tentativa, a regra dos 10 minutos e o botão "Tentar novamente" (T32).
- Exclusão de curso e limpeza no OCI (T33).
- A etapa `planeja` (T29).
- Mudar a indexação, a busca, o grafo, os agentes ou a publicação. Este ticket só chama essas funções.
- Mudar o frontend. A tela do curso já consulta a API a cada 3 segundos enquanto algum conteúdo está `pending` ou `running`.
- Gerar conteúdos em paralelo. A tarefa gera um conteúdo por vez.

## Contrato

### Módulos que este ticket usa

O código deste ticket chama estes módulos sem alterá-los. A única exceção é a constante `PROMPT_VERSION`, descrita abaixo.

```python
# app.core.llm
class LLMError(Exception): ...


def embed_texts(
    texts: Sequence[str], *, task: Literal["document", "query"]
) -> list[list[float]]: ...


# app.services.indexing (T19)
class IndexingError(Exception):
    """A mensagem é o texto gravado em source_document.error_message."""


def index_document(
    *, session: Session, storage: Storage, document_id: uuid.UUID
) -> int: ...


# app.services.retrieval (T03)
def search_chunks(
    *,
    session: Session,
    course_id: uuid.UUID,
    owner_id: uuid.UUID,
    query_embedding: Sequence[float],
    embedding_model: str,
    limit: int = 8,
) -> list[RetrievedChunk]: ...


# app.services.generation_graph (T24)
def generate_content(request: WriteRequest) -> GenerationResult: ...


# app.services.publishing (T22)
class PublishError(Exception):
    """A mensagem é um texto para course_content.error_message."""


def publish_content(
    *,
    session: Session,
    storage: Storage,
    content_id: uuid.UUID,
    generated: GeneratedBase,
    review: ReviewResult,
    report: GroundingReport,
    chunks: Sequence[RetrievedChunk],
) -> CourseContent: ...
```

`index_document` marca o documento como `processing`, grava os chunks e o estado `indexed` e devolve o número de chunks. Um documento já `indexed` volta sem nova chamada ao Gemini. Nas falhas que trata, `index_document` marca o documento como `failed`, grava `error_message` e levanta `IndexingError`. Erros fora desse tratamento, como uma falha no primeiro `commit`, saem da função.

`publish_content` grava o JSON no OCI, publica o conteúdo e as citações e muda o curso para `ready`. Em falha, desfaz a transação e levanta `PublishError`.

### Constante que este ticket acrescenta ao grafo

Em `backend/app/services/generation_graph.py`, logo depois dos imports:

```python
PROMPT_VERSION = f"{writer.PROMPT_VERSION}+{reviewer.PROMPT_VERSION}"
```

O valor hoje é `escreve-v3+revisa-v2`. A constante fica no grafo porque o grafo sabe quais agentes participam de uma geração. T29 acrescenta a versão de `planeja`. Não mude mais nada em `generation_graph.py`.

### Módulo que este ticket cria

Em `backend/app/services/course_generation.py`:

```python
def retrieve_chunks(
    *, session: Session, course: Course, query: str
) -> list[RetrievedChunk]: ...


def run_course_generation(*, storage: Storage, course_id: uuid.UUID) -> None: ...
```

`retrieve_chunks` chama `llm.embed_texts([query], task="query")` e passa o vetor a `search_chunks`, com `course_id=course.id`, `owner_id=course.owner_id` e `embedding_model=settings.GEMINI_EMBEDDING_MODEL`. O `limit` fica no padrão de 8. Um `LLMError` sai sem mudança.

`run_course_generation` nunca levanta exceção. Ela roda depois da resposta HTTP, e uma exceção ali só apareceria no log.

### O que `run_course_generation` faz

1. Abre uma sessão própria (`Session(engine)`). A tarefa usa o `course_id` e nunca acessa a sessão do pedido HTTP. Se o curso não existe, registra um aviso no log e termina.
2. Indexa cada documento do curso que não está `indexed`, um por vez, em ordem de `created_at` e depois de `id`. Para isso chama `index_document`.
3. Se a indexação de um documento falha, a tarefa para. Ela não indexa os documentos seguintes e não gera nenhum conteúdo. Ela marca cada conteúdo `pending` como `failed`, com a mensagem "O conteúdo não foi gerado, porque um documento do curso falhou." O documento guarda o próprio motivo, gravado por `index_document`.
4. Pega os conteúdos `pending` do curso em ordem de `position`. Para cada um:
    1. Reserva o conteúdo com um único `UPDATE ... WHERE id = :id AND status = 'pending' RETURNING id`. O comando muda o estado para `running` e grava `llm_model = settings.GEMINI_GENERATION_MODEL`, `prompt_version = generation_graph.PROMPT_VERSION`, `error_message = NULL` e `updated_at` com a hora atual. Se o comando não devolve linha, pule para o próximo. Faça `commit` antes de chamar `retrieve_chunks`. Só quem reservou o conteúdo segue para a geração.
    2. Chama `retrieve_chunks(query=content.focus)`. Sem chunks, o conteúdo fica `failed` com "Não foi possível gerar o conteúdo, porque o curso não tem trechos indexados."
    3. Monta o `WriteRequest` com o formato e o foco do conteúdo, o `audience_level` do curso, o `name` e o `prompt_hint` do nicho e os chunks.
    4. Chama `generation_graph.generate_content(request)`.
    5. Com `decision == publish`, chama `publish_content` com os dados do resultado e os mesmos chunks. Com `decision == fail`, o conteúdo fica `failed` com `result.error_message`.
5. Depois de processar os conteúdos ou tratar uma falha de indexação, marque o curso como `failed` com um `UPDATE` condicional. A linha ainda deve estar `initializing`, sem conteúdo publicado (par `content` e `oci_object_key`) e sem conteúdo `pending` ou `running`. Quem muda o curso para `ready` é `publish_content`, no primeiro conteúdo publicado.

Um conteúdo que falha não interrompe os seguintes.

A rota agenda uma tarefa por curso novo. A reserva com `UPDATE` protege cada conteúdo. T32 precisa coordenar novas tentativas do mesmo curso para que duas tarefas não indexem o mesmo documento ao mesmo tempo.

### Falhas na geração de um conteúdo

| Falha | `error_message` do conteúdo |
| --- | --- |
| `LLMError` no embedding do foco | `f"Não foi possível gerar o conteúdo. {erro}"`, a mesma forma do grafo |
| Curso sem chunks elegíveis | Não foi possível gerar o conteúdo, porque o curso não tem trechos indexados. |
| `decision == fail` | `result.error_message` |
| `PublishError` | `str(erro)` |
| Qualquer outra exceção | Não foi possível gerar o conteúdo. |

Em qualquer outra exceção de conteúdo, faça `rollback`, registre no log com `logger.exception` o `course_id` e o `content_id` e grave a falha em uma sessão nova. Se a reserva ainda não foi confirmada, grave a falha só se o conteúdo segue `pending`. Se a reserva foi confirmada, grave a falha só se segue `running`.

Se `index_document` levanta outra exceção, faça `rollback` e registre o `course_id` e o `document_id` no log. Em uma sessão nova, marque o documento como `failed` com "Não foi possível indexar o documento {nome}." se ele ainda não está `indexed`, e siga o passo 3. Use um `UPDATE` que só altere conteúdos ainda `pending` nesse passo.

Ao marcar um conteúdo como `failed`, mude só `status`, `error_message` e `updated_at`. Preserve o título, o conteúdo, os metadados, as notas, a chave do objeto e as citações da última publicação. Ao marcar o curso como `failed`, atualize também `course.updated_at`.

Se abrir a sessão ou gravar a recuperação falhar, registre a exceção no log com o `course_id` e encerre a tarefa. Sem acesso ao banco, o estado pode ficar pendente até a recuperação de T32.

### Agendamento na rota

Em `backend/app/api/routes/courses.py`, `create_course` recebe `background_tasks: BackgroundTasks`. Depois do `commit` com sucesso, e só nesse caso, a rota agenda:

```python
background_tasks.add_task(
    course_generation.run_course_generation, storage=storage, course_id=course.id
)
```

- Importe o módulo (`from app.services import course_generation`) e chame a função pelo módulo, para os testes trocarem `app.services.course_generation.run_course_generation`.
- Passe a mesma instância de `storage` que a rota usou para gravar os documentos. Assim a tarefa lê os arquivos do mesmo lugar, inclusive com o armazenamento em memória dos testes.
- Uma validação que falha (HTTP 422 ou 404) ou um armazenamento fora do ar (HTTP 503) não agenda nada.
- A resposta HTTP 201 não muda: o curso continua `initializing` e os conteúdos `pending`.

### Log

Registre em `INFO`, sem texto do documento nem do conteúdo:

- ao fim de cada conteúdo: `course_id`, `content_id`, formato, estado final, `attempts` do resultado, quando houver, e o tempo em segundos;
- ao fim da tarefa: `course_id`, estado final do curso e o tempo total em segundos.

O tempo total responde à pergunta de `criar-curso.md`: quanto leva um curso com três saídas.

## Detalhes técnicos

- Chame os serviços pelo módulo (`from app.services import generation_graph, indexing, publishing` e `generation_graph.generate_content(...)`). Os testes trocam `app.services.generation_graph.generate_content` e `app.core.llm.embed_texts` com `monkeypatch.setattr`.
- A função é síncrona. O FastAPI roda uma tarefa síncrona em uma thread, depois de enviar a resposta.
- O `TestClient` espera as tarefas de fundo antes de devolver a resposta ao teste. A resposta 201 continua com os estados iniciais, mas uma consulta seguinte já poderia encontrar outros estados.
- Em `test_courses_create.py`, acrescente uma fixture `autouse` que troca `app.services.course_generation.run_course_generation` por um `Mock` e o devolve. Assim os testes da rota não executam a geração real.
- Os testes de `test_course_generation.py` chamam `run_course_generation` direto, com um `InMemoryStorage` que já guarda os documentos. A tarefa abre sessões próprias no mesmo banco de teste. Leia os resultados em uma sessão nova ou depois de `db.expire_all()`.
- O embedding falso devolve vetores não nulos de 768 valores. No teste com dois documentos, use textos distintos e curtos o suficiente para gerar um chunk por documento. Assim ambos entram no limite de oito.
- O OpenAPI não muda, porque `BackgroundTasks` não aparece no schema. `frontend/src/client/` não pode aparecer no diff.
- Nenhum teste chama o Gemini nem o OCI.

## Documentação

Em `docs/ARCHITECTURE.md`:

- Na tabela "Mapa do código", mude o estado de `backend/app/services/course_generation.py` para "Existe" e o conteúdo para "Tarefa de fundo: indexação, busca, geração e publicação".
- Troque "O fluxo completo depende do grafo de geração (T24) e da tarefa de fundo (T28)." por uma frase que diga que a rota de criação agenda a tarefa de fundo.
- Na tabela "Decisões", mude o estado de "Tarefa de fundo com `BackgroundTasks`" para "Existe". Na linha "Publicar só com foco coberto...", troque "Decisão em `grounding.py`. O fluxo depende de T24 e T28." por "Existe".
- Na tabela "Falhas e recuperação", acrescente uma linha para a falha de indexação. A tarefa para, marca cada conteúdo `pending` como `failed` com a mensagem do passo 3 e aplica a regra de falha do curso do passo 5.
- Depois da tabela, atualize a frase sobre o que já existe para incluir a recuperação de falhas da tarefa de fundo. As linhas sobre a regra dos 10 minutos, nova tentativa e limpeza de objetos ao excluir um curso ou uma conta seguem a construir.

Em `docs/product-specs/criar-curso.md`, na tabela "Erros que a pessoa pode ver", linha "Falha ao ler ou indexar um documento", acrescente à mensagem: "Cada conteúdo mostra: O conteúdo não foi gerado, porque um documento do curso falhou."

Se a verificação manual rodou, troque em `criar-curso.md` a frase "A equipe mede o tempo de um curso com três saídas e ajusta os limites se for preciso." pelo tempo medido, com a data, o tamanho do documento e o modelo.

## Verificação com o Gemini e o OCI reais

Rode uma vez antes de abrir o PR, com `GEMINI_API_KEY`, `GEMINI_GENERATION_MODEL` e o armazenamento OCI de desenvolvimento configurados no `.env` do worktree.

1. Suba o backend e o frontend do worktree e entre com um usuário de desenvolvimento.
2. Em "Novo curso", envie um documento `.md` público, de 10 mil a 30 mil caracteres, sobre um só assunto técnico. Use um título que o documento trate. Escolha as três saídas.
3. Acompanhe a tela do curso até nenhum conteúdo ficar "Na fila" ou "Gerando".
4. Registre no PR:
    - o documento, o título e o nível de público;
    - o estado final de cada conteúdo e do curso;
    - o tempo de cada conteúdo e o tempo total, lidos no log;
    - a mensagem de cada conteúdo que falhou;
    - a quantidade de objetos de documentos e de conteúdos sob `courses/{course_id}/`.
5. Se algum conteúdo foi publicado, abra o leitor e confira o conteúdo, a avaliação e os trechos citados.

Os objetos ficam no bucket de desenvolvimento até T33. Registre o `course_id` no PR.

Uma reprovação pela regra de fidelidade não é um defeito deste ticket. Registre a mensagem: T30 mede essas reprovações. Sem acesso ao Gemini ou ao OCI, registre no PR que pulou a verificação.

## Critérios de aceite

- [ ] Criar um curso agenda `run_course_generation` uma vez, com o mesmo armazenamento e o `id` do curso. Falhas de validação, de armazenamento ou de `commit` não agendam a tarefa.
- [ ] A tarefa indexa os documentos e gera os conteúdos `pending`, um por vez, na ordem de `position`.
- [ ] Um conteúdo publicado fica `succeeded`. O primeiro deles muda o curso para `ready`.
- [ ] Cada conteúdo gerado grava `llm_model` e `prompt_version` ao começar, com sucesso ou não.
- [ ] Se um documento falha na indexação, nenhum conteúdo é gerado, cada conteúdo `pending` fica `failed` com a mensagem do contrato e o curso fica `failed`.
- [ ] Cada falha de conteúdo grava a mensagem da tabela do contrato. Um conteúdo que falha não interrompe os seguintes.
- [ ] Quando todos os conteúdos iniciais falham, o curso fica `failed`.
- [ ] Uma falha não muda o conteúdo publicado antes, nem as notas e as citações.
- [ ] Um conteúdo que não está `pending` quando a tarefa chega a ele não é gerado.
- [ ] `run_course_generation` não levanta exceção.
- [ ] Os documentos de `docs/` estão atualizados como descrito.
- [ ] O PR traz o resultado da verificação manual ou diz que ela foi pulada.
- [ ] Nenhum teste chama o Gemini nem o OCI.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Em `backend/tests/services/test_course_generation.py`. Cada cenário cria no banco de teste um usuário, um curso `initializing`, documentos `uploaded` com os arquivos no `InMemoryStorage` e conteúdos `pending`. O embedding falso e um `generate_content` falso guardam os argumentos. O `generate_content` falso devolve um `GenerationResult` fixo por formato, com o relatório calculado por `grounding.evaluate`. A publicação é a real, com o armazenamento em memória.

1. Dois documentos e três conteúdos (quiz na posição 0, tutorial na 1, flashcards na 2). Os dois documentos ficam `indexed`. `generate_content` recebe os três pedidos nessa ordem, com formato, foco, nível de público, nome e `prompt_hint` do nicho e chunks dos dois documentos. Os três conteúdos ficam `succeeded`, o curso fica `ready` e o armazenamento tem três objetos sob `courses/{course_id}/contents/`. Cada conteúdo tem `llm_model` igual a `settings.GEMINI_GENERATION_MODEL` e `prompt_version` igual a `generation_graph.PROMPT_VERSION`.
2. Durante a chamada do segundo conteúdo, lido em uma sessão nova: o primeiro está `succeeded`, o curso está `ready`, o segundo está `running` com `llm_model` e `prompt_version` gravados, e o terceiro está `pending`.
3. O arquivo do segundo documento não está no armazenamento. O primeiro documento fica `indexed`, o segundo fica `failed` com a mensagem de `index_document`, cada conteúdo fica `failed` com "O conteúdo não foi gerado, porque um documento do curso falhou." e o curso fica `failed`. `generate_content` não é chamado.
4. O grafo devolve `fail` com "O documento não trata do assunto pedido." para o primeiro conteúdo e `publish` para o segundo. O primeiro fica `failed` com essa mensagem, sem `content` nem `oci_object_key`. O segundo fica `succeeded` e o curso fica `ready`.
5. O grafo devolve `fail` para todos os conteúdos. O curso fica `failed` e o armazenamento não tem objeto sob `contents/`.
6. O embedding do foco do primeiro conteúdo levanta `LLMError("cota")`. O primeiro conteúdo fica `failed` com "Não foi possível gerar o conteúdo. cota". O segundo é gerado.
7. O armazenamento falha ao gravar o JSON de um conteúdo. O conteúdo fica `failed` com "Não foi possível guardar o conteúdo no armazenamento."
8. `generate_content` levanta `RuntimeError` no primeiro conteúdo. O primeiro fica `failed` com "Não foi possível gerar o conteúdo.", o segundo é gerado e o log tem um registro `ERROR` com o `course_id` e o `content_id`.
9. Entre a seleção de um conteúdo `pending` e a reserva, outra sessão grava `running`. A tarefa pula esse conteúdo e gera só o próximo, que falha. O primeiro continua `running`, e o curso segue `initializing`.
10. Publique um conteúdo e devolva a linha a `pending`, como fará a nova tentativa de T32. O grafo devolve `fail`. O conteúdo fica `failed` e mantém o título, o conteúdo, as notas, a chave do objeto e as citações da publicação. O objeto continua no armazenamento e o curso continua `ready`.
11. Um `course_id` que não existe: a função termina sem exceção.
12. Os documentos já estão `indexed` com outro `embedding_model`. Sem chunks elegíveis, a tarefa grava a mensagem do contrato e não chama `generate_content`.
13. `index_document` levanta `RuntimeError` ao processar um documento. Uma sessão nova vê o documento e os conteúdos `pending` como `failed`, com as mensagens do contrato, e o curso como `failed`.

Em `backend/tests/api/routes/test_courses_create.py`:

14. Um curso criado com sucesso agenda a tarefa uma vez, com a instância de `storage` da fixture e `course_id` igual ao `id` da resposta.
15. Os testes de falha de validação (HTTP 422 e 404), armazenamento (HTTP 503) e `commit` confirmam que a tarefa não foi agendada.
