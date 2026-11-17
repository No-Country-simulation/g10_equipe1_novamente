---
id: T07
title: Monte o passo 1 de "Novo curso", com arquivos e texto digitado
blocked_by: [T06]
touches:
  - frontend/src/routes/_layout/courses/new.tsx
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

Leia antes: `docs/product-specs/telas.md`, `docs/product-specs/criar-curso.md` e `frontend/src/routes/_layout/courses/new.tsx`.

## Escopo

- Lista de até 3 documentos, guardada no navegador.
- Anexar arquivos `.md` e PDF, com conferência de tipo e tamanho.
- Digitar um texto, que vira um arquivo `.md`.
- Remover um documento.
- Botão "Continuar", que leva ao passo 2, e botão "Voltar" no passo 2.

## Fora do escopo

- Campos dos passos 2 e 3 e o envio a `POST /api/v1/courses/` (T27).
- Ler o conteúdo de um PDF no navegador. O servidor confere se o PDF tem texto (T37).
- Conferir arquivo repetido. O servidor responde "Este arquivo já está no curso." (T23).
- Guardar a lista entre recargas da página. Um `File` não sobrevive a uma recarga.

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

O cartão do passo 1 mantém o rótulo "ETAPA 1 DE 3" e o título "Documentos" de T06. Abaixo deles, de cima para baixo:

1. Um texto de apoio: "Anexe até 3 documentos. Aceitamos arquivos .md e PDF de até 5 MiB, ou um texto digitado."
2. Duas abas (`Tabs`): "Enviar arquivo" e "Digitar texto". "Enviar arquivo" abre primeiro.
3. A lista "Documentos do curso", com um item por documento.
4. No rodapé do cartão, à direita, o botão "Continuar".

### Aba "Enviar arquivo"

- Um campo de arquivo com o rótulo "Arquivos", que aceita vários arquivos (`multiple`) e sugere `.md` e `.pdf` (`accept`).
- Cada arquivo escolhido passa por `checkFile`, na ordem em que veio. O arquivo que passa entra na lista. O arquivo que falha não entra.
- Um arquivo que chega com a lista cheia não entra, com a mensagem "Envie até 3 documentos."
- As mensagens de erro aparecem em um `Alert` de erro, abaixo do campo, uma linha por arquivo recusado, no formato `nome-do-arquivo: mensagem`. O alerta some na próxima escolha de arquivos.

### Aba "Digitar texto"

- Um `Textarea` com o rótulo "Texto do documento" e o botão "Adicionar texto".
- O botão fica desabilitado com o campo vazio.
- No clique, o texto passa por `checkTypedText`. Se passa, `typedTextFile` cria o arquivo, o documento entra na lista e o campo fica vazio. Se falha, a mensagem aparece abaixo do campo.

### Lista de documentos

- Cada item mostra o nome do arquivo em IBM Plex Mono (`font-mono`), o tamanho em KiB ou MiB com uma casa decimal e o botão "Remover", com `aria-label` "Remover nome-do-arquivo".
- Sem documentos, a lista mostra "Nenhum documento anexado."
- Com 3 documentos, o campo de arquivo, o `Textarea` e o botão "Adicionar texto" ficam desabilitados, e aparece o texto "Limite de 3 documentos atingido."

### Troca de passo

- "Continuar" fica desabilitado com a lista vazia.
- O clique em "Continuar" muda `step` para 2. A coluna de etapas mostra a etapa 1 como concluída e a 2 como atual (`StepList current={2} completed={[1]}`).
- No passo 2, o cartão mostra "ETAPA 2 DE 3", o título "Perfil" e o botão "Voltar". T27 acrescenta os campos.
- "Voltar" muda `step` para 1 e mantém a lista de documentos.

Pendência: os documentos de design do Drive não estavam acessíveis quando este ticket foi escrito. A disposição acima e os textos "Limite de 3 documentos atingido.", "Envie até 3 documentos." e "Nenhum documento anexado." são uma leitura conservadora de `telas.md`. Uma pessoa confere com o design na revisão.

## Detalhes técnicos

- Use componentes shadcn em toda a interface, sem HTML cru para elementos que têm componente: `Tabs`, `Input`, `Label`, `Button`, `Alert` e `Card` já existem em `frontend/src/components/ui/`. Adicione o `Textarea` com `bunx shadcn@latest add textarea`. Esse componente não traz dependência nova, então `frontend/package.json` e `bun.lock` não mudam. Se mudarem, pare e relate.
- `STEPS` e `StepList` vêm de `@/components/NewCourse/StepList`. Não edite esse arquivo.
- T17 e T18 rodam na mesma onda. Não edite `frontend/src/components/Common/TopNav.tsx`, `frontend/tests/navigation.spec.ts` nem `frontend/tests/utils/`. T17 muda o destino de `/`: nos testes, abra `/courses/new` direto e não dependa da tela `/`.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Nos testes, anexe arquivos com `setInputFiles` e um `buffer`. Não guarde arquivo binário no repositório.
- O teste "New course page shows the title, the steps and the step card", em `navigation.spec.ts`, precisa continuar passando sem edição.

## Critérios de aceite

- [ ] A pessoa anexa arquivos `.md` e PDF, digita um texto e remove um documento.
- [ ] Um arquivo de outro tipo, vazio ou maior que 5 MiB não entra na lista, e a mensagem diz o motivo.
- [ ] A lista nunca passa de 3 documentos.
- [ ] "Continuar" só funciona com pelo menos um documento, e "Voltar" mantém a lista.
- [ ] `documents.ts` e `DocumentsStep` cumprem o contrato.
- [ ] Os testes Playwright que já existem passam.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/new-course.spec.ts`, com o login padrão do projeto:

1. `/courses/new` mostra as abas "Enviar arquivo" e "Digitar texto", o texto "Nenhum documento anexado." e o botão "Continuar" desabilitado.
2. Anexar `guia.md` com 2.048 bytes: a lista mostra `guia.md` e "2.0 KiB", e "Continuar" fica habilitado.
3. Anexar `guia.pdf` com alguns bytes: a lista mostra `guia.pdf`.
4. Anexar `notas.txt`: a lista continua vazia e o alerta mostra "notas.txt: Envie um arquivo .md ou PDF, ou digite o texto."
5. Anexar `vazio.md` com 0 bytes: o alerta mostra "vazio.md: O arquivo não tem texto."
6. Anexar `grande.md` com 5 MiB mais 1 byte: o alerta mostra "grande.md: O arquivo passa de 5 MiB." Com 5 MiB exatos, o arquivo entra.
7. Digitar um texto e clicar em "Adicionar texto": a lista mostra `texto-digitado.md` e o campo fica vazio. Um segundo texto vira `texto-digitado-2.md`.
8. Anexar 4 arquivos válidos de uma vez: a lista mostra os 3 primeiros, o alerta mostra "Envie até 3 documentos." para o quarto, e o campo de arquivo, o campo de texto e "Adicionar texto" ficam desabilitados.
9. Com 3 documentos, remover um: o documento sai da lista e os campos voltam a ficar habilitados.
10. Com um documento, clicar em "Continuar": a tela mostra "ETAPA 2 DE 3" e "Perfil", e a etapa 2 tem `aria-current="step"`. Clicar em "Voltar": a tela mostra "ETAPA 1 DE 3" e o documento continua na lista.
