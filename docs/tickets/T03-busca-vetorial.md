---
id: T03
title: Busque os chunks mais próximos de um embedding dentro de um curso
blocked_by: []
touches:
  - backend/app/services/__init__.py
  - backend/app/services/retrieval.py
  - backend/tests/services/__init__.py
  - backend/tests/services/test_retrieval.py
executor: agente
size: 2
---

# T03 - Busque os chunks mais próximos de um embedding dentro de um curso

## Contexto

A geração de um conteúdo começa pela busca dos 8 chunks mais próximos do `focus` (passo 6 de `docs/ARCHITECTURE.md`). A tabela `document_chunk` já guarda embeddings de 768 dimensões com pgvector. Falta a consulta.

A tarefa de fundo (T28) chama esta função. Os casos de avaliação da busca (T30) também.

Leia antes: `docs/ARCHITECTURE.md`, seção "A criação de um curso segue doze passos", e `backend/tests/test_schema.py`, que mostra como criar as linhas do esquema em um teste.

## Escopo

Uma função de busca por similaridade de cosseno, com os filtros de dono, estado do documento e modelo de embedding.

## Fora do escopo

- Gerar o embedding da consulta. Quem chama passa o vetor pronto.
- Índice HNSW. A busca é exata (decisão em `docs/ARCHITECTURE.md`).
- Rota de API.

## Contrato

Em `backend/app/services/retrieval.py`:

```python
class CourseNotFoundError(LookupError): ...


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    page_number: int | None
    similarity: float


def search_chunks(
    *,
    session: Session,
    course_id: uuid.UUID,
    owner_id: uuid.UUID,
    query_embedding: Sequence[float],
    embedding_model: str,
    limit: int = 8,
) -> list[RetrievedChunk]: ...
```

Regras:

- `CourseNotFoundError` se o curso não existe ou `owner_id` não é o dono.
- `ValueError` se `query_embedding` não tem 768 valores.
- A busca usa só chunks de documentos com `status = indexed` e `embedding_model` igual ao parâmetro.
- `similarity` é `1 - distância de cosseno`, arredondada a 3 casas e limitada ao intervalo de -1 a 1. A coluna `content_citation.similarity` é `numeric(4, 3)`.
- A ordem é da maior similaridade à menor. No empate, vale `chunk_index` e depois `chunk_id`, para a ordem ser estável.
- Sem chunk elegível, a função devolve lista vazia.

## Detalhes técnicos

- Use o operador de cosseno do pgvector pelo SQLAlchemy: `DocumentChunk.embedding.cosine_distance(vetor)`.
- Uma consulta resolve dono e chunks. Não carregue os embeddings para o Python.
- Não importe `app.core.llm`. Esse módulo nasce em T15, na mesma onda.

## Critérios de aceite

- [ ] `search_chunks` cumpre o contrato.
- [ ] Nenhum chunk de outro curso, de documento não indexado ou de outro modelo aparece no resultado.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

Use vetores feitos à mão. Com `e0` e `e1` como vetores com 1.0 em uma só posição: chunk A = `e0`, chunk B = `e1`, chunk C = `e0 + e1`.

1. A consulta `e0` devolve A (similaridade 1.0), C (cerca de 0.707) e B (0.0), nessa ordem.
2. Com 9 chunks elegíveis, a função devolve 8. Com `limit=2`, devolve 2.
3. Um documento `uploaded`, `processing` ou `failed` não entra no resultado.
4. Um documento com outro `embedding_model` não entra no resultado.
5. Um chunk de outro curso do mesmo dono não entra no resultado.
6. Outro `owner_id` e um `course_id` inexistente levantam `CourseNotFoundError`.
7. Um vetor com 767 valores levanta `ValueError`.
8. Um curso sem documentos indexados devolve lista vazia.
