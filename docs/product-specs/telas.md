# Telas

O MVP tem cinco telas: acesso, lista de cursos, novo curso, curso e dados da conta. São as telas que o esquema do banco sustenta.

Os documentos de design no Drive detalham o layout das telas. Eles valem para o layout. Em regras de produto (limites, formatos, campos), este documento e `criar-curso.md` valem.

As cores e as fontes da marca já estão aplicadas no frontend.

## Telas do MVP

| Tela | O que a pessoa faz | Rota | Estado |
| --- | --- | --- | --- |
| Acesso | Entra com e-mail e senha, ou cria uma conta | `/login`, `/signup` | Existe |
| Cursos | Vê seus cursos com título, nível e estado. Abre um curso. Clica em "Novo curso" | `/courses` | A construir |
| Novo curso | Preenche o curso em 3 passos (ver abaixo) | `/courses/new` | A construir |
| Curso | Vê os conteúdos do curso em ordem, com o estado de cada um, e lê um conteúdo | `/courses/$courseId` | A construir |
| Dados da conta | Muda nome, e-mail e senha. Exclui a conta | `/settings` | Existe |

Com um só conteúdo, a tela "Curso" mostra o conteúdo direto. Com mais de um, ela mostra a lista e abre um conteúdo por vez.

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

## O que a tela de um conteúdo mostra

- Título do conteúdo, nível de público e setor do curso.
- Tempo estimado, conceitos-chave e pré-requisitos.
- O conteúdo, conforme o formato:
  - Tutorial: resumo de abertura e seções em Markdown. O resumo usa o layout "Resumo" dos documentos de design.
  - Flashcards: um cartão por vez, com frente, verso e dica.
  - Quiz: uma pergunta por vez. A justificativa aparece depois da resposta.
- Fidelidade ao documento, clareza e observações da revisão.
- Trechos citados do documento.

Se a geração falhou, a tela mostra o motivo e o botão "Tentar novamente".

## O que não é tela do MVP

- Dashboard de desempenho.
- Progresso do curso, resultados por etapa e tela de finalização.
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
- A lista de cursos e a tela do curso se atualizam a cada 3 segundos enquanto algum conteúdo está na fila ou em geração.
- Uma mensagem de erro diz o que aconteceu e o que a pessoa pode fazer.
- A pessoa só vê os próprios cursos.
