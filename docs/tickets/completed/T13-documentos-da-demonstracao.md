---
id: T13
title: Escolha os três documentos da demonstração e confira as licenças
blocked_by: []
touches:
  - examples/README.md
  - examples/sources/
  - docs/product-specs/demonstracao.md
executor: agente
size: 2
---

# T13 - Escolha os três documentos da demonstração e confira as licenças

## Contexto

O briefing exige três execuções com documentos reais ou simulados. Os mesmos documentos servem de entrada para os casos de avaliação (T41) e para a geração final (T34).

O roteiro de `docs/product-specs/demonstracao.md` cita três temas, VCN na OCI, Kubernetes e OpenTelemetry Collector. Esses temas vieram de um rascunho que não existe mais e não foram uma decisão da equipe. Este ticket os substitui.

O banco traz quatro setores: `geral`, `fintech`, `saude` e `e-commerce`. A demonstração mostra a adaptação ao setor com dois documentos do mesmo setor e um de outro.

O agente pesquisa, propõe e prepara os arquivos. Uma pessoa da equipe confere a tabela de licenças no PR antes do merge.

## Escopo

Três documentos prontos para envio, com fonte e licença registradas, e o roteiro da demonstração atualizado.

## Regras para o conjunto

- Dois documentos são do mesmo setor e um é de outro setor. Os setores são `geral`, `fintech`, `saude` ou `e-commerce`.
- O assunto de cada documento combina com o setor. Por exemplo, pagamentos para `fintech`.
- Um dos documentos é o principal. Ele vira dois cursos, com níveis de público diferentes, como pede o briefing.

## Regras para cada documento

- É público ou fictício. O plano gratuito do Gemini pode usar os dados enviados.
- É um arquivo `.md`. Se a fonte é HTML ou PDF, converta o texto para Markdown sem mudar o conteúdo.
- Tem texto corrido suficiente para cerca de 20 a 100 chunks de 1.000 caracteres, e fica abaixo de 150 mil caracteres e de 5 MiB.
- Trata de um só assunto, com fatos que um revisor consegue conferir.
- Está em um só idioma. Prefira português. Se a fonte só existe em inglês, mantenha em inglês e anote.

## Licenças

- Leia os termos de uso na página da fonte. Copie para o repositório só texto cuja licença permite a cópia, e guarde a atribuição pedida.
- A Lei 9.610/98, art. 8, IV, exclui leis, decretos e regulamentos da proteção de direitos autorais. Normas oficiais, como resoluções do Banco Central ou diretrizes do Ministério da Saúde publicadas como norma, são um ponto de partida em português. Confirme que o texto escolhido é a norma, não um material explicativo com outros termos.
- Sem licença de cópia, guarde só o link, ou escreva um documento fictício próprio e marque-o como fictício.

## Fora do escopo

- Gerar conteúdo (T34).
- Escrever os casos de avaliação (T41).

## O que entregar

1. `examples/sources/`, com os três arquivos `.md`.
2. `examples/README.md`, com uma tabela: documento, setor, arquivo ou link, fonte, licença com o link da página que a declara, atribuição, idioma, número de caracteres e data da cópia.
3. No PR, os candidatos considerados, 2 ou 3 por vaga, com fonte, licença, idioma e tamanho, e o motivo da escolha.
4. Em `docs/product-specs/demonstracao.md`:
    - troque o roteiro proposto pelos três documentos escolhidos, com curso, nível, setor e conteúdos, mantendo o documento principal em dois cursos;
    - troque a frase que cita `docs/needs-validation/RELATORIO_TECNICO_PROJETO.md` por uma referência a `examples/README.md`;
    - troque "A equipe ainda não escolheu os arquivos" pelo estado real.

## Critérios de aceite

- [x] Os três documentos cumprem as regras do conjunto e de cada documento.
- [x] Cada documento tem fonte, licença e atribuição em `examples/README.md`.
- [x] Nenhum texto sem licença de cópia está no repositório.
- [x] O PR lista os candidatos e o motivo da escolha.
- [x] `demonstracao.md` traz o novo roteiro e não cita arquivo inexistente.
- [x] Os hooks passam.
- [x] Uma pessoa da equipe conferiu a tabela de licenças antes do merge.

## Verificação do aceite

- PR revisado: [#45](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/45), integrado no commit `8ffe599`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Documentos: Open Finance, Resolução Conjunta nº 1/2020, versão 10 (`fintech`, documento principal), Regulamento do Pix, Resolução BCB nº 1/2020, redação original (`fintech`), e Lei de Acesso à Informação, Lei nº 12.527/2011 (`geral`).
- Revisão automática sobre o commit `507b41c`: conferiu cada fonte e cada base legal na página de origem. Três achados, corrigidos no commit `668b14e`: o link do Pix aponta para o DOU certificado, as notas de alteração da LAI voltaram ao texto e o aviso do Banco Central voltou à nota de origem do Open Finance.
- A pessoa que fez o merge conferiu a tabela de licenças.
