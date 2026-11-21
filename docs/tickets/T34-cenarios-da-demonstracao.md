---
id: T34
title: Rode os cenários da demonstração e guarde os JSON
blocked_by: [T13, T31, T32, T42]
touches:
  - examples/outputs/
  - examples/teste-de-adaptacao/roteiro.md
  - examples/README.md
  - docs/product-specs/demonstracao.md
executor: agente
size: 3
---

# T34 - Rode os cenários da demonstração e guarde os JSON

## Contexto

O [roteiro da demonstração](../product-specs/demonstracao.md#roteiro-da-demonstração) pede quatro cursos, seis conteúdos, os tempos medidos e os JSON publicados. A equipe também precisa abrir os cursos durante a apresentação. Este ticket entrega os arquivos, o guia para recriar os cursos e a passagem para quem apresenta. T43 usa os seis conteúdos para medir a adaptação ao público e a clareza.

Leia a [especificação do pacote](../product-specs/pacote-json-e-armazenamento.md), as seções "Erros que a pessoa pode ver" e "Nova tentativa" de [Criar um curso](../product-specs/criar-curso.md) e a [lista de fontes](../../examples/README.md).

## Cursos

Use o título como está na tabela. O produto usa esse título como foco de cada saída.

| Curso | Título | Documento em `examples/sources/` | `audience_level` | Setor | Saídas, nesta ordem |
| --- | --- | --- | --- | --- | --- |
| A | Compartilhar dados e revogar o consentimento | `open-finance.md` | `non_technical` | `fintech` | `flashcards`, `tutorial` |
| B | Implementar a jornada de compartilhamento | `open-finance.md` | `technical_advanced` | `fintech` | `flashcards`, `tutorial` |
| C | Entender a iniciação e a liquidação de um Pix | `regulamento-do-pix.md` | `technical_basic` | `fintech` | `tutorial` |
| D | Receber pedidos de informação e encaminhar recursos | `lei-de-acesso-a-informacao.md` | `technical_basic` | `geral` | `quiz` |

## Gere os cursos

1. Na raiz, suba o PostgreSQL se necessário e rode `bash scripts/worktree-setup.sh T34`. Configure o `.env` do worktree com os modelos e as credenciais de desenvolvimento autorizados. Confirme o banco e o bucket ativos. Em `backend/`, rode `uv run python scripts/verify_storage.py`.
2. Em `backend/`, suba a API com `uv run fastapi run --port 8000` ou escolha outra porta livre. Guarde o log fora do repositório. No `frontend/.env`, aponte `VITE_API_URL` para essa API.
3. Use o Swagger em `/docs` ou um cliente HTTP. Crie uma conta de demonstração em `POST /api/v1/users/signup`. Em `POST /api/v1/login/access-token`, envie o e-mail em `username` e a senha em `password` no formulário. Use o token Bearer para ler os IDs dos setores em `GET /api/v1/niches/`. Guarde o acesso da conta fora do repositório.
4. Envie cada curso com `POST /api/v1/courses/` em `multipart/form-data`. Envie `title`, `niche_id`, `audience_level`, o arquivo em `files` e um campo `formats` para cada saída, na ordem da tabela.
5. Consulte `GET /api/v1/courses/{course_id}` a cada 10 segundos. Espere os conteúdos saírem de `pending` e `running` antes de abrir o próximo curso. Confira `documents[].status` igual a `indexed` e cada `contents[].status` igual a `succeeded`. O curso pode estar `ready` desde a primeira publicação.

Os quatro cursos usam cerca de 321 embeddings e até 30 chamadas de texto antes das novas tentativas. Confira o saldo do projeto, incluindo a avaliação de T42 se ela rodou no mesmo dia. Os limites medidos estão na seção "Modelos de IA" da [arquitetura](../ARCHITECTURE.md#modelos-de-ia).

### Recupere uma falha

A nova tentativa da interface chama `POST /api/v1/courses/{course_id}/contents/{content_id}/retry`. A rota aceita conteúdo `failed` e retorna HTTP 202. Se retornar 409 por interrupção, aguarde a recuperação periódica de T32 e confira os estados. Aguarde o resultado antes de repetir. Registre a data e hora, a mensagem, o diagnóstico e o resultado de cada tentativa.

| Sinal | Ação |
| --- | --- |
| HTTP 503 do Gemini, 429 ou "A geração foi interrompida. Tente novamente." | O cliente Gemini já repete 429 e 503. Espere dois minutos para 503 ou limite por minuto. Para cota diária esgotada, espere a renovação. Para interrupção, confirme que o serviço voltou e que o conteúdo está `failed`. Faça até três novas tentativas manuais por conteúdo para falhas temporárias. |
| Documento `failed` | Confira `documents[].error_message` e o log da indexação. Corrija a causa ou aguarde se ela for temporária. Tente um conteúdo `failed` para retomar a indexação. Depois, tente só as saídas que ainda estiverem `failed`. A tarefa pula documentos já `indexed`. |
| "A API devolveu uma resposta vazia." ou "A resposta não segue o schema de `_ReviewOut`" | Faça uma nova tentativa com as mesmas entradas. Se o erro de resposta persistir, registre a etapa e peça decisão à equipe. |
| "Afirmações sem apoio no documento:" ou "O documento não trata do assunto pedido." | Confira o foco, as afirmações disponíveis e o apoio no documento. Se a fonte sustenta o foco, faça uma nova tentativa com as mesmas entradas. O grafo já faz a reescrita prevista por T40 quando ela se aplica. |
| Falha persistente ou falta de apoio ao foco | Registre o que conseguiu confirmar e peça decisão à equipe. Corrija configurações inválidas antes de repetir. Mudar o título muda o foco e o roteiro. Se a equipe aprovar a mudança, atualize a tabela de demonstração e gere de novo apenas o curso afetado, com o título aprovado. |

## Guarde a evidência

- Use `course_id=... content_id=... formato=... estado=... tentativas=... segundos=...` para o tempo por conteúdo. `tentativas` conta as escritas do grafo. Conte as novas tentativas manuais à parte.
- Use `course_id=... estado=... segundos=...` para o tempo de cada tarefa do curso. Se houve nova tentativa, registre a primeira tarefa, as seguintes e o tempo total até todas as saídas ficarem prontas. Use um cronômetro para o total e marque quando faltar uma linha de log. Identifique os tempos com nova tentativa.
- Para cada saída publicada, leia `oci_object_key` no detalhe do curso. Em `backend/`, busque os bytes com `app.core.storage.get_storage().get(key)`. Valide com `ContentPackage.model_validate_json` e com `parse_content(package.format, package.content)`, ambos de `app.services.content_schemas`.
- Salve cada pacote em `examples/outputs/` como `<letra>-<documento>-<formato>.json`. Use um objeto por linha para cada seção, cartão ou pergunta e mantenha as chaves da raiz legíveis. Compare os dados com `json.loads` dos bytes da OCI. Preserve todos os valores.
- Confira três afirmações técnicas de cada saída no documento e cite suas linhas no PR. No quiz, confira também se cada pergunta tem uma única resposta defensável e se a justificativa tem apoio. Se encontrar um erro, deixe o aceite pendente e registre a evidência. O produto só oferece nova tentativa a conteúdos que falharam.

Crie `examples/outputs/README.md` como referência. Inclua a data UTC, o commit efetivamente executado, os dois modelos Gemini e `generation_graph.PROMPT_VERSION`. Confirme `course_content.prompt_version` nas seis linhas publicadas com uma consulta só de leitura. A API e o pacote da OCI não expõem esse campo. Use uma linha por JSON com o curso, links para o arquivo e a fonte, nível, setor, formato, fidelidade, clareza, tempo e novas tentativas. Inclua os tempos dos quatro cursos e links para a lista de fontes, a especificação do pacote e o guia para recriar.

## Passe os cursos para quem apresenta

Crie `examples/outputs/recriar.md` como guia prático para a máquina da apresentação. Use os comandos de instalação do projeto e linke a tabela dos quatro cursos em `demonstracao.md`. Inclua as variáveis de PostgreSQL, Gemini e OCI e como subir o backend e o frontend. Mostre como criar os cursos pela interface, com os títulos sem a letra do roteiro. Explique como usar "Tentar novamente" e conferir os seis leitores, a avaliação com citações e os objetos de origem e de saída no console do OCI.

Combine com a equipe qual ambiente, conta e pessoa vão apresentar. Mantenha os cursos prontos no ambiente combinado. Se a geração ocorreu em outro banco, use o guia para recriá-los antes da apresentação e verifique os novos conteúdos. A geração pode variar. Os arquivos JSON guardados são a referência da execução medida. A aplicação usa o PostgreSQL, o bucket e a conta que possui os cursos.

Peça à pessoa que vai apresentar que entre com a conta, confirme os quatro cursos na lista, abra as seis saídas e verifique as citações. Registre no PR a confirmação e a versão usada. Passe as URLs dos cursos e o acesso por um canal interno da equipe. Preserve os cursos, a conta e os objetos até a apresentação.

## Prepare o teste com uma pessoa de fora

Crie `examples/teste-de-adaptacao/roteiro.md` como guia de uma página para quem conduz o teste. Inclua o perfil de participante de [T43](T43-teste-de-adaptacao-com-pessoa-de-fora.md), a duração prevista de 30 a 40 minutos e os passos abaixo.

1. Copie para o roteiro as três descrições de nível de [Conteúdos e formatos](../product-specs/conteudos-e-formatos.md#o-nível-de-público-muda-a-linguagem-e-a-profundidade). Inclua as perguntas a ler em voz alta e a ficha com seis linhas para número, nível escolhido, motivo, clareza e motivo da clareza.
2. Na primeira rodada, apresente os seis itens, um por vez, por até cinco minutos cada. Peça o nível e uma frase de motivo. Fixe as seis respostas antes de revelar qualquer nível.
3. Na segunda rodada, diga o público pretendido para cada item. Peça clareza para esse público e uma frase de motivo. Use "baixa" se difícil de acompanhar, "média" se compreensível com esforço e "alta" se fácil de acompanhar. Compare com a nota do revisor só após registrar todas as respostas.

Prepare uma cópia avulsa de `material.md` com os seis `content` em ordem embaralhada, numerados de 1 a 6. Formate os textos, cartões e perguntas de forma legível. Inclua no quiz a resposta marcada e a justificativa. Omita metadados e rótulos explícitos de público. Preserve o texto de estudo. Se precisar ocultar um rótulo dentro de `content`, registre a omissão no gabarito. Confira que seja possível apresentar o material em papel ou num arquivo renderizado.

Entregue `material.md` e `gabarito.md` a quem conduz, em local interno da equipe fora do repositório. No gabarito, ligue cada número ao JSON e à versão do conjunto. Separe a lista dos níveis pretendidos das notas do revisor, com `low` como baixa, `medium` como média e `high` como alta. Confirme que a pessoa consegue abrir os dois arquivos. Quem participa vê só a cópia avulsa do material.

## Atualize as referências

Em `demonstracao.md`, registre a data da geração e linke a referência dos JSON e a lista de fontes. Na seção "Antes da apresentação", linke o guia de recriação. Em `examples/README.md`, acrescente um link para `outputs/README.md`.

O ensaio, a falha provocada para a banca, o deploy da VM e a sessão com a pessoa de fora ficam com seus responsáveis.

## Critérios de aceite

- [ ] Os quatro cursos correspondem à tabela. Todos os documentos estão `indexed` e as seis saídas estão `succeeded`, na ordem pedida e geradas com `revisa-v3`.
- [ ] Os seis JSON passam na validação do pacote e do formato e correspondem aos objetos da OCI.
- [ ] O PR traz os tempos, as falhas e as tentativas, a conferência dos 18 fatos e a revisão das perguntas do quiz. Uma pessoa da equipe confere o material antes do merge.
- [ ] A referência traz os modelos, a versão, os tempos e as fontes. Os links para ela e para o guia de recriação abrem.
- [ ] A pessoa que apresenta confirmou acesso aos quatro cursos, abriu as seis saídas e conferiu as citações no ambiente combinado.
- [ ] Quem conduz T43 confirmou acesso ao roteiro, ao material e ao gabarito privado.
- [ ] Os hooks passam. O PR mira menos de 400 linhas no total, incluindo os JSON. Arquivos e evidências públicas ficam sem credenciais e identificadores da conta ou do bucket.
