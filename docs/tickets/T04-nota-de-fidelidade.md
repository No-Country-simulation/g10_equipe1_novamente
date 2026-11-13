---
id: T04
title: Calcule a nota de fidelidade e decida publicar, reescrever ou falhar
blocked_by: []
touches:
  - backend/app/services/__init__.py
  - backend/app/services/grounding.py
  - backend/tests/services/__init__.py
  - backend/tests/services/test_grounding.py
executor: agente
size: 2
---

# T04 - Calcule a nota de fidelidade e decida publicar, reescrever ou falhar

## Contexto

A promessa do produto é fidelidade ao documento. O modelo lista as afirmações e aponta o chunk de cada uma, mas quem calcula a nota e decide é o backend (regras 2 a 5 de "Regras que o código mantém", em `docs/ARCHITECTURE.md`).

Este ticket entrega essa parte como funções puras, sem banco e sem modelo. O agente `revisa` (T21) devolve um `ReviewResult`. O grafo de geração (T24) chama `evaluate` e `decide`. A publicação (T22) usa `cited_chunk_ids`.

Leia antes: `docs/product-specs/fidelidade-e-qualidade.md`.

## Escopo

Os modelos da resposta do revisor, o cálculo da nota, a decisão e a mensagem de falha.

## Fora do escopo

- Chamar o modelo (T21).
- Gravar nota e citações no banco (T22).
- Medir o revisor com casos reais (T30).

## Contrato

Em `backend/app/services/grounding.py`:

```python
MIN_GROUNDING_SCORE = Decimal("0.80")
MAX_ATTEMPTS = 2


class ClaimReview(BaseModel):
    claim: str
    supported: bool
    chunk_id: uuid.UUID | None = None


class ReviewResult(BaseModel):
    claims: list[ClaimReview]
    clarity: ClarityLevel
    review_notes: str


class Decision(StrEnum):
    publish = "publish"
    rewrite = "rewrite"
    fail = "fail"


@dataclass(frozen=True, slots=True)
class GroundingReport:
    score: Decimal
    passed: bool
    supported: list[ClaimReview]
    unsupported: list[ClaimReview]
    cited_chunk_ids: list[uuid.UUID]


def evaluate(
    review: ReviewResult,
    valid_chunk_ids: Set[uuid.UUID],
    *,
    min_score: Decimal = MIN_GROUNDING_SCORE,
) -> GroundingReport: ...


def decide(report: GroundingReport, *, attempt: int) -> Decision: ...


def failure_message(report: GroundingReport) -> str: ...
```

Regras:

- Uma afirmação conta como sustentada só se `supported` é verdadeiro e `chunk_id` está em `valid_chunk_ids`. Sem chunk válido, ela vai para `unsupported`.
- `passed` compara a fração exata, sem arredondar: `sustentadas / total >= min_score`.
- `score` é a fração arredondada para baixo, com 2 casas. A coluna `course_content.grounding_score` é `numeric(3, 2)`. Arredondar para baixo impede que 0,795 apareça como 0,80.
- Sem nenhuma afirmação, `score` é `0.00` e `passed` é falso. Um conteúdo sem afirmação técnica não trata do assunto pedido.
- `cited_chunk_ids` traz os chunks das afirmações sustentadas, sem repetição, na ordem em que aparecem.
- `decide`: `publish` se `passed`. Senão, `rewrite` na tentativa 1 e `fail` da tentativa `MAX_ATTEMPTS` em diante. `attempt` começa em 1. Um valor menor que 1 levanta `ValueError`.
- `failure_message` devolve um texto em português para `course_content.error_message`: a frase "Afirmações sem apoio no documento:" e uma linha por afirmação reprovada. Sem nenhuma afirmação, devolve "O documento não trata do assunto pedido."

## Detalhes técnicos

- `ClarityLevel` vem de `app.models`.
- Use `Decimal` e `ROUND_FLOOR` no arredondamento. Não use `float` no cálculo.
- O módulo não importa banco, OCI nem Gemini.

## Critérios de aceite

- [ ] As três funções cumprem o contrato.
- [ ] Nenhum caminho devolve `publish` com `passed` falso.
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

1. 8 de 10 sustentadas: `score` 0.80, `passed` verdadeiro, `publish`.
2. 7 de 10 sustentadas: `score` 0.70, `rewrite` na tentativa 1 e `fail` na tentativa 2.
3. 159 de 200 sustentadas (0,795): `score` 0.79 e `passed` falso.
4. Uma afirmação `supported` com `chunk_id` nulo ou fora de `valid_chunk_ids` conta como não sustentada.
5. Lista de afirmações vazia: `score` 0.00, `passed` falso e a mensagem de assunto ausente.
6. Duas afirmações com o mesmo chunk geram um só item em `cited_chunk_ids`.
7. `failure_message` lista cada afirmação reprovada em uma linha.
8. `decide` com `attempt=0` levanta `ValueError`.
