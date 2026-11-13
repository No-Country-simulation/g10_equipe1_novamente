# Criar um curso

Uma pessoa autenticada preenche um formulário, anexa os documentos, escolhe as saídas e recebe um curso com um conteúdo por saída.

Estado: a construir.

## O que a pessoa informa

| Campo | Regra |
| --- | --- |
| Título | De 1 a 255 caracteres, sem contar espaços nas pontas |
| Setor | Fintech, Saúde, E-commerce ou Geral |
| Nível de público | Não técnico, técnico básico ou técnico avançado |
| Documentos | De 1 a 3 documentos. Cada um é um arquivo `.md`, um arquivo PDF com texto, ou um texto digitado em um campo. Cada arquivo tem até 5 MiB. Cada documento tem até 150 mil caracteres de texto |
| Saídas | De 1 a 3, uma de cada formato: tutorial, flashcards ou quiz |

O conteúdo de todos os documentos vale para todas as saídas. A pessoa não liga um documento a uma saída.

O foco de cada saída começa igual ao título do curso. Por isso o curso aceita só uma saída de cada formato: duas saídas iguais no formato e no foco sairiam quase iguais.

A equipe mede o tempo de um curso com três saídas e ajusta os limites se for preciso.

O nível e o setor ficam fixos depois da primeira geração com sucesso. Para outro nível, a pessoa cria outro curso com os mesmos arquivos.

O texto digitado em um campo conta como um documento. O navegador o envia como um arquivo `.md` (`texto-digitado.md`, com número se houver mais de um). A API recebe só arquivos e trata os três tipos da mesma forma.

## O que a pessoa vê

1. A pessoa clica em "Novo curso" e preenche os 3 passos de `/courses/new`: documentos, perfil (título, setor e nível) e formatos. O navegador confere tipo e tamanho dos arquivos. Ao clicar em "Criar curso", ele envia tudo em um só pedido.
2. O curso aparece na lista com o estado "Gerando".
3. A tela se atualiza sozinha a cada 3 segundos.
4. O produto gera uma saída por vez, na ordem escolhida.
5. O curso muda para "Pronto" quando a primeira saída é publicada. As outras saídas continuam em geração.
6. A pessoa abre o curso e vê cada conteúdo com o seu estado.

O briefing pede poucos cliques. Depois de preencher o formulário, a pessoa chega ao primeiro conteúdo com dois cliques.

## Estados que a pessoa vê

| Rótulo do curso | Estado no banco | Significado |
| --- | --- | --- |
| Gerando | `course.status = initializing` | Nenhuma saída foi publicada ainda. |
| Pronto | `course.status = ready` | Pelo menos uma saída está publicada. |
| Falhou | `course.status = failed` | Nenhuma saída criada com o curso foi publicada. |

Dentro do curso, cada conteúdo mostra o próprio estado: na fila, gerando, pronto ou falhou.

A tela não mostra um curso "Gerando" ou "Falhou" como produto pronto.

## Erros que a pessoa pode ver

| Situação | Resposta | Mensagem |
| --- | --- | --- |
| Título vazio | HTTP 422 | Informe um título. |
| Nenhum documento ou nenhuma saída | HTTP 422 | Envie pelo menos um documento e escolha pelo menos uma saída. |
| Mais de 3 documentos ou mais de 3 saídas | HTTP 422 | Envie até 3 documentos e escolha até 3 saídas. |
| Duas saídas do mesmo formato | HTTP 422 | Escolha só uma saída de cada formato. |
| Tipo de arquivo não aceito | HTTP 422 | Envie um arquivo `.md` ou PDF, ou digite o texto. |
| Arquivo vazio ou só com espaços | HTTP 422 | O arquivo não tem texto. |
| Arquivo maior que 5 MiB | HTTP 422 | O arquivo passa de 5 MiB. |
| Texto com mais de 150 mil caracteres | HTTP 422 | O documento é longo demais. Envie um documento menor ou divida o arquivo. |
| Arquivo Markdown que não é UTF-8 | HTTP 422 | Não foi possível ler o arquivo como texto. |
| PDF só com imagens | HTTP 422 | Este PDF não tem texto. Envie um PDF com texto. |
| Mesmo arquivo duas vezes no curso | HTTP 422 | Este arquivo já está no curso. |
| Setor inexistente | HTTP 404 | Setor não encontrado. |
| Falha ao ler ou indexar um documento | Curso "Falhou" | O documento que falhou e o motivo. |
| Falha no modelo ou no armazenamento | Conteúdo "Falhou" | O que falhou e o botão "Tentar novamente". |
| Conteúdo reprovado na revisão | Conteúdo "Falhou" | As afirmações sem apoio no documento. |
| Geração parada por 10 minutos | Conteúdo "Falhou" | A geração foi interrompida. Tente novamente. |

Os textos das mensagens são um ponto de partida. A equipe fecha a redação final.

A validação acontece antes de gravar qualquer arquivo ou linha.

Se um documento falha na indexação, o produto não gera nenhuma saída. Uma saída gerada sem um dos documentos não cumpre o que a pessoa pediu.

## Nova tentativa

Depois de uma falha, a pessoa clica em "Tentar novamente" no conteúdo que falhou. O conteúdo volta para a fila e usa os mesmos documentos. Um segundo clique durante a geração não inicia outra.

## Excluir um curso

A pessoa exclui um curso que não está em geração. O produto apaga o curso, os documentos e os conteúdos, no banco e no OCI. Um curso em geração não pode ser excluído.

Excluir a conta apaga todos os cursos da pessoa da mesma forma. A rota de exclusão de conta já existe e ainda não limpa o OCI, porque o produto ainda não grava arquivos lá.

## O que fica fora

- Editar o título, o nível ou o setor de um curso pronto.
- Adicionar ou excluir um documento de um curso já criado.
- Escolher quais documentos cada saída usa.
- Rascunho de curso. Um curso só existe com um documento e um conteúdo.
