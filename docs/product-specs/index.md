# Especificações de produto do NovaMente

O NovaMente transforma um documento técnico em conteúdos de estudo adaptados a um público, em minutos, sem inventar fatos que o documento não traz.

Esta pasta descreve o que o produto faz e para quem. Cada arquivo trata de um assunto. A forma como o sistema é construído fica em [`ARCHITECTURE.md`](../../ARCHITECTURE.md), e o esquema do banco fica em [`docs/generated/db-schema.md`](../generated/db-schema.md).

## Leia nesta ordem

| Arquivo | Responde a |
| --- | --- |
| [`visao-e-publico.md`](visao-e-publico.md) | Que problema o produto resolve e para quem? |
| [`escopo-do-mvp.md`](escopo-do-mvp.md) | O que entra na entrega do hackathon e o que fica fora? |
| [`criar-curso.md`](criar-curso.md) | Como uma pessoa cria um curso a partir de um documento? |
| [`conteudos-e-formatos.md`](conteudos-e-formatos.md) | O que é um tutorial, um conjunto de flashcards e um quiz? |
| [`fidelidade-e-qualidade.md`](fidelidade-e-qualidade.md) | Como o produto garante que o conteúdo é fiel ao documento? |
| [`pacote-json-e-armazenamento.md`](pacote-json-e-armazenamento.md) | Que JSON o produto entrega e onde ele fica guardado? |
| [`telas.md`](telas.md) | Que telas a pessoa vê? |
| [`demonstracao.md`](demonstracao.md) | O que a equipe mostra à banca? |
| [`decisoes-pendentes.md`](decisoes-pendentes.md) | O que a equipe ainda precisa decidir? |

## Como ler o estado de cada item

- **Existe**: está no branch `master`.
- **A construir**: a equipe decidiu, mas o código ainda não existe.
- **Pendente**: depende de uma decisão em [`decisoes-pendentes.md`](decisoes-pendentes.md).

## O que vale em caso de conflito

1. O briefing do hackathon define o que a banca avalia.
2. `docs/generated/db-schema.md` define os dados que o produto guarda.
3. Esta pasta define o comportamento do produto.

Um conflito entre essas fontes vira um item em `decisoes-pendentes.md`. Ninguém resolve um conflito só no código.

O JSON de exemplo do briefing é só um exemplo. O produto usa nomes em inglês e uma resposta própria.

## Fontes usadas e o que ainda vale em cada uma

| Fonte | Onde está | O que ainda vale | O que ficou velho |
| --- | --- | --- | --- |
| `README.md` | Raiz | A lista de tecnologias, em parte | A descrição do produto, que fala em pessoas neurodivergentes, modo foco e roadmaps adaptativos |
