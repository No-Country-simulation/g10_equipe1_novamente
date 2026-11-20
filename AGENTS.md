# Mapa da base de conhecimento

Este arquivo indica onde achar cada informação do NovaMente. Leia só o documento que a tarefa pede. Arquivos fora de `docs/` não valem (veja o fim deste arquivo).

O NovaMente transforma um documento técnico em conteúdos de estudo fiéis a ele. A base de conhecimento fica em `docs/`.

## Por onde começar

| Se você precisa de... | Leia |
| --- | --- |
| Escrever uma resposta, relatório, `commit` ou PR | [`docs/WRITING.md`](docs/WRITING.md) |
| Executar um ticket | [`docs/tickets/README.md`](docs/tickets/README.md), depois o ticket |
| Entender o que o produto faz | [`docs/product-specs/index.md`](docs/product-specs/index.md) |
| Entender como o sistema é construído | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Saber que dados o banco guarda | [`docs/generated/db-schema.md`](docs/generated/db-schema.md) |

## Escrita

- [`docs/WRITING.md`](docs/WRITING.md): regras de escrita para respostas, relatórios, mensagens de `commit`, descrições de PR e documentação. Vale para toda sessão de agente.

## Arquitetura

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): as cinco partes do sistema, o caminho de uma geração e as regras que o código mantém.
- [`docs/system-diagram/arquitetura.png`](docs/system-diagram/arquitetura.png): diagrama da arquitetura. A fonte editável é `arquitetura.excalidraw`, na mesma pasta.

## Esquema do banco (gerado)

- [`docs/generated/db-schema.md`](docs/generated/db-schema.md): as sete tabelas, o que cada uma guarda e as regras de integridade.
- [`docs/generated/erd.svg`](docs/generated/erd.svg): diagrama entidade-relacionamento.

Não edite estes arquivos para mudar o esquema. O código em `backend/app/models.py` define as tabelas.

## Especificações de produto

O índice [`docs/product-specs/index.md`](docs/product-specs/index.md) lista os arquivos na ordem de leitura e define o que vale em caso de conflito.

| Arquivo | Responde a |
| --- | --- |
| [`visao-e-publico.md`](docs/product-specs/visao-e-publico.md) | Que problema o produto resolve e para quem? |
| [`escopo-do-mvp.md`](docs/product-specs/escopo-do-mvp.md) | O que entra na entrega do hackathon e o que fica fora? |
| [`criar-curso.md`](docs/product-specs/criar-curso.md) | Como uma pessoa cria um curso a partir de um documento? |
| [`conteudos-e-formatos.md`](docs/product-specs/conteudos-e-formatos.md) | O que é um tutorial, um conjunto de flashcards e um quiz? |
| [`fidelidade-e-qualidade.md`](docs/product-specs/fidelidade-e-qualidade.md) | Como o produto garante que o conteúdo é fiel ao documento? |
| [`pacote-json-e-armazenamento.md`](docs/product-specs/pacote-json-e-armazenamento.md) | Que JSON o produto entrega e onde ele fica guardado? |
| [`telas.md`](docs/product-specs/telas.md) | Que telas a pessoa vê? |
| [`demonstracao.md`](docs/product-specs/demonstracao.md) | O que a equipe mostra à banca? |

## Design

- [`docs/design/telas-finais/`](docs/design/telas-finais/README.md): capturas das Telas finais do Drive, a única fonte de layout. O ticket de cada tela cita as capturas que usa.

## Tickets

Cada ticket `TNN-*.md` é uma unidade de trabalho que um agente executa do branch ao PR. [`docs/tickets/README.md`](docs/tickets/README.md) traz o fluxo, as verificações, as regras de conflito e a tabela de ondas com as dependências.

Tickets escritos (onda 1):

| Ticket | Entrega |
| --- | --- |
| [`T02`](docs/tickets/completed/T02-api-de-leitura-de-cursos.md) | API de leitura de setores e cursos, e seed de desenvolvimento |
| [`T03`](docs/tickets/completed/T03-busca-vetorial.md) | Busca vetorial dos 8 chunks mais próximos |
| [`T04`](docs/tickets/completed/T04-nota-de-fidelidade.md) | Nota de fidelidade e decisão de publicar |
| [`T05`](docs/tickets/completed/T05-modelos-do-json-de-conteudo.md) | Modelos do JSON de tutorial, flashcards e quiz |
| [`T06`](docs/tickets/completed/T06-navegacao-no-topo.md) | Navegação no topo, fontes, cores e base da tela "Novo curso" |
| [`T12`](docs/tickets/T12-medir-gemini-e-conferir-oci.md) | Medir o plano gratuito do Gemini e conferir o bucket da OCI |
| [`T13`](docs/tickets/T13-documentos-da-demonstracao.md) | Escolher os três documentos da demonstração |
| [`T14`](docs/tickets/completed/T14-armazenamento-na-oci.md) | Módulo de armazenamento na OCI |
| [`T15`](docs/tickets/completed/T15-acesso-ao-gemini.md) | Módulo de acesso ao Gemini |
| [`T16`](docs/tickets/completed/T16-leitura-de-documentos-md.md) | Leitura e validação de documentos `.md` |

Tickets escritos (onda 2):

| Ticket | Entrega |
| --- | --- |
| [`T07`](docs/tickets/completed/T07-novo-curso-passo-1.md) | Novo curso, passo 1: documentos e texto digitado |
| [`T17`](docs/tickets/completed/T17-tela-cursos.md) | Tela "Cursos" |
| [`T18`](docs/tickets/completed/T18-tela-curso.md) | Tela "Curso": cartões de conteúdo, estados e metadados |
| [`T19`](docs/tickets/completed/T19-indexacao.md) | Indexação: chunks e embeddings |
| [`T20`](docs/tickets/completed/T20-agente-escreve-tutorial.md) | Agente `escreve`: tutorial |
| [`T21`](docs/tickets/completed/T21-agente-revisa.md) | Agente `revisa` |
| [`T22`](docs/tickets/completed/T22-publicacao.md) | Publicação: JSON na OCI e transação no banco |
| [`T23`](docs/tickets/completed/T23-api-de-criacao-de-curso.md) | API de criação de curso |
| [`T37`](docs/tickets/completed/T37-leitura-de-pdf.md) | Leitura de PDF com texto |
| [`T39`](docs/tickets/completed/T39-ritmo-dos-limites-do-gemini.md) | Ritmo dos limites por minuto do Gemini |

Tickets escritos da onda 3:

| Ticket | Entrega |
| --- | --- |
| [`T08`](docs/tickets/T08-leitor-de-tutorial.md) | Leitor de tutorial |
| [`T09`](docs/tickets/T09-leitor-de-flashcards.md) | Leitor de flashcards |
| [`T10`](docs/tickets/completed/T10-leitor-de-quiz.md) | Leitor de quiz com justificativa após a resposta |
| [`T40`](docs/tickets/completed/T40-regras-de-fidelidade.md) | Revisão de conteúdo, cobertura do foco e publicação só com afirmações sustentadas |
| [`T24`](docs/tickets/T24-grafo-de-geracao.md) | Grafo de geração: escreve, revisa, reescreve uma vez |
| [`T25`](docs/tickets/completed/T25-agente-escreve-flashcards.md) | Agente `escreve`: flashcards |
| [`T27`](docs/tickets/completed/T27-novo-curso-passos-2-e-3.md) | Novo curso, passos 2 e 3, e envio |
| [`T38`](docs/tickets/completed/T38-tela-curso-avaliacao.md) | Tela "Curso": fidelidade, clareza, observações e trechos citados |

Na onda 4, só o [T26](docs/tickets/T26-agente-escreve-quiz.md), agente `escreve` para quiz, está escrito. Os demais tickets das ondas 4 a 6 estão na [tabela de ondas](docs/tickets/README.md#ondas).

## Fora de `docs/`

Ignore os arquivos fora de `docs/`, como `README.md`, `CONTRIBUTING.md`, `development.md` e `deployment.md`. Eles vêm do template ou estão velhos e não descrevem o projeto. Só o código em `backend/` e `frontend/` e os documentos de `docs/` valem.
