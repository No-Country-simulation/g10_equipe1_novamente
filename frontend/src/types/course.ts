// types/course.ts - Contratos de Criação e Configuração de Cursos NovaMente

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

export interface NovoCursoPayload {
  documento_titulo: string;
  documento_conteudo?: string;
  arquivo?: File;
  perfil_destinatario: PerfilDestinatario;
  formato_saida: FormatoPedagogico;
  nicho_setor: NichoSetor;
  nivel_detalhe?: 'Didático' | 'Avançado';
}

export interface TemaSugerido {
  id: string;
  titulo: string;
  categoria: string;
  duracao_estimada: string;
  descricao: string;
  icone?: string;
}
