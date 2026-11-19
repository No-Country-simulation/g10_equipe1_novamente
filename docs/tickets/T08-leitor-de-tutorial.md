---
id: T08
title: Mostre o tutorial publicado, com resumo, seções em Markdown e "Para levar"
blocked_by: [T18]
touches:
  - frontend/src/components/Course/readers/TutorialReader.tsx
  - frontend/package.json
  - bun.lock
  - frontend/tests/tutorial-reader.spec.ts
  - frontend/tests/course.spec.ts
executor: agente
size: 2
---

# T08 - Mostre o tutorial publicado, com resumo, seções em Markdown e "Para levar"

## Contexto

T18 entregou a tela de um conteúdo. Hoje `TutorialReader` mostra só "O leitor deste formato ainda não está disponível." O tutorial tem um resumo, de 1 a 8 seções em Markdown e de 1 a 5 itens "Para levar".

Este ticket troca o conteúdo de `TutorialReader.tsx`. A moldura, os metadados e o aviso de estado são de T18 e não mudam.

O layout vem da captura [`tela-6-conteudo-tutorial.png`](../design/telas-finais/tela-6-conteudo-tutorial.png): o cartão branco abaixo do cabeçalho escuro.

Leia antes: `docs/product-specs/conteudos-e-formatos.md`, seção "Tutorial", `docs/tickets/completed/T18-tela-curso.md`, seção "Contrato", e `backend/app/services/content_schemas.py`, classe `TutorialContent`.

## Escopo

- O leitor do tutorial, dentro do cartão branco da tela 6.
- O texto das seções em Markdown, com listas, tabelas, blocos de código e código no meio do texto.
- O aviso para um conteúdo guardado fora do formato do tutorial.
- A dependência que lê Markdown.

## Fora do escopo

- A moldura da tela, o cabeçalho escuro, os metadados e os avisos de estado (T18, pronto).
- Fidelidade, clareza e trechos citados (T38).
- Os três quadros "SERVIÇO", "SPAN" e "DURAÇÃO" da captura. O formato do tutorial não tem esse campo.
- O botão "Finalizar". `telas.md` deixa a tela de finalização fora do MVP.
- Leitores de flashcards (T09) e de quiz (T10).

## Contrato

### Módulos que este ticket usa

Do `master`. Não edite esses arquivos.

```ts
// frontend/src/components/Course/readers/types.ts (T18)
export interface ReaderProps {
  /** `ContentPublic.content`, na forma do formato. */
  content: { [key: string]: unknown }
}
```

`ContentView.tsx` monta `ContentReader` quando `ContentPublic.content` tem um valor, inclusive nos estados `running` e `failed`. `ContentReader.tsx` escolhe `TutorialReader` para o formato `tutorial`.

A forma do tutorial vem de `TutorialContent`, em `backend/app/services/content_schemas.py`:

```python
class TutorialSection(StrictModel):
    title: Text  # 1 caractere ou mais
    body: Text  # Markdown


class TutorialContent(StrictModel):
    summary: Text
    sections: list[TutorialSection]  # de 1 a 8
    takeaways: list[Text]  # de 1 a 5
```

### O que este ticket muda

`frontend/src/components/Course/readers/TutorialReader.tsx` continua a exportar `TutorialReader(props: ReaderProps)`. Não mude o nome, a assinatura nem o caminho.

## Comportamento esperado

### Conteúdo no formato do tutorial

Use `zod` para validar os campos que o leitor usa em `TutorialContent`. Exija os tipos indicados, textos com ao menos um caractere após `trim()`, de 1 a 8 seções e de 1 a 5 itens em "Para levar". Ignore campos extras no leitor.

Com `content` válido, o leitor mostra um `Card` centralizado, com largura máxima de 800 px, borda de 1 px, raio de 12 px, fundo `bg-card` e padding de 40 px (24 px abaixo de 640 px). De cima para baixo:

1. O resumo: 17 px, altura de linha 1,6, `text-foreground`.
2. Cada seção, na ordem de `sections`:
    - o título, como `h3`, em Space Grotesk (`font-heading`), 22 px, peso 700, com 32 px acima;
    - o texto, lido como Markdown, com 15 a 16 px, altura de linha 1,6 e `text-muted-foreground`.
3. "Para levar", como `h3`, no mesmo estilo dos títulos das seções, e uma lista com marcadores, um item por elemento de `takeaways`.

O título do conteúdo não aparece no leitor: ele já está no card "Sobre este conteúdo", de T18.

### Markdown

Use `react-markdown` para renderizar o Markdown em React. O plugin `remark-gfm` dá suporte às tabelas que a especificação pede. Use a prop `components` para aplicar as classes do Tailwind.

| Elemento | Aparência |
| --- | --- |
| Parágrafo | 16 px de espaço abaixo |
| Lista com marcadores ou numerada | Marcador visível, recuo de 20 px |
| Código no meio do texto | `font-mono`, 14 px, fundo `bg-muted`, padding de 2 por 6 px, raio 4 |
| Bloco de código | `font-mono`, 14 px, fundo `bg-muted`, padding de 16 px, raio 8, rolagem horizontal (`overflow-x-auto`) |
| Tabela | Borda de 1 px nas células, padding de 8 px, cabeçalho em peso 600, rolagem horizontal em telas estreitas |
| Título dentro do texto (`#` a `######`) | `h4`, 17 px, peso 600. O texto vem do modelo e não pode criar um título maior que o da seção. |
| Link | `text-info`, sublinhado, com `target="_blank"` e `rel="noreferrer"` |

O Markdown vem do modelo, que leu um documento enviado pela pessoa. Use `skipHtml` para descartar as tags HTML e mantenha o `urlTransform` padrão de `react-markdown`.

### Conteúdo fora do formato

Quando `content` não passa no schema, por exemplo `{}`, o leitor mostra só um `Alert` com o texto "Não foi possível mostrar este conteúdo, porque ele não está no formato esperado." O backend valida o formato ao publicar (T22). O aviso cobre dados fora do contrato, que o seed de testes permite criar.

T09 e T10 usam a mesma frase nos seus leitores. Não crie um arquivo comum: cada leitor tem a sua cópia, para os três tickets rodarem ao mesmo tempo sem conflito.

## Onde o design e a especificação divergem

| Elemento | Telas finais | Este ticket | Motivo |
| --- | --- | --- | --- |
| Títulos "Etapa 1: Instale o SDK" | Título da seção | `section.title`, como o modelo escreveu | O formato não numera as seções. |
| Quadros "SERVIÇO", "SPAN" e "DURAÇÃO" | Dentro da etapa 5 | Saem | O formato não tem esse campo. |
| Botão "Finalizar" | Abaixo do cartão | Sai | Fora do MVP (`telas.md`). |
| Fundo azul claro da página | Atrás do cartão | Fundo da página do layout | O layout de T18 não muda o fundo. |
| Aviso de conteúdo fora do formato | Não aparece | `Alert` com a frase acima. Proposta. | `telas.md`: uma mensagem de erro diz o que aconteceu. |

## Testes que mudam

Em `frontend/tests/course.spec.ts`, preencha o campo `content` de `publishedTutorial` com um tutorial válido. Nas duas verificações abaixo, troque `readerPlaceholder` pelo texto do resumo desse tutorial.

- No teste "abre diretamente o único conteúdo com seus metadados".
- No teste "mantém o conteúdo publicado legível durante falha ou geração", na tela do tutorial `failed`, após o título "Introdução".

T09 atualiza o caso de flashcards `running` no mesmo teste. Depois do `rebase`, o último dos dois tickets apaga `readerPlaceholder` se a constante ficar sem uso.

`frontend/tests/courses.spec.ts` não muda: ele usa `content: {}`, mas não confere o texto do leitor.

## Detalhes técnicos

- Na pasta `frontend`, rode `bun add react-markdown@10.1.0 remark-gfm@4.0.1` com a versão do Bun usada no CI (1.3.12). O comando atualiza `frontend/package.json` e o `bun.lock` da raiz. Confira o lockfile com `bun install --frozen-lockfile` na raiz. Em caso de conflito, siga a regra de arquivos gerados do [README dos tickets](README.md). [react-markdown](https://github.com/remarkjs/react-markdown/releases/tag/10.1.0), [remark-gfm](https://www.npmjs.com/package/remark-gfm/v/4.0.1), [Bun workspaces](https://bun.com/guides/install/workspaces).
- Use o `zod` 4 já instalado (`4.6.5` no `bun.lock`). Defina o schema dentro de `TutorialReader.tsx`.
- Use componentes shadcn onde houver: `Card` e `Alert` já existem em `frontend/src/components/ui/`.
- Use só as variáveis de cor de `frontend/src/index.css`. Não escreva valor hexadecimal.
- Não edite `ContentReader.tsx`, `ContentView.tsx`, `readers/types.ts`, os outros leitores nem `frontend/tests/utils/`.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Nos testes, use uma sessão vazia, crie o usuário com `createUser`, crie o curso com `createCourse` e entre com `logInUser`, como em `course.spec.ts`. O seed permite criar um tutorial `succeeded` com `content` válido ou inválido para testar a tela real.

## Critérios de aceite

- [ ] Um tutorial válido mostra o resumo, cada seção com título e texto, e "Para levar" com os itens, na ordem.
- [ ] O texto das seções mostra listas, tabelas, blocos de código e código no meio do texto.
- [ ] Uma tag HTML no Markdown não vira elemento na página.
- [ ] Um `content` fora do formato mostra o aviso, sem erro no console.
- [ ] `course.spec.ts` confirma que o resumo do tutorial publicado aparece na rota direta e continua visível após uma falha de geração.
- [ ] Nenhum componente tem valor hexadecimal.
- [ ] Os testes Playwright que já existem passam.
- [ ] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/tutorial-reader.spec.ts`, abra um curso com um só tutorial direto em `/courses/{id}`, salvo no cenário com a grade.

1. Um tutorial com resumo, 2 seções e 2 itens "Para levar": a tela mostra o resumo, os `h3` das duas seções e "Para levar", nessa ordem, e uma lista com os 2 itens.
2. Uma seção com uma lista com marcadores, uma tabela de 2 colunas, um bloco de código e `` `comando` `` no meio do texto: a tela mostra a lista, uma `table` com o texto das células, um `pre` com o código e um `code` com "comando" fora do `pre`.
3. Uma seção com `# Título interno` no texto: a tela mostra "Título interno" como `h4`, não como `h1`.
4. Uma seção com HTML cru, como `<b>negrito</b>`. O leitor exibe o texto sem criar o elemento `b`.
5. Um tutorial com `content: {"summary": "Resumo"}`. A tela mostra só o aviso no lugar do leitor, sem emitir erro no console.
6. Em um curso com tutorial e quiz, clique no link "Abrir" do tutorial pelo nome acessível que inclui o título. A tela de conteúdo mostra o resumo.
