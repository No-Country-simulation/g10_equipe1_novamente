# T12 - Evidências e encerramento

## Período e ambiente

Os registros de geração estão datados de 16 e 17/11/2026 (UTC). As capturas de embeddings, quotas, chamada estruturada do backend e configuração OCI são de 18/11/2026. Os testes de embedding usaram textos sintéticos; a recuperação foi simulada localmente, sem PostgreSQL. Os modelos comparados foram `gemini-3.5-flash-lite` e `gemini-3.8-flash`; embeddings usaram `gemini-embedding-2`.

Os artefatos de medição, scripts manuais e capturas estão organizados nesta pasta. A estrutura de origem dos CSVs e do pacote consolidado foi mantida para preservar a trilha de auditoria.

No CSV principal, os três caminhos absolutos de saída foram normalizados para caminhos relativos aos JSONs movidos. Os campos de medição e seus valores não foram alterados.

## Embeddings

As capturas mostram o modelo `gemini-embedding-2` devolvendo vetores de 768 dimensões. A e B foram executados duas vezes cada. Cada execução fez uma chamada ao método do SDK; B enviou três textos por chamada. Quantidade de vetores e quantidade de requisições são medidas diferentes.

| Teste | Execuções | Requisições | Entrada | Vetores | Dimensões | Latência registrada |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| A | 2 | 2 | 1 texto por execução | 2 | 768 | 0,68 s e 0,63 s |
| B | 2 | 2 | 3 textos por execução | 6 | 768 | 0,61 s e 0,62 s |
| C | 1 | 1 | 10 chunks, 10.019 caracteres | 10 | 768 | 1,25 s |
| D | 1 | 2 | 10 documentos e 10 consultas | 20 | 768 | 1,82 s no total de API |
| **Total** | **6** | **7** |  | **38** |  |  |

No teste D, HitRate@1 = 100%, HitRate@3 = 100% e MRR@3 = 1,00. A avaliação usou dez pares de consulta e documento sintéticos, com o gabarito conhecido. É evidência de um conjunto controlado, não uma medida de precisão garantida em produção.

O painel indicou limites de 100 RPM, 30.000 TPM e 1.000 RPD para embeddings. Uma captura após A e B mostra 4 RPM, 83 TPM e **8 RPD**. O pedido de consolidação informava 5 RPD; a captura disponível sustenta 8. Após o conjunto, outra captura mostra 38 RPD. O painel não deve ser interpretado como equivalência entre vetores e requisições: A e B produziram 8 vetores em 4 chamadas do SDK, e o painel registrou valores próprios de uso.

Evidências: [limites observados](screenshots/t12-gemini-embedding-20261118145048.png), [A e B](screenshots/t12-gemini-embedding-20261118145415.png), [C](screenshots/t12-gemini-embedding-20261118145737.png), [D e métricas de recuperação](screenshots/t12-gemini-embedding-20261118145938.png), [quota após A e B](screenshots/t12-gemini-embedding-20261118145509.png), [quota após o conjunto](screenshots/t12-gemini-embedding-20261118150015.png).

## Comparação de geração

Os CSVs registram 12 execuções comparativas: sete sucessos e cinco falhas HTTP 503. `gemini-3.5-flash-lite` teve sete sucessos e uma falha 503; `gemini-3.8-flash` teve quatro falhas 503 e nenhum sucesso. O resultado não prova incompatibilidade permanente de `gemini-3.8-flash`.

| Modelo | RPM | TPM | RPD | Resultado comparativo |
| --- | ---: | ---: | ---: | --- |
| `gemini-3.5-flash-lite` | 15 | 250.000 | 500 | 7 sucessos, 1 HTTP 503 |
| `gemini-3.8-flash` | 5 | 250.000 | 20 | 4 HTTP 503, nenhum sucesso |

As quotas foram lidas no painel do AI Studio: [limites de embeddings](screenshots/t12-gemini-embedding-20261118145048.png) e [limites dos modelos de texto](screenshots/t12-geracao-conteudo-20261118151043.png).

O CSV tem sete execuções com métricas de token, somando 2.416 tokens de entrada, 2.949 de saída e 5.365 no total. Uma execução simples consumiu 519 tokens. Quatro tutoriais consumiram em média 767 tokens cada; houve quatro respostas válidas com três seções. Uma geração de flashcards consumiu 776 tokens e produziu oito cartões válidos. Uma geração de quiz consumiu 1.002 tokens e produziu cinco questões válidas.

O inventário também contém um segundo arquivo de flashcards válido, com oito cartões, mas sem execução correspondente no CSV. Ele não entra na contagem de execuções nem no consumo de tokens. Os tempos registrados para sucessos foram 8,36 s (simples), média de 3,856 s (quatro tutoriais), 21,687 s (flashcards) e 5,117 s (quiz). O CSV consolidado foi reconciliado com os arquivos de origem. Em dois registros de tutorial sem captura que confirme casas decimais, as durações 2,114 s e 1,993 s foram inferidas pela formatação, conforme a auditoria; não são medições independentes confirmadas.

Evidências primárias: [medições CSV](generation/t12_resultados/medicoes.csv), [auditoria dos registros de origem](generation/t12_resultados/auditoria_origens.csv), [inventário e validação dos arquivos](generation/t12_resultados/inventario_respostas.csv), [metadados da descoberta de modelos](generation/t12_resultados/modelos.json) e [relatório de consolidação](generation/T12_resultados_consolidados/RELATORIO_T12.md).

## Geração contextualizada com RAG simulado

O teste local selecionou trechos por simulação lexical e enviou contexto sintético ao modelo. Os três formatos retornaram JSON válido:

| Formato | Tokens | Duração | Validação |
| --- | ---: | ---: | --- |
| Tutorial | 1.324 | 3,519 s | JSON válido |
| Flashcards | 1.383 | 3,170 s | JSON válido |
| Quiz | 1.489 | 3,699 s | JSON válido |
| **Total** | **4.196** | **10,388 s** | **3 JSONs válidos** |

Durante a preparação houve uma falha local por referência a `QuizContent`, que foi corrigida antes das três execuções válidas. Uma simulação artificial de HTTP 503 verificou o registro do erro; ela é distinta das cinco respostas HTTP 503 reais da comparação de modelos. Esses resultados testam geração com contexto simulado, não a integração de recuperação vetorial do backend.

Evidências: [CSV com as três execuções](generation/t12_resultados/medicoes.csv), [resposta tutorial](generation/t12_resultados/20261117T192733414202Z_0e196900_gemini-3.5-flash-lite_tutorial_rag_resposta.json), [resposta flashcards](generation/t12_resultados/20261117T192811592609Z_12879912_gemini-3.5-flash-lite_flashcards_rag_resposta.json), [resposta quiz](generation/t12_resultados/20261117T193555144932Z_17c5d847_gemini-3.5-flash-lite_quiz_rag_resposta.json).

## Validação estruturada com o backend

Em 18/11/2026, uma captura registra uma chamada real a `generate_structured()` com `gemini-3.5-flash-lite` e `GeneratedTutorial`. A API aceitou o JSON Schema e o Pydantic validou a resposta. Isso confirma a estrutura de saída; não homologa fidelidade ao documento nem qualidade pedagógica.

Evidência: [execução estruturada no backend](screenshots/t12-geracao-conteudo-20261118151754.png). A seleção de `gemini-3.5-flash-lite` se apoia nessa chamada válida e nos sete sucessos comparativos; os erros 503 observados no outro modelo não demonstram falha permanente.

## OCI Object Storage

O bucket configurado foi `novamente-docs`, na região `sa-saopaulo-1`, com autenticação local `api_key` pelo OCI Python SDK. O resultado manual informado foi aprovado para PUT, GET com comparação dos bytes, LIST e DELETE com confirmação da remoção. A captura disponível comprova bucket, região, método de autenticação e presença local da chave, mas não mostra a saída dessas quatro operações. Portanto, o resultado operacional está registrado como resultado informado, sem comprovante de execução detalhado entre os artefatos locais. Também não há evidência de que cada pessoa desenvolvedora tenha uma chave própria.

Foi reportado que, na preparação, `key_file` apontava para um diretório, em vez do arquivo PEM, e que o apontamento foi corrigido antes do teste aprovado. Não registramos credenciais, fingerprint, OCIDs, namespace ou caminhos pessoais. A validação não cobre instance principal nem o pipeline completo de geração e publicação.

Evidências: [captura da configuração OCI](screenshots/t12-bucket-oci-20261118152141.png) e [script de verificação](../../../../backend/scripts/verify_storage.py). O script comprova que a ferramenta verifica PUT, GET, LIST e DELETE; seu código, por si só, não prova que a execução remota ocorreu.

## Capacidade, riscos e encerramento

Com 500 requisições de texto por dia e até 12 chamadas por curso com três saídas, `floor(500 / 12) = 41` cursos por dia. Esse é um limite teórico da quota diária, não throughput comprovado. Não inclui concorrência, erros, variações de tamanho de saída nem disponibilidade. Para embeddings, cerca de 100 chunks por documento podem ser enviados em lotes de até 20, reduzindo a quantidade de requisições; o processamento também consome quota e há embeddings para consultas.

As medições mostram que `gemini-embedding-2` produz 768 dimensões, que `gemini-3.5-flash-lite` aceitou a saída estruturada e que o bucket de desenvolvimento foi reportado como funcional. Permanecem riscos de alteração de quotas, HTTP 503, concorrência, fidelidade e qualidade não homologadas, falta de teste com instance principal e falta de validação ponta a ponta. Recomenda-se encerrar T12 com a escolha de `gemini-3.5-flash-lite`, mantendo essas limitações registradas para T19/T28 e para a validação de implantação.
