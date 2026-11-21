# Como escrever casos de avaliação

Use um arquivo JSON por documento. Salve os arquivos em `examples/evals/`, a pasta que o CI valida. Em `document`, escreva o caminho a partir da raiz do repositório. O script aceita Markdown (`.md`) e PDF com texto. Em `niche`, use `geral`, `fintech`, `saude` ou `e-commerce`. O banco já traz esses quatro nichos.

## Crie o arquivo de casos

Na raiz do repositório, abra o arquivo em um editor de texto.

```bash
nano examples/evals/pods.json
```

Cole o exemplo, adapte os campos ao seu documento e salve. No `nano`, pressione `Ctrl+O`, `Enter` e `Ctrl+X`. O exemplo supõe que `examples/sources/pods.md` contém a frase copiada em `expected`. Troque o caminho, a frase e os casos pelos do seu documento. Mantenha as três listas no arquivo. Você pode deixar uma lista vazia com `[]`, desde que escreva pelo menos um caso em outra lista.

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

- Em `retrieval`, escreva uma pergunta que o documento responde. Copie para `expected` uma frase curta de um único parágrafo. Copie do próprio arquivo `.md` para preservar marcas de negrito, links e crases que a página formatada esconde. Preserve maiúsculas e acentos. A busca divide o documento em trechos de até 1.000 caracteres. A frase precisa caber inteira em um trecho.
- Em `review`, escreva um conteúdo sobre o `focus` usando fatos do documento. Dê a cada caso um `id` próprio. Para um conteúdo fiel, use `null` em `planted_error`. Para plantar um erro, copie um caso fiel, troque o `id`, substitua um fato por um fato errado e copie o texto exato desse erro para `planted_error`. No quiz, plante o erro no enunciado, na resposta correta ou na justificativa.
- Em `generation`, escreva o `focus` e escolha o formato e o público. O script pede ao Gemini que escreva e revise o conteúdo.

Os valores de `format` são `tutorial`, `flashcards` e `quiz`. Os valores de `audience_level` são `non_technical`, `technical_basic` e `technical_advanced`. Mantenha apenas os campos de `content` do formato escolhido.

## Monte o conteúdo de cada formato

O tutorial do exemplo tem um resumo em `summary`, de 1 a 8 seções em `sections` e de 1 a 5 conclusões em `takeaways`. Cada seção tem um título e um texto.

Para criar outro caso, copie o objeto `pods-fiel` da lista `review` e troque o `id`, o `focus`, o `format` e o `content`.

### Flashcards

Use `format` igual a `flashcards`. Em `content`, escreva uma introdução em `introduction` e inclua de 8 a 12 cartões em `cards`. Cada cartão tem uma pergunta em `front` e uma resposta em `back`. Você pode incluir uma dica em `hint`.

```json
{
  "introduction": "Conceitos básicos de Pods.",
  "cards": [
    {"front": "Qual é a menor unidade que o Kubernetes implanta?", "back": "Um Pod."},
    {"front": "Quantos contêineres cabem em um Pod?", "back": "Um ou mais."},
    {"front": "Os contêineres de um Pod dividem a rede?", "back": "Sim.", "hint": "Pense no endereço IP."},
    {"front": "Os contêineres de um Pod dividem armazenamento?", "back": "Sim."},
    {"front": "Em que nó rodam os contêineres de um Pod?", "back": "No mesmo nó."},
    {"front": "Qual recurso pode gerenciar Pods de uma aplicação?", "back": "Um Deployment."},
    {"front": "Quando rodam os contêineres de inicialização?", "back": "Durante a inicialização do Pod."},
    {"front": "Para que serve um contêiner efêmero?", "back": "Para investigar problemas em um Pod em execução."}
  ]
}
```

### Quiz

Use `format` igual a `quiz`. Em `content`, inclua exatamente 5 perguntas em `questions`. Cada pergunta tem um enunciado em `prompt`, 4 opções diferentes em `options` e uma justificativa em `explanation`. Em `correct_index`, use um número de 0 a 3 para apontar a resposta correta. O número 0 aponta a primeira opção, 1 a segunda, 2 a terceira e 3 a quarta.

```json
{
  "questions": [
    {
      "prompt": "Qual é a menor unidade que o Kubernetes implanta?",
      "options": ["Pod", "Nó", "Cluster", "Namespace"],
      "correct_index": 0,
      "explanation": "O Pod é a menor unidade de implantação do Kubernetes."
    },
    {
      "prompt": "Quantos contêineres um Pod pode conter?",
      "options": ["Nenhum", "Um ou mais", "Sempre dois", "Pelo menos três"],
      "correct_index": 1,
      "explanation": "Um Pod pode conter um único contêiner ou agrupar vários."
    },
    {
      "prompt": "Qual recurso os contêineres de um Pod compartilham?",
      "options": ["O cluster inteiro", "O acesso de administrador", "A rede do Pod", "A imagem do contêiner"],
      "correct_index": 2,
      "explanation": "Os contêineres de um Pod compartilham os recursos de rede do Pod."
    },
    {
      "prompt": "Onde rodam os contêineres de um Pod?",
      "options": ["Em nós distintos", "Em clusters distintos", "Fora do cluster", "No mesmo nó"],
      "correct_index": 3,
      "explanation": "O Kubernetes coloca os contêineres de um Pod no mesmo nó."
    },
    {
      "prompt": "Qual recurso pode gerenciar Pods de uma aplicação?",
      "options": ["Deployment", "Contêiner efêmero", "Endereço IP", "Imagem de contêiner"],
      "correct_index": 0,
      "explanation": "Um Deployment pode criar e gerenciar as réplicas dos Pods."
    }
  ]
}
```

## Quanto da cota a avaliação usa

- A indexação usa um embedding por trecho do documento.
- Cada caso de busca, revisão ou geração usa um embedding para buscar trechos.
- Cada caso de revisão usa uma chamada de texto.
- Cada caso de geração usa até quatro chamadas de texto. Com a etapa `planeja` do T29, o limite sobe para cinco.
- Cada pista do relatório usa mais um embedding para buscar o trecho mais próximo da afirmação.

## Valide o arquivo sem gastar cota

Na raiz do repositório, crie o `.env` se ele ainda não existir.

```bash
cp .env.example .env
```

Valide o arquivo. O comando funciona com o banco desligado e sem chave do Gemini. Se salvou o JSON com outro nome, troque `pods.json` pelo nome que você escolheu.

```bash
(cd backend && uv run python scripts/evaluate.py --check ../examples/evals/pods.json)
```

Se o comando indicar uma correção, abra o JSON, faça a correção e repita a validação.

```bash
nano examples/evals/pods.json
```

## Rode a avaliação com o Gemini

Na raiz do repositório, abra o `.env`.

```bash
nano .env
```

Na linha `GEMINI_API_KEY=`, tire o `#` do início, se houver, e escreva sua chave depois do `=`. Para avaliar o revisor ou a geração, tire o `#` da linha `GEMINI_GENERATION_MODEL=` e use o nome de modelo escolhido pela equipe. Salve com `Ctrl+O`, `Enter` e `Ctrl+X`.

Ainda na raiz, inicie o banco.

```bash
docker compose up -d --wait db
```

Entre em `backend/`, instale as dependências e aplique as migrations. As migrations preparam as tabelas e os quatro nichos.

```bash
cd backend && uv sync && uv run bash scripts/prestart.sh
```

Em `backend/`, rode a avaliação e grave o relatório.

```bash
uv run python scripts/evaluate.py ../examples/evals/pods.json > relatorio.md
```

Leia o relatório.

```bash
cat relatorio.md
```

Confira no documento se o trecho da pista sustenta a afirmação. A posição do trecho ajuda a investigar a reprovação.
