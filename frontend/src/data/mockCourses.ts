// data/mockCourses.ts - Cursos de Exemplo para Demonstração e Desenvolvimento Offline
import type { CursoCompleto, EstatisticasDashboard } from '../types/studyContent';
import type { TemaSugerido } from '../types/course';

export const mockTemasSugeridos: TemaSugerido[] = [
  {
    id: 'sug-1',
    titulo: 'Arquitetura de Redes VCN na Oracle Cloud',
    categoria: 'Nuvem & Infraestrutura',
    duracao_estimada: '15 min',
    descricao: 'Aprenda sub-redes, internet gateways e security lists com analogias práticas.',
  },
  {
    id: 'sug-2',
    titulo: 'Conceitos Fundamentais de Kubernetes',
    categoria: 'DevOps & Contêineres',
    duracao_estimada: '25 min',
    descricao: 'Entenda Pods, Deployments e Services com exemplos de manifesto YAML.',
  },
  {
    id: 'sug-3',
    titulo: 'Observabilidade com OpenTelemetry',
    categoria: 'Engenharia de Software',
    duracao_estimada: '20 min',
    descricao: 'Traces distribuídos, métricas e instrumentação de microsserviços.',
  },
];

export const mockCursos: CursoCompleto[] = [
  {
    id: 'curso-vcn-oci',
    titulo: 'Dominando Redes na Nuvem (VCN) do Zero',
    descricao: 'Guia completo sobre Virtual Cloud Network na Oracle Cloud Infrastructure com analogias e laboratório prático.',
    status: 'em_andamento',
    progresso_percentual: 50,
    criado_em: '2026-10-26T14:30:00Z',
    documento_origem: 'oci_vcn_architecture_manual.pdf',
    metadados: {
      perfil_aplicado: 'Iniciante',
      formato_gerado: 'Tutorial',
      tempo_estimado_estudo_minutos: 15,
      conceitos_chave: ['VCN', 'Sub-redes Públicas/Privadas', 'Internet Gateway', 'Security Lists', 'Route Tables'],
    },
    etapas: [
      {
        id: 'etapa-1',
        numero: 1,
        titulo: 'Introdução e Fundamentos da VCN',
        status: 'concluido',
        conteudo: {
          titulo: 'O que é uma Virtual Cloud Network?',
          introducao_contextualizada: 'Imagine a VCN como o seu próprio bairro particular e seguro dentro da nuvem da Oracle, onde você decide quem entra, quem sai e onde cada servidor mora.',
          formato_padrao: 'Tutorial',
          secoes_tutorial: [
            {
              passo: 1,
              titulo: 'Visão Geral do Conceito',
              conteudo_markdown: 'Uma **Virtual Cloud Network (VCN)** é uma rede definida por software que você configura nos data centers da Oracle Cloud Infrastructure. Ela é isolada e segura, equivalente à rede local tradicional de uma empresa.',
            },
            {
              passo: 2,
              titulo: 'Componentes Vitais de Rede',
              conteudo_markdown: 'Toda VCN é composta por:\n- **Bloco CIDR:** Exemplo: `10.0.0.0/16`\n- **Sub-redes:** Públicas (acesso à Internet) e Privadas (bancos de dados isolados)\n- **Tabelas de Roteamento:** As vias que direcionam o tráfego\n- **Security Lists:** Porteiros virtuais com regras de firewall',
              codigo_exemplo: '# Bloco CIDR padrão de uma VCN didática\nCIDR_BLOCK="10.0.0.0/16"\nPUBLIC_SUBNET="10.0.1.0/24"\nPRIVATE_SUBNET="10.0.2.0/24"',
              linguagem_codigo: 'bash',
            },
          ],
          itens_flashcards: [
            {
              id: 'fc-1',
              frente: 'O que é uma VCN na Oracle Cloud?',
              verso: 'É a sua rede virtual privada e personalizável na OCI, funcionando como o data center tradicional da sua empresa.',
              dica_didatica: 'Pense nela como o terreno cercado onde seus servidores moram.',
            },
            {
              id: 'fc-2',
              frente: 'Para que servem as Security Lists (Listas de Segurança)?',
              verso: 'São porteiros virtuais com regras que controlam exatamente que pacotes de rede entram (ingress) ou saem (egress).',
              dica_didatica: 'Regras de entrada e saída no nível de sub-rede.',
            },
            {
              id: 'fc-3',
              frente: 'Qual a diferença entre Sub-rede Pública e Sub-rede Privada?',
              verso: 'A sub-rede pública permite que instâncias recebam IPs públicos e conversem com a Internet via Internet Gateway; a privada é isolada.',
              dica_didatica: 'Banco de dados fica na privada; servidor web na pública.',
            },
          ],
          questoes_quiz: [
            {
              id: 'qz-1',
              enunciado: 'Qual componente é indispensável para permitir que servidores em uma sub-rede pública acessem diretamente a Internet?',
              opcoes: [
                'Dynamic Routing Gateway (DRG)',
                'Internet Gateway (IGW)',
                'Local Peering Gateway (LPG)',
                'Service Gateway (SGW)',
              ],
              resposta_correta_idx: 1,
              justificativa: 'O Internet Gateway (IGW) é o roteador virtual da OCI responsável por conectar sua VCN à rede pública mundial.',
            },
            {
              id: 'qz-2',
              enunciado: 'Por que recomendamos colocar bancos de dados em uma sub-rede privada?',
              opcoes: [
                'Para economizar consumo de banda Always Free',
                'Porque instâncias em sub-redes privadas não podem sofrer ataques diretos da Internet',
                'Porque a OCI não permite MySQL em redes públicas',
                'Para aumentar a velocidade do processador da VM',
              ],
              resposta_correta_idx: 1,
              justificativa: 'Sub-redes privadas não possuem rotas diretas para a Internet pública, fornecendo camada essencial de segurança.',
            },
          ],
        },
        resultado: {
          acertos: 2,
          total: 2,
          feedback: 'util',
          concluido_em: '2026-10-26T15:10:00Z',
        },
      },
      {
        id: 'etapa-2',
        numero: 2,
        titulo: 'Sub-redes e Roteamento Seguro',
        status: 'disponivel',
        conteudo: {
          titulo: 'Configurando Rotas e Portões de Segurança',
          introducao_contextualizada: 'Agora que você conhece a estrutura do bairro, vamos construir os portões de controle de acesso e as avenidas de tráfego.',
          formato_padrao: 'Flashcards',
          itens_flashcards: [
            {
              id: 'fc-4',
              frente: 'Qual o papel de uma Route Table (Tabela de Roteamento)?',
              verso: 'Contém um conjunto de regras que direciona o tráfego de sub-redes para destinos fora da VCN (ex: Internet Gateway).',
              dica_didatica: 'A placa de trânsito que indica para onde enviar o pacote 0.0.0.0/0.',
            },
            {
              id: 'fc-5',
              frente: 'O que faz o NAT Gateway na OCI?',
              verso: 'Permite que servidores privados acessem a Internet (para baixar updates), mas impede que a Internet inicie conexões para eles.',
              dica_didatica: 'Tráfego só de saída, nunca de entrada não solicitada.',
            },
          ],
          questoes_quiz: [
            {
              id: 'qz-3',
              enunciado: 'Como uma VM sem IP público pode baixar atualizações do Linux com segurança na OCI?',
              opcoes: [
                'Através de um NAT Gateway configurado na tabela de rotas da sub-rede privada',
                'Abrindo todas as portas na Security List',
                'Usando uma VPN externa',
                'Conectando-se ao bucket público do OCI Object Storage',
              ],
              resposta_correta_idx: 0,
              justificativa: 'O NAT Gateway permite que instâncias privadas acessem a internet sem expô-las a tráfego de entrada.',
            },
          ],
          secoes_tutorial: [
            {
              passo: 1,
              titulo: 'Criando a Tabela de Roteamento',
              conteudo_markdown: 'Na OCI, cada sub-rede está associada a uma tabela de rotas. Para a rota pública, definimos:\n\n- **Destino CIDR:** `0.0.0.0/0` (Todo tráfego externo)\n- **Target Type:** `Internet Gateway`',
            },
          ],
        },
      },
      {
        id: 'etapa-3',
        numero: 3,
        titulo: 'Gateways e Conectividade Externa',
        status: 'bloqueado',
      },
      {
        id: 'etapa-4',
        numero: 4,
        titulo: 'Prática de Defesa e Melhores Práticas',
        status: 'bloqueado',
      },
    ],
  },
  {
    id: 'curso-k8s-arch',
    titulo: 'Arquitetura Interna do Kubernetes para Produção',
    descricao: 'Do Control Plane ao Kubelet: ciclo de vida de Pods, Deployments e Services para engenheiros.',
    status: 'concluido',
    progresso_percentual: 100,
    criado_em: '2026-10-25T10:00:00Z',
    documento_origem: 'kubernetes_deep_dive_whitepaper.md',
    metadados: {
      perfil_aplicado: 'Desenvolvedor Pleno',
      formato_gerado: 'Quiz',
      tempo_estimado_estudo_minutos: 25,
      conceitos_chave: ['etcd', 'Kube-apiserver', 'Kubelet', 'Kube-proxy', 'CNI'],
    },
    etapas: [
      {
        id: 'k8s-1',
        numero: 1,
        titulo: 'Control Plane e Persistência etcd',
        status: 'concluido',
        resultado: { acertos: 3, total: 3, feedback: 'util' },
      },
      {
        id: 'k8s-2',
        numero: 2,
        titulo: 'Ciclo de Vida do Pod e Scheduling',
        status: 'concluido',
        resultado: { acertos: 4, total: 4, feedback: 'util' },
      },
    ],
    avaliacao_geral: {
      nota_estrelas: 5,
      comentario: 'Didática fantástica! A analogia com orquestra facilitou muito a compreensão do Kubelet.',
    },
  },
];

export const mockDashboardData: EstatisticasDashboard = {
  taxa_finalizacao_percentual: 75,
  cursos_gerados: 4,
  cursos_concluidos: 3,
  tempo_total_estudo_minutos: 65,
  evolucao_semanal: [
    { semana: 'Sem 1', estudos: 2, quizzes_respondidos: 5 },
    { semana: 'Sem 2', estudos: 3, quizzes_respondidos: 9 },
    { semana: 'Sem 3', estudos: 5, quizzes_respondidos: 14 },
    { semana: 'Sem 4', estudos: 8, quizzes_respondidos: 22 },
  ],
  distribuicao_temas: [
    { tema: 'Nuvem OCI', quantidade: 4 },
    { tema: 'Kubernetes', quantidade: 3 },
    { tema: 'Observabilidade', quantidade: 2 },
    { tema: 'Segurança & IAM', quantidade: 1 },
  ],
  historico_recente: [
    {
      id: 'hist-1',
      curso_titulo: 'Arquitetura Interna do Kubernetes para Produção',
      formato: 'Quiz Interativo',
      conclusao_data: '25/10/2026',
      score: 100,
      status: 'Concluído',
    },
    {
      id: 'hist-2',
      curso_titulo: 'Dominando Redes na Nuvem (VCN) do Zero',
      formato: 'Tutorial + Flashcards',
      conclusao_data: 'Em andamento',
      score: 100,
      status: 'Em Andamento',
    },
    {
      id: 'hist-3',
      curso_titulo: 'OpenTelemetry e Tracing Distribuído',
      formato: 'Flashcards 3D',
      conclusao_data: '23/10/2026',
      score: 90,
      status: 'Concluído',
    },
  ],
};
