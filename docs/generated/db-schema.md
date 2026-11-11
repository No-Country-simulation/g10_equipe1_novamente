# Esquema do banco de dados

O NovaMente guarda usuários, cursos, metadados de documentos, chunks com embeddings de 768 dimensões e citações em PostgreSQL 18 com pgvector. Os arquivos originais e o JSON gerado de cada conteúdo ficam no OCI Object Storage. O banco guarda a chave de cada objeto. O JSON publicado de cada conteúdo fica também em `course_content.content`, e a API lê o conteúdo dessa coluna.

Este documento descreve a versão 5 do ERD. `backend/app/models.py` define as sete tabelas, e a migration de base fica em `backend/app/alembic/versions/`.

O diagrama está em [`erd.svg`](erd.svg). O fluxo que usa estas tabelas está em [`ARCHITECTURE.md`](../../ARCHITECTURE.md).

## Sete tabelas formam o esquema

| Tabela | Guarda |
| --- | --- |
| `user` | Conta de acesso. Vem do template do backend. |
| `niche` | Setor de aplicação usado nos exemplos: Fintech, Saúde, E-commerce ou Geral. |
| `course` | Curso de um usuário, com um único `audience_level`. |
| `source_document` | Metadados de um documento enviado ao curso. |
| `document_chunk` | Trecho de um documento, com texto e embedding. |
| `course_content` | Peça gerada do curso: tutorial, flashcards ou quiz. |
| `content_citation` | Ligação entre um conteúdo publicado e os chunks que ele cita. |

O esquema não tem histórico de gerações, rascunho de curso, nível de público por conteúdo, `detail_level` nem seleção de documentos por conteúdo.

A escala planejada é de 10 usuários, 5 cursos por usuário, 3 documentos por curso e cerca de 100 chunks por documento. O total fica perto de 15.000 chunks.

## Chaves estrangeiras compostas impedem dados de outro curso

Toda chave estrangeira apaga em cascata, exceto `course.niche_id`, que bloqueia a exclusão do nicho.

| Origem | Destino | `ON DELETE` |
| --- | --- | --- |
| `course.owner_id` | `user.id` | `CASCADE` |
| `course.niche_id` | `niche.id` | `RESTRICT` |
| `source_document.course_id` | `course.id` | `CASCADE` |
| `document_chunk.(document_id, course_id)` | `source_document.(id, course_id)` | `CASCADE` |
| `course_content.course_id` | `course.id` | `CASCADE` |
| `content_citation.(content_id, course_id)` | `course_content.(id, course_id)` | `CASCADE` |
| `content_citation.(chunk_id, course_id)` | `document_chunk.(id, course_id)` | `CASCADE` |

A chave composta de `document_chunk` impede que um chunk aponte para um curso diferente do curso do seu documento. As duas chaves compostas de `content_citation` impedem que um conteúdo cite um chunk de outro curso. Cada destino composto tem um índice único em `(id, course_id)`.

A cascata do SQL não apaga objetos no OCI. A exclusão de um curso exige uma limpeza separada dos objetos sob `courses/{course_id}/`. A exclusão de um usuário apaga os cursos dele em cascata e exige a mesma limpeza para cada curso.

## Enums

| Enum | Valores |
| --- | --- |
| `audience_level` | `non_technical`, `technical_basic`, `technical_advanced` |
| `content_format` | `tutorial`, `flashcards`, `quiz` |
| `document_status` | `uploaded`, `processing`, `indexed`, `failed` |
| `generation_status` | `pending`, `running`, `succeeded`, `failed` |
| `clarity_level` | `low`, `medium`, `high` |
| `course_status` | `initializing`, `ready`, `failed` |

Os valores de `document_status` têm este significado:

- `uploaded`: o arquivo está no OCI e ainda não foi indexado.
- `processing`: o backend está lendo, dividindo e gerando embeddings do arquivo.
- `indexed`: os chunks participam de toda geração do curso.
- `failed`: a indexação falhou.

Os valores de `course_status` têm este significado:

- `initializing`: o curso e os conteúdos criados com ele existem, mas nenhum foi publicado e a geração inicial não terminou. Não é um rascunho.
- `ready`: pelo menos um conteúdo está publicado.
- `failed`: nenhum conteúdo criado com o curso foi publicado. Uma nova tentativa usa as mesmas linhas de conteúdo.

## Tabelas

### `user`

A tabela já existe no template do backend. O ERD não altera as colunas dela.

| Coluna | Tipo | Nulo | Padrão | Nota |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | não | | Chave primária. |
| `email` | `varchar(255)` | não | | Único. |
| `full_name` | `varchar(255)` | sim | | |
| `hashed_password` | `varchar` | não | | |
| `is_active` | `boolean` | não | `true` | |
| `created_at` | `timestamptz` | sim | | |

### `niche`

A tabela alimenta o dropdown de setor. Um nicho é um setor de aplicação, não um tema como RAG ou embeddings.

| Coluna | Tipo | Nulo | Padrão | Nota |
| --- | --- | --- | --- | --- |
| `id` | `smallint` | não | auto incremento | Chave primária. |
| `slug` | `varchar(50)` | não | | Único. Exemplos: `fintech`, `saude`, `e-commerce`, `geral`. |
| `name` | `varchar(100)` | não | | Rótulo na interface. |
| `description` | `text` | sim | | Explica o setor para o usuário. |
| `prompt_hint` | `text` | não | | Orienta o LLM a usar exemplos do setor. |

O arquivo de CHECKs do ERD traz este seed. Ele usa `ON CONFLICT (slug) DO UPDATE` e atualiza `name`, `description` e `prompt_hint` de um slug existente.

| `slug` | `name` | `description` |
| --- | --- | --- |
| `fintech` | Fintech | Financial technology and digital finance |
| `saude` | Saúde | Healthcare and health technology |
| `e-commerce` | E-commerce | Online shops and retail platforms |
| `geral` | Geral | General-purpose examples |

O seed não remove slugs antigos de tema, como `rag` ou `prompt-engineering`. A remoção deles exige tratar antes os cursos que os referenciam.

### `course`

| Coluna | Tipo | Nulo | Padrão | Nota |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | não | | Chave primária. |
| `owner_id` | `uuid` | não | | Referencia `user.id`. Indexada. |
| `niche_id` | `smallint` | não | | Referencia `niche.id`. |
| `title` | `varchar(255)` | não | | |
| `description` | `text` | sim | | |
| `audience_level` | `audience_level` | não | | Vale para todo conteúdo do curso. |
| `status` | `course_status` | não | `initializing` | |
| `created_at` | `timestamptz` | não | `now()` | |
| `updated_at` | `timestamptz` | não | `now()` | O código da aplicação atualiza a coluna. |

`audience_level` e `niche_id` ficam fixos depois da primeira geração com sucesso. Só uma regeneração de todo o conteúdo justifica mudar os dois.

### `source_document`

| Coluna | Tipo | Nulo | Padrão | Nota |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | não | | Chave primária. |
| `course_id` | `uuid` | não | | Referencia `course.id`. |
| `title` | `varchar(255)` | não | | |
| `original_filename` | `varchar(255)` | não | | |
| `mime_type` | `varchar(100)` | não | | `application/pdf`, `text/markdown` ou `text/plain`. |
| `size_bytes` | `bigint` | não | | |
| `sha256` | `char(64)` | não | | Hash hexadecimal em minúsculas. |
| `oci_object_key` | `varchar(512)` | não | | Única. Formato `courses/{course_id}/documents/{id}.{ext}`. |
| `status` | `document_status` | não | `uploaded` | |
| `embedding_model` | `varchar(100)` | não | `gemini-embedding-2` | Precisa ser compatível com o modelo da consulta. |
| `error_message` | `text` | sim | | |
| `created_at` | `timestamptz` | não | `now()` | |

Índices:

- `(course_id, sha256)` único. Bloqueia o mesmo arquivo duas vezes no mesmo curso. O mesmo arquivo pode existir em cursos diferentes.
- `(id, course_id)` único. É o destino da chave composta de `document_chunk`.

CHECKs:

- `ck_source_document_size_positive`: `size_bytes > 0`.
- `ck_source_document_sha256_hex`: `sha256 ~ '^[0-9a-f]{64}$'`.

A exclusão de um documento isolado está fora do escopo do MVP.

### `document_chunk`

| Coluna | Tipo | Nulo | Padrão | Nota |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | não | | Chave primária. |
| `document_id` | `uuid` | não | | Parte da chave composta para `source_document`. |
| `course_id` | `uuid` | não | | Cópia de `source_document.course_id` para filtrar a busca por curso. |
| `chunk_index` | `int` | não | | Posição do chunk no documento. |
| `text` | `text` | não | | |
| `page_number` | `int` | sim | | Página do PDF, quando existe. |
| `token_count` | `int` | sim | | |
| `embedding` | `vector(768)` | não | | Documento e consulta usam a mesma configuração de 768 dimensões. |

Índices:

- `(document_id, chunk_index)` único.
- `(id, course_id)` único. É o destino da chave composta de `content_citation`.
- `course_id`.

CHECKs:

- `ck_document_chunk_position`: `chunk_index >= 0`.
- `ck_document_chunk_text_nonempty`: `length(btrim(text)) > 0`.
- `ck_document_chunk_page`: `page_number IS NULL OR page_number >= 1`.
- `ck_document_chunk_tokens`: `token_count IS NULL OR token_count > 0`.

A coluna `embedding` não tem índice HNSW. A busca começa com vizinho mais próximo exato por distância de cosseno. Um índice HNSW só entra depois de um benchmark. A busca usa todos os documentos `indexed` do curso:

```sql
SELECT c.id, c.text, c.embedding <=> :query_vector AS distance
FROM document_chunk c
JOIN source_document d
	ON d.id = c.document_id AND d.course_id = c.course_id
WHERE c.course_id = :course_id
	AND d.status = 'indexed'
	AND d.embedding_model = :embedding_model
ORDER BY c.embedding <=> :query_vector
LIMIT :k;
```

### `course_content`

Cada linha guarda a última geração e o último resultado publicado de uma peça do curso. Uma regeneração substitui a mesma linha. O banco não guarda versões anteriores.

| Coluna | Tipo | Nulo | Padrão | Nota |
| --- | --- | --- | --- | --- |
| `id` | `uuid` | não | | Chave primária. |
| `course_id` | `uuid` | não | | Referencia `course.id`. |
| `format` | `content_format` | não | | |
| `position` | `int` | não | `0` | Ordem na lista. Aceita empate. |
| `focus` | `text` | não | | Assunto da peça. Também entra na busca. |
| `title` | `varchar(255)` | sim | | |
| `status` | `generation_status` | não | `pending` | Estado da última geração. |
| `error_message` | `text` | sim | | |
| `llm_model` | `varchar(100)` | sim | | |
| `prompt_version` | `varchar(50)` | sim | | |
| `content` | `jsonb` | sim | | Objeto JSON validado do tutorial, dos flashcards ou do quiz. |
| `estimated_minutes` | `int` | sim | | |
| `key_concepts` | `jsonb` | sim | | Array de strings. |
| `prerequisites` | `jsonb` | sim | | Array de strings. |
| `grounding_score` | `numeric(3,2)` | sim | | Fração das afirmações técnicas do conteúdo que têm apoio em um chunk, de 0 a 1. O backend calcula. Não é a similaridade de cosseno. |
| `clarity` | `clarity_level` | sim | | |
| `review_notes` | `text` | sim | | |
| `oci_object_key` | `varchar(512)` | sim | | Única. Cada regeneração usa uma chave nova. |
| `created_at` | `timestamptz` | não | `now()` | |
| `updated_at` | `timestamptz` | não | `now()` | O código atualiza a coluna em toda mudança de `status`. |

As colunas de `status` a `prompt_version` descrevem a última geração. As colunas de `content` a `oci_object_key` descrevem o último resultado publicado. Uma geração `running` ou `failed` mantém o resultado publicado anterior legível.

A lista de conteúdos ordena por `position`, `created_at` e `id`.

Índices:

- `(course_id, position)`.
- `(id, course_id)` único. É o destino da chave composta de `content_citation`.

O esquema não impõe unicidade em `(course_id, format, focus)`. Um usuário pode criar duas peças com o mesmo foco. A regeneração identifica a peça por `id`.

CHECKs:

- `ck_course_content_position`: `position >= 0`.
- `ck_course_content_focus_nonempty`: `length(btrim(focus)) > 0`.
- `ck_course_content_minutes`: `estimated_minutes IS NULL OR estimated_minutes > 0`.
- `ck_course_content_grounding`: `grounding_score IS NULL OR grounding_score BETWEEN 0 AND 1`.
- `ck_course_content_body_json`: `content` é nulo ou um objeto JSON.
- `ck_course_content_key_concepts_array`: `key_concepts` é nulo ou um array JSON.
- `ck_course_content_prerequisites_array`: `prerequisites` é nulo ou um array JSON.
- `ck_course_content_published_pair`: `content` e `oci_object_key` são ambos nulos ou ambos preenchidos.
- `ck_course_content_successful_published`: uma linha `succeeded` tem `content` e `oci_object_key` preenchidos.

### `content_citation`

Cada linha liga o conteúdo publicado de um `course_content` a um chunk citado. Uma regeneração troca o conjunto inteiro de citações na mesma transação que atualiza o conteúdo.

| Coluna | Tipo | Nulo | Padrão | Nota |
| --- | --- | --- | --- | --- |
| `course_id` | `uuid` | não | | Igual ao curso do conteúdo e ao curso do chunk. |
| `content_id` | `uuid` | não | | Parte da chave primária. |
| `chunk_id` | `uuid` | não | | Parte da chave primária. |
| `similarity` | `numeric(4,3)` | sim | | Similaridade de cosseno, igual a `1 - distância de cosseno`. Vai de -1 a 1. |

Índices:

- `(content_id, chunk_id)`. Chave primária.
- `(chunk_id, course_id)`. Atende a cascata pela chave composta para `document_chunk`.

CHECK:

- `ck_content_citation_cosine_similarity`: `similarity IS NULL OR similarity BETWEEN -1 AND 1`.

## O backend garante as regras que o banco não expressa

As chaves e os CHECKs não cobrem o ciclo de vida do curso. O backend aplica estas regras:

1. O backend cria o `course` com `status = initializing` e os conteúdos escolhidos na criação, cada um com `status = pending`, na mesma transação. Todo curso nasce com pelo menos um documento e um conteúdo. Nenhum `endpoint` cria um curso sozinho.
2. O backend nunca apaga o último conteúdo de um curso sem apagar o curso.
3. O backend marca o curso como `ready` só quando existe pelo menos um conteúdo com `content` e `oci_object_key` preenchidos.
4. Se nenhum conteúdo criado com o curso é publicado, o backend marca o curso como `failed`. A nova tentativa de um conteúdo usa a mesma linha de `course_content`.
5. A geração usa os chunks de todos os documentos `indexed` do curso com `embedding_model` compatível.
6. Uma regeneração com sucesso segue esta ordem: envia o JSON novo ao OCI com uma chave nova, atualiza o conteúdo e as citações em uma transação e depois apaga o objeto antigo no OCI. Se a exclusão do objeto antigo falha, o backend tenta de novo.
7. Um mesmo `course_content` não tem duas gerações ao mesmo tempo.
8. Toda leitura e toda busca vetorial confirmam que o usuário autenticado é o dono do curso.
9. O backend identifica um curso só pelo `id`. Título, `audience_level` e `niche_id` iguais não indicam o mesmo curso.
10. A API não apresenta um curso `initializing` ou `failed` como produto pronto.
