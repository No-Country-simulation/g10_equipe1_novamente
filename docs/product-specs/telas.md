# Telas

O MVP tem cinco telas: acesso, lista de cursos, novo curso, curso e dados da conta. São as telas que o esquema do banco sustenta.

O layout segue só o arquivo `[Telas finais] NovaMente jornada com modelos de conteúdo.html`, no Drive. Ele vale para o layout. Em regras de produto (limites, formatos, campos e estados), este documento e `criar-curso.md` valem. As capturas que os tickets usam ficam em [`docs/design/telas-finais/`](../design/telas-finais/README.md).

Os documentos de design anteriores não valem, nem para desempatar: `[Antigo - Não usar] NovaMente modelos de conteúdo.html`, as "Histórias 1 a 5", as propostas V2 e V3 e a pasta "Materiais antigos".

As cores e as fontes da marca já estão aplicadas no frontend.

## Telas do MVP

| Tela | O que a pessoa faz | Rota | Estado |
| --- | --- | --- | --- |
| Acesso | Entra com e-mail e senha, ou cria uma conta | `/login`, `/signup` | Existe |
| Cursos | Vê seus cursos com título, nível e estado. Abre um curso. Clica em "Novo curso" | `/courses` | A construir |
| Novo curso | Preenche o curso em 3 passos (ver abaixo) | `/courses/new` | A construir |
| Curso | Vê os conteúdos do curso em ordem, com o estado de cada um, e lê um conteúdo | `/courses/$courseId`, `/courses/$courseId/contents/$contentId` | A construir |
| Dados da conta | Muda nome, e-mail e senha. Exclui a conta | `/settings` | Existe |

Com um só conteúdo, `/courses/$courseId` mostra o conteúdo direto. Com mais de um, ela mostra um cartão por conteúdo, e cada cartão abre o conteúdo em `/courses/$courseId/contents/$contentId`.

Toda tela, exceto a de acesso, exige login. Sem login, a pessoa vai para a tela de acesso.

## Navegação

O frontend usa uma navegação no topo, com "Home" (a lista de cursos) e "Novo curso". Ela substitui a barra lateral do template. Todas as telas do layout assumem essa navegação.

## Tela "Novo curso" em 3 passos

A tela `/courses/new` é uma página, não um diálogo, porque três documentos e três formatos não cabem em um diálogo.

| Passo | O que a pessoa faz |
| --- | --- |
| 1. Documentos | Anexa até 3 documentos: arquivos `.md` ou PDF, ou texto digitado em um campo |
| 2. Perfil | Escolhe título, setor e nível de público |
| 3. Formatos | Escolhe de 1 a 3 saídas: tutorial, flashcards ou quiz, e cria o curso |

O navegador confere tipo e tamanho de cada arquivo ao anexá-lo. O envio ao servidor acontece uma vez, no fim do passo 3.

## Como a tela "Curso" adapta as Telas finais

A tela "Curso" segue as telas 5 e 6 das Telas finais, com estas adaptações:

- `/courses/$courseId` mostra os conteúdos em uma grade de cartões, como a tela 5. Cada cartão traz o estado da geração ("Na fila", "Gerando", "Pronto" ou "Falhou") no lugar do progresso.
- Abaixo dos cartões, o bloco "Resumo do curso" mostra setor, nível, formatos e os documentos do curso. Ele não mostra progresso.
- Um conteúdo abre em uma tela própria, como a tela 6: um cabeçalho escuro com o título do curso, um link de volta para o curso e o conteúdo abaixo. Essa tela não tem o botão "Finalizar".

## O que a tela de um conteúdo mostra

- Título do conteúdo, nível de público e setor do curso.
- Tempo estimado, conceitos-chave e pré-requisitos.
- O conteúdo, conforme o formato:
  - Tutorial: resumo de abertura e seções em Markdown, como na tela 6 das Telas finais.
  - Flashcards: um cartão por vez, com frente, verso e dica.
  - Quiz: uma pergunta por vez. A justificativa aparece depois da resposta.
- Fidelidade ao documento, clareza e observações da revisão.
- Trechos citados do documento.

Se a geração falhou, a tela mostra o motivo e o botão "Tentar novamente".

## O que não é tela do MVP

- Dashboard de desempenho.
- Progresso do curso: os estados "Concluído", "Em andamento" e "Não iniciado", conteúdos que liberam o próximo, a barra de progresso e a contagem de conteúdos concluídos.
- Resultados por etapa.
- Tela de finalização de um conteúdo (telas 7, 7a, 7b e 7c das Telas finais) e o botão "Finalizar" ou "Concluir conteúdo".
- Avaliação do curso por estrelas e por conteúdo.
- Assistente de conversa.
- Nivelamento por perguntas.
- Biblioteca de materiais já disponíveis na plataforma.
- Busca, filtro e sugestão de temas na lista de cursos.
- Campos de empresa, código de uso e aceite de termos no cadastro.

O esquema não guarda os dados que essas telas pedem.

## Regras de interface

- Os textos da interface ficam em português do Brasil.
- Os estados do curso aparecem como "Gerando", "Pronto" e "Falhou".
- Os estados de um conteúdo aparecem como "Na fila", "Gerando", "Pronto" e "Falhou".
- A lista de cursos e a tela do curso se atualizam a cada 3 segundos enquanto algum conteúdo está na fila ou em geração.
- Uma mensagem de erro diz o que aconteceu e o que a pessoa pode fazer.
- A pessoa só vê os próprios cursos.
