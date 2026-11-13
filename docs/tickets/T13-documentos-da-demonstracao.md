---
id: T13
title: Escolha os três documentos da demonstração e confira as licenças
blocked_by: []
touches:
  - examples/README.md
  - examples/sources/
  - docs/product-specs/demonstracao.md
executor: pessoa
size: 2
---

# T13 - Escolha os três documentos da demonstração e confira as licenças

## Contexto

O briefing exige três execuções com documentos reais ou simulados, e `docs/product-specs/demonstracao.md` já define o roteiro: redes VCN na OCI, conceitos do Kubernetes e OpenTelemetry Collector. Os arquivos ainda não foram escolhidos.

Os mesmos documentos servem de entrada para os casos de avaliação (T30) e para a geração final (T34). Escolher cedo deixa a equipe testar com o material real desde a primeira geração.

Uma pessoa decide, porque a escolha envolve ler termos de uso. Um agente com acesso à web pode propor os arquivos e a tabela.

## Escopo

Três documentos prontos para envio, com fonte e licença registradas.

## Regras para cada documento

- É público ou fictício. O plano gratuito do Gemini pode usar os dados enviados.
- É um arquivo `.md`. O PDF entra só em T37, e a primeira geração usa `.md`.
- Tem texto corrido suficiente para cerca de 20 a 100 chunks de 1.000 caracteres, e fica abaixo de 150 mil caracteres e de 5 MiB.
- Trata de um só assunto, com fatos técnicos que um revisor consegue conferir.
- Está em um só idioma. Prefira português. Se a fonte só existe em inglês, mantenha em inglês e anote.

## Licenças: o que conferir

| Tema | Ponto de partida | Atenção |
| --- | --- | --- |
| Conceitos do Kubernetes | Documentação oficial do Kubernetes | A documentação declara licença Creative Commons com atribuição. Confirme na página e guarde a atribuição. |
| OpenTelemetry Collector | Documentação oficial do OpenTelemetry | Idem. Confirme na página e guarde a atribuição. |
| Redes VCN na OCI | Documentação da Oracle | A documentação da Oracle não tem licença aberta. Não copie o texto para o repositório. Escreva um documento fictício próprio sobre VCN, com os mesmos conceitos do exemplo do briefing, ou guarde só o link. |

As duas primeiras linhas são o que a equipe espera encontrar, não uma conferência feita. Leia os termos de cada fonte antes de copiar qualquer texto.

## Fora do escopo

- Gerar conteúdo (T34).
- Escrever as perguntas e os erros plantados dos casos de avaliação (T30).

## O que entregar

1. `examples/sources/`, com os arquivos `.md` cuja licença permite a cópia.
2. `examples/README.md`, com uma tabela: documento, arquivo ou link, fonte, licença, atribuição, idioma, número de caracteres e data da cópia.
3. Em `docs/product-specs/demonstracao.md`:
    - troque a frase que cita `docs/needs-validation/RELATORIO_TECNICO_PROJETO.md`, arquivo que não existe mais, por uma referência a `examples/README.md`;
    - troque "A equipe ainda não escolheu os arquivos" pelo estado real.

## Critérios de aceite

- [ ] Os três documentos cumprem as regras acima.
- [ ] Cada documento tem fonte, licença e atribuição em `examples/README.md`.
- [ ] Nenhum texto sem licença de cópia está no repositório.
- [ ] `demonstracao.md` não cita arquivo inexistente.
- [ ] Os hooks passam.
