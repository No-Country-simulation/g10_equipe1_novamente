const mockRoadmaps = [
  {
    id: 1,
    title: "TypeScript e Arquitetura Limpa",
    description: "Conceitos avançados de SOLID, Generics e Design Patterns aplicados.",
    material: "PDF Documento",
    materialType: "pdf",
    level: "Avançado",
    progress: 40,
    hasPendingReview: true,
    reviewDaysLeft: 1
  },
  {
    id: 2,
    title: "Estruturas de Dados Avançadas",
    description: "Grafos, Árvores AVL, Tabelas Hash e Análise de Complexidade Algorítmica.",
    material: "Áudio Aula",
    materialType: "audio",
    level: "Intermediário",
    progress: 75,
    hasPendingReview: true,
    reviewDaysLeft: 3
  },
  {
    id: 3,
    title: "Fundamentos de UI/UX Design",
    description: "Hierarquia visual, sistemas de cor, acessibilidade e componentes.",
    material: "Texto & Resumo",
    materialType: "texto",
    level: "Iniciante",
    progress: 100,
    hasPendingReview: false,
    reviewDaysLeft: null
  },
  {
    id: 4,
    title: "Docker e Conteinização",
    description: "Criação de imagens, Docker Compose, volumes e redes de contentores.",
    material: "PDF Manual",
    materialType: "pdf",
    level: "Intermediário",
    progress: 20,
    hasPendingReview: false,
    reviewDaysLeft: null
  }
];

let currentFilter = "all";
let searchQuery = "";

document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  renderRoadmaps();
  setupEventListeners();
});

function setupEventListeners() {
  const themeToggleBtn = document.getElementById("themeToggle");
  themeToggleBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme");
    const isDark = document.body.classList.contains("dark-theme");
    document.getElementById("themeIcon").setAttribute("data-lucide", isDark ? "moon" : "sun");
    lucide.createIcons();
  });

  const searchInput = document.getElementById("searchInput");
  searchInput.addEventListener("input", (e) => {
    searchQuery = e.target.value.toLowerCase();
    renderRoadmaps();
  });

  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentFilter = tab.getAttribute("data-filter");
      renderRoadmaps();
    });
  });

  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-target");
      if (target !== "home") {
        navigateTo(target);
      }
    });
  });

  document.getElementById("userProfileBtn").addEventListener("click", () => {
    navigateTo("dados-pessoais");
  });

  document.getElementById("closeModal").addEventListener("click", closeModal);
}

function renderRoadmaps() {
  const pendingGrid = document.getElementById("pendingGrid");
  const roadmapsGrid = document.getElementById("roadmapsGrid");
  const pendingSection = document.getElementById("pendingSection");

  const filtered = mockRoadmaps.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery) ||
                          item.description.toLowerCase().includes(searchQuery);
    
    if (!matchesSearch) return false;

    if (currentFilter === "pending") return item.hasPendingReview;
    if (currentFilter === "progress") return item.progress > 0 && item.progress < 100;
    if (currentFilter === "completed") return item.progress === 100;
    return true;
  });

  const pendingItems = mockRoadmaps.filter(i => i.hasPendingReview);
  document.getElementById("pendingCount").innerText = pendingItems.length;

  if (currentFilter === "all" && searchQuery === "") {
    pendingSection.style.display = "block";
    pendingGrid.innerHTML = pendingItems.map(item => createCardHTML(item, true)).join("");
  } else {
    pendingSection.style.display = "none";
  }

  roadmapsGrid.innerHTML = filtered.map(item => createCardHTML(item, false)).join("");
  
  lucide.createIcons();
}

function createCardHTML(item, isPendingHighlight) {
  return `
    <div class="card ${isPendingHighlight ? 'highlight' : ''}">
      <div class="card-top">
        <span class="tag ${item.materialType}">${item.material}</span>
        <span class="level">${item.level}</span>
      </div>
      
      <div class="card-body">
        <h3>${item.title}</h3>
        <p>${item.description}</p>
      </div>

      <div class="progress-bar-container">
        <div class="progress-bar" style="width: ${item.progress}%;"></div>
      </div>

      <div class="card-actions">
        <button class="btn-primary-sm" onclick="navigateTo('roadmap', '${item.title}')">
          <i data-lucide="play-circle"></i> ${item.progress === 100 ? 'Revisar' : 'Continuar'}
        </button>
        ${item.hasPendingReview ? `
          <button class="btn-secondary-sm" onclick="navigateTo('revisar', '${item.title}')">
            <i data-lucide="rotate-ccw"></i> Fazer Revisão
          </button>
        ` : ''}
      </div>
    </div>
  `;
}

function navigateTo(screen, extraParam = "") {
  const modal = document.getElementById("screenModal");
  const content = document.getElementById("modalContent");

  let title = "";
  let description = "";
  let screenCode = "";

  switch(screen) {
    case 'novo-curso':
      screenCode = "Tela 4";
      title = "Novo Curso";
      description = extraParam 
        ? `A gerar roadmap para o tema: <strong>"${extraParam}"</strong>...` 
        : "Carregando formulário para submeter novo material (PDF, Áudio ou Texto)...";
      break;

    case 'desempenho':
      screenCode = "Tela 3";
      title = "Dashboard de Desempenho";
      description = "A carregar estatísticas de retenção, tempo de estudo e métricas de revisões...";
      break;

    case 'roadmap':
      screenCode = "Tela 5";
      title = `Roadmap: ${extraParam}`;
      description = "Redirecionando para a visualização detalhada do curso e módulos...";
      break;

    case 'revisar':
      screenCode = "Tela 5 (Modo Revisão)";
      title = `Revisão Pendente: ${extraParam}`;
      description = "Iniciando sessão de cards e questões para reforço de memória...";
      break;

    case 'dados-pessoais':
      screenCode = "Tela 9";
      title = "Dados Pessoais";
      description = "Acedendo ao perfil do utilizador, definições de conta e preferências...";
      break;
  }

  content.innerHTML = `
    <div style="text-align: center; padding: 10px;">
      <span style="background: rgba(240, 90, 34, 0.1); color: #f05a22; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.8rem;">${screenCode}</span>
      <h2 style="margin: 16px 0 8px 0; font-size: 1.4rem;">${title}</h2>
      <p style="color: var(--text-secondary); font-size: 0.95rem;">${description}</p>
    </div>
  `;

  modal.classList.remove("hidden");
}

function closeModal() {
  document.getElementById("screenModal").classList.add("hidden");
}