# 🧠 NovaMente — Planejamento Estratégico, Arquitetural e Operacional do Front-End

**Hackathon ONE Grupo 10 | Parceria Alura & Oracle Cloud Infrastructure (OCI)**  
**Projeto:** NovaMente — Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional  
**Responsáveis pelo Front-End:** Marcos & Joel  
**Versão:** 2.0 (Revisada e Alinhada com as Observações Técnicas de Joel)  
**Data:** Outubro de 2026  

---

## 1. Visão Geral e Alinhamento com o Desafio ONE / OCI

A partir das diretrizes oficiais do Hackathon (documento `ae6fa416-4107-43c1-886f-04bf87029ba1.pdf`) e da estrutura de telas prototipada pela equipe de UX/Design, a solução **NovaMente** ataca um dos maiores gargalos corporativos e educacionais em tecnologia: **a densidade e inacessibilidade de documentações técnicas brutas**.

### O Desafio
Manuais de infraestrutura, arquitetura de nuvem (OCI), APIs e frameworks levam semanas para serem traduzidos em cursos e materiais de treinamento para diferentes níveis de maturidade (iniciantes, plenos, lideranças técnicas ou executivos).

### A Solução NovaMente
Uma plataforma interativa que ingere documentações técnicas (PDF, Markdown, texto) e, através de um pipeline inteligente de RAG (Vector Store) integrado ao **OCI Object Storage (Camada Always Free)** e LLMs (Gemini / Claude / GPT), gera automaticamente:
1. **Trilhas de Aprendizagem estruturadas (Roadmaps didáticos)**;
2. **Conteúdos Multiformato adaptados** ao perfil e nicho do usuário:
   - **Tutoriais Práticos Passo a Passo** (com sintaxe e código formatado);
   - **Flashcards 3D de Memorização Ativa** (frente, verso e dica mnemônica);
   - **Quizzes Interativos com Avaliação Imediata** (justificativa de erro/acerto ancorada na documentação);
   - **Resumos Executivos (TL;DR)** e **Roteiros Didáticos**.
3. **Assistente IA Flutuante** contextualizado com citação de fontes (RAG) em todas as telas;
4. **Dashboard de Métricas e Retenção** com histórico e gráficos analíticos.

---

## 2. Incorporação Oficial das Observações Técnicas de Joel

Durante a revisão do planejamento preliminar, **Joel** apontou 4 observações arquiteturais e operacionais fundamentais. Todas foram analisadas e formalmente integradas a este documento:

### 2.1 Ponto 1: Formato Dinâmico na Tela 5 vs. Tipagem `ConteudoAdaptado`
* **Apontamento de Joel:** *"Na Tela 5 dá pra trocar entre Tutorial, Flashcard e Quiz, mas o tipo `ConteudoAdaptado` tem só um formato. Vale combinar com o back."*
* **Resolução Arquitetural:**
  - A interface `ConteudoAdaptado` foi reformulada para suportar um **pacote didático multiformato** por módulo.
  - O campo deixa de ser exclusivo (`formato: FormatoPedagogico`) e passa a conter os blocos opcionais preenchidos simultaneamente: `secoes_tutorial`, `itens_flashcards`, `questoes_quiz` e `resumo_tldr`.
  - **Alinhamento com o Back-end / RAG:** No payload de resposta do backend, a IA retornará as 3 modalidades didáticas para cada etapa do curso. Dessa forma, a alternância de abas na Tela 5 é instantânea e visualmente rica, sem necessidade de novas requisições síncronas que aumentariam a latência da experiência durante a banca avaliadora.

### 2.2 Ponto 2: Envio de Arquivos via `FormData`
* **Apontamento de Joel:** *"Upload: o arquivo precisa ir como FormData, não JSON."*
* **Resolução Técnica:**
  - No Wizard de Criação (Tela 3), o usuário realiza o upload/drag-and-drop de arquivos técnicos (`.pdf`, `.md`, `.txt`).
  - `JSON.stringify()` não suporta instâncias nativas de `File` / `Blob` sem codificação Base64 (que aumentaria em 33% o tamanho da carga e consumiria memória excessiva).
  - A camada de serviço HTTP (`services/api.ts`) utilizará a API nativa `FormData()` do navegador.
  - **Regra do `fetch`:** O cabeçalho `Content-Type` **não** será definido manualmente, permitindo que o navegador configure automaticamente o `multipart/form-data; boundary=...`.

### 2.3 Ponto 3: Rebalanceamento Estratégico das Frentes (A vs B)
* **Apontamento de Joel:** *"Divisão: a Frente B está bem mais pesada. Dá pra passar a Tela 8 ou a 7 pra Frente A?"*
* **Diagnóstico:** A Frente B concentrava as telas mais ricas e densas (Roadmap, os 3 players da Tela 5, Finalização, Dashboard com gráficos e o Assistente IA flutuante).
* **Nova Distribuição Homogênea:**
  - **Tela 8 (Assistente IA Flutuante) migra para a Frente A (Marcos):** Como Marcos é o responsável pelo layout compartilhado (`PageWrapper`, `Header`, `variables.css`), o Assistente IA é um componente de nível de aplicação (`components/assistant/AssistantModal.tsx`) renderizado globalmente em todas as rotas. Faz total sentido arquitetural estar sob responsabilidade de Marcos.
  - **Joel foca 100% no "Core Loop de Aprendizagem":** Joel assume com exclusividade as Telas 4 (Roadmap), 5 (Ambiente de Estudo com Tutorial, Flashcard e Quiz), 6 (Finalização/Feedback) e 7 (Dashboard de Desempenho).

### 2.4 Ponto 4: Bibliotecas Essenciais Adicionadas ao Setup
* **Apontamento de Joel:** *"Faltam bibliotecas: Recharts (gráficos), react-markdown (tutoriais) e algo pra exportar PDF."*
* **Resolução:** As seguintes dependências passam a integrar a stack oficial:
  1. **`recharts`**: Para os gráficos de evolução temporal (linhas/área) e distribuição por temas (barras) no Dashboard (Tela 7).
  2. **`react-markdown` + `remark-gfm`**: Para renderizar tutoriais e blocos de código com formatação impecável na Tela 5.
  3. **`jspdf` + `html2canvas`**: Para exportação instantânea do conteúdo em PDF didático diretamente pelo navegador.
  4. **Exportação Anki CSV (`exportService.ts`)**: Utilitário em TypeScript puro para gerar e baixar arquivos CSV (`frente;verso`) compatíveis com o software Anki.

---

## 3. Matriz de Divisão de Trabalho Atualizada

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DIVISÃO OFICIAL DE ESCOPO                       │
├──────────────────────────────────┬─────────────────────────────────────┤
│ FRENTE A (Marcos)                │ FRENTE B (Joel)                     │
│ Plataforma, Acesso & Layout      │ Experiência de Estudo & Métricas    │
├──────────────────────────────────┼─────────────────────────────────────┤
│ • Setup Base & Design Tokens     │ • Tela 4: Roadmap de Conteúdos      │
│ • Layout Global (Header/Footer)  │   - Timeline com nós interativos    │
│ • Tela 1: Login & Cadastro       │   - Estados: Antes e Depois         │
│ • Tela 2: Home do Estudante      │ • Tela 5: Ambiente de Conteúdo      │
│ • Tela 3: Wizard "Novo Curso"    │   - Tab Tutorial (react-markdown)   │
│   - Stepper em 4 passos          │   - Tab Flashcards (Flip 3D)        │
│   - Upload FormData (PDF/MD/TXT) │   - Tab Quiz (Feedback instantâneo) │
│ • Tela 8: Assistente IA Global   │   - Exportador (PDF, MD, Anki CSV)  │
│   - Botão flutuante retrátil     │ • Tela 6: Finalização & Comemoração │
│   - Chat com fontes RAG e FAQ    │   - Avaliação por estrelas e CTAs   │
│ • Tela 9: Gestão Dados Pessoais  │ • Tela 7: Dashboard de Desempenho   │
│                                  │   - Gráficos Recharts e KPIs        │
└──────────────────────────────────┴─────────────────────────────────────┘
```

---

## 4. Stack Tecnológica e Alinhamento com o Template Oficial (FastAPI Full-Stack)

A equipe definiu a adoção do repositório oficial **`fastapi/full-stack-fastapi-template`** como acelerador e alicerce do projeto. Essa decisão técnica é excelente para o contexto do hackathon, pois entrega infraestrutura de nível de produção pronta, permitindo foco total nas regras de negócio e na experiência do usuário.

### 4.1 O que o Template já entrega pronto:
* **Autenticação Robusta Completa:** Fluxo OAuth2 com JWT (Login, Logout, Recuperação de Senha, Hash de Senha no backend);
* **Gestão de Perfil / Conta (Tela 9 Pronta):** Módulo `/settings` funcional com edição de dados e senha;
* **Geração Automática do Cliente de API (`openapi-ts`):** O frontend sincroniza automaticamente os tipos TypeScript e funções HTTP diretamente da documentação OpenAPI gerada pelo FastAPI;
* **Arquitetura de Estado e Cache:** TanStack Query (React Query) integrado, perfeito para gerenciar o estado assíncrono e polling da IA;
* **Componentes Base Acessíveis:** Primitivas Radix UI (`@radix-ui/react-tabs`, `dialog`, etc.) e ícones `lucide-react`.

### 4.2 Tabela Comparativa e Stack Oficial Atualizada:

| Camada | Tecnologia Adotada | Benefício no Hackathon |
| :--- | :--- | :--- |
| **Core & Build** | **React 19 + TypeScript + Vite** | Inicialização ultrarrápida, HMR instantâneo e tipagem segura. |
| **Roteamento** | **TanStack Router** | Roteamento baseado em arquivos com type-safety de parâmetros e rotas protegidas. |
| **Estilização** | **Tailwind CSS v4 + Radix UI** | Produtividade 3x maior, mantendo os Design Tokens da NovaMente (Laranja `#F26B21`, Preto `#11151C`). |
| **Consumo de API & Cache** | **TanStack Query + Axios / OpenAPI-TS** | Cache inteligente de cursos gerados e controle de loading do RAG. |
| **Gráficos (Tela 7)** | **recharts** *(Adicionada - Joel)* | Visualização de evolução semanal e KPIs de retenção. |
| **Markdown (Tela 5)** | **react-markdown + remark-gfm** *(Adicionada - Joel)* | Renderização técnica de tutoriais, tabelas e código. |
| **Exportação PDF** | **jspdf + html2canvas** *(Adicionada - Joel)* | Geração de PDFs didáticos no navegador. |
| **Backend & IA** | **FastAPI + LangChain / OCI SDK** | Servidor Python assíncrono, ideal para RAG, embeddings e integração com OCI Object Storage Always Free. |

---

## 5. Design System & Tokens Visuais (Protótipo Oficial)

O design system baseia-se na identidade visual técnica do protótipo V2 (`NovaMente - Estrutura de Telas navegável V2.html`), com foco em ergonomia visual para leitura prolongada:

### Paleta de Cores
* **Laranja Primário (Accent/Destaque):** `#F26B21` (Botões de CTA, nós ativos, barras de progresso);
* **Preto Grafite (Títulos & Destaques):** `#11151C`;
* **Cinza Neutro / Muted (Subtítulos & Labels):** `#555B66`;
* **Fundo da Aplicação (Off-white Papel):** `#F6F7F4` (Ergonomia visual, sem cansaço ocular);
* **Superfície dos Cards (Branco Puro):** `#FFFFFF`;
* **Bordas & Linhas Divisórias:** `#D5D9D2`;
* **Azul Interativo (Links & Info):** `#1F4FD8` (hover: `#163BA3`);
* **Feedback Semântico:** Verde Sucesso (`#16A34A`), Vermelho Erro (`#DC2626`), Amarelo Dica (`#D97706`).

### Tipografia
1. **Headings e Chamadas:** `'Bricolage Grotesque', sans-serif` (pesos 600 e 700);
2. **Textos Corridos e Componentes:** `'IBM Plex Sans', sans-serif` (pesos 400, 500 e 600);
3. **Badges, Passos e Metadados:** `'IBM Plex Mono', monospace` (para tags `ETAPA 1 DE 4`, minutos e códigos).

---

## 6. Contratos de Dados Atualizados com TypeScript

### 6.1 `src/types/course.ts`
```typescript
export type PerfilDestinatario =
  | 'Iniciante'
  | 'Desenvolvedor Júnior'
  | 'Desenvolvedor Pleno'
  | 'Líder Técnico / Arquiteto'
  | 'Gestor / Executivo (Não Técnico)';

export type FormatoPedagogico =
  | 'Tutorial'
  | 'Flashcards'
  | 'Quiz'
  | 'Resumo Executivo (TL;DR)'
  | 'Roteiro de Aula';

export type NichoSetor = 'Fintech' | 'Saúde' | 'E-commerce' | 'Geral';

// Payload enviado via FormData na Tela 3
export interface NovoCursoPayload {
  documento_titulo: string;
  documento_conteudo?: string;
  arquivo?: File;
  perfil_destinatario: PerfilDestinatario;
  formato_saida: FormatoPedagogico;
  nicho_setor: NichoSetor;
  nivel_detalhe?: 'Didático' | 'Avançado';
}
```

### 6.2 `src/types/studyContent.ts` (Com Suporte Multiformato)
```typescript
export interface MetadadosCurso {
  perfil_aplicado: PerfilDestinatario;
  formato_gerado: FormatoPedagogico;
  tempo_estimado_estudo_minutos: number;
  conceitos_chave: string[];
}

export interface FlashcardItem {
  id: string;
  frente: string;
  verso: string;
  dica_didatica?: string;
}

export interface QuizQuestao {
  id: string;
  enunciado: string;
  opcoes: string[];
  resposta_correta_idx: number;
  justificativa: string;
}

export interface TutorialSecao {
  passo: number;
  titulo: string;
  conteudo_markdown: string;
  codigo_exemplo?: string;
}

// Multiformato por módulo na Tela 5 (Observação de Joel)
export interface ConteudoAdaptado {
  titulo: string;
  introducao_contextualizada: string;
  formato_padrao?: FormatoPedagogico;
  secoes_tutorial?: TutorialSecao[];
  itens_flashcards?: FlashcardItem[];
  questoes_quiz?: QuizQuestao[];
  resumo_tldr?: string[];
}

export interface EtapaCurso {
  id: string;
  numero: number;
  titulo: string;
  status: 'disponivel' | 'concluido' | 'bloqueado';
  conteudo?: ConteudoAdaptado;
  resultado?: {
    acertos?: number;
    total?: number;
    feedback?: 'util' | 'pode_melhorar';
  };
}

export interface CursoCompleto {
  id: string;
  titulo: string;
  descricao?: string;
  status: 'em_andamento' | 'concluido';
  progresso_percentual: number;
  metadados: MetadadosCurso;
  etapas: EtapaCurso[];
  avaliacao_geral?: {
    nota_estrelas: number;
    comentario?: string;
  };
}
```

---

## 7. Estrutura de Diretórios Proposta

```
novamente-frontend/
├── public/
│   ├── favicon.ico
│   └── docs_exemplo/                  # Documentações técnicas para teste de upload
├── src/
│   ├── assets/                        # SVGs, logotipos e ilustrações
│   ├── components/
│   │   ├── common/                    # Button, Card, Badge, Modal, Input, Stepper
│   │   ├── layout/                    # Header, Footer, PageWrapper
│   │   ├── assistant/                 # Tela 8: Popup IA Flutuante (Frente A)
│   │   │   ├── AssistantTrigger.tsx
│   │   │   ├── AssistantChat.tsx
│   │   │   └── ReportErrorModal.tsx
│   │   └── study/                     # Tela 5: Visualizadores Interativos (Frente B)
│   │       ├── TutorialViewer.tsx
│   │       ├── FlashcardViewer.tsx
│   │       ├── QuizViewer.tsx
│   │       └── ExportBar.tsx
│   ├── context/
│   │   ├── AuthContext.tsx            # Login simulado / dados da conta
│   │   └── CourseContext.tsx          # Curso ativo, histórico e persistência
│   ├── data/
│   │   ├── mockCourses.ts             # Dados ricos para teste imediato de todas as telas
│   │   └── mockAssistantFaq.ts        # Base de conhecimento e FAQ para o assistente
│   ├── pages/
│   │   ├── LoginCadastro/             # Tela 1 (Frente A)
│   │   ├── Home/                      # Tela 2 (Frente A)
│   │   ├── NovoCurso/                 # Tela 3 (Frente A)
│   │   ├── Roadmap/                   # Tela 4 (Frente B)
│   │   ├── Conteudo/                  # Tela 5 (Frente B)
│   │   ├── Finalizacao/               # Tela 6 (Frente B)
│   │   ├── Dashboard/                 # Tela 7 (Frente B)
│   │   └── DadosPessoais/             # Tela 9 (Frente A)
│   ├── services/
│   │   ├── api.ts                     # Chamadas fetch tipadas com FormData
│   │   └── exportService.ts           # Geradores de PDF, Markdown e Anki CSV
│   ├── styles/
│   │   ├── variables.css              # Tokens oficiais de cores, fontes e espaçamento
│   │   └── globals.css                # Reset CSS e estilos utilitários base
│   ├── types/
│   │   ├── course.ts
│   │   ├── studyContent.ts
│   │   └── user.ts
│   ├── App.tsx                        # Definição das rotas e wrappers globais
│   └── main.tsx
```

---

## 8. Estratégia de Documentação Contínua & Relatório para a Banca

Para atender integralmente aos critérios de avaliação do Hackathon ONE / OCI (Requisito 4 e Checklist), manteremos um registro contínuo e vivo em arquivos dedicados:

1. **`README.md` Principal:** Documento vitrine do repositório, com badges de status, arquitetura visual, passos de execução (`npm run dev`), tecnologias e prints das telas.
2. **`RELATORIO_TECNICO_PROJETO.md`:** Relatório técnico detalhado para a banca contendo:
   - Apresentação do problema e solução;
   - Matriz de papéis e responsabilidades;
   - Diagrama de arquitetura da solução (Front-end + RAG + OCI Object Storage);
   - Registro de Decisões Arquiteturais (ADRs) com justificativas técnicas;
   - Os 3 cenários práticos de demonstração exigidos pelo edital (ex: Redes OCI para Iniciante vs. Arquiteto; Kubernetes para Desenvolvedor).

---

## 9. Próximos Passos Imediatos de Execução

1. **Validação do Alinhamento:** Confirmação com Marcos e Joel deste planejamento oficial V2;
2. **Criação do Projeto Vite:** Inicialização com TypeScript e instalação das dependências (`recharts`, `react-markdown`, `remark-gfm`, `jspdf`, `html2canvas`, `lucide-react`);
3. **Criação do Design System Base (`variables.css` & `globals.css`):** Configuração das fontes Google e cores oficiais;
4. **Camada de Mock Data:** Criação de `mockCourses.ts` para que todas as telas possam ser testadas e visualizadas em paralelo desde a primeira hora de código.
