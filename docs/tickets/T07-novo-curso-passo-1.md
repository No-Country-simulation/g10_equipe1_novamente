---
id: T07
title: Monte o passo 1 de "Novo curso", com arquivos e texto digitado
blocked_by: [T06]
touches:
  - frontend/src/routes/_layout/courses/new.tsx
  - frontend/src/components/NewCourse/StepList.tsx
  - frontend/src/components/NewCourse/DocumentsStep.tsx
  - frontend/src/components/NewCourse/documents.ts
  - frontend/src/components/ui/textarea.tsx
  - frontend/tests/new-course.spec.ts
executor: agente
size: 3
---

# T07 - Monte o passo 1 de "Novo curso", com arquivos e texto digitado

## Contexto

T06 entregou a rota `/courses/new` com o título, a coluna de etapas e um cartão vazio. `docs/product-specs/telas.md` define o passo 1: a pessoa anexa até 3 documentos, que são arquivos `.md`, arquivos PDF ou texto digitado em um campo. O navegador confere tipo e tamanho ao anexar. O envio ao servidor acontece uma vez, no fim do passo 3.

Este ticket entrega o passo 1 e a troca de passo. Os passos 2 e 3 e o envio entram em T27, que usa a lista de documentos definida aqui.

O layout segue o documento de design "NovaMente História 2 - Novo curso, etapa 1: materiais base", do Drive. As medidas e os textos do design estão copiados neste ticket: você não precisa abrir o Drive. O design vale para o layout. `telas.md` e `criar-curso.md` valem para as regras de produto. A seção "Onde o design e a especificação divergem" lista cada escolha.

Leia antes: `docs/product-specs/telas.md`, `docs/product-specs/criar-curso.md`, `frontend/src/routes/_layout/courses/new.tsx` e `frontend/src/components/NewCourse/StepList.tsx`.

## Escopo

- Lista de até 3 documentos, guardada no navegador.
- Anexar arquivos `.md` e PDF, pelo botão ou arrastando, com conferência de tipo e tamanho.
- Digitar um texto, que vira um arquivo `.md`.
- Remover um documento.
- Mostrar na lista o arquivo recusado, com o motivo.
- Botão "Continuar", que leva ao passo 2, e botão "Voltar" no passo 2.
- Clique em uma etapa concluída da coluna de etapas.

## Fora do escopo

- Campos dos passos 2 e 3 e o envio a `POST /api/v1/courses/` (T27).
- Ler o conteúdo de um PDF no navegador. O servidor confere se o PDF tem texto (T37).
- Conferir arquivo repetido. O servidor responde "Este arquivo já está no curso." (T23).
- Guardar a lista entre recargas da página. Um `File` não sobrevive a uma recarga.
- Botão "Tentar de novo" na linha de um arquivo recusado. Veja a seção das divergências.

## Contrato

T27 é escrito contra estes nomes. Não mude nome, assinatura nem caminho.

Em `frontend/src/components/NewCourse/documents.ts`:

```ts
export const MAX_DOCUMENTS = 3
export const MAX_FILE_BYTES = 5 * 1024 * 1024
export const MAX_TEXT_CHARS = 150_000
export const ACCEPTED_EXTENSIONS = [".md", ".pdf"] as const

export interface DraftDocument {
  /** Identificador local, de `crypto.randomUUID()`. */
  id: string
  /** O arquivo que T27 envia no campo `files`. */
  file: File
  source: "upload" | "typed"
}

/** Devolve a mensagem de erro, ou `null` se o arquivo passa. */
export function checkFile(file: File): string | null

/** Devolve a mensagem de erro, ou `null` se o texto passa. */
export function checkTypedText(text: string): string | null

/** Cria o arquivo `.md` de um texto digitado, com um nome livre na lista. */
export function typedTextFile(text: string, documents: DraftDocument[]): File
```

Em `frontend/src/components/NewCourse/DocumentsStep.tsx`:

```ts
interface DocumentsStepProps {
  documents: DraftDocument[]
  onChange: (documents: DraftDocument[]) => void
  onContinue: () => void
}

export function DocumentsStep(props: DocumentsStepProps): JSX.Element
```

`documents` traz só os documentos aceitos. Os arquivos recusados ficam em um estado local de `DocumentsStep` e nunca chegam a T27.

Em `frontend/src/components/NewCourse/StepList.tsx`, `StepListProps` ganha uma prop opcional:

```ts
interface StepListProps {
  current: number
  completed: number[]
  /** Chamada com o número da etapa quando a pessoa clica em uma etapa concluída. */
  onSelect?: (step: number) => void
}
```

Em `frontend/src/routes/_layout/courses/new.tsx`, o componente `NewCourse` guarda dois estados com `useState`: `step` (1, 2 ou 3, começa em 1) e `documents` (`DraftDocument[]`, começa vazio). T27 acrescenta os estados dos passos 2 e 3 no mesmo componente.

Regras de `checkFile`, nesta ordem:

| Ordem | Condição | Mensagem |
| --- | --- | --- |
| 1 | O nome não termina em `.md` nem em `.pdf`, sem diferenciar maiúsculas | Envie um arquivo .md ou PDF, ou digite o texto. |
| 2 | `file.size` é 0 | O arquivo não tem texto. |
| 3 | `file.size` passa de `MAX_FILE_BYTES` | O arquivo passa de 5 MiB. |

Regras de `checkTypedText`:

| Condição | Mensagem |
| --- | --- |
| O texto é vazio ou só tem espaços | O arquivo não tem texto. |
| O texto tem mais de `MAX_TEXT_CHARS` caracteres | O documento é longo demais. Envie um documento menor ou divida o arquivo. |

Regras de `typedTextFile`:

- O arquivo tem tipo `text/markdown` e o texto em UTF-8.
- O nome é `texto-digitado.md`. Se a lista já tem um documento com esse nome, o nome é `texto-digitado-2.md`, e depois `texto-digitado-3.md`.

As mensagens são as de `criar-curso.md`. Não mude a redação.

## Comportamento esperado

### Cartão da etapa

O cartão tem fundo branco, borda de 1 px (`--border`), raio 12 e altura mínima de 560. O conteúdo tem padding 24 e 24 de espaço entre os blocos. O rodapé fica colado ao fundo do cartão.

De cima para baixo:

1. O cabeçalho, com 8 de espaço entre as linhas:
    - "ETAPA 1 DE 3": IBM Plex Sans, 12 px, peso 600, caixa alta, espaçamento de 0,08 em, cor `--foreground-tertiary`;
    - o título "Documentos": Space Grotesk, 30 px, peso 700;
    - a frase "Envie os seus materiais. Todos entram no curso.": 16 px, entrelinha 1,5, cor `--muted-foreground`.
2. O rótulo "Seus próprios materiais", com 16 px e peso 600.
3. Duas abas (`Tabs`): "Enviar arquivo" e "Digitar texto". "Enviar arquivo" abre primeiro.
4. A lista de documentos, 12 px abaixo das abas.
5. O rodapé: uma faixa de largura total, com padding 24, linha superior de 1 px (`--border`) e fundo `--muted` com 50% de opacidade. À direita, o botão "Continuar". No passo 1 não há "Voltar".

T06 deixou o rótulo da etapa e o título com outros tamanhos e outra cor. Ajuste os dois em `new.tsx` para os valores acima. O título continua em `CardTitle`, porque um teste de T06 o procura por `data-slot="card-title"`.

### Aba "Enviar arquivo"

A aba mostra a área de envio: padding de 20 na vertical e 24 na horizontal, borda tracejada de 2 px (`--border-strong`), raio 12 e fundo igual ao da página (`--background`).

- À esquerda, o ícone `Upload` do `lucide-react` (32 px, traço 1,75). A 14 px dele, o texto "Arraste os arquivos até aqui" (16 px, peso 600) e, abaixo, a dica "MD ou PDF, até 5 MiB" (14 px, cor `--muted-foreground`).
- À direita, o botão "Escolher arquivos" (`Button` com `variant="outline"`, altura mínima 48, padding lateral 22).
- O botão abre a seleção de arquivos de um `Input` de arquivo escondido, com o rótulo acessível "Arquivos", que aceita vários arquivos (`multiple`) e sugere `.md` e `.pdf` (`accept`).
- Soltar arquivos sobre a área tem o mesmo efeito de escolher pelo botão.
- Cada arquivo passa por `checkFile`, na ordem em que veio. O arquivo que passa entra em `documents`. O arquivo que falha entra na lista como linha recusada, com a mensagem de `checkFile`.
- Um arquivo que chega com `documents` cheio entra como linha recusada, com a mensagem "Envie até 3 documentos."

### Aba "Digitar texto"

- Um `Textarea` com o rótulo "Texto do documento" e o botão "Adicionar texto".
- O botão fica desabilitado com o campo vazio.
- No clique, o texto passa por `checkTypedText`. Se passa, `typedTextFile` cria o arquivo, o documento entra em `documents` e o campo fica vazio. Se falha, a mensagem aparece abaixo do campo.

### Lista de documentos

Uma linha por arquivo, com 12 de espaço entre as linhas. Os documentos aceitos vêm primeiro, na ordem de `documents`. As linhas recusadas vêm depois.

| Linha | Aparência |
| --- | --- |
| Aceita | Altura mínima 52, padding lateral 16, borda de 1 px (`--border`), raio 8. À esquerda, o ícone `FileText` (20 px, traço 1,75) e o nome do arquivo em IBM Plex Mono (`font-mono`), 14 px. À direita, o botão de remover. |
| Recusada | Borda de 1,5 px (`--destructive`), raio 8, fundo branco. À esquerda, o ícone `FileText` na cor `--destructive`, o nome do arquivo e, abaixo do nome, a mensagem (13 px, peso 600, cor `--destructive`). À direita, o botão de remover. |

- O botão de remover é um `Button` só com o ícone `X` (18 px, traço 1,75), em uma área de 44 por 44, com `aria-label` "Remover nome-do-arquivo".
- Remover uma linha aceita tira o documento de `documents`. Remover uma linha recusada tira só a linha.
- Uma linha recusada não conta para o limite de 3 e não impede o "Continuar".
- As linhas recusadas ficam na lista até a pessoa removê-las. Elas se perdem na troca de passo, porque vivem no estado local de `DocumentsStep`.
- Sem nenhuma linha, a lista não mostra nada.
- Com 3 documentos aceitos, o botão "Escolher arquivos", a área de envio, o `Textarea` e o botão "Adicionar texto" ficam desabilitados, e aparece o texto "Limite de 3 documentos atingido."

### Troca de passo

- "Continuar" é o botão escuro do design: fundo `--foreground`, texto branco, altura mínima 48, padding lateral 28, raio 6. Desabilitado, ele usa fundo `--muted` e texto `--foreground-tertiary`.
- "Continuar" fica desabilitado sem documento aceito.
- O clique em "Continuar" muda `step` para 2. A coluna de etapas mostra a etapa 1 como concluída e a 2 como atual (`StepList current={2} completed={[1]}`).
- No passo 2, o cartão mostra "ETAPA 2 DE 3", o título "Perfil" e, no rodapé, à esquerda, o botão "Voltar" (`variant="outline"`, altura mínima 48, padding lateral 22). T27 acrescenta os campos e o "Continuar" do passo 2.
- "Voltar" muda `step` para 1 e mantém os documentos aceitos.

### Coluna de etapas

- Com `onSelect`, cada etapa concluída vira um `Button` sem fundo (`variant="ghost"`) que chama `onSelect` com o número da etapa. A etapa atual e as etapas futuras não respondem ao clique.
- Sem `onSelect`, `StepList` se comporta como hoje.
- `NewCourse` passa `onSelect={setStep}`. No passo 2, o clique na etapa 1 volta ao passo 1 e mantém os documentos.
- O texto de cada item da lista não muda: "1Documentos", "2Perfil" e "3Formatos". Um teste de T06 confere esse texto.

## Onde o design e a especificação divergem

| Tema | Design | Este ticket | Motivo |
| --- | --- | --- | --- |
| Tamanho do arquivo | 2 MB | 5 MiB | Regra de produto, de `criar-curso.md`. |
| Número de arquivos | Sem limite | Até 3 | Regra de produto. |
| Tipos | PDF, Markdown e texto | `.md` e PDF | Regra de produto. O `.txt` não entra. |
| Nomes das etapas | Materiais base, Nível e tema, Formato | Documentos, Perfil, Formatos | `telas.md` e T06, já no `master`. |
| Mensagem do arquivo recusado | "Falha no envio do arquivo." para qualquer caso | A mensagem de `checkFile` | `telas.md`: uma mensagem de erro diz o que aconteceu e o que a pessoa pode fazer. |
| Botão "Tentar de novo" | Na linha recusada | Não entra | O passo 1 não envia nada ao servidor. Conferir de novo o mesmo arquivo dá o mesmo resultado. |
| Texto digitado | Não existe | Aba "Digitar texto" | `criar-curso.md` exige o texto digitado. |

Pendência: o design não desenha o texto digitado. As abas "Enviar arquivo" e "Digitar texto" e os textos "Limite de 3 documentos atingido." e "Envie até 3 documentos." são uma proposta deste ticket. Quem cuida do design confere na revisão.

Pendência: este ticket foi escrito a partir do texto do documento de design. As imagens do documento não foram vistas. Uma pessoa compara a tela com as imagens na revisão.

## Detalhes técnicos

- Use componentes shadcn em toda a interface, sem HTML cru para elementos que têm componente: `Tabs`, `Input`, `Label`, `Button` e `Card` já existem em `frontend/src/components/ui/`. Adicione o `Textarea` com `bunx shadcn@latest add textarea`. Esse componente não traz dependência nova, então `frontend/package.json` e `bun.lock` não mudam. Se mudarem, pare e relate.
- Use as variáveis de cor de `frontend/src/index.css`. Não escreva valor hexadecimal nos componentes.
- A área de envio trata `onDragOver` e `onDrop` e lê `event.dataTransfer.files`. Não acrescente biblioteca de arrastar.
- Nenhum outro ticket da onda edita `StepList.tsx` nem `new.tsx`.
- T17 e T18 rodam na mesma onda. Não edite `frontend/src/components/Common/TopNav.tsx`, `frontend/tests/navigation.spec.ts` nem `frontend/tests/utils/`. T17 muda o destino de `/`: nos testes, abra `/courses/new` direto e não dependa da tela `/`.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Nos testes, anexe arquivos com `setInputFiles` e um `buffer`. Não guarde arquivo binário no repositório.
- O teste "New course page shows the title, the steps and the step card", em `navigation.spec.ts`, precisa continuar passando sem edição.

## Critérios de aceite

- [ ] A pessoa anexa arquivos `.md` e PDF, pelo botão ou arrastando, digita um texto e remove um documento.
- [ ] Um arquivo de outro tipo, vazio ou maior que 5 MiB aparece como linha recusada, com o motivo, e não entra em `documents`.
- [ ] `documents` nunca passa de 3 documentos.
- [ ] "Continuar" só funciona com pelo menos um documento aceito, e "Voltar" mantém os documentos.
- [ ] O clique em uma etapa concluída leva a essa etapa. As etapas futuras não respondem ao clique.
- [ ] `documents.ts`, `DocumentsStep` e `StepList` cumprem o contrato.
- [ ] Os testes Playwright que já existem passam.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/new-course.spec.ts`, com o login padrão do projeto:

1. `/courses/new` mostra "Seus próprios materiais", as abas "Enviar arquivo" e "Digitar texto", o texto "Arraste os arquivos até aqui", o botão "Escolher arquivos" e o botão "Continuar" desabilitado.
2. Anexar `guia.md` com 2.048 bytes: a lista mostra `guia.md` e o botão "Remover guia.md", e "Continuar" fica habilitado.
3. Anexar `guia.pdf` com alguns bytes: a lista mostra `guia.pdf`.
4. Anexar `notas.txt`: a lista mostra `notas.txt` com "Envie um arquivo .md ou PDF, ou digite o texto.", e "Continuar" continua desabilitado.
5. Anexar `vazio.md` com 0 bytes: a linha mostra "O arquivo não tem texto."
6. Anexar `grande.md` com 5 MiB mais 1 byte: a linha mostra "O arquivo passa de 5 MiB." Com 5 MiB exatos, o arquivo entra sem mensagem.
7. Com `guia.md` aceito e `notas.txt` recusado, "Continuar" fica habilitado. Remover `notas.txt` tira só essa linha.
8. Digitar um texto e clicar em "Adicionar texto": a lista mostra `texto-digitado.md` e o campo fica vazio. Um segundo texto vira `texto-digitado-2.md`.
9. Anexar 4 arquivos válidos de uma vez: os 3 primeiros entram, o quarto aparece com "Envie até 3 documentos.", e "Escolher arquivos", o campo de texto e "Adicionar texto" ficam desabilitados.
10. Com 3 documentos, remover um: o documento sai da lista e os campos voltam a ficar habilitados.
11. Com um documento, clicar em "Continuar": a tela mostra "ETAPA 2 DE 3" e "Perfil", e a etapa 2 tem `aria-current="step"`. Clicar em "Voltar": a tela mostra "ETAPA 1 DE 3" e o documento continua na lista.
12. No passo 2, clicar na etapa "Documentos" da coluna volta ao passo 1. No passo 1, a etapa "Perfil" não é um botão.
13. Soltar `guia.md` sobre a área de envio, com um evento `drop` e um `DataTransfer` montado no navegador: a lista mostra `guia.md`.
