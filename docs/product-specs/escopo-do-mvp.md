# Escopo do MVP

O MVP entrega um caminho completo: enviar um documento, gerar conteúdo revisado em três formatos para três níveis de público e guardar tudo no OCI.

Hoje o branch `master` tem conta, login e o esquema do banco. Nenhuma função do produto existe ainda.

## O que entra

A coluna "Ordem" sugere a sequência de construção. O primeiro passo é o caminho mais curto de ponta a ponta: um arquivo `.txt`, um tutorial e a gravação no OCI.

| Item | Pedido do briefing que atende | Estado | Ordem |
| --- | --- | --- | --- |
| Cadastro, login e edição dos dados da conta | Nenhum. Decisão da equipe | Existe | |
| Esquema do banco com sete tabelas | RAG com vector store | Existe | |
| Criar curso com um arquivo `.txt` | Ingestão de documentos e escolha de perfil, formato e nicho | A construir | 1 |
| Indexação: chunks, embeddings e busca vetorial | RAG com chunking, embeddings e busca vetorial | A construir | 1 |
| Tutorial gerado com Gemini | Orquestração com LLM e metadados de aprendizado | A construir | 1 |
| Documento e JSON no OCI Object Storage | Integração com o OCI Object Storage | A construir | 1 |
| Telas "Cursos", "Novo curso" e "Curso" | Interface interativa | A construir | 1 |
| Revisão de fidelidade antes de publicar | Verificação de fidelidade e avaliação pedagógica | A construir | 2 |
| Nota de fidelidade, clareza e trechos citados na tela | Avaliação pedagógica na saída | A construir | 2 |
| Flashcards e quiz | Dois formatos para o mesmo conteúdo | A construir | 3 |
| Várias saídas e vários documentos no mesmo curso | Geração de múltiplos formatos com poucos cliques | A construir | 3 |
| Arquivos Markdown e PDF com texto | Ingestão de PDF, Markdown ou texto | A construir | 3 |
| Nova tentativa depois de uma falha | Tratamento de exceções | A construir | 4 |
| Exclusão de curso com limpeza no OCI | Nenhum. Evita arquivos sem uso | A construir | 4 |
| Mensagens de erro em português claro | Mensagens de erro amigáveis | A construir | 4 |
| README com arquitetura, fluxo e guia de instalação | Documentação com diagrama de arquitetura | A construir | 5 |
| Etapa `planeja`, que propõe a estrutura do conteúdo | Cadeia para planejar, redigir e revisar | A construir | 5 |
| Três documentos de exemplo processados | Três exemplos de execução | A construir | 5 |

## O que entra se sobrar tempo

Estes itens são diferenciais opcionais do briefing ou melhorias. A equipe só começa um deles quando todos os itens acima têm evidência.

| Item | Observação |
| --- | --- |
| Deploy em uma VM Always Free da OCI | Diferencial do briefing. O desenho está em `ARCHITECTURE.md`. |
| Quiz respondido na tela, com correção imediata | Diferencial do briefing. Funciona no navegador, sem guardar respostas. |
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
| Materiais já disponíveis na plataforma | Todo curso parte de um arquivo enviado. |
| Resumo executivo e roteiro de aula | A equipe decidiu manter três formatos. |
| Nível de detalhe (`nivel_detalhe`) | O nível de público já define a profundidade. |
| Texto colado em um campo | A pessoa envia um arquivo `.txt`, Markdown ou PDF. |
| Trilha de conteúdos proposta pelo modelo | A pessoa escolhe as saídas. |
| Nomes de campo do JSON de exemplo do briefing | O produto usa nomes em inglês. |
| Histórico de versões de um conteúdo | Uma regeneração substitui a mesma linha. |
| Recuperação de senha por e-mail | A API não tem essa rota nem servidor de e-mail. |
| Leitura de imagens e diagramas | Diferencial opcional do briefing, com alto custo de tempo. |
| Bot no Telegram | A equipe escolheu um site próprio. |

Alguns documentos de design no Drive mostram várias dessas telas. A equipe trabalha só com as telas de `telas.md`.

## Limites do MVP

| Limite | Valor | Definido em |
| --- | --- | --- |
| Usuários | 10 | Esquema |
| Cursos por usuário | 5 | Esquema |
| Documentos por curso | 3 | Esquema e `criar-curso.md` |
| Saídas por curso | 3, uma de cada formato | `criar-curso.md` |
| Chunks por documento | Cerca de 100 | Esquema |
| Tamanho do arquivo | 5 MiB e 150 mil caracteres de texto | `criar-curso.md` |
| Tempo de geração | Minutos. A equipe mede e registra o valor real. | Briefing |
| Custo | Zero | Briefing |

Os limites de usuários, cursos e documentos são a escala planejada. O código ainda não os impõe.

## Restrições

- Só recursos Always Free da OCI. O briefing exige.
- Plano gratuito para o modelo e para os embeddings.
- No máximo duas escritas e duas revisões por geração.
- Só documentos públicos ou fictícios, porque o plano gratuito do modelo pode usar os dados enviados.
- Chaves e senhas fora do repositório.
