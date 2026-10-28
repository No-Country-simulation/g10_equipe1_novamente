# NovaMente 🧠✨

> **Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional**  
> *Projeto desenvolvido para a Simulação No-Country — G10 Equipe 1*

---

## 📌 Sobre o Projeto

O **NovaMente** é uma plataforma educacional inteligente projetada para transformar o aprendizado de pessoas neurodivergentes (como TDAH, TEA e dislexia) e profissionais em transição de carreira. A plataforma utiliza Inteligência Artificial generativa para criar trilhas de estudo personalizadas (*roadmaps*), quebrar conteúdos complexos em microlearning e oferecer suporte adaptativo contínuo, reduzindo a sobrecarga cognitiva e a frustração no estudo.

### 🌟 Principais Funcionalidades

- **🗺️ Roadmaps Adaptativos Inteligentes**: Criação de trilhas de aprendizado dinâmicas, divididas por fases, semanas e tópicos claros.
- **🎯 Modo Foco & Acessibilidade**: Interface limpa, com controle de distrações e formatação visual voltada para menor estresse cognitivo.
- **💬 Assistente Pedagógico Integrado**: Tire dúvidas em tempo real com explicação adaptada ao seu estilo de aprendizado e FAQ inteligente contextual.
- **📊 Acompanhamento de Progresso**: Dashboard com métricas de evolução, tempo de estudo focado e metas atingidas.
- **📚 Documentação e Planejamento**: Documentos técnicos, diagramas e relatórios arquiteturais disponíveis no repositório na pasta `docs/`.

---

## 🛠️ Tecnologias Utilizadas

- **Frontend**: [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/) & [shadcn/ui](https://ui.shadcn.com/)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+), [Pydantic v2](https://docs.pydantic.dev/), [SQLModel](https://sqlmodel.tiangolo.com/)
- **Banco de Dados**: [PostgreSQL](https://www.postgresql.org/)
- **Infraestrutura**: [Docker](https://www.docker.com/) & Docker Compose, [Traefik](https://traefik.io/) (proxy reverso)
- **Gerenciamento de Pacotes**: [uv](https://github.com/astral-sh/uv) (Python) e [Bun](https://bun.sh/) / npm (Frontend)

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) e Docker Compose instalados **OU**
- Node.js (v18+) / Bun e Python 3.10+ para execução local sem Docker.

### Opção 1: Execução com Docker (Recomendada)
Para subir o banco de dados, o backend e o frontend juntos:

```bash
# 1. Clone o repositório
git clone git@github.com:No-Country-simulation/g10_equipe1_novamente.git
cd g10_equipe1_novamente

# 2. Crie o arquivo de ambiente a partir do exemplo
cp .env.example .env

# 3. Suba os containers
docker compose up -d
```

Acesse:
- **Frontend**: http://localhost:5173 (ou http://localhost)
- **API Docs (Swagger)**: http://localhost/docs ou http://localhost:8000/docs

---

### Opção 2: Desenvolvimento Local (Frontend)
Para rodar apenas o frontend de forma rápida:

```bash
cd frontend
npm install # ou bun install
npm run dev # ou bun run dev
```
Acesse: `http://localhost:5173`

---

## 📂 Estrutura do Repositório

```
g10_equipe1_novamente/
├── frontend/           # Aplicação Web em React + Vite + TypeScript
│   ├── src/
│   │   ├── components/ # Componentes (Sidebar, Assistente, Logos, etc.)
│   │   ├── routes/     # Rotas (Dashboard, Novo Curso, Roadmap, Conteúdo)
│   │   └── services/   # Integração com APIs
├── backend/            # API REST em FastAPI e modelos de dados
│   ├── app/
│   │   ├── api/        # Rotas da API
│   │   ├── models/     # Modelos do banco de dados (SQLModel)
│   │   └── core/       # Configurações de segurança e autenticação
├── docs/               # Documentação técnica e relatórios do projeto
└── compose.yml         # Configuração de containers Docker
```

---

## 👥 Equipe NovaMente (No-Country G10 - Equipe 1)

Projeto desenvolvido com dedicação e foco em impacto social e inclusão educacional.
Licença sob a [Licença MIT](LICENSE).
