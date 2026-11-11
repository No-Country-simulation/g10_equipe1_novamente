# Visão e público

O NovaMente reduz de semanas para minutos o tempo de transformar uma documentação técnica em material de estudo, e mantém o material fiel à documentação.

## O problema

Empresas e escolas de tecnologia produzem documentação técnica densa. Um mesmo manual precisa ser ensinado de formas diferentes a quem começa a programar e a quem decide sobre arquitetura. Hoje, especialistas e designers instrucionais fazem essa adaptação à mão.

## Quem usa

| Pessoa | O que ela quer |
| --- | --- |
| Estudante | Aprender o conteúdo de um documento técnico no seu nível, em um formato que ajude a estudar. |
| Pessoa que prepara treinamentos | Gerar material para um público a partir de um documento, sem reescrever tudo. |

No MVP, a mesma pessoa envia o documento e estuda o conteúdo. O produto não separa os dois papéis.

O README atual descreve outro público: pessoas neurodivergentes e em transição de carreira. A equipe decidiu reescrever o README a partir deste documento.

## O que o produto promete

1. **Fidelidade**: o conteúdo reflete o documento enviado. O produto não publica um conteúdo que reprovou na revisão.
2. **Adaptação**: o mesmo documento vira conteúdos diferentes para públicos diferentes e setores diferentes.
3. **Vários formatos**: tutorial, flashcards e quiz.
4. **Rapidez**: do envio ao conteúdo pronto em minutos, com poucos cliques.
5. **Custo zero**: só recursos gratuitos da OCI e do modelo.

## O que a pessoa escolhe

| Parâmetro | Opções | Onde fica no esquema |
| --- | --- | --- |
| Nível de público | Não técnico (iniciante ou gestor), técnico básico (dev júnior ou pleno), técnico avançado (líder técnico ou arquiteto) | `course.audience_level` |
| Setor (nicho) | Fintech, Saúde, E-commerce, Geral | `course.niche_id` |
| Formato | Tutorial, flashcards, quiz | `course_content.format` |

O nível e o setor valem para o curso inteiro. O formato vale para cada conteúdo do curso.

A pessoa também escolhe os documentos do curso e as saídas que quer gerar. Todos os documentos valem para todas as saídas.

O briefing lista quatro perfis de exemplo. O produto os agrupa em três níveis.

## Como a equipe mede o resultado

A banca confere oito itens do checklist do briefing. A equipe considera o MVP entregue quando os oito têm evidência:

1. O sistema recebe documentos técnicos.
2. O sistema usa RAG com chunks, embeddings e busca vetorial.
3. Um LLM escreve o conteúdo em etapas.
4. Um documento vira conteúdo para dois públicos e dois formatos.
5. A saída é um JSON, e há uma interface ou uma API REST.
6. Os documentos e os JSON ficam no OCI Object Storage.
7. A equipe mostra três execuções com documentos reais ou simulados.
8. O repositório tem documentação e diagrama de arquitetura.

## O que o produto não é

- Não é um chat sobre o documento.
- Não é uma plataforma de cursos com turmas, notas e certificados.
- Não corrige nem atualiza a documentação original.
- Não lê imagens nem diagramas do documento.
