# Escopo do MVP

O MVP entrega um caminho completo: enviar um documento, gerar conteúdo revisado em três formatos para três níveis de público e guardar tudo no OCI.

## O que entra

| Item | Pedido do briefing que atende | Estado |
| --- | --- | --- |
| Cadastro, login e edição dos dados da conta | Nenhum. Decisão da equipe | Existe |
| PostgreSQL com pgvector e oito tabelas | RAG com vector store | Existe |
| Até três documentos Markdown, PDF com texto ou texto digitado | Ingestão de documentos | Existe |
| Chunks, embeddings e busca vetorial | RAG | Existe |
| Tutorial, flashcards e quiz no mesmo curso | Geração de múltiplos formatos com Gemini | Existe |
| Etapas `planeja`, `escreve` e `revisa` | Orquestração de agentes | Existe |
| Documento e JSON no OCI Object Storage | Armazenamento em nuvem | Existe |
| Telas "Cursos", "Novo curso" e "Curso", com leitores | Interface interativa | Existe |
| Fidelidade, clareza, observações e trechos citados | Avaliação do conteúdo | Existe |
| Quiz com correção e justificativa na tela | Exercício interativo | Existe |
| Mensagens de erro e nova tentativa | Recuperação de falhas | Existe |
| Exclusão de curso e conta com limpeza no OCI | Nenhum. Evita arquivos sem uso | Existe |
| README, guia de instalação e diagrama do T35 | Documentação | Existe |
| Três fontes públicas para o [roteiro da demonstração](demonstracao.md) | Três exemplos de execução | Existe |

## O que entra se sobrar tempo

Estes itens são diferenciais opcionais do briefing ou melhorias. A equipe só começa um deles quando todos os itens acima têm evidência.

| Item | Observação |
| --- | --- |
| Deploy na VM `VM.Standard.A2.Flex` (arm64) que a equipe já tem na OCI | Planejado no T36. Veja [Implantação](../ARCHITECTURE.md#implantação). |
| Baixar o conteúdo em Markdown ou CSV para Anki | Diferencial do briefing. Gera o arquivo a partir do JSON publicado. |
| Regenerar um conteúdo publicado | O esquema já define a ordem de publicação. |

## O que fica fora

| Item | Motivo |
| --- | --- |
| Dashboard de desempenho | O esquema não guarda progresso nem resultados. |
| Progresso, conclusão de etapas e tela de finalização | O esquema não guarda progresso. |
| Avaliação do curso por estrelas e por conteúdo | O esquema não guarda avaliações. |
| Assistente de conversa em todas as telas | É um segundo produto de RAG, com base própria. |
| Nivelamento por perguntas | O nível é uma escolha direta da pessoa. |
| Materiais já disponíveis na plataforma | Todo curso parte de documentos informados pela pessoa. |
| Resumo executivo e roteiro de aula | A equipe decidiu manter três formatos. |
| Nível de detalhe (`nivel_detalhe`) | O nível de público já define a profundidade. |
| Trilha de conteúdos proposta pelo modelo | A pessoa escolhe as saídas. |
| Nomes de campo do JSON de exemplo do briefing | O produto usa nomes em inglês. |
| Histórico de versões de um conteúdo | Uma regeneração substitui a mesma linha. |
| Recuperação de senha por e-mail | A API não tem essa rota nem servidor de e-mail. |
| Leitura de imagens e diagramas | Diferencial opcional do briefing, com alto custo de tempo. |
| Bot no Telegram | A equipe escolheu um site próprio. |

Alguns documentos de design no Drive mostram várias dessas telas. A equipe usa o layout do Drive, mas só nas telas de `telas.md`. Em regras de produto, os documentos deste repositório valem.

## Limites do MVP

| Limite | Valor | Definido em |
| --- | --- | --- |
| Usuários | 10 | Esquema |
| Cursos por usuário | 5 | Esquema |
| Documentos por curso | 3 | Esquema e `criar-curso.md` |
| Saídas por curso | 3, uma de cada formato | `criar-curso.md` |
| Chunks por documento | Cerca de 100 | Esquema |
| Tamanho do arquivo | 5 MiB | `criar-curso.md` |
| Tamanho do texto de um documento | 150 mil caracteres | `criar-curso.md` |
| Tempo de geração | Minutos. A equipe mede e registra o valor real. | Briefing |
| Custo | Zero no briefing, com exceção para o deploy opcional | Briefing e decisão abaixo |

Os totais de usuários, cursos por usuário e chunks são estimativas de escala. A API limita os documentos, as saídas, o tamanho dos arquivos e o tamanho do texto.

## Restrições

- O briefing exige recursos Always Free da OCI. A equipe registrou abaixo a exceção para o deploy opcional.
- Plano gratuito para o modelo e para os embeddings.
- No máximo duas escritas e duas revisões por geração.
- Só documentos públicos ou fictícios, porque o plano gratuito do modelo pode usar os dados enviados.
- Chaves e senhas fora do repositório.

No T36, a equipe usa a `VM.Standard.A2.Flex` (arm64) que já está em execução. Esse shape fica fora do Always Free. A Oracle cobra por OCPU-hora e GB-hora de memória. A pessoa que publicar registra a estimativa mensal com base na configuração e no preço aplicável no console. [Preços da OCI](https://www.oracle.com/cloud/price-list/).

A `VM.Standard.A1.Flex` é a alternativa documentada para um futuro deploy dentro do Always Free, conforme a cota e a capacidade na região inicial da conta. [Recursos Always Free da OCI](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm#compute).
