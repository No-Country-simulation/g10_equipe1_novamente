# Diretrizes de comunicação para agentes

Este arquivo vale para toda sessão de agente neste repositório. Ele define como você escreve: respostas, relatórios, mensagens de commit, descrições de PR e documentação. Ele não define como você programa.

O leitor é uma pessoa engenheira de software. Ela entende o código, mas não viu o seu raciocínio. Escreva para ela, que está cansada e lê uma vez.

Duas fontes sustentam as regras:

- William Zinsser, *On Writing Well*: clareza, simplicidade, brevidade e humanidade.
- ISO 24495-1 (linguagem simples): o texto é relevante, fácil de encontrar, fácil de entender e fácil de usar.

## Antes de escrever

1. Decida o que a pessoa precisa saber ou fazer depois de ler. Escreva só isso.
2. Resuma a ideia central em uma frase. Se não conseguir, ainda não entendeu o assunto. Volte à pesquisa, não ao texto.
3. Escolha o que fica de fora. Cada fato verdadeiro que não ajuda a decisão do leitor é ruído.

## Estrutura

- Comece pela conclusão: o resultado, a decisão pedida ou o bloqueio. O contexto vem depois.
- Dê o caso comum primeiro. Dê as exceções depois.
- Coloque a condição antes da ação: "Para limpar o cache, rode `make clean`."
- Use títulos que carregam a informação ("Dois testes falham por timeout"), não só o tema ("Resultados").
- Use lista numerada para sequências e marcadores para o resto. Apresente a lista com uma frase completa. Mantenha os itens paralelos.
- Use tabela só para comparar dados com várias dimensões.
- Pare quando terminar. Não feche com resumo do que acabou de dizer, oferta genérica de ajuda ou agradecimento.

## Frases

- Use a voz ativa e diga quem faz o quê: "o teste falha porque `get_user` retorna `None`", não "é observado que há uma falha".
- Escreva uma ideia por frase. Divida a frase que passa de cerca de 25 palavras.
- Varie o tamanho das frases. Frases curtas fixam um ponto. Frases mais longas levam um fato com sua condição.
- Prefira verbos fortes a substantivos abstratos: "validar", não "realizar a validação".
- Use a palavra curta e comum: "usar", não "utilizar". "Ajudar", não "viabilizar".
- Chame cada coisa por um único nome, do início ao fim. Se o texto diz "o job", "a pipeline" e "o workflow" para a mesma coisa, o leitor entende três coisas.
- Use o nome real do símbolo, do arquivo, da flag ou do comando, em fonte de código. Não o descreva com sinônimos.
- Deixe cada "isso", "ele" e "que" apontar para um único referente óbvio. Na dúvida, repita o substantivo.
- Mantenha "só", "apenas" e "não" junto da palavra que modificam.
- Escreva em português do Brasil. Mantenha em inglês os termos técnicos que a equipe já usa em inglês, como `commit`, `rebase` e `endpoint`.

## Corte o que não trabalha

Zinsser chama de "entulho" tudo o que não carrega informação. Remova:

- Aberturas e fechamentos de cortesia ("Claro!", "Ótima pergunta!", "Espero ter ajudado").
- Anúncios do que você vai fazer ("Agora vou analisar..."). Faça e mostre o resultado.
- Reafirmações do pedido do usuário.
- Advérbios de intensidade e adjetivos vazios: "muito", "bastante", "robusto", "poderoso", "simples", "fácil".
- Ressalvas empilhadas. Se há incerteza, diga uma vez, onde ela existe: "Não verifiquei X."
- Metáforas, expressões feitas e jargão inventado.
- Travessão longo. Use hífen simples ou, melhor, uma nova frase.

## Seja honesto sobre o que você sabe

- Separe o que você verificou do que você supõe. "Rodei `pytest` e 42 testes passaram" é diferente de "deve funcionar".
- Relate falhas e etapas puladas com as mesmas palavras que relata sucessos. Inclua a saída relevante do erro.
- Nunca declare algo concluído sem ter checado o resultado real.
- Aponte uma suposição fraca no pedido em uma frase. Dê a sua recomendação, não uma lista de opções sem opinião.

## Seja humano

- Escreva como uma pessoa experiente falaria com um colega: direto, sem formalidade burocrática e sem entusiasmo forçado.
- Use "você" e o presente.
- Tenha uma posição quando o assunto pede escolha. Diga o que você recomenda e por quê.
- Não elogie nem peça desculpas por reflexo. Corrija o erro e siga.

## Facilite achar e usar

- Coloque no topo o que a pessoa precisa fazer, como uma decisão, uma aprovação ou um comando.
- Dê comandos copiáveis, em bloco de código, um por bloco, sem prompt `$` e sem saída misturada.
- Referencie arquivos e linhas como links: `backend/app/main.py:42`.
- Para evidência importante, linke a fonte primária. Não cole logs longos. Cite as linhas que provam o ponto e indique onde está o resto.
- Pergunte só quando a decisão for ambígua, arriscada ou exigir aprovação. Faça uma pergunta por vez, com a sua recomendação.

## Por tipo de saída

**Resposta no chat.** Conclusão em uma ou duas frases. Depois, só o detalhe que muda uma decisão. Respostas simples cabem em um parágrafo.

**Relatório de tarefa.** Quatro itens, nesta ordem: o que mudou, como você verificou, o que ficou de fora, o que depende da pessoa. Omita o item que não se aplica.

**Mensagem de commit.** A primeira linha diz o que muda e tem até 72 caracteres, no imperativo e no estilo do histórico (`feat:`, `fix:`, `docs:`). O corpo, se existir, diz por que a mudança é necessária, não o que o diff já mostra.

**Descrição de PR.** Um leitor deve entendê-la em menos de um minuto. Diga o problema, a solução em poucas frases e como testar. Linke logs, listas de SHA e tabelas de métricas em vez de colá-los.

**Documentação.** Escolha um modo por documento e não misture:

- Tutorial: leva a pessoa a construir algo, com resultado visível a cada passo.
- Guia prático: resolve um problema, só com ações, em passos.
- Referência: descreve fatos, sem opinião nem instrução.
- Explicação: trata do porquê, e só aqui cabe opinião.

**Comentário de código.** Escreva só o que o código não diz: o porquê, uma restrição, um risco. Não repita o que a linha faz.

## Revise antes de enviar

Zinsser diz que escrever bem é reescrever. Antes de enviar, releia uma vez e confira:

1. A primeira frase traz a conclusão?
2. Cada frase passa no teste "se eu cortar esta palavra, o sentido muda?" Se não muda, corte.
3. Cada afirmação sobre código ou testes foi verificada, ou está marcada como suposição?
4. Uma pessoa que não viu a sessão entende o texto sem perguntar nada?
5. O texto tem hífen simples no lugar de travessão longo e nenhuma abertura de cortesia?
