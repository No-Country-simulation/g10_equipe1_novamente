---
id: T33
title: Exclua cursos e contas e conclua a limpeza dos arquivos na OCI
blocked_by: [T28]
touches:
  - backend/app/models.py
  - backend/app/alembic/versions/
  - backend/app/services/course_deletion.py
  - backend/app/api/routes/courses.py
  - backend/app/api/routes/users.py
  - backend/tests/conftest.py
  - backend/tests/services/test_course_deletion.py
  - backend/tests/api/routes/test_courses_delete.py
  - backend/tests/api/routes/test_users.py
  - frontend/src/components/Course/DeleteCourse.tsx
  - frontend/src/components/Course/CourseSummary.tsx
  - frontend/src/client/
  - frontend/tests/course-delete.spec.ts
  - docs/ARCHITECTURE.md
  - docs/product-specs/criar-curso.md
  - docs/product-specs/telas.md
executor: agente
size: 5
---

# T33 - Exclua cursos e contas e conclua a limpeza dos arquivos na OCI

`DELETE /api/v1/users/me` já apaga a conta e seus cursos no banco. Os documentos originais e os JSON publicados ficam na OCI, com as chaves descritas na [especificação de armazenamento](../../product-specs/pacote-json-e-armazenamento.md). A [especificação de criação](../../product-specs/criar-curso.md) permite excluir um curso quando ele sai de geração e aplica a mesma regra aos cursos da conta. A [arquitetura](../../ARCHITECTURE.md) define a ordem, banco primeiro e OCI depois. Guarde a pendência no banco antes de responder, para que a limpeza possa terminar mesmo se a OCI falhar ou o backend cair.

## API e transações

Crie `DELETE /api/v1/courses/{course_id}` como `delete_course`, depois de `read_course`. Use `CurrentUser`. Filtre pela posse e bloqueie a linha de `Course` com `SELECT ... FOR UPDATE`. Se a consulta não encontrar o curso, responda HTTP 404 com "Curso não encontrado." Depois de pegar o lock, consulte os estados dos conteúdos:

- Se algum está `pending` ou `running`, responda HTTP 409 com "Espere a geração terminar para excluir o curso." Mantenha curso, dados e arquivos.
- Senão, apague o curso e grave a pendência de limpeza na mesma transação. As chaves estrangeiras apagam documentos, chunks, conteúdos e citações. Responda HTTP 204 sem corpo após o `commit`.

Em `delete_user_me` de `users.py`, bloqueie a linha da conta e depois as linhas de seus cursos, em ordem de ID. Se a conta sumiu após a autenticação, responda HTTP 404 com "User not found". Consulte os estados depois de obter os locks. Se qualquer curso estiver na fila ou em geração, rejeite o pedido inteiro com HTTP 409 e "Espere a geração dos seus cursos terminar para excluir a conta." Se puder excluir, grave uma pendência por curso e apague o usuário em uma transação. Use a cascata do banco. Preserve HTTP 200 com `Message(message="User deleted successfully")`.

Em `create_course`, confirme e bloqueie a linha do dono antes do primeiro `put`, dentro da transação que cria o curso. Se a conta sumiu desde a autenticação, responda HTTP 404 com "User not found", como `get_current_user`. Assim uma exclusão de conta concorrente espera a criação ficar visível ou impede que ela grave arquivos. Quando T32 estiver integrado, o retry e a exclusão usam o mesmo lock na linha de `Course`. Se o retry vencer, a exclusão vê o estado ativo. Se a exclusão vencer, o retry não encontra o curso.

Gere `CoursesService.deleteCourse` com `bash scripts/generate-client.sh`.

## Limpeza persistente

Adicione a tabela `course_object_cleanup`, com modelo `CourseObjectCleanup` e migration. Guarde `course_id` como chave primária, sem chave estrangeira, e `next_attempt_at` em UTC. A linha precisa sobreviver ao curso. O cliente da OCI não participa da transação da API.

Crie `course_deletion.py` para compartilhar a gravação das pendências e processá-las. No `lifespan` de `users.router`, inicie a limpeza no startup e volte a procurar trabalho a cada 30 segundos. Use sessão própria e operações síncronas em uma thread. O shutdown encerra o laço. A limpeza usa `get_storage`, com o `dependency_overrides` do app quando configurado para testes.

1. Selecione uma pendência vencida com `FOR UPDATE SKIP LOCKED`, em ordem de `next_attempt_at` e ID. Trabalhe em uma pendência por transação, para que outros processos possam limpar os outros cursos.
2. Use `Storage.list(course_prefix(course_id))` e `Storage.delete` para remover as chaves do prefixo. Um objeto já ausente conta como removido. Apague a pendência só depois que a listagem e todas as exclusões concluírem com sucesso.
3. Se obter o armazenamento, listar ou apagar falhar, mantenha a pendência, adie a próxima tentativa por pelo menos um minuto e registre `course_id`, operação, tipo do erro e chave quando houver. Continue com os outros cursos. Se o processo parar no meio, a próxima execução pode repetir as exclusões. Registre só metadados no log.
4. Se a transação falhar, registre a falha e deixe o próximo ciclo tentar. Os ciclos processam um lote pequeno para dar vez a outros cursos. Uma falha permanente mantém a pendência visível no banco até a configuração voltar a funcionar.

O sucesso da API confirma que o curso ou a conta sumiu do produto e que a limpeza foi registrada. A conclusão na OCI pode levar mais tempo. O teste da API deve conferir a pendência antes de acionar a limpeza.

## Tela do curso

Crie `DeleteCourse.tsx` e monte o componente no `CourseSummary`, que aparece em cursos com uma ou mais saídas. Use os componentes de diálogo e toast de `DeleteConfirmation.tsx`.

- "Excluir curso" abre "Excluir este curso?", com os botões "Cancelar" e "Excluir". Informe que a ação apaga o curso, os documentos e os conteúdos e é irreversível.
- Enquanto `hasActiveContent(course.contents)` for verdadeiro, desabilite o botão e mostre "Espere a geração terminar para excluir o curso."
- Em sucesso, mostre "Curso excluído.", volte a `/courses`, remova a consulta `courseQueryKey(courseId)` e invalide `coursesQueryKey`. Em erro, mostre o detalhe da API e mantenha a página. Desabilite o envio enquanto o pedido estiver em andamento.

## Documentação

Em [`docs/ARCHITECTURE.md`](../../ARCHITECTURE.md), ajuste as três linhas de exclusão em "Falhas e recuperação" para explicar a regra de geração ativa, o registro da pendência e a nova tentativa da limpeza. Em [`criar-curso.md`](../../product-specs/criar-curso.md), atualize "Excluir um curso" com a ação na tela, a mesma regra para a conta e a limpeza em segundo plano. Em [`telas.md`](../../product-specs/telas.md), acrescente a exclusão à linha "Curso".

## Cenários de teste e aceite

- [ ] Em `test_courses_delete.py` novo, HTTP 204 para o dono de um curso inativo, HTTP 404 para curso ausente ou de outra pessoa, HTTP 401 sem sessão e HTTP 409 com conteúdo `pending` ou `running`. Confira a cascata e a pendência na mesma transação. Se o `commit` falhar, o curso e os arquivos ficam e não há pendência. Confira que a API aceita a exclusão sem armazenamento configurado.
- [ ] Em `test_users.py`, confirme o HTTP 200 existente e uma pendência por curso apagado. Um único curso ativo bloqueia a exclusão de toda a conta, com HTTP 409. Teste a criação concorrente com duas sessões. A conta só some se todos os cursos que chegaram ao banco puderem ser excluídos.
- [ ] Em `test_course_deletion.py` novo, use PostgreSQL e `InMemoryStorage`. Um erro de configuração, listagem ou exclusão mantém a pendência e não impede a limpeza de outro curso. Após uma nova execução com a OCI disponível, o prefixo fica vazio e a pendência desaparece. Um prefixo alheio permanece intacto. Teste o `lifespan` com a instância de teste e um novo ciclo após reinício.
- [ ] Em `conftest.py`, isole a resolução de armazenamento do limpador nos testes backend para que as credenciais do `.env` não sejam usadas. Mantenha a resolução e as fixtures das rotas de criação. Use um armazenamento controlado nos testes do `lifespan`.
- [ ] Em `course-delete.spec.ts` novo, use os seeds de `course.spec.ts`. Confira o botão no resumo com uma e várias saídas, o cancelamento e a exclusão pela rota real com retorno à lista. Confira o botão desabilitado em geração e simule HTTP 409 depois de abrir o diálogo para conferir o toast.
- [ ] Passe os hooks, os testes do backend com a cobertura exigida e o lint e build do frontend. Mire menos de 400 linhas escritas à mão. Se houver acesso ao bucket de desenvolvimento, crie um curso descartável, liste seu prefixo antes e depois de excluí-lo pela tela e registre o resultado no PR.

## Verificação do aceite

- PR revisado: [#47](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/47), integrado no commit `5054fb0`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Revisão automática sobre o commit `351f061`: quatro achados, corrigidos no commit `7b49a5f`. Os testes resolvem o armazenamento do limpador em memória, o tratamento morto de `ObjectNotFoundError` saiu, um teste cobre a exclusão da conta que confirma antes da criação do curso e a tela recarrega o curso após HTTP 409.
- Testes: 413 testes do backend passaram, com 99% de cobertura, e 128 testes do Playwright. O Alembic mostrou um único head.
- Verificação com a OCI de desenvolvimento: a exclusão pela tela retornou HTTP 204 e a listagem do prefixo do curso ficou vazia.
