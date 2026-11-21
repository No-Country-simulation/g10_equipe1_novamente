---
id: T32
title: Permita tentar de novo um conteúdo que falhou e encerre gerações paradas
blocked_by: [T28]
touches:
  - backend/app/models.py
  - backend/app/alembic/versions/
  - backend/app/services/course_generation.py
  - backend/app/services/indexing.py
  - backend/app/api/routes/courses.py
  - backend/tests/services/test_course_generation.py
  - backend/tests/api/routes/test_courses_create.py
  - backend/tests/api/routes/test_courses_retry.py
  - frontend/src/components/Course/RetryButton.tsx
  - frontend/src/components/Course/ContentView.tsx
  - frontend/src/components/Course/ContentCard.tsx
  - frontend/src/components/Course/ContentPage.tsx
  - frontend/src/client/
  - frontend/tests/content-retry.spec.ts
  - docs/ARCHITECTURE.md
  - docs/product-specs/criar-curso.md
executor: agente
size: 5
---

# T32 - Permita tentar de novo um conteúdo que falhou e encerre gerações paradas

Desde [T28](completed/T28-tarefa-de-fundo.md), a tarefa de fundo gera as saídas em ordem. Uma queda pode deixar o curso com conteúdo na fila ou em geração sem ninguém para concluir. A [especificação](../product-specs/criar-curso.md) pede que a pessoa possa tentar de novo depois de uma falha.

## Nova tentativa

Crie `POST /api/v1/courses/{course_id}/contents/{content_id}/retry`, com a função `retry_content` no fim de `courses.py`. Responda HTTP 202 com `CourseDetail`. Use `CurrentUser` e a mesma resolução de `get_storage` de `create_course`. O handler de `StorageError` já devolve HTTP 503 quando obter o armazenamento falha.

- Curso ausente ou de outra pessoa: HTTP 404, "Curso não encontrado." Conteúdo ausente ou de outro curso: HTTP 404, "Conteúdo não encontrado."
- A rota aceita só conteúdo `failed`. Para os outros estados, responda HTTP 409, "Só um conteúdo que falhou pode ser gerado de novo."
- Sob um `SELECT ... FOR UPDATE` da linha de `Course`, confirme a posse e faça um `UPDATE` condicional de `failed` para `pending`, com `error_message=NULL` e `updated_at` atual. Preserve os documentos, a última publicação, suas citações e os dados do modelo até a próxima reserva. Um curso `failed` volta a `initializing` na mesma transação. Um curso `ready` continua `ready`.
- Se já há uma tarefa válida para o curso, a saída volta à fila dessa tarefa. Se a tarefa não existe, crie uma nova identificação e agende uma tarefa após o `commit`. Monte o `CourseDetail` com `read_course` antes de liberar o lock, para refletir a transição para `pending` no HTTP 202. Uma falha antes do `commit` não agenda trabalho.
- Se há trabalho ativo já vencido ou sem identificação, aguarde a recuperação periódica. Responda HTTP 409 com "A geração foi interrompida. Tente novamente." Um pedido de retry não prorroga uma geração vencida.

Gere `CoursesService.retryContent` com `bash scripts/generate-client.sh`. Crie `RetryButton.tsx` com `LoadingButton`, desabilitado durante o pedido. Mostre o botão só para conteúdo `failed`, no alerta de `ContentView` e no cartão de `ContentCard`. `ContentScreen` em `ContentPage.tsx` passa o ID do curso a `ContentView`. No sucesso, atualize `courseQueryKey(courseId)` com a resposta e invalide `coursesQueryKey`. O `useCourse` volta a consultar a API a cada três segundos. No erro, mostre o detalhe da API com `handleError` e o toast existente.

## Uma tarefa por curso

Acrescente `Course.generation_id`, um UUID interno e anulável, com migration. Em `create_course`, grave o UUID junto com os conteúdos iniciais. Passe-o a `run_course_generation(*, storage: Storage, course_id: uuid.UUID, generation_id: uuid.UUID)`. Ajuste os testes de T28 que chamam a função, conferem o agendamento ou mudam `running` para `pending` diretamente. Cubra a tarefa vencida pelo caminho de expiração e retry. Linhas antigas com trabalho incompleto e sem UUID entram na mesma recuperação de 10 minutos.

Use a linha de `Course` para coordenar as transações de retry, expiração, reserva, publicação e encerramento. Depois de pegar o lock, leia o UUID e os estados do banco. A tarefa só altera dados enquanto o UUID confere e o trabalho não venceu.

1. Indexe só os documentos ainda não `indexed`. Acrescente a `index_document` um parâmetro opcional para validar a geração antes de gravar `processing`, os chunks ou uma falha. A validação pega o lock do curso na mesma sessão da gravação. Se a geração perdeu a identificação, encerre sem cair no tratamento de falha de indexação. O caminho sem esse parâmetro mantém o contrato atual de `index_document`.
2. Dentro do lock, reserve o próximo `pending` pela ordem de `position` com o `UPDATE` de T28. Confirme a transação antes de chamar o Gemini. Depois de cada saída, procure a próxima com uma consulta nova. O lock vale para a transação de reserva, sem manter outra conexão presa durante a geração.
3. Antes de publicar ou gravar uma falha de geração, confirme o UUID, o prazo e o estado `running` sob o lock. Preserve a recuperação de uma reserva que falhou antes do `commit`: ela só pode marcar como `failed` um conteúdo ainda `pending` da mesma geração. Mantenha o lock até o `commit` de `publish_content`, desde antes de gravar o JSON no armazenamento. Uma tarefa vencida perde o direito de gravar JSON, citações, chunks ou o erro de uma tentativa posterior. A leitura do armazenamento e as chamadas ao Gemini ficam fora do lock.
4. Sob o mesmo lock, se a fila acabou, aplique a condição de `_finish_course` e limpe o UUID na mesma transação. Se a indexação falhar, aplique a falha aos conteúdos pendentes e encerre a tarefa em uma transação. Mova os `commit` internos desses passos para a transação do chamador. Um retry que chega antes do encerramento entra na fila atual. Um retry que chega depois cria a próxima identificação e agenda uma tarefa.

Se um documento em processamento ficar sem tarefa, a recuperação o marca `failed` para a próxima tentativa reindexá-lo. Nenhum resultado publicado é removido.

## Recuperação sem depender de leituras

Crie `expire_stalled_courses` em `course_generation.py`. Chame no início do `lifespan` de `courses.router` e depois a cada 30 segundos, com sessão própria e SQL síncrono em uma thread. Encerre o laço no shutdown e registre falhas de banco para tentar no próximo ciclo.

Para cada curso com conteúdo ativo, pegue o lock da linha de `Course`, pule linhas já bloqueadas por outro processo e recalcule o prazo sob o lock. Se o maior `course_content.updated_at` do curso tem pelo menos dez minutos, marque os conteúdos `pending` e `running` e os documentos `processing` como `failed`, com "A geração foi interrompida. Tente novamente." Limpe o UUID e aplique a condição de `_finish_course` na mesma transação. Ao atingir o prazo, uma tarefa ainda viva também perde o direito de gravar. O estado pode aparecer na tela no próximo ciclo de recuperação, seguido da próxima consulta do frontend.

`GET /api/v1/courses/` e `GET /api/v1/courses/{course_id}` continuam só lendo. O prazo é do curso, contado desde a última mudança de estado de qualquer conteúdo. Um `pending` antigo espera a vez enquanto o curso tem progresso recente.

## Documentação

Em [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md), ajuste a linha `course` em "Os estados tornam a tarefa de fundo observável", as linhas "Processo cai durante a geração" e "Nova tentativa" e os parágrafos sobre a regra dos 10 minutos. Explique a identificação da tarefa, a recuperação periódica e a transição de `failed` para `initializing`. Em [`criar-curso.md`](../product-specs/criar-curso.md), atualize "Nova tentativa" com o botão por conteúdo e o reaproveitamento dos documentos indexados.

## Cenários de teste e aceite

- [ ] Em `test_courses_retry.py` novo, confira HTTP 202, a transição e o agendamento só ao abrir uma nova fila. Confira HTTP 409 para conteúdo `pending`, `running` ou `succeeded`, HTTP 404 nos casos de posse e IDs, HTTP 401 sem token e HTTP 503 sem armazenamento. Nos erros, o curso e o conteúdo mantêm os estados e nenhuma tarefa é agendada.
- [ ] Em `test_course_generation.py`, use PostgreSQL e duas sessões. Enquanto a tarefa está gerando outra saída, faça retry da que falhou. A mesma tarefa gera a saída recolocada na fila e duas requisições sobre o mesmo `failed` não reservam duas vezes.
- [ ] No mesmo arquivo, avance o relógio controlado com a tarefa parada em indexação ou geração. Rode a recuperação sem fazer GET. Confira os estados e a mensagem, o resultado anterior intacto e o curso `ready` quando já publicou algo. Volte a tentar, solte a tarefa vencida e confira que ela não grava chunks, JSON, citações nem erro da tentativa atual. Um curso ainda dentro do prazo, inclusive com algum `pending` antigo, permanece ativo.
- [ ] Confira que a recuperação roda pelo `lifespan` e que as duas rotas GET não alteram estados. Depois de uma falha de indexação, a nova tentativa reindexa o documento que falhou e reaproveita os `indexed`.
- [ ] Em `content-retry.spec.ts` novo, use os seeds de `course.spec.ts`. Confira o botão no alerta de uma saída e só no cartão que falhou quando há várias. Com `page.route`, mantenha o POST em andamento para conferir um único envio, simule HTTP 202 e o GET seguinte com o conteúdo `pending` e confira o estado em fila. Simule um HTTP 409 e confira o toast.
- [ ] Os testes automatizados dispensam Gemini e OCI. Passe os hooks, o backend com a cobertura exigida e o lint e build do frontend. Mire menos de 400 linhas escritas à mão. No PR, se houver credenciais de desenvolvimento, registre também a recuperação de um curso durante uma reinicialização e a nova tentativa pela tela.
