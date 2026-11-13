# Tickets

Cada arquivo `TNN-*.md` desta pasta é uma unidade de trabalho que um agente executa sozinho, do branch ao PR. O ticket é o prompt: ele traz o contexto, o contrato, os arquivos e os critérios de aceite.

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

Um ticket sem bloqueio aberto está na onda 1. A onda de um ticket é a maior onda entre seus bloqueios, mais um. Tickets da mesma onda rodam ao mesmo tempo.

Um ticket só começa quando todos os seus bloqueios estão no `master`. Cada branch nasce do `origin/master` atualizado.

## Fluxo de todo ticket

1. Leia o ticket inteiro, o `AGENTS.md` e os documentos que o ticket cita.
2. Atualize o `master` e crie o branch `tNN-descricao-curta` a partir de `origin/master`.
3. Em ticket de backend, prepare o banco do worktree:

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

## Regras de escrita de tickets

- Não existe ticket só de testes. Os testes entram no ticket do código.
- Migration e modelo ficam no mesmo ticket.
- Cada ticket gera um PR que uma pessoa revisa em minutos. O alvo é ficar abaixo de 400 linhas.
- As dependências ficam em `blocked_by`. Ninguém as deduz do título.
- Um ticket que entrega um módulo sem uso imediato traz a interface exata na seção "Contrato". O ticket que usa o módulo repete a mesma interface.

## Ondas

Os tickets da onda 1 estão escritos. Os demais são escritos quando a onda anterior termina, porque a onda anterior muda detalhes.

| Onda | Ticket | Entrega | Bloqueado por |
| --- | --- | --- | --- |
| 1 | T02 | API de leitura: setores, lista de cursos, curso. Seed de desenvolvimento | - |
| 1 | T03 | Busca vetorial dos 8 chunks mais próximos | - |
| 1 | T04 | Nota de fidelidade e decisão de publicar | - |
| 1 | T05 | Modelos do JSON de tutorial, flashcards e quiz | - |
| 1 | T06 | Navegação no topo, fontes, cores e base da tela "Novo curso" | - |
| 1 | T11 | Limpeza do repositório para agentes | - |
| 1 | T12 | Medir o plano gratuito do Gemini e conferir o bucket da OCI | - |
| 1 | T13 | Escolher os três documentos da demonstração | - |
| 1 | T14 | Módulo de armazenamento na OCI | - |
| 1 | T15 | Módulo de acesso ao Gemini | - |
| 1 | T16 | Leitura e validação de documentos `.md` | - |
| 2 | T07 | Novo curso, passo 1: documentos e texto digitado | T06 |
| 2 | T17 | Tela "Cursos" | T02, T06 |
| 2 | T18 | Tela "Curso": estados, metadados, fidelidade e trechos citados | T02, T06 |
| 2 | T19 | Indexação: chunks e embeddings | T14, T15, T16 |
| 2 | T20 | Agente `escreve`: tutorial | T05, T15 |
| 2 | T21 | Agente `revisa` | T04, T15 |
| 2 | T22 | Publicação: JSON na OCI e transação no banco | T04, T05, T14 |
| 2 | T23 | API de criação de curso | T02, T14, T16 |
| 2 | T37 | Leitura de PDF com texto | T16 |
| 3 | T08 | Leitor de tutorial | T18 |
| 3 | T09 | Leitor de flashcards | T18 |
| 3 | T10 | Leitor de quiz com correção | T18 |
| 3 | T24 | Grafo de geração: escreve, revisa, reescreve uma vez | T20, T21 |
| 3 | T25 | Agente `escreve`: flashcards | T20 |
| 3 | T26 | Agente `escreve`: quiz | T20 |
| 3 | T27 | Novo curso, passos 2 e 3, e envio | T07, T23 |
| 4 | T28 | Tarefa de fundo, de ponta a ponta | T03, T19, T22, T23, T24 |
| 4 | T29 | Etapa `planeja` | T24 |
| 4 | T30 | Casos de avaliação da busca e do revisor | T03, T24 |
| 4 | T31 | Teste da jornada completa no navegador | T08, T09, T10, T17, T27 |
| 5 | T32 | Nova tentativa e regra dos 10 minutos | T28 |
| 5 | T33 | Exclusão de curso com limpeza na OCI | T28 |
| 5 | T34 | Rodar os cenários da demonstração e guardar os JSON | T13, T25, T26, T28, T37 |
| 5 | T35 | README, diagrama e guia de instalação | T28 |
| 5 | T36 | Deploy na VM da OCI (opcional) | T28 |

O `id` T01 foi retirado. As dependências e as configurações que ele traria entram em T14 e T15.

O caminho mais longo é T15, T20, T24, T28, T34. Quando vários PRs esperam revisão, revise esses primeiro.
