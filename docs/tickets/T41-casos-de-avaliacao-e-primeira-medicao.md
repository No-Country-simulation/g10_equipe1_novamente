---
id: T41
title: Escreva os casos de avaliação sobre os documentos da demonstração e registre a primeira medição
blocked_by: [T13, T30]
touches:
  - examples/evals/
  - docs/product-specs/fidelidade-e-qualidade.md
executor: agente
size: 3
---

# T41 - Escreva os casos de avaliação sobre os documentos da demonstração e registre a primeira medição

## Contexto

T30 entrega o script de avaliação e o formato dos casos. T13 escolhe os documentos da demonstração. Este ticket junta os dois: escreve os casos sobre esses documentos, roda a avaliação com o Gemini real e registra os números.

As metas de `docs/product-specs/fidelidade-e-qualidade.md` ainda não foram medidas. A medição responde se a regra de T40, que reprova um conteúdo com qualquer afirmação sem apoio, reprova conteúdos fiéis com frequência e por quê.

Um agente escreve os casos, roda a avaliação e lê as pistas. Uma pessoa da equipe confere os casos e a leitura das pistas no PR antes do merge. A nota de clareza da pessoa (item 5 de "O que entregar") não pode vir do agente: o agente publica no PR os 10 conteúdos do revisor sem as notas do revisor, a pessoa dá as notas no PR e o agente as registra.

Leia antes: `examples/evals/README.md`, `examples/README.md` e `docs/product-specs/fidelidade-e-qualidade.md`.

Rode os comandos de avaliação em `backend/`. Use o banco de desenvolvimento com as migrations aplicadas e configure `GEMINI_API_KEY` e `GEMINI_GENERATION_MODEL` no `.env`.

## Escopo

- Um arquivo de casos `.json` em `examples/evals/` por documento de `examples/sources/`.
- Uma rodada da avaliação por arquivo, com o Gemini real.
- A comparação da clareza dada pelo revisor com a nota de uma pessoa.
- O registro dos números e da leitura das pistas em `fidelidade-e-qualidade.md`.

## Fora do escopo

- Mudar o script, os agentes, a busca ou as regras de publicação. Se a medição pedir uma mudança, registre a proposta no PR. A mudança vira outro ticket.
- O teste de adaptação ao público com uma pessoa de fora. Ele usa os conteúdos gerados para a demonstração (T34).
- Documentos que não estão em `examples/sources/`. Um documento só com link, sem cópia, fica fora.

## O que entregar

1. Entre todos os arquivos de casos:
    - 20 perguntas de busca, divididas entre os documentos;
    - 5 conteúdos com um erro plantado e 5 conteúdos fiéis para o revisor, com pelo menos um de cada formato entre os fiéis;
    - 6 casos de geração, 2 de cada formato, com os três níveis de público.
2. Cada arquivo passa em `uv run python scripts/evaluate.py --check <arquivo>`.
3. Uma rodada da avaliação por arquivo, no mesmo commit e com os mesmos modelos. Guarde os relatórios no PR.
4. Para cada erro plantado, confira se o revisor marcou aquele fato como sem apoio. Para cada pista, confira a afirmação, os chunks do caso e o documento. Registre se a busca omitiu o apoio, se o revisor deixou de reconhecê-lo, se a afirmação não tem apoio ou se faltam dados para decidir. Para uma geração sem pistas, registre o motivo da falha quando for possível.
5. Para os 10 conteúdos do revisor, a nota de clareza de uma pessoa (baixa, média ou alta), dada antes de ler a nota do revisor. O agente publica os 10 conteúdos num comentário do PR, sem as notas do revisor, e espera a resposta da pessoa antes de calcular a concordância.
6. Em `fidelidade-e-qualidade.md`, acrescente a seção "Medições" depois de "Como a equipe mede a qualidade". Reúna os resultados dos documentos em uma tabela para a rodada:
    - data, modelo de texto, modelo de embeddings e versão dos prompts, copiados do relatório;
    - busca: trecho esperado entre os 8, em número e porcentagem;
    - revisor: erros plantados identificados na conferência e alarmes falsos, com o total medido de cada grupo;
    - clareza: concordância entre o revisor e a pessoa, entre os casos com as duas notas;
    - geração: conteúdos aprovados para publicação e reprovações por motivo, incluindo os casos sem causa confirmada. Só conte como falsa reprovação uma versão que cobre o foco e cujas afirmações têm apoio no documento. Um caso pode ter mais de uma causa;
    - erros de execução, separados dos casos medidos.
7. Se um número fica abaixo da meta, uma frase com a causa provável, tirada das pistas. Não mude as metas neste ticket: a equipe decide o ajuste depois de ler a medição.

## Critérios de aceite

- [ ] `examples/evals/` tem um arquivo JSON por documento copiado em `examples/sources/`, e o CI valida todos.
- [ ] Os casos somam 20 perguntas, 10 conteúdos do revisor e 6 gerações.
- [ ] Nenhum conteúdo fiel traz um fato fora do documento.
- [ ] O PR traz os relatórios, a conferência dos erros plantados e a leitura de cada pista.
- [ ] `fidelidade-e-qualidade.md` registra a primeira medição na seção "Medições".
- [ ] As notas de clareza vêm de uma pessoa, dadas no PR antes de ela ver as notas do revisor. Se a equipe não tem quem julgue o assunto, a seção "Medições" registra a clareza como não medida, com o motivo, e a conferência passa para o teste de adaptação com uma pessoa de fora (T34).
- [ ] Os hooks passam.
- [ ] Uma pessoa da equipe conferiu os casos e a leitura das pistas antes do merge.
