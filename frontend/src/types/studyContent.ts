// types/studyContent.ts - Contratos de Conteúdo Didático, Avaliação e Métricas NovaMente
import type { FormatoPedagogico, PerfilDestinatario } from './course';

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
  linguagem_codigo?: string;
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
    concluido_em?: string;
  };
}

export interface CursoCompleto {
  id: string;
  titulo: string;
  descricao?: string;
  status: 'em_andamento' | 'concluido';
  progresso_percentual: number;
  criado_em: string;
  documento_origem: string;
  metadados: MetadadosCurso;
  etapas: EtapaCurso[];
  avaliacao_geral?: {
    nota_estrelas: number;
    comentario?: string;
  };
}

export interface EstatisticasDashboard {
  taxa_finalizacao_percentual: number;
  cursos_gerados: number;
  cursos_concluidos: number;
  tempo_total_estudo_minutos: number;
  evolucao_semanal: {
    semana: string;
    estudos: number;
    quizzes_respondidos: number;
  }[];
  distribuicao_temas: {
    tema: string;
    quantidade: number;
  }[];
  historico_recente: {
    id: string;
    curso_titulo: string;
    formato: string;
    conclusao_data: string;
    score?: number;
    status: 'Concluído' | 'Em Andamento';
  }[];
}

export interface AssistantFaqItem {
  id: string;
  pergunta: string;
  resposta: string;
  fonte_citada: string;
  categoria: 'oci' | 'didatica' | 'suporte';
}

export interface AssistantMessage {
  id: string;
  remetente: 'usuario' | 'assistente';
  texto: string;
  data_hora: string;
  fontes?: string[];
  sugestoes_seguintes?: string[];
}
