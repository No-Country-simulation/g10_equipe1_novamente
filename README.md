# NovaMente

O NovaMente transforma documentação técnica em material de estudo para quem está aprendendo ou preparando um treinamento. Ao criar um curso, você envia até três documentos, escolhe o título, o setor, o nível de público e os formatos que quer gerar: tutorial, flashcards e quiz. O produto publica um conteúdo quando a revisão confirma que ele cobre o foco e que todas as afirmações técnicas têm apoio nos trechos dos documentos.

## Arquitetura

![Diagrama das cinco partes do NovaMente e dos 12 passos da geração](docs/system-diagram/arquitetura.png)

- O **frontend React** oferece as telas de conta, cursos e leitores.
- O **backend FastAPI** valida as entradas, executa a geração em segundo plano e decide o que publicar. O LangGraph encadeia `planeja`, `escreve` e `revisa`.
- O **PostgreSQL com pgvector** guarda os cursos, os chunks, os embeddings, os conteúdos publicados e as citações.
- O **OCI Object Storage** guarda os documentos originais e um pacote JSON por conteúdo publicado, em um bucket privado.
- A **API Gemini** gera os embeddings e o texto usado pelos agentes.

As cinco partes já funcionam no ambiente de desenvolvimento. O deploy está planejado para uma VM `VM.Standard.A2.Flex` (ARM) na OCI. Veja [os doze passos da geração](docs/ARCHITECTURE.md#a-criação-de-um-curso-segue-doze-passos).

## Demonstração

- **Open Finance** gera tutorial e flashcards para dois públicos: não técnico e técnico avançado.
- **Regulamento do Pix**, na redação de 2020, serve de fonte para um tutorial de nível técnico básico.
- **Lei de Acesso à Informação** serve de fonte para um quiz de nível técnico básico.

Veja o [roteiro da demonstração](docs/product-specs/demonstracao.md) e os [arquivos de entrada, fontes e condições de uso](examples/README.md).

Exemplo de campos do pacote JSON de um quiz.

```json
{
  "format": "quiz",
  "audience_level": "technical_basic",
  "niche": "geral",
  "title": "Pedidos de acesso à informação",
  "grounding_score": 1.0
}
```

O bucket guarda um pacote por conteúdo. A API entrega os conteúdos dentro da resposta do curso, com estados e citações. Veja a [especificação do pacote JSON](docs/product-specs/pacote-json-e-armazenamento.md).

## Rode localmente

O backend usa Python, FastAPI, SQLModel e LangGraph. O frontend usa React, TypeScript, Vite e TanStack Router. O Docker Compose sobe o PostgreSQL com pgvector. O `uv` instala as dependências Python e o Bun instala e executa as do frontend.

O [guia de instalação](development.md) leva do clone ao primeiro curso com Gemini e OCI. Ele também mostra como testar a geração no navegador com respostas controladas, sem credenciais externas.

## Documentação

- [Arquitetura e fluxo de geração](docs/ARCHITECTURE.md)
- [Especificações do produto](docs/product-specs/index.md)
- [Fluxo e lista de tickets](docs/tickets/README.md)
- [Mapa da base de conhecimento](AGENTS.md)

Projeto da Equipe 1 do G10, Simulação No-Country. [Licença MIT](LICENSE).
