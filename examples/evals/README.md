# Como escrever casos de avaliação

Use um arquivo JSON por documento. Em `document`, escreva o caminho a partir da raiz do repositório. O script aceita Markdown (`.md`) e PDF com texto. Em `niche`, informe o código do nicho no banco, como `geral`.

O exemplo abaixo supõe que `examples/sources/pods.md` contém a frase copiada em `expected`. Troque o caminho, a frase e os casos pelos do seu documento. Mantenha as três listas no arquivo. Você pode deixar uma lista vazia com `[]`, desde que escreva pelo menos um caso em outra lista.

```json
{
  "document": "examples/sources/pods.md",
  "niche": "geral",
  "retrieval": [
    {
      "question": "Qual é a menor unidade que o Kubernetes implanta?",
      "expected": "Um Pod é a menor unidade que o Kubernetes pode implantar."
    }
  ],
  "review": [
    {
      "id": "pods-fiel",
      "focus": "Implantação de Pods",
      "audience_level": "technical_basic",
      "format": "tutorial",
      "planted_error": null,
      "content": {
        "summary": "O Kubernetes implanta aplicações em Pods.",
        "sections": [
          {
            "title": "A unidade de implantação",
            "body": "Um Pod é a menor unidade que o Kubernetes pode implantar."
          }
        ],
        "takeaways": ["O Pod é a menor unidade de implantação."]
      }
    }
  ],
  "generation": [
    {
      "focus": "Implantação de Pods",
      "audience_level": "non_technical",
      "format": "quiz"
    }
  ]
}
```

- Em `retrieval`, escreva uma pergunta que o documento responde. Copie uma frase curta de um único parágrafo para `expected`. Preserve maiúsculas e acentos. A frase precisa caber inteira em um trecho da busca.
- Em `review`, escreva um conteúdo sobre o `focus` usando fatos do documento. Dê a cada caso um `id` próprio. Para um conteúdo fiel, use `null` em `planted_error`. Para plantar um erro, copie um caso fiel, troque o `id`, substitua um fato por um fato errado e copie o texto exato desse erro para `planted_error`. No quiz, plante o erro no enunciado, na resposta correta ou na justificativa.
- Em `generation`, escreva o `focus` e escolha o formato e o público. O script pede ao Gemini que escreva e revise o conteúdo.

Os valores de `format` são `tutorial`, `flashcards` e `quiz`. Os valores de `audience_level` são `non_technical`, `technical_basic` e `technical_advanced`. Para ver os campos de `content` de cada formato, consulte [os modelos de conteúdo](../../backend/app/services/content_schemas.py). Mantenha apenas os campos do formato escolhido.

## Quanto da cota a avaliação usa

- A indexação usa um embedding por trecho do documento.
- Cada caso de busca, revisão ou geração usa um embedding para buscar trechos.
- Cada caso de revisão usa uma chamada de texto.
- Cada caso de geração usa até quatro chamadas de texto. Com a etapa `planeja` do T29, o limite sobe para cinco.
- Cada pista do relatório usa mais um embedding para buscar o trecho mais próximo da afirmação.

## Como validar e rodar

Na pasta `backend/`, com o `.env` de desenvolvimento preparado, valide o arquivo. Esse comando funciona com o banco desligado e sem chave do Gemini.

```bash
uv run python scripts/evaluate.py --check ../examples/evals/pods.json
```

Para medir, suba o banco com as migrations aplicadas e confira se o nicho existe. Defina `GEMINI_API_KEY` no `.env`. Para casos de revisão ou geração, defina também `GEMINI_GENERATION_MODEL`.

```bash
uv run python scripts/evaluate.py ../examples/evals/pods.json > relatorio.md
```

Confira no documento se o trecho da pista sustenta a afirmação. A posição do trecho ajuda a investigar a reprovação.
