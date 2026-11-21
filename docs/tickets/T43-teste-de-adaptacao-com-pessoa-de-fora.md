---
id: T43
title: Rode o teste de adaptação ao público com uma pessoa de fora e registre o resultado
blocked_by: [T34]
touches:
  - examples/teste-de-adaptacao/respostas.md
  - docs/product-specs/fidelidade-e-qualidade.md
executor: pessoa
size: 1
---

# T43 - Rode o teste de adaptação ao público com uma pessoa de fora e registre o resultado

Uma pessoa de fora da equipe classifica o público dos seis conteúdos da demonstração. Depois, ela avalia a clareza de cada conteúdo para o nível pretendido. A equipe compara essas notas com as do revisor. T41 deixou essa comparação pendente.

## Prepare a sessão

1. Abra o `roteiro.md` que T34 deixou em `examples/teste-de-adaptacao/`. Use o `material.md` e o `gabarito.md` entregues pelo canal interno da equipe. Confira que os seis números correspondem ao mesmo conjunto de arquivos. Separe a ficha de respostas do roteiro.
2. Convide uma pessoa de fora da equipe que não tenha lido os documentos de origem nem visto os conteúdos. Escolha alguém que consiga distinguir a linguagem dos três públicos. Reserve até 40 minutos e combine o registro das respostas sem identificação.
3. Abra ou imprima só o material de leitura para quem participa. Mantenha o roteiro, os JSON, o gabarito e a aplicação fora da tela compartilhada. A sessão funciona com os arquivos renderizados ou em papel.

## Conduza a sessão

1. Leia as três descrições de nível do roteiro. Mostre um item por vez. Pergunte qual é o nível e o que levou a pessoa a escolher esse nível. Registre as seis escolhas antes de revelar qualquer resposta.
2. Consulte só a lista de níveis do gabarito e informe o nível pretendido de cada item. Peça uma nota de clareza para esse público e uma frase de motivo. Mantenha as escolhas de nível da primeira rodada e guarde as notas do revisor até concluir as seis avaliações.
3. Compare as escolhas com os níveis pretendidos. Conte os acertos. Compare as notas de clareza com as notas do revisor e conte as concordâncias.

## Registre o resultado

- Crie `examples/teste-de-adaptacao/respostas.md` com a data, o perfil sem nome, a versão dos prompts e a ficha preenchida. Use uma linha por item com o número, o nível escolhido, o motivo, a nota de clareza e seu motivo. Mantenha a correspondência entre números e JSON e as respostas esperadas no gabarito privado.
- Acrescente uma rodada à seção "Medições" de [Fidelidade e qualidade](../product-specs/fidelidade-e-qualidade.md#medições). Preserve o histórico. Registre a data, o perfil, o commit da geração e a versão dos prompts de `examples/outputs/README.md`. Indique cada divergência pelo número do material e resuma o motivo dado pela pessoa.
- Registre os dois resultados como "x de 6". A adaptação atinge a meta com 6 de 6. A clareza em seis conteúdos dá uma medida preliminar. A meta de concordância em 8 de 10 permanece. Registre os resultados mesmo quando a meta de adaptação ficar abaixo de 6 de 6.

A pessoa que conduz pode pedir a um agente que transcreva a ficha, atualize a documentação e rode os hooks. A sessão só exige o roteiro, a ficha, o material e o gabarito.

## Critérios de aceite

- [ ] Uma pessoa de fora classificou os seis itens antes de ver qualquer nível pretendido e avaliou os seis após a revelação, sem consultar as notas do revisor.
- [ ] `respostas.md` registra as seis respostas de nível e clareza e seus motivos, sem dados de identificação nem a chave de correção.
- [ ] "Medições" registra data, perfil, commit, versão, acertos de nível, concordância de clareza e motivos das divergências.
- [ ] Os hooks passam.
