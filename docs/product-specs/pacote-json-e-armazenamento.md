# JSON de saída e armazenamento

Cada conteúdo publicado tem um JSON com nomes de campo em inglês, entregue pela API e gravado no OCI Object Storage ao lado dos documentos originais.

Estado: a construir.

## O produto usa nomes próprios, em inglês

O briefing mostra um JSON de exemplo com nomes em português. Ele é só um exemplo. O produto usa os nomes do esquema do banco, em inglês, e uma resposta adaptada ao que o produto guarda.

A API é uma API REST com login. Um sistema externo que tenha um token usa as mesmas rotas da interface.

## O que a API devolve para um conteúdo

| Campo | Significado |
| --- | --- |
| `id` | Identificador do conteúdo |
| `format` | `tutorial`, `flashcards` ou `quiz` |
| `status` | `pending`, `running`, `succeeded` ou `failed` |
| `title` | Título do conteúdo |
| `content` | O conteúdo gerado, na estrutura do formato |
| `estimated_minutes` | Tempo estimado de estudo |
| `key_concepts` | Conceitos-chave |
| `prerequisites` | Pré-requisitos |
| `grounding_score` | Fidelidade ao documento, de 0 a 1 |
| `clarity` | `low`, `medium` ou `high` |
| `review_notes` | Observações da revisão |
| `oci_object_key` | Chave do arquivo JSON no OCI |
| `citations` | Trechos citados, cada um com o texto e a similaridade |
| `error_message` | Motivo da falha, quando o estado é `failed` |

O curso traz `audience_level`, o setor e a lista de documentos. Os nomes finais de cada campo seguem os schemas da API, gerados no OpenAPI do backend.

## Como o exemplo do briefing se liga à resposta

Esta tabela serve para explicar à banca onde está cada informação que o briefing pede.

| No exemplo do briefing | No produto |
| --- | --- |
| `status` | `status` do conteúdo |
| `metadados.perfil_aplicado` | `audience_level` do curso |
| `metadados.formato_gerado` | `format` |
| `metadados.tempo_estimado_estudo_minutos` | `estimated_minutes` |
| `metadados.conceitos_chave` | `key_concepts` |
| Pré-requisitos, citados no texto do briefing | `prerequisites` |
| `conteudo_adaptado` | `title` e `content` |
| `avaliacao_qualidade.ancoragem_fonte_score` | `grounding_score` |
| `avaliacao_qualidade.clareza_pedagogica` | `clarity` |
| `avaliacao_qualidade.observacoes` | `review_notes` |
| `armazenamento_oci.objeto_id` | `oci_object_key` |
| `nivel_detalhe`, na entrada | Não existe. O nível de público define a profundidade |

## Entrada pela API

O produto recebe um formulário com arquivos (`multipart/form-data`): título, setor, nível de público, documentos e saídas. O briefing mostra o texto do documento dentro do JSON. O produto recebe arquivos, porque um documento pode ser um PDF.

## O que o produto guarda no OCI

| Arquivo | Quando é gravado | Chave |
| --- | --- | --- |
| Documento original | Na criação do curso | `courses/{course_id}/documents/{document_id}.{ext}` |
| JSON de um conteúdo | Na publicação, depois da revisão | `courses/{course_id}/contents/{content_id}/{uuid}.json` |

O bucket é privado. A pessoa lê o conteúdo pela aplicação, não por um link do bucket.

O índice vetorial não vai para o OCI. Chunks e embeddings ficam só no PostgreSQL. O briefing só pede no OCI os documentos e os JSON.

## O que entra no arquivo JSON de um conteúdo

O arquivo traz tudo o que um sistema externo precisa para entender o conteúdo sem consultar o banco. Os nomes ficam em inglês.

| Campo | Origem |
| --- | --- |
| `format` | `course_content.format` |
| `audience_level` | `course.audience_level` |
| `niche` | `niche.slug` |
| `title` | `course_content.title` |
| `content` | `course_content.content` |
| `estimated_minutes` | `course_content.estimated_minutes` |
| `key_concepts` | `course_content.key_concepts` |
| `prerequisites` | `course_content.prerequisites` |
| `grounding_score` | `course_content.grounding_score` |
| `clarity` | `course_content.clarity` |
| `review_notes` | `course_content.review_notes` |

A coluna `course_content.content` guarda só o conteúdo gerado. O arquivo no OCI guarda o conteúdo e os outros campos desta tabela.

## Se a gravação no OCI falhar

O conteúdo não é publicado, e a pessoa vê uma mensagem clara com a opção de tentar de novo. O esquema não permite um conteúdo publicado sem arquivo no OCI.

## O que fica fora

- Seguir os nomes de campo do JSON de exemplo do briefing.
- Link temporário para baixar um arquivo direto do bucket.
- Reaproveitar o resultado de outro curso com os mesmos documentos e o mesmo nível.
- Guardar no OCI os arquivos exportados em Markdown, PDF ou CSV.
- Um bucket por tipo de arquivo. O produto usa um bucket por ambiente.
