# Tickets

Cada arquivo `TNN-*.md` desta pasta é uma unidade de trabalho que uma pessoa ou um agente executa do branch ao PR. O ticket traz o contexto, o contrato, os arquivos e os critérios de aceite.

Uma pessoa revisa e faz o merge de cada PR. Nenhum agente faz merge.

## Como ler um ticket

Cada ticket abre com um cabeçalho:

| Campo | Significado |
| --- | --- |
| `id` | Identificador fixo. Um `id` nunca é reutilizado. |
| `title` | O que o ticket entrega, no imperativo. |
| `blocked_by` | Tickets que precisam estar no `master` antes deste começar. |
| `touches` | Arquivos e pastas que o ticket cria ou altera. |
| `executor` | `agente` ou `pessoa`. Um ticket de `pessoa` pede chaves, contas ou uma decisão. |
| `size` | Esforço de 1 a 5. Um ticket acima de 5 é dividido. |

O ticket não guarda estado. O estado vem do GitHub:

| Estado | Sinal |
| --- | --- |
| A fazer | Não existe branch `tNN-*` no remoto. |
| Em andamento | Existe branch `tNN-*`, sem PR. |
| Em revisão | Existe PR aberto do branch `tNN-*`. |
| Pronto | O PR do branch `tNN-*` está no `master`. |

## Como a ordem é calculada

No planejamento inicial, um ticket sem bloqueio entra na onda 1. Os demais entram uma onda depois de seu bloqueio mais tardio. T40 entrou depois do planejamento e foi incluído na onda 3, sem bloqueios. Nessa onda, comece T40 em paralelo com os tickets que já podem rodar. Comece T24 e T25 depois do merge de T40.

Um ticket só começa quando todos os seus bloqueios estão no `master`. Cada branch nasce do `origin/master` atualizado.

## Fluxo de todo ticket

1. Leia o ticket inteiro, o `AGENTS.md` e os documentos que o ticket cita.
2. Atualize o `master` e crie o branch `tNN-descricao-curta` a partir de `origin/master`.
3. Prepare o banco e o `.env` do worktree. Todo ticket precisa deles, porque os testes Playwright do frontend rodam contra o backend:

    ```bash
    bash scripts/worktree-setup.sh TNN
    ```

4. Implemente só o escopo do ticket. Os testes entram no mesmo PR.
5. Rode as verificações da seção abaixo e corrija todas as falhas.
6. Faça commits no padrão do histórico (`feat:`, `fix:`, `docs:`, `test:`), em português.
7. Abra o PR contra `master`. O título cita o `id`, por exemplo `feat: expõe a leitura de cursos (T02)`. A descrição diz o problema, a solução e como testar.
8. Acompanhe o CI e corrija as falhas. Pare quando o CI estiver verde.

Se o ticket contradiz o código ou uma especificação, pare e relate a contradição no PR ou na sessão. Não resolva a contradição só no código.

## Verificações antes do PR

Para qualquer ticket, rode os hooks sobre o que mudou:

```bash
uv run prek run --from-ref origin/master --to-ref HEAD
```

Para ticket de backend, rode os testes e confira a cobertura. O CI exige 90%.

```bash
cd backend && uv run bash scripts/tests-start.sh && uv run coverage report --fail-under=90
```

Para ticket de frontend, rode o lint e o build. Os testes Playwright rodam no CI, porque usam portas fixas.

```bash
cd frontend && bun run lint && bun run build
```

## Um banco por worktree

Vários agentes rodam na mesma máquina. Todos usam o mesmo servidor PostgreSQL, na porta 5432, e cada worktree usa um banco próprio.

Suba o servidor uma vez, no checkout principal:

```bash
docker compose up -d --wait db
```

Em cada worktree, `scripts/worktree-setup.sh TNN` cria o banco `app_tnn`, aponta o `.env` para ele e roda as migrations.

## Arquivos que mais de um ticket altera

Dois tickets da mesma onda não editam o mesmo trecho de um arquivo escrito à mão. Quando dois tickets precisam do mesmo arquivo, cada ticket diz onde inserir as linhas.

Estes arquivos são gerados. Em um conflito, nunca junte as duas versões à mão. Faça `rebase` no `master` e gere o arquivo de novo:

| Arquivo | Como gerar |
| --- | --- |
| `uv.lock` | `uv lock` |
| `bun.lock` | `bun install` |
| `frontend/src/client/` | `bash scripts/generate-client.sh` |
| `frontend/src/routeTree.gen.ts` | `cd frontend && bun run build` |

Vários tickets criam `backend/app/services/__init__.py`, `backend/tests/services/__init__.py` e `backend/tests/core/__init__.py`. Crie cada um vazio. Arquivos idênticos não geram conflito.

T17 criou `frontend/src/lib/courses.ts` e `frontend/tests/utils/course.ts`, que T18 também usa. T18 não edita esses arquivos.

## Regras de escrita de tickets

- Os testes de cada mudança entram no ticket do código. T30 e T31 cobrem avaliações e testes que atravessam vários tickets.
- Migration e modelo ficam no mesmo ticket.
- Cada ticket gera um PR que uma pessoa revisa em minutos. O alvo é ficar abaixo de 400 linhas.
- As dependências ficam em `blocked_by`. Ninguém as deduz do título.
- Um ticket que entrega um módulo sem uso imediato traz a interface exata na seção "Contrato". O ticket que usa o módulo repete a mesma interface.

## Ondas

Os tickets das ondas 1 a 5 estão escritos, além de T29, T30 e T41. Escreva os demais quando os contratos de que dependem estiverem definidos.

| Onda | Ticket | Entrega | Bloqueado por |
| --- | --- | --- | --- |
| 1 | T02 | API de leitura: setores, lista de cursos, curso. Seed de desenvolvimento | - |
| 1 | T03 | Busca vetorial dos 8 chunks mais próximos | - |
| 1 | T04 | Nota de fidelidade e decisão de publicar | - |
| 1 | T05 | Modelos do JSON de tutorial, flashcards e quiz | - |
| 1 | T06 | Navegação no topo, fontes, cores e base da tela "Novo curso" | - |
| 1 | T12 | Medir o plano gratuito do Gemini e conferir o bucket da OCI | - |
| 1 | T13 | Escolher os três documentos da demonstração | - |
| 1 | T14 | Módulo de armazenamento na OCI | - |
| 1 | T15 | Módulo de acesso ao Gemini | - |
| 1 | T16 | Leitura e validação de documentos `.md` | - |
| 2 | T07 | Novo curso, passo 1: documentos e texto digitado | T06 |
| 2 | T17 | Tela "Cursos" | T02, T06 |
| 2 | T18 | Tela "Curso": cartões de conteúdo, estados e metadados | T02, T06 |
| 2 | T19 | Indexação: chunks e embeddings | T14, T15, T16 |
| 2 | T20 | Agente `escreve`: tutorial | T03, T05, T15 |
| 2 | T21 | Agente `revisa` | T03, T04, T05, T15 |
| 2 | T22 | Publicação: JSON na OCI e transação no banco | T03, T04, T05, T14 |
| 2 | T23 | API de criação de curso | T02, T14, T16 |
| 2 | T37 | Leitura de PDF com texto | T16 |
| 2 | T39 | Ritmo dos limites por minuto do Gemini | T15 |
| 3 | T08 | Leitor de tutorial | T18 |
| 3 | T09 | Leitor de flashcards | T18 |
| 3 | T10 | Leitor de quiz com justificativa após a resposta | T18 |
| 3 | T40 | Revisão de conteúdo, cobertura do foco e publicação só com afirmações sustentadas | - |
| 3 | T24 | Grafo de geração: escreve, revisa, reescreve uma vez | T20, T21, T40 |
| 3 | T25 | Agente `escreve`: flashcards | T20, T40 |
| 3 | T27 | Novo curso, passos 2 e 3, e envio | T07, T18, T23, T37 |
| 3 | T38 | Tela "Curso": fidelidade, clareza, observações e trechos citados | T18 |
| 4 | T26 | Agente `escreve`: quiz | T25 |
| 5 | T28 | Tarefa de fundo para gerar os três formatos | T03, T19, T22, T23, T24, T26, T39 |
| 6 | T29 | Etapa `planeja` | T24, T28 |
| 6 | T30 | Avaliação da busca e do revisor, com medição de falsas reprovações | T03, T24, T28, T37 |
| 6 | T31 | Teste no navegador da criação à leitura do conteúdo gerado | T08, T09, T10, T17, T27, T28, T38 |
| 6 | T32 | Nova tentativa e regra dos 10 minutos | T28 |
| 6 | T33 | Exclusão de curso com limpeza na OCI | T28 |
| 6 | T36 | Deploy na VM da OCI (opcional) | T28 |
| 7 | T34 | Rodar os cenários da demonstração e guardar os JSON | T13, T25, T26, T28, T29, T37 |
| 7 | T35 | README, diagrama e guia de instalação | T28, T29 |
| 7 | T41 | Casos de avaliação sobre os documentos da demonstração e primeira medição | T13, T30 |

T39 saiu das medições de T12: a cota de embeddings conta cada texto como um pedido, e a indexação de um documento grande passava do limite por minuto. T28 passou a listar T39.

T38 saiu de T18, que passava de 5 pontos: T18 ficou com a página, os estados e os metadados, e T38 com a avaliação. T20, T21 e T22 passaram a listar T03, porque recebem o `RetrievedChunk` da busca. T21 passou a listar T05, porque recebe o conteúdo gerado.

O `id` T01 foi retirado. As dependências e as configurações que ele traria entram em T14 e T15. O `id` T11 também foi retirado: as correções de links e de instruções já estão feitas.

T40 saiu da verificação de 19/11/2026 com o Gemini. A decisão antiga aprovou um tutorial com dois fatos falsos e um tutorial que fugiu do assunto pedido. T24 e T25 usam o contrato novo de revisão.

T26 passou a esperar T25, e não T20: os dois editam as mesmas linhas de `writer.py` (`PROMPT_VERSION` e `FORMAT_INSTRUCTIONS`) e de `test_writer.py`. T25 já espera T40, então T26 recebe as regras de T40 por T25.

T08 muda os casos de tutorial em `frontend/tests/course.spec.ts`. T09 muda o caso de flashcards. Depois do `rebase`, o último dos dois remove `readerPlaceholder` se ficar sem uso.

Em `docs/product-specs/criar-curso.md`, T27 atualiza "O que a pessoa vê" e T40 atualiza "Erros que a pessoa pode ver".

T28 espera T26 para gerar todos os formatos que a API aceita. T31 cria um curso no navegador, espera a tarefa de fundo publicar um conteúdo e abre o leitor. O teste automatizado usa respostas controladas para o Gemini e a OCI.

T28 cria `PROMPT_VERSION` em `generation_graph.py`, e T29 acrescenta a versão de `planeja` à constante. T30 usa a mesma versão e a função `retrieve_chunks` de T28, além da leitura de PDF de T37.

Na onda 6, T29 e T30 editam `docs/ARCHITECTURE.md`. T29 edita o fluxo, as regras, os modelos de IA e a tabela de decisões. T30 edita a seção "Testes".

T30 entrega o script de avaliação e o formato dos casos. T41 executa o trabalho de avaliação que T13 cita: uma pessoa escreve os casos sobre os documentos escolhidos e registra a primeira medição com a versão de geração que ela usou.

T34 e T35 passaram a esperar T29. `ARCHITECTURE.md` diz que `planeja` entra antes da demonstração, e o diagrama de T35 precisa mostrar a etapa.

T28 libera T29, T30, T31, T32, T33 e T36. Priorize a revisão de T28 quando o PR estiver pronto.
