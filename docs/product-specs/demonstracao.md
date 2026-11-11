# Demonstração para a banca

A demonstração usa três documentos públicos. Um deles gera quatro conteúdos: dois formatos para dois níveis de público.

Estado: a construir. Nenhum documento foi processado ainda.

## O que o briefing exige

| Exigência | Origem | Como a demonstração atende |
| --- | --- | --- |
| Três execuções com documentos reais ou simulados | Checklist | Três documentos diferentes processados |
| Três cenários de adaptação para um mesmo documento | Documentação e Demonstração | O documento principal gera quatro conteúdos |
| Dois perfis e dois formatos para o mesmo conteúdo | Checklist | Dois cursos do documento principal, cada um com dois formatos |

O briefing pode ser lido como uma exigência ou duas. A equipe atende às duas.

## Roteiro proposto

O documento principal vira dois cursos, porque cada curso tem um nível de público.

| Documento | Curso | Nível | Setor | Conteúdos |
| --- | --- | --- | --- | --- |
| Redes VCN na OCI | A | Não técnico | Geral | Flashcards e tutorial |
| Redes VCN na OCI | B | Técnico avançado | Fintech | Flashcards e tutorial |
| Conceitos do Kubernetes | C | Técnico básico | E-commerce | Tutorial |
| OpenTelemetry Collector | D | Técnico avançado | Geral | Quiz |

Os três temas vêm de `docs/needs-validation/RELATORIO_TECNICO_PROJETO.md`. A equipe ainda não escolheu os arquivos.

## O que a banca precisa ver

1. O envio de um documento e a escolha de nível, setor e formato.
2. O curso em "Gerando" e depois em "Pronto", com o tempo medido.
3. Dois conteúdos do mesmo documento, lado a lado, para níveis diferentes.
4. A fidelidade ao documento e os trechos citados de um conteúdo.
5. Um erro provocado de propósito, com a mensagem clara.
6. Os objetos no console do OCI: o documento original e o JSON gerado.
7. O JSON de um conteúdo.

## Regras para os documentos

- Só documentos públicos ou fictícios.
- A equipe confere os termos de uso de cada documento.
- Cada documento tem texto. Um PDF só com imagens não serve.
- Cada documento é um arquivo `.txt`, Markdown ou PDF, dentro do limite de tamanho.

## O que guardar no repositório

- Os documentos de entrada, se a licença permitir, ou o link para cada um.
- O JSON de cada conteúdo gerado, em uma pasta `examples/`.
- A lista de fontes, com o link de cada documento.

## Antes da apresentação

- A equipe ensaia duas vezes, com cronômetro.
- A equipe gera os conteúdos antes e mantém os cursos prontos. Uma geração ao vivo depende do plano gratuito do modelo.
- Se a aplicação estiver na VM da OCI, a equipe confere a VM alguns dias antes.
