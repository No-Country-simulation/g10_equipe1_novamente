---
id: T05
title: Defina os modelos do JSON de tutorial, flashcards e quiz
blocked_by: []
touches:
  - backend/app/services/__init__.py
  - backend/app/services/content_schemas.py
  - backend/tests/services/__init__.py
  - backend/tests/services/test_content_schemas.py
  - docs/product-specs/conteudos-e-formatos.md
executor: agente
size: 2
---

# T05 - Defina os modelos do JSON de tutorial, flashcards e quiz

## Contexto

`course_content.content` guarda um JSON por formato, mas nenhum código diz qual é a forma desse JSON. Sem um modelo, o agente `escreve` (T20, T25, T26), a publicação (T22) e os leitores da interface (T08, T09, T10) podem divergir.

Este ticket fixa as três formas e o arquivo que vai para a OCI. O briefing pede saída validada com tipagem estrita.

Leia antes: `docs/product-specs/conteudos-e-formatos.md` e `docs/product-specs/pacote-json-e-armazenamento.md`.

## Escopo

Modelos Pydantic do conteúdo de cada formato, da resposta do agente `escreve` e do arquivo JSON da OCI.

## Fora do escopo

- Prompts e chamadas ao modelo (T20).
- Gravar o arquivo na OCI (T22).
- Tipos TypeScript. Os leitores da interface copiam as formas deste ticket.

## Contrato

Em `backend/app/services/content_schemas.py`. Todo modelo recusa campos extras (`extra="forbid"`), tira os espaços das pontas dos textos e recusa texto vazio.

```python
class TutorialSection(BaseModel):
    title: str
    body: str  # Markdown


class TutorialContent(BaseModel):
    summary: str  # resumo de abertura
    sections: list[TutorialSection]  # de 1 a 8
    takeaways: list[str]  # lista "Para levar", de 1 a 5


class Flashcard(BaseModel):
    front: str
    back: str
    hint: str | None = None


class FlashcardsContent(BaseModel):
    introduction: str
    cards: list[Flashcard]  # de 8 a 12


class QuizQuestion(BaseModel):
    prompt: str
    options: list[str]  # exatamente 4, sem repetição
    correct_index: int  # de 0 a 3
    explanation: str


class QuizContent(BaseModel):
    questions: list[QuizQuestion]  # exatamente 5


class GeneratedBase(BaseModel):
    title: str  # de 1 a 255 caracteres
    estimated_minutes: int  # de 1 a 600
    key_concepts: list[str]  # de 1 a 10
    prerequisites: list[str]  # de 0 a 10


class GeneratedTutorial(GeneratedBase):
    content: TutorialContent


class GeneratedFlashcards(GeneratedBase):
    content: FlashcardsContent


class GeneratedQuiz(GeneratedBase):
    content: QuizContent


CONTENT_MODELS: dict[ContentFormat, type[BaseModel]]
GENERATED_MODELS: dict[ContentFormat, type[GeneratedBase]]


def parse_content(content_format: ContentFormat, data: dict[str, Any]) -> BaseModel: ...


class ContentPackage(BaseModel):
    format: ContentFormat
    audience_level: AudienceLevel
    niche: str  # niche.slug
    title: str
    content: dict[str, Any]
    estimated_minutes: int
    key_concepts: list[str]
    prerequisites: list[str]
    grounding_score: float  # de 0 a 1
    clarity: ClarityLevel
    review_notes: str
```

`parse_content` valida `data` com o modelo do formato e devolve a instância. Um JSON inválido levanta `pydantic.ValidationError`.

`ContentPackage` é o arquivo da OCI. Ele tem exatamente os onze campos da tabela "O que entra no arquivo JSON de um conteúdo", em `pacote-json-e-armazenamento.md`.

### Exemplos

Tutorial:

```json
{
  "summary": "Uma VCN é a rede privada da sua empresa dentro da nuvem.",
  "sections": [
    {"title": "O que é uma VCN", "body": "Uma **VCN** é uma rede virtual..."}
  ],
  "takeaways": ["A VCN isola os seus recursos."]
}
```

Flashcards:

```json
{
  "introduction": "Cartões sobre os conceitos de rede da OCI.",
  "cards": [
    {"front": "O que é uma VCN?", "back": "Uma rede virtual privada.", "hint": "Pense em um terreno cercado."}
  ]
}
```

Quiz:

```json
{
  "questions": [
    {
      "prompt": "Qual recurso controla o tráfego de entrada?",
      "options": ["Security List", "Bucket", "Compartment", "Tenancy"],
      "correct_index": 0,
      "explanation": "A Security List define as regras de entrada e de saída."
    }
  ]
}
```

Os exemplos de flashcards e de quiz estão curtos para caber aqui. Um JSON válido tem de 8 a 12 cartões e 5 perguntas.

## Detalhes técnicos

- `ContentFormat`, `AudienceLevel` e `ClarityLevel` vêm de `app.models`.
- `takeaways` não está em `conteudos-e-formatos.md`. Ele vem do layout "Resumo" dos documentos de design, que a especificação manda usar no tutorial. Acrescente a lista "Para levar" à seção "Tutorial" de `docs/product-specs/conteudos-e-formatos.md` neste mesmo PR.
- O módulo não importa banco, OCI nem Gemini.

## Critérios de aceite

- [ ] Os modelos cumprem o contrato, com os limites de quantidade.
- [ ] `CONTENT_MODELS` e `GENERATED_MODELS` têm uma entrada para cada valor de `ContentFormat`.
- [ ] `ContentPackage` serializa para um JSON com exatamente onze chaves.
- [ ] `conteudos-e-formatos.md` cita a lista "Para levar".
- [ ] Os hooks e os testes passam, com cobertura de 90% ou mais.

## Cenários de teste

1. Um exemplo válido de cada formato passa por `parse_content`.
2. Flashcards com 7 e com 13 cartões falham. Com 8 e com 12, passam.
3. Quiz com 4 e com 6 perguntas falha.
4. Pergunta com 3 opções, com duas opções iguais ou com `correct_index` 4 falha.
5. Tutorial sem seção ou sem `takeaways` falha.
6. Texto só com espaços falha em qualquer campo de texto obrigatório.
7. Um campo extra falha em qualquer modelo.
8. `hint` ausente e `hint` nulo passam.
9. `ContentPackage` vai para JSON e volta sem perder dados.
