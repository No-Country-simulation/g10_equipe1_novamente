# Planos de Execução (ExecPlans):

Este documento descreve os requisitos de um plano de execução ("ExecPlan"), um documento de design que um agente de código pode seguir para entregar uma funcionalidade ou uma mudança de sistema funcionando. Trate o leitor como um iniciante completo neste repositório: ele tem apenas a árvore de trabalho atual e o único arquivo de ExecPlan que você fornece. Não há memória de planos anteriores nem contexto externo.

## Como usar ExecPlans e o PLANS.md

Ao redigir uma especificação executável (ExecPlan), siga o PLANS.md _à risca_. Se ele não estiver no seu contexto, atualize a memória lendo o arquivo PLANS.md inteiro. Leia (e releia) o material de origem com rigor para produzir uma especificação precisa. Ao criar uma especificação, comece pelo esqueleto e detalhe-o conforme você pesquisa.

Ao implementar uma especificação executável (ExecPlan), não pergunte ao usuário quais são os "próximos passos"; siga direto para o marco seguinte. Mantenha todas as seções atualizadas e, a cada ponto de parada, adicione ou divida itens da lista para declarar de forma afirmativa o progresso feito e os próximos passos. Resolva ambiguidades de forma autônoma e faça `commit` com frequência.

Ao discutir uma especificação executável (ExecPlan), registre as decisões em um log dentro da especificação, para a posteridade; deve ficar inequívoco por que qualquer mudança na especificação foi feita. ExecPlans são documentos vivos, e deve ser sempre possível recomeçar _apenas_ a partir do ExecPlan, sem nenhum outro trabalho.

Ao pesquisar um design com requisitos difíceis ou muitas incógnitas, use marcos para implementar provas de conceito, "implementações de brinquedo" e similares, que permitam validar se a proposta do usuário é viável. Leia o código-fonte das bibliotecas, encontrando-as ou obtendo-as, pesquise a fundo e inclua protótipos para orientar uma implementação mais completa.

## Requisitos

REQUISITOS INEGOCIÁVEIS:

* Todo ExecPlan deve ser totalmente autocontido. Autocontido significa que, em sua forma atual, ele contém todo o conhecimento e todas as instruções de que um iniciante precisa para ter sucesso.
* Todo ExecPlan é um documento vivo. Quem contribui é obrigado a revisá-lo conforme o progresso avança, conforme surgem descobertas e conforme as decisões de design são finalizadas. Cada revisão deve continuar totalmente autocontida.
* Todo ExecPlan deve permitir que um iniciante completo implemente a funcionalidade de ponta a ponta, sem conhecimento prévio deste repositório.
* Todo ExecPlan deve produzir um comportamento demonstravelmente funcional, e não apenas mudanças de código que "cumpram uma definição".
* Todo ExecPlan deve definir em linguagem simples cada termo técnico, ou então não usá-lo.

Propósito e intenção vêm primeiro. Comece explicando, em poucas frases, por que o trabalho importa do ponto de vista do usuário: o que alguém consegue fazer depois desta mudança que não conseguia antes, e como ver isso funcionando. Depois, conduza o leitor pelos passos exatos para alcançar esse resultado, incluindo o que editar, o que executar e o que ele deve observar.

O agente que executa o seu plano pode listar arquivos, ler arquivos, pesquisar, executar o projeto e executar testes. Ele não conhece nenhum contexto anterior e não consegue inferir o que você quis dizer em marcos anteriores. Repita toda suposição em que você se apoia. Não aponte para blogs ou documentos externos; se um conhecimento for necessário, incorpore-o ao próprio plano, com as suas palavras. Se um ExecPlan se baseia em um ExecPlan anterior e esse arquivo está versionado, incorpore-o por referência. Se não estiver, você deve incluir todo o contexto relevante daquele plano.

## Formatação

O formato e o envelope são simples e rígidos. Cada ExecPlan deve ser um único bloco de código delimitado, rotulado como `md`, que começa e termina com três crases. Não aninhe outros blocos de código com três crases dentro dele; quando precisar mostrar comandos, transcrições, diffs ou código, apresente-os como blocos indentados dentro desse único bloco. Use indentação para dar clareza, em vez de blocos de código dentro de um ExecPlan, para não fechar prematuramente o bloco de código do ExecPlan. Use duas quebras de linha depois de cada título, use `#`, `##` e assim por diante, e a sintaxe correta para listas ordenadas e não ordenadas.

Ao escrever um ExecPlan em um arquivo Markdown (.md) cujo conteúdo *é somente* o único ExecPlan, omita as três crases.

Escreva em prosa simples. Prefira frases a listas. Evite listas de verificação, tabelas e enumerações longas, a menos que a brevidade prejudicasse o sentido. Listas de verificação são permitidas apenas na seção `Progresso`, onde são obrigatórias. As seções narrativas devem continuar sendo prosa em primeiro lugar.

## Diretrizes

Autocontenção e linguagem simples são essenciais. Se você introduzir uma expressão que não é português comum ("daemon", "middleware", "RPC gateway", "filter graph"), defina-a imediatamente e lembre o leitor de como ela se manifesta neste repositório (por exemplo, nomeando os arquivos ou comandos em que aparece). Não diga "como definido anteriormente" nem "de acordo com o documento de arquitetura". Inclua aqui a explicação necessária, mesmo que isso o faça se repetir.

Evite os modos comuns de falha. Não dependa de jargão indefinido. Não descreva "a letra de uma funcionalidade" de forma tão restrita que o código resultante compile, mas não faça nada de significativo. Não terceirize decisões importantes ao leitor. Quando houver ambiguidade, resolva-a no próprio plano e explique por que você escolheu esse caminho. Peque por explicar demais os efeitos visíveis ao usuário e por especificar de menos os detalhes de implementação incidentais.

Ancore o plano em resultados observáveis. Diga o que o usuário pode fazer depois da implementação, os comandos a executar e as saídas que ele deve ver. Formule a aceitação como comportamento que uma pessoa consegue verificar ("depois de iniciar o servidor, acessar [http://localhost:8080/health](http://localhost:8080/health) retorna HTTP 200 com o corpo OK"), e não como atributos internos ("foi adicionada uma struct HealthCheck"). Se a mudança for interna, explique como o seu impacto ainda pode ser demonstrado (por exemplo, executando testes que falham antes e passam depois, e mostrando um cenário que usa o novo comportamento).

Especifique o contexto do repositório de forma explícita. Nomeie os arquivos com caminhos completos relativos ao repositório, nomeie funções e módulos com precisão e descreva onde os novos arquivos devem ser criados. Se a mudança toca várias áreas, inclua um parágrafo curto de orientação que explique como essas partes se encaixam, para que um iniciante navegue com confiança. Ao executar comandos, mostre o diretório de trabalho e a linha de comando exata. Quando o resultado depender do ambiente, declare as suposições e ofereça alternativas quando for razoável.

Seja idempotente e seguro. Escreva os passos de modo que possam ser executados várias vezes sem causar dano ou divergência. Se um passo puder falhar no meio, inclua como tentar de novo ou adaptar. Se uma migração ou operação destrutiva for necessária, detalhe os backups ou os recursos seguros de contingência. Prefira mudanças aditivas e testáveis, que possam ser validadas ao longo do caminho.

Validação não é opcional. Inclua instruções para executar testes, iniciar o sistema, se aplicável, e observá-lo fazendo algo útil. Descreva testes abrangentes para qualquer funcionalidade ou capacidade nova. Inclua as saídas e as mensagens de erro esperadas, para que um iniciante distinga sucesso de falha. Sempre que possível, mostre como provar que a mudança é efetiva além da compilação (por exemplo, por meio de um pequeno cenário de ponta a ponta, uma invocação de CLI ou uma transcrição de requisição/resposta HTTP). Indique os comandos de teste exatos, apropriados à toolchain do projeto, e como interpretar os resultados.

Registre evidências. Quando os seus passos produzirem saída de terminal, diffs curtos ou logs, inclua-os dentro do único bloco delimitado, como exemplos indentados. Mantenha-os concisos e focados no que prova o sucesso. Se precisar incluir um patch, prefira diffs restritos a um arquivo ou pequenos trechos que o leitor consiga recriar seguindo as suas instruções, em vez de colar grandes blocos.

## Marcos

Marcos são narrativa, não burocracia. Se você dividir o trabalho em marcos, introduza cada um com um parágrafo breve que descreva o escopo, o que existirá ao final do marco e não existia antes, os comandos a executar e a aceitação que você espera observar. Mantenha a leitura como uma história: objetivo, trabalho, resultado, prova. Progresso e marcos são distintos: marcos contam a história, o progresso acompanha o trabalho granular. Ambos devem existir. Nunca abrevie um marco só por brevidade, e não deixe de fora detalhes que possam ser cruciais para uma implementação futura.

Cada marco deve ser verificável de forma independente e implementar de forma incremental o objetivo geral do plano de execução.

## Planos vivos e decisões de design

* ExecPlans são documentos vivos. Ao tomar decisões de design importantes, atualize o plano para registrar tanto a decisão quanto o raciocínio por trás dela. Registre todas as decisões na seção `Registro de Decisões`.
* ExecPlans devem conter e manter uma seção `Progresso`, uma seção `Surpresas e Descobertas`, um `Registro de Decisões` e uma seção `Resultados e Retrospectiva`. Elas não são opcionais.
* Quando você descobrir comportamento do otimizador, trade-offs de desempenho, bugs inesperados ou semântica inversa/de desfazer (inverse/unapply) que moldaram a sua abordagem, registre essas observações na seção `Surpresas e Descobertas`, com trechos curtos de evidência (a saída de testes é o ideal).
* Se você mudar de rumo durante a implementação, documente o motivo no `Registro de Decisões` e reflita as implicações em `Progresso`. Planos são guias para quem contribuir depois tanto quanto são listas de verificação para você.
* Ao concluir uma tarefa grande ou o plano inteiro, escreva uma entrada em `Resultados e Retrospectiva` resumindo o que foi alcançado, o que falta e as lições aprendidas.

# Marcos de prototipagem e implementações paralelas

É aceitável - e muitas vezes recomendável - incluir marcos explícitos de prototipagem quando eles reduzem o risco de uma mudança maior. Exemplos: adicionar um operador de baixo nível a uma dependência para validar a viabilidade, ou explorar duas ordens de composição medindo os efeitos no otimizador. Mantenha os protótipos aditivos e testáveis. Rotule claramente o escopo como "prototipagem"; descreva como executar e observar os resultados; e declare os critérios para promover ou descartar o protótipo.

Prefira mudanças de código aditivas seguidas de subtrações que mantenham os testes passando. Implementações paralelas (por exemplo, manter um adaptador ao lado de um caminho antigo durante a migração) são aceitáveis quando reduzem o risco ou permitem que os testes continuem passando durante uma migração grande. Descreva como validar os dois caminhos e como aposentar um deles com segurança, com testes. Ao trabalhar com várias bibliotecas novas ou áreas de funcionalidade, considere criar spikes que avaliem a viabilidade dessas funcionalidades _independentemente_ umas das outras, provando que a biblioteca externa se comporta como esperado e implementa, isoladamente, as funcionalidades de que precisamos.

## Esqueleto de um Bom ExecPlan

    # <Descrição curta, orientada à ação>

    Este ExecPlan é um documento vivo. As seções `Progresso`, `Surpresas e Descobertas`, `Registro de Decisões` e `Resultados e Retrospectiva` devem ser mantidas atualizadas conforme o trabalho avança.

    Se o arquivo PLANS.md estiver versionado no repositório, referencie aqui o caminho dele a partir da raiz do repositório e registre que este documento deve ser mantido de acordo com o PLANS.md.

    ## Propósito / Visão Geral

    Explique em poucas frases o que alguém ganha depois desta mudança e como pode ver isso funcionando. Declare o comportamento visível ao usuário que você vai habilitar.

    ## Progresso

    Use uma lista com caixas de seleção para resumir os passos granulares. Todo ponto de parada deve ser documentado aqui, mesmo que isso exija dividir uma tarefa parcialmente concluída em duas ("feito" e "restante"). Esta seção deve sempre refletir o estado real e atual do trabalho.

    - [x] (2025-10-01 13:00Z) Exemplo de passo concluído.
    - [ ] Exemplo de passo incompleto.
    - [ ] Exemplo de passo parcialmente concluído (concluído: X; restante: Y).

    Use marcas de tempo para medir o ritmo do progresso.

    ## Surpresas e Descobertas

    Documente comportamentos inesperados, bugs, otimizações ou insights descobertos durante a implementação. Forneça evidências concisas.

    - Observação: …
      Evidência: …

    ## Registro de Decisões

    Registre toda decisão tomada durante o trabalho no plano, no formato:

    - Decisão: …
      Justificativa: …
      Data/Autor: …

    ## Resultados e Retrospectiva

    Resuma os resultados, as lacunas e as lições aprendidas nos marcos principais ou na conclusão. Compare o resultado com o propósito original.

    ## Contexto e Orientação

    Descreva o estado atual relevante para esta tarefa como se o leitor não soubesse nada. Nomeie os arquivos e módulos principais pelo caminho completo. Defina qualquer termo não óbvio que você for usar. Não se refira a planos anteriores.

    ## Plano de Trabalho

    Descreva, em prosa, a sequência de edições e adições. Para cada edição, nomeie o arquivo e o local (função, módulo) e o que inserir ou alterar. Mantenha concreto e mínimo.

    ## Passos Concretos

    Declare os comandos exatos a executar e onde executá-los (diretório de trabalho). Quando um comando gerar saída, mostre uma transcrição esperada curta, para que o leitor possa comparar. Esta seção deve ser atualizada conforme o trabalho avança.

    ## Validação e Aceitação

    Descreva como iniciar ou exercitar o sistema e o que observar. Formule a aceitação como comportamento, com entradas e saídas específicas. Se houver testes, diga "execute <comando de teste do projeto> e espere <N> passando; o novo teste <nome> falha antes da mudança e passa depois".

    ## Idempotência e Recuperação

    Se os passos podem ser repetidos com segurança, diga isso. Se um passo for arriscado, forneça um caminho seguro de nova tentativa ou de rollback. Deixe o ambiente limpo após a conclusão.

    ## Artefatos e Notas

    Inclua as transcrições, diffs ou trechos mais importantes como exemplos indentados. Mantenha-os concisos e focados no que prova o sucesso.

    ## Interfaces e Dependências

    Seja prescritivo. Nomeie as bibliotecas, módulos e serviços a usar e por quê. Especifique os tipos, traits/interfaces e assinaturas de função que devem existir ao final do marco. Prefira nomes e caminhos estáveis, como `crate::module::function` ou `package.submodule.Interface`. Por exemplo:

    Em crates/foo/planner.rs, defina:

        pub trait Planner {
            fn plan(&self, observed: &Observed) -> Vec<Action>;
        }

Se você seguir a orientação acima, um único agente sem estado - ou uma pessoa iniciante - poderá ler o seu ExecPlan de cima a baixo e produzir um resultado funcional e observável. Esse é o critério: AUTOCONTIDO, AUTOSSUFICIENTE, QUE GUIE O INICIANTE, FOCADO NO RESULTADO.

Ao revisar um plano, você deve garantir que as suas mudanças sejam refletidas de forma abrangente em todas as seções, incluindo as seções de documento vivo, e deve escrever ao final do plano uma nota que descreva a mudança e o motivo dela. ExecPlans devem descrever não só o quê, mas também o porquê de quase tudo.
