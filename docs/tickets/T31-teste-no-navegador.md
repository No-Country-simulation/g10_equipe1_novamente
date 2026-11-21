---
id: T31
title: Teste no navegador o caminho da criação do curso até a leitura do conteúdo gerado
blocked_by: [T08, T09, T10, T17, T27, T28, T29, T38]
touches:
  - backend/tests/playwright_app.py
  - compose.playwright.yml
  - .github/workflows/playwright.yml
  - frontend/tests/generation.spec.ts
  - docs/ARCHITECTURE.md
executor: agente
size: 3
---

# T31 - Teste no navegador o caminho da criação do curso até a leitura do conteúdo gerado

## Contexto

`new-course.spec.ts` intercepta o POST de criação para testar o sucesso do formulário. `course.spec.ts` usa cursos criados pela API privada. Os testes de T28 exercitam a tarefa de fundo sem navegador. Falta percorrer o caminho que liga essas partes.

Leia [T28](completed/T28-tarefa-de-fundo.md), [T29](completed/T29-etapa-planeja.md) e as seções "A criação de um curso segue doze passos" e "Testes" da [arquitetura](../ARCHITECTURE.md).

## Backend do Playwright

Crie `backend/tests/playwright_app.py` como ponto de entrada do servidor de teste. Importe `app.main.app` e configure as respostas controladas antes de o servidor aceitar pedidos:

1. Crie uma instância de `InMemoryStorage` e registre `app.dependency_overrides[get_storage]` para devolver sempre essa instância. `create_course` já passa o armazenamento que usou para gravar os documentos a `run_course_generation`.
2. Troque `app.core.llm.embed_texts` por uma função que devolve um vetor não nulo de `retrieval.EMBEDDING_DIMENSIONS` (768) por texto, para `task="document"` e `task="query"`. Use um Markdown curto que gere um só chunk e confira a citação desse chunk.
3. Troque `app.core.llm.generate_structured` por uma função com a assinatura existente. Escolha a resposta pelo `response_model` e valide com o próprio modelo. Use os modelos de plano de `planner`, os modelos `GENERATED_MODELS` de `content_schemas` e `reviewer._ReviewOut`. Um modelo inesperado deve falhar com erro claro.

Use um plano válido por formato, com os itens exigidos pelo modelo e `chunk_numbers=[1]`. Na resposta controlada de escrita, confira que o prompt recebeu um tópico do plano de teste. Use um tutorial com uma seção e um item em "Para levar", oito flashcards e cinco perguntas de quiz com quatro opções distintas cada. A revisão aprovada usa `focus_covered=True`, uma afirmação sustentada com `chunk_number=1`, clareza alta e observação fixa. No curso de falha, use um título que começa com `[falha]` e devolva `focus_covered=False` ao revisar esse foco. A tarefa, o grafo com `planeja`, `escreve` e `revisa`, a busca no pgvector, o cálculo da nota e a publicação continuam executando o código do produto.

Crie `compose.playwright.yml` como sobreposição explícita de `compose.yml` e `compose.override.yml`. Altere só o serviço `backend`: monte `playwright_app.py` como leitura e execute o módulo com Uvicorn, por exemplo `uvicorn --app-dir /app/backend/tests playwright_app:app --host 0.0.0.0 --port 8000`. Use um processo para manter o mesmo armazenamento em memória. O [Dockerfile do backend](../../backend/Dockerfile) copia `backend/app` e `backend/scripts`. O módulo montado fica em `backend/tests`, fora da imagem. A aplicação de desenvolvimento e a de produção mantêm seus pontos de entrada.

No passo "Run Playwright tests" de `.github/workflows/playwright.yml`, use os três arquivos Compose, nessa ordem. Depois das migrations, espere o healthcheck do backend com `docker compose up -d --wait backend` antes de rodar o Playwright. Preserve a divisão em shards, os relatórios e `--fail-on-flaky-tests`. O filtro `compose*.yml` já inclui a sobreposição. Mantenha os testes existentes e as interceptações de falhas de rede e de armazenamento.

## Cenários no navegador

Crie `frontend/tests/generation.spec.ts`. Use `createUser` de `tests/utils/privateApi.ts` e `logInUser` de `tests/utils/user.ts`. Use os seletores de `new-course.spec.ts` como referência. Crie o curso pela tela, com um único Markdown válido com uma frase reconhecível. Nos dois cenários, confira o HTTP 201 do POST real e use a URL do curso devolvido. Espere os estados finais com as asserções do Playwright. O estado inicial pode passar antes da primeira renderização.

1. **Da criação aos leitores.** Escolha "Geral", "Técnico básico" e os três formatos. Confira três cartões "Pronto", a linha "Pronto" na lista e o leitor de cada formato. No tutorial, confira resumo, seção, "Para levar", 100% de fidelidade e a frase do arquivo em "Trechos citados". Em flashcards, clique em "Virar cartão" e confira o verso. No quiz, escolha uma opção e confira a justificativa exibida.
2. **Revisão que reprova.** Use o título com `[falha]` e só a saída de tutorial. Confira "A geração falhou" e "O documento não trata do assunto pedido." na página do curso e "Falhou" na lista. O leitor não aparece.

## Como verificar

Na raiz de um clone de teste, prepare `.env` e `frontend/.env` a partir dos exemplos. Use um projeto Compose próprio e deixe livres as portas que ele publica. Rode os comandos no mesmo shell:

```bash
export COMPOSE_FILE=compose.yml:compose.override.yml:compose.playwright.yml
export COMPOSE_PROJECT_NAME=novamente-e2e
docker compose build backend playwright
docker compose run --rm backend bash scripts/prestart.sh
docker compose up -d --wait backend
docker compose run --rm playwright bunx playwright test tests/generation.spec.ts
```

Registre o resultado do teste e a execução completa do Playwright no CI. Atualize o item "Frontend" da seção "Testes" de [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) com a sobreposição, os comandos e as fronteiras substituídas. Mire menos de 400 linhas no PR, incluindo os dois cenários.

## Critérios de aceite

- [ ] Os dois cenários passam com Chromium, PostgreSQL e a API do produto. Nenhum deles intercepta as rotas de curso, cria o curso pela API de seed ou precisa de credenciais externas.
- [ ] A saída aprovada passa pelo grafo e a saída reprovada resulta da decisão do grafo. O leitor mostra a citação do Markdown enviado.
- [ ] O Compose de teste monta o ponto de entrada só quando a sobreposição é carregada. Nenhum arquivo de `backend/app`, variável de produto ou imagem de produção contém o modo de teste.
- [ ] O Playwright do CI mantém os testes existentes e executa os dois cenários novos. Os hooks, o lint e o build do frontend passam.
