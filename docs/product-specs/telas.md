# Telas

O MVP tem cinco telas: acesso, lista de cursos, novo curso, curso e dados da conta. São as telas que o esquema do banco sustenta.

Alguns documentos de design no Drive mostram outras telas. Elas não fazem parte do projeto. Em caso de diferença, este documento vale.

As cores e as fontes da marca já estão aplicadas no frontend.

## Telas do MVP

| Tela | O que a pessoa faz | Rota | Estado |
| --- | --- | --- | --- |
| Acesso | Entra com e-mail e senha, ou cria uma conta | `/login`, `/signup` | Existe |
| Cursos | Vê seus cursos com título, nível e estado. Abre um curso. Clica em "Novo curso" | `/courses` | A construir |
| Novo curso | Preenche título, setor e nível, anexa os documentos e escolhe as saídas | Diálogo em `/courses` | A construir |
| Curso | Vê os conteúdos do curso em ordem, com o estado de cada um, e lê um conteúdo | `/courses/$courseId` | A construir |
| Dados da conta | Muda nome, e-mail e senha. Exclui a conta | `/settings` | Existe |

Com um só conteúdo, a tela "Curso" mostra o conteúdo direto. Com mais de um, ela mostra a lista e abre um conteúdo por vez.

Toda tela, exceto a de acesso, exige login. Sem login, a pessoa vai para a tela de acesso.

## O que a tela de um conteúdo mostra

- Título do conteúdo, nível de público e setor do curso.
- Tempo estimado, conceitos-chave e pré-requisitos.
- O conteúdo, conforme o formato:
  - Tutorial: resumo e seções em Markdown.
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
