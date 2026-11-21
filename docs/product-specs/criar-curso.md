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

Em 21/11/2026, a geração de um curso com três saídas levou 175,024 segundos. A equipe usou um documento Markdown de 12.932 caracteres, com `gemini-3.5-flash-lite` para geração e `gemini-embedding-2` para embeddings.

O nível e o setor ficam fixos depois da primeira geração com sucesso. Para outro nível, a pessoa cria outro curso com os mesmos arquivos.

O texto digitado em um campo conta como um documento. O navegador o envia como um arquivo `.md` (`texto-digitado.md`, com número se houver mais de um). A API recebe só arquivos e trata os três tipos da mesma forma.

## O que a pessoa vê

1. A pessoa clica em "Novo curso" e preenche os 3 passos de `/courses/new`: documentos, perfil (título, setor e nível) e formatos. O navegador confere tipo e tamanho dos arquivos. Ao clicar em "Criar curso", ele envia tudo em um só pedido.
2. Se o envio dá certo, a pessoa vai direto à tela do curso criado. Cada conteúdo mostra o próprio estado e começa como "Na fila". Na lista de cursos, o curso aparece como "Gerando".
3. A lista de cursos e a tela do curso se atualizam a cada 3 segundos enquanto algum conteúdo está na fila ou em geração.
4. O produto gera uma saída por vez, na ordem escolhida.
5. O curso muda para "Pronto" quando a primeira saída é publicada. As outras saídas continuam em geração.

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
| Título com mais de 255 caracteres | HTTP 422 | O título passa de 255 caracteres. |
| Nenhum documento ou nenhuma saída | HTTP 422 | Envie pelo menos um documento e escolha pelo menos uma saída. |
| Mais de 3 documentos ou mais de 3 saídas | HTTP 422 | Envie até 3 documentos e escolha até 3 saídas. |
| Duas saídas do mesmo formato | HTTP 422 | Escolha só uma saída de cada formato. |
| Tipo de arquivo não aceito | HTTP 422 | Envie um arquivo `.md` ou PDF, ou digite o texto. |
| Arquivo vazio ou só com espaços | HTTP 422 | O arquivo não tem texto. |
| Arquivo maior que 5 MiB | HTTP 422 | O arquivo passa de 5 MiB. |
| Texto com mais de 150 mil caracteres | HTTP 422 | O documento é longo demais. Envie um documento menor ou divida o arquivo. |
| Arquivo Markdown que não é UTF-8 | HTTP 422 | Não foi possível ler o arquivo como texto. |
| PDF só com imagens | HTTP 422 | Este PDF não tem texto. Envie um PDF com texto. |
| PDF corrompido ou com senha | HTTP 422 | Não foi possível abrir o PDF. Envie um PDF sem senha. |
| Mesmo arquivo duas vezes no curso | HTTP 422 | Este arquivo já está no curso. |
| Setor inexistente | HTTP 404 | Setor não encontrado. |
| Armazenamento de arquivos fora do ar | HTTP 503 | O armazenamento de arquivos não está disponível. Tente novamente mais tarde. |
| Falha ao ler ou indexar um documento | Curso "Falhou" | O documento que falhou e o motivo. Cada conteúdo mostra: O conteúdo não foi gerado, porque um documento do curso falhou. |
| Falha no modelo ou no armazenamento | Conteúdo "Falhou" | O que falhou e o botão "Tentar novamente". |
| Foco não coberto ou segunda revisão sem afirmações | Conteúdo "Falhou" | O documento não trata do assunto pedido. |
| Segunda revisão com foco coberto e afirmações sem apoio | Conteúdo "Falhou" | Afirmações sem apoio no documento: uma linha por afirmação. |
| Geração parada por 10 minutos | Conteúdo "Falhou" | A geração foi interrompida. Tente novamente. |

Quando o erro é de um documento, a mensagem vem depois do nome do arquivo: `guia.txt: Envie um arquivo .md ou PDF, ou digite o texto.`

Os textos das mensagens são um ponto de partida. A equipe fecha a redação final.

A validação acontece antes de gravar qualquer arquivo ou linha.

Se um documento falha na indexação, o produto não gera nenhuma saída. Uma saída gerada sem um dos documentos não cumpre o que a pessoa pediu.

## Nova tentativa

Depois de uma falha, a pessoa clica em "Tentar novamente" no alerta ou no cartão do conteúdo que falhou. Essa saída volta para a fila. Um segundo clique durante a geração não inicia outra. A tarefa reaproveita os documentos já indexados e indexa os demais. Se o curso já tem uma publicação, ela continua disponível.

## Excluir um curso

No resumo do curso, clique em "Excluir curso" e confirme. Se algum conteúdo estiver na fila ou em geração, o botão fica desabilitado.

Para excluir a conta, todos os cursos precisam estar fora da fila e da geração. Em ambos os casos, o produto apaga os dados no banco e remove os documentos e os JSON da OCI em segundo plano.

## O que fica fora

- Editar o título, o nível ou o setor de um curso pronto.
- Adicionar ou excluir um documento de um curso já criado.
- Escolher quais documentos cada saída usa.
- Rascunho de curso. Um curso só existe com um documento e um conteúdo.
