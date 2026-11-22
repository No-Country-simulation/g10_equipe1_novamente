---
id: T35
title: Reescreva o README, atualize o diagrama e escreva o guia de instalação
blocked_by: [T29, T31, T32, T33, T42]
touches:
  - README.md
  - development.md
  - docs/system-diagram/arquitetura.excalidraw
  - docs/system-diagram/arquitetura.png
  - docs/ARCHITECTURE.md
  - docs/generated/db-schema.md
  - docs/product-specs/index.md
  - docs/product-specs/visao-e-publico.md
  - docs/product-specs/escopo-do-mvp.md
  - docs/product-specs/criar-curso.md
  - docs/product-specs/conteudos-e-formatos.md
  - docs/product-specs/fidelidade-e-qualidade.md
  - docs/product-specs/pacote-json-e-armazenamento.md
  - docs/product-specs/telas.md
  - AGENTS.md
  - examples/README.md
  - examples/lei-de-acesso-a-informacao.quiz.json
executor: agente
size: 3
---

# T35 - Reescreva o README, atualize o diagrama e escreva o guia de instalação

O README e o guia da raiz descrevem o template ou uma proposta anterior. O checklist em [`visao-e-publico.md`](../product-specs/visao-e-publico.md) pede documentação com diagrama. T29 entrega `planeja`, T31 entrega o teste sem credenciais, T32 e T33 fecham o ciclo de vida dos cursos e T42 corrige o revisor do quiz.

Siga o [guia de escrita](../WRITING.md). Use o código e os [documentos do produto](../product-specs/index.md) que estiverem no `master` quando executar o ticket. O escopo é documentação. Se o guia revelar um defeito no produto, registre-o no PR.

## README

Escreva para quem vai avaliar ou rodar o NovaMente pela primeira vez. Inclua:

1. O problema e o que a pessoa escolhe ao criar um curso. Cite os três formatos e a regra de publicação com apoio nos documentos.
2. O PNG e um resumo das cinco partes de [`ARCHITECTURE.md`](../ARCHITECTURE.md). Linke os doze passos da geração. Distinga o que já roda do deploy planejado.
3. Os cenários da demonstração e um trecho identificado do pacote JSON descrito na [especificação do pacote](../product-specs/pacote-json-e-armazenamento.md). Linke a especificação e o arquivo de fontes entregue por T13. O pacote publicado na OCI tem estrutura diferente da resposta HTTP do curso.
4. O caminho para rodar localmente e um link para `development.md`. Cite as tecnologias a partir de `backend/pyproject.toml`, `frontend/package.json` e `compose.yml`. Se incluir versões, indique se vêm do lockfile, de uma faixa de dependência ou de uma tag de imagem.
5. Links para a arquitetura, as especificações, os tickets e `AGENTS.md`. Preserve a atribuição da equipe e linke `LICENSE`.

## Guia de instalação

Em `development.md`, escreva passos que funcionem em um clone novo:

1. Confira Python em `.python-version`, Bun no workflow Playwright, Docker Compose e `uv`. Instale as dependências com `uv sync --locked` em `backend/` e `bun ci` na raiz.
2. Copie `.env.example` e `frontend/.env.example` para os respectivos `.env`. Explique os segredos e as variáveis que o produto usa. Para o Gemini, linke "Modelos de IA" da arquitetura e use só documentos públicos ou fictícios. Para OCI, use bucket privado, a API signing key fora do repositório e `uv run python scripts/verify_storage.py` em `backend/`.
3. Suba o banco com `docker compose up -d --wait db` na raiz. Rode `uv run bash scripts/prestart.sh` e `uv run fastapi dev` em `backend/`. Rode `bun run dev` na raiz. Indique as URLs do frontend, da API e do Swagger. Se a porta 5432 já estiver em uso, mostre como apontar `DATABASE_URL` para um banco de desenvolvimento separado.
4. Crie uma conta e o primeiro curso pela interface. Use um documento de exemplo, acompanhe até "Pronto", abra o leitor e exclua o curso de teste. Explique como confirmar a limpeza do prefixo depois que o processamento em segundo plano terminar.
5. Documente os comandos de teste de [`docs/tickets/README.md`](README.md) e o caminho controlado de T31 com `compose.playwright.yml`. Use o comando verificado no ticket, inclua as migrations e deixe claro que o conteúdo controlado só é gerado pelo servidor de teste. Sem chaves, o servidor padrão sobe e a geração real depende de configurar Gemini e OCI.
6. Registre os problemas de instalação reproduzidos. Para cada um, dê a mensagem observada e a ação que resolveu.

O caminho com chaves usa o backend local. Antes de descrever geração com o backend do Compose comum, confira quais variáveis as composições realmente passam ao contêiner.

## Diagrama e documentos

Atualize [`arquitetura.excalidraw`](../system-diagram/arquitetura.excalidraw) e exporte [`arquitetura.png`](../system-diagram/arquitetura.png) da mesma fonte. Mostre `planeja` entre busca e `escreve`, com plano e chunks. Confira as setas e os números com os doze passos da arquitetura. A decisão após `revisa` exige foco coberto e todas as afirmações sustentadas. Remova a referência à v0 de um documento e uma saída. Mostre a recuperação periódica e a limpeza persistente da OCI. Confira os rótulos do contêiner e da VM com `backend/Dockerfile` e os arquivos de implantação. Identifique componentes planejados, como o deploy se T36 ainda não estiver no `master`.

Em `docs/ARCHITECTURE.md`, confira as tabelas "O sistema tem cinco partes", "Mapa do código" e "Decisões". Atualize o parágrafo de "Falhas e recuperação" após T32 e T33. Mantenha a seção "Testes" coerente com T31. Em `docs/generated/db-schema.md`, registre `course.generation_id` e `course_object_cleanup` conforme os modelos e migrations. Identifique o SVG como o ERD v5 de base e mantenha o texto alinhado com o esquema atual.

Nos arquivos de produto listados em `touches`, atualize estados e referências obsoletas ao README. Confira cada "Existe" contra o código e cada link com o arquivo ou âncora de destino. Use as fontes e o roteiro de `demonstracao.md` entregues por T13. Em `AGENTS.md`, atualize a descrição do esquema e indique que `README.md` e `development.md` valem. Os guias de contribuição e deploy ficam fora deste ticket.

## Critérios de aceite

- [ ] O README descreve o produto do `master`, mostra o PNG e aponta para o JSON real da demonstração.
- [ ] Os dois arquivos do diagrama correspondem. O PNG está legível no README renderizado.
- [ ] Os estados e os links novos batem com o código e os arquivos no branch do PR.
- [ ] Em um clone do branch do PR, siga só o guia. Sem credenciais, o cenário de T31 chega ao leitor pelo Compose de teste. Com credenciais de desenvolvimento, crie, leia e exclua um curso pela aplicação comum e confirme a limpeza da OCI. Se faltar acesso externo, registre a etapa pendente para a revisão.
- [ ] O PR relata o clone usado, o resultado de cada caminho e as correções feitas no guia. Os hooks passam. Mire menos de 400 linhas escritas à mão. O diff serializado do Excalidraw é revisto pelo PNG.
