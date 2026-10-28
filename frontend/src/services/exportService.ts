// services/exportService.ts - Utilitários de Exportação Didática (PDF, Markdown e Anki CSV)
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import type { FlashcardItem, TutorialSecao } from '../types/studyContent';

/**
 * Exporta Flashcards no formato CSV compatível com o aplicativo Anki (frente;verso)
 */
export function exportarFlashcardsParaAnki(titulo: string, flashcards: FlashcardItem[]): void {
  if (!flashcards || flashcards.length === 0) return;

  const linhasCsv = flashcards.map((card) => {
    // Sanitiza e escapa aspas
    const frente = `"${card.frente.replace(/"/g, '""')}"`;
    const verso = `"${card.verso.replace(/"/g, '""')}${card.dica_didatica ? ` <br><small><i>Dica: ${card.dica_didatica}</i></small>` : ''}"`;
    return `${frente};${verso}`;
  });

  const conteudoCsv = `Frente;Verso\n${linhasCsv.join('\n')}`;
  const blob = new Blob([conteudoCsv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `${titulo.toLowerCase().replace(/\s+/g, '_')}_anki.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Exporta seções de tutorial em arquivo Markdown (.md)
 */
export function exportarTutorialParaMarkdown(titulo: string, secoes: TutorialSecao[]): void {
  if (!secoes || secoes.length === 0) return;

  let conteudoMd = `# ${titulo}\n\n*Gerado pela plataforma NovaMente (RAG Educacional)*\n\n---\n\n`;

  secoes.forEach((sec) => {
    conteudoMd += `## Passo ${sec.passo}: ${sec.titulo}\n\n`;
    conteudoMd += `${sec.conteudo_markdown}\n\n`;
    if (sec.codigo_exemplo) {
      conteudoMd += `\`\`\`${sec.linguagem_codigo || 'text'}\n${sec.codigo_exemplo}\n\`\`\`\n\n`;
    }
    conteudoMd += `---\n\n`;
  });

  const blob = new Blob([conteudoMd], { type: 'text/markdown;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `${titulo.toLowerCase().replace(/\s+/g, '_')}_tutorial.md`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Exporta um elemento HTML renderizado diretamente para PDF didático formatado
 */
export async function exportarElementoParaPdf(elementId: string, nomeArquivo: string): Promise<void> {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Elemento com ID #${elementId} não encontrado para exportação em PDF.`);
    return;
  }

  try {
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
    });

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    const imgWidth = 210; // A4 width in mm
    const pageHeight = 297; // A4 height in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    while (heightLeft >= 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    pdf.save(`${nomeArquivo.toLowerCase().replace(/\s+/g, '_')}.pdf`);
  } catch (error) {
    console.error('Erro ao gerar PDF didático:', error);
  }
}
