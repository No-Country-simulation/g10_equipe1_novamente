// data/mockAssistantFaq.ts - FAQ e Base de Conhecimento RAG para o Assistente Flutuante (Tela 8)
import type { AssistantFaqItem } from '../types/studyContent';

export const mockAssistantFaqs: AssistantFaqItem[] = [
  {
    id: 'faq-1',
    pergunta: 'O que é a camada Always Free da OCI?',
    resposta: 'A camada Always Free da Oracle Cloud Infrastructure oferece serviços de nuvem gratuitos por tempo ilimitado para estudantes e empresas, incluindo instâncias de computação AMD/ARM, Autonomous Database e até 20 GB de OCI Object Storage.',
    fonte_citada: 'Oracle Cloud Free Tier Documentation — Services Overview',
    categoria: 'oci',
  },
  {
    id: 'faq-2',
    pergunta: 'Como funciona a mitigação de alucinações no NovaMente?',
    resposta: 'O NovaMente utiliza uma pipeline de RAG (Retrieval-Augmented Generation) com busca vetorial em Vector Store (ChromaDB/FAISS). As respostas geradas pela LLM são rigidamente ancoradas e validadas por um agente crítico com base no documento técnico original.',
    fonte_citada: 'NovaMente RAG Pipeline Architecture & Quality Evaluator',
    categoria: 'didatica',
  },
  {
    id: 'faq-3',
    pergunta: 'Como exportar os Flashcards para o Anki?',
    resposta: 'Na barra de utilitários da Tela 5, clique no botão "Exportar" e selecione "Anki (CSV)". O arquivo gerado conterá a frente e o verso formatados com separador ponto-e-vírgula pronto para importação no aplicativo Anki.',
    fonte_citada: 'Guia de Exportação Pedagógica Multiformato',
    categoria: 'suporte',
  },
  {
    id: 'faq-4',
    pergunta: 'Quais formatos de arquivo posso enviar no Wizard de Novo Curso?',
    resposta: 'O NovaMente suporta documentos técnicos nos formatos PDF (.pdf), Markdown (.md) e texto puro (.txt). No upload via FormData, o arquivo é processado e persistido no bucket OCI Object Storage.',
    fonte_citada: 'Manual de Ingestão de Documentos Técnicos',
    categoria: 'suporte',
  },
];
