---
id: T12
title: Meça o plano gratuito do Gemini e confira o bucket da OCI
blocked_by: []
touches:
  - docs/ARCHITECTURE.md
executor: pessoa
size: 2
---

# T12 - Meça o plano gratuito do Gemini e confira o bucket da OCI

## Contexto

`docs/ARCHITECTURE.md` diz que os limites do plano gratuito do Gemini não foram conferidos e que a equipe ainda não escolheu o modelo de texto. Um curso com três saídas usa até 12 chamadas de texto e cerca de 100 embeddings por documento. Se o plano gratuito não comporta isso, a indexação (T19) e a tarefa de fundo (T28) mudam.

O armazenamento na OCI é o único requisito obrigatório de infraestrutura do briefing. Um bucket que funciona no primeiro dia tira o maior risco externo do projeto.

Este ticket é de uma pessoa, porque pede uma conta do Google AI Studio e uma conta da OCI. Ele não bloqueia nenhum outro ticket, mas o resultado pode mudar T19 e T28. Faça no primeiro dia.

## Escopo

Quatro respostas, registradas em `docs/ARCHITECTURE.md`.

### 1. O modelo de embeddings existe e devolve 768 dimensões?

O esquema fixa `gemini-embedding-2` e 768 dimensões. Peça um embedding de teste com a chave gratuita e confira o nome do modelo e o tamanho do vetor.

Se o nome estiver errado, pare e avise a equipe. O nome está no valor padrão de `source_document.embedding_model`, e a correção pede uma migration.

### 2. Quais são os limites do plano gratuito?

Anote, para o modelo de embeddings e para cada modelo de texto candidato:

- pedidos por minuto;
- pedidos por dia;
- tokens por minuto;
- quantos textos cabem em um pedido de embeddings.

### 3. Qual modelo de texto a equipe usa?

Escolha o modelo de texto do plano gratuito que aceita saída em JSON com schema e comporta 12 chamadas por curso. Esse valor vai para `GEMINI_GENERATION_MODEL`.

Confira o schema com uma chamada real. T05 e T15 já estão no `master`: com a chave e o modelo no `.env`, chame `app.core.llm.generate_structured` com `response_model=GeneratedTutorial`, de `app.services.content_schemas`, e um prompt curto. Anote:

- se a API aceitou o schema de `GeneratedTutorial`;
- se a resposta validou no model sem erro de tipo.

T20 e T21 foram escritos sem essa conferência. Se a API recusa o schema, avise a equipe antes de T24 começar. A segunda resposta decide o modo estrito do Pydantic (`strict=True`), que T05 e T20 deixaram em aberto.

### 4. O bucket funciona?

1. Crie o bucket privado `novamente-docs` em uma conta Always Free.
2. Crie uma API signing key para cada pessoa que desenvolve. Guarde a chave fora da pasta do repositório.
3. Envie, leia, liste e apague um arquivo. Se T14 já estiver no `master`, use `backend/scripts/verify_storage.py`. Senão, use a OCI CLI.
4. Anote o namespace e a região.

## Fora do escopo

- Bucket de produção e instance principal (T36).
- Mudar código. Se um limite pede mudança de desenho, abra a discussão com a equipe.

## Onde registrar

Em `docs/ARCHITECTURE.md`, seção "Modelos de IA":

- troque "A equipe ainda não escolheu o modelo" pelo modelo escolhido;
- troque "Os limites do plano gratuito do Gemini não foram conferidos" por uma tabela com os limites medidos e a data da medição;
- diga quantos cursos com três saídas cabem em um dia.

Na seção "Armazenamento de objetos", confirme o nome do bucket e anote a região.

Não escreva chave, OCID de usuário nem fingerprint no repositório.

Depois que T15 estiver no `master`, abra um PR de uma linha com o modelo escolhido como valor de `GEMINI_GENERATION_MODEL` em `.env.example`.

## Critérios de aceite

- [X] `docs/ARCHITECTURE.md` traz o modelo de texto, os limites medidos e a data.
- [X] O nome do modelo de embeddings e as 768 dimensões estão confirmados, ou a equipe foi avisada do erro.
- [X] Uma chamada real com `GeneratedTutorial` foi feita, e o resultado está anotado.
- [X] Um arquivo foi enviado, lido, listado e apagado em `novamente-docs`.
- [ ] Cada pessoa que desenvolve tem uma chave própria, fora do repositório.
- [ ] Se algum limite não comporta um curso com três saídas, a equipe sabe antes de T19 começar.

## Execução e encerramento

Verificações e medições consolidadas em 16–18/11/2026. As evidências apontam `gemini-embedding-2` com 768 dimensões e `gemini-3.5-flash-lite` como modelo de texto selecionado. A chamada estruturada com `GeneratedTutorial` validou no Pydantic. O teste de recuperação foi sintético e controlado; os resultados não garantem precisão em produção.

O bucket de desenvolvimento testado foi `novamente-docs`, na região `sa-saopaulo-1`, usando autenticação local por API signing key. PUT, GET, LIST e DELETE foram reportados como aprovados. A captura local confirma as configurações, mas não contém a saída das operações. Instance principal e publicação ponta a ponta continuam sem validação.

O [registro de evidências do T12](evidences/t12/T12-evidencias.md) detalha resultados, consumo, latências, quotas, ocorrências e limitações. Ele também registra divergências identificadas nos artefatos e as referências primárias.

**Recomendação:** encerrar o ticket quanto à seleção do modelo, às medições de quota e à verificação reportada do bucket. Manter a ressalva de que o resultado de PUT/GET/LIST/DELETE não tem log local de execução disponível e que o teto de 41 cursos por dia é teórico.
