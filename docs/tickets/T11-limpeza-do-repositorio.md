---
id: T11
title: Corrija as instruções e os links que desviam um agente
blocked_by: []
touches:
  - AGENTS.md
  - CONTRIBUTING.md
  - docs/ARCHITECTURE.md
  - docs/product-specs/index.md
  - docs/generated/db-schema.md
executor: agente
size: 1
---

# T11 - Corrija as instruções e os links que desviam um agente

## Contexto

Um agente lê `AGENTS.md` e `CONTRIBUTING.md` antes de trabalhar. Hoje os dois têm instruções erradas para este projeto, e alguns links da documentação apontam para arquivos que não existem. Cada um desses erros custa tempo de um agente em toda sessão.

## Escopo

Corrigir os cinco problemas da tabela abaixo. Só documentação.

| Arquivo | Problema | Correção |
| --- | --- | --- |
| `AGENTS.md` | A seção "ExecPlans" manda seguir `docs/PLANS.md`, que foi apagado. | Troque a seção por "Tickets": o trabalho segue `docs/tickets/README.md`, e o branch principal é `master`. |
| `CONTRIBUTING.md` | É o texto do template. Cita o repositório do template e diz que PRs feitos por IA são fechados. | Reescreva para este projeto, conforme a seção abaixo. |
| `docs/ARCHITECTURE.md` | Os links internos começam com `docs/`, mas o arquivo já está em `docs/`. A imagem aponta para `docs/assets/`, que não existe. | Use caminhos relativos a `docs/`: `generated/db-schema.md`, `product-specs/index.md`, `system-diagram/arquitetura.png` e `system-diagram/arquitetura.excalidraw`. |
| `docs/product-specs/index.md` | O link para `ARCHITECTURE.md` usa `../../`. | Use `../ARCHITECTURE.md`. |
| `docs/generated/db-schema.md` | O link para `ARCHITECTURE.md` usa `../../`. | Use `../ARCHITECTURE.md`. |

## Fora do escopo

- `README.md` da raiz (T35).
- `docs/product-specs/demonstracao.md` (T13) e `docs/product-specs/telas.md` (T06).
- `development.md` e `deployment.md`.
- Qualquer mudança de conteúdo nas especificações.

## Conteúdo do novo `CONTRIBUTING.md`

Um guia prático, em português, com até uma tela de texto:

1. O trabalho é dividido em tickets, em `docs/tickets/`. Agentes e pessoas seguem o mesmo fluxo, descrito em `docs/tickets/README.md`.
2. Todo PR vai contra `master`, cita o `id` do ticket no título e passa no CI.
3. Uma pessoa da equipe revisa e faz o merge. Nenhum agente faz merge.
4. A escrita segue `AGENTS.md`.
5. O ambiente de desenvolvimento está em `development.md`.

## Detalhes técnicos

- Siga as regras de escrita do próprio `AGENTS.md`.
- Confira cada link corrigido: o arquivo de destino existe no caminho novo.
- Procure outros links quebrados em `docs/` e em `AGENTS.md`. Corrija os que estiverem nos arquivos deste ticket. Liste os outros na descrição do PR.

## Critérios de aceite

- [ ] `AGENTS.md` não cita `docs/PLANS.md` nem ExecPlans.
- [ ] `CONTRIBUTING.md` não cita o template nem a regra de fechar PRs feitos por IA.
- [ ] Todo link relativo dos cinco arquivos aponta para um arquivo que existe.
- [ ] A imagem da arquitetura aparece em `docs/ARCHITECTURE.md` no GitHub.
- [ ] Os hooks passam.

## Cenários de teste

Não há teste automático. Rode este comando na raiz e confira que ele não devolve nada:

```bash
grep -rn "PLANS.md\|docs/assets\|\.\./\.\./ARCHITECTURE\|full-stack-fastapi-template/discussions" AGENTS.md CONTRIBUTING.md docs/ARCHITECTURE.md docs/product-specs/index.md docs/generated/db-schema.md
```
