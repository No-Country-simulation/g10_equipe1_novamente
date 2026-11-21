---
id: T09
title: Mostre os flashcards publicados, um cartão por vez, com frente, verso e dica
blocked_by: [T18]
touches:
  - frontend/src/components/Course/readers/FlashcardsReader.tsx
  - frontend/tests/flashcards-reader.spec.ts
  - frontend/tests/course.spec.ts
executor: agente
size: 2
---

# T09 - Mostre os flashcards publicados, um cartão por vez, com frente, verso e dica

## Contexto

T18 entregou a tela de um conteúdo e o ponto de encaixe dos leitores. Hoje `FlashcardsReader` mostra só "O leitor deste formato ainda não está disponível." `docs/product-specs/conteudos-e-formatos.md` define os flashcards: um título, uma introdução curta e de 8 a 12 cartões, cada um com frente, verso e uma dica opcional. `docs/product-specs/telas.md` diz que a tela mostra um cartão por vez.

Este ticket troca o conteúdo de `FlashcardsReader.tsx`. A moldura, os metadados e o aviso de estado são de T18 e não mudam.

O layout vem da captura [`tela-f1-flashcards.png`](../../design/telas-finais/tela-f1-flashcards.png): o cartão branco à direita, com o contador, a barra, o cartão azul e os botões "Anterior" e "Próximo".

Leia antes: `docs/product-specs/conteudos-e-formatos.md`, seção "Flashcards", `docs/tickets/completed/T18-tela-curso.md`, seção "Contrato", e `backend/app/services/content_schemas.py`, classe `FlashcardsContent`.

## Escopo

- O leitor dos flashcards: introdução, contador, barra de posição, cartão que vira e navegação.
- A dica, quando o cartão tem uma.
- O aviso para um conteúdo guardado fora do formato dos flashcards.

## Fora do escopo

- A moldura da tela, os metadados e os avisos de estado (T18, pronto).
- A coluna de cartões à esquerda da captura. Veja "Onde o design e a especificação divergem".
- Guardar quais cartões a pessoa já viu. O esquema não guarda progresso.
- Fidelidade, clareza e trechos citados (T38).

## Contrato

### Módulos que este ticket usa

Do `master`. Não edite esses arquivos.

```ts
// frontend/src/components/Course/readers/types.ts (T18)
export interface ReaderProps {
  content: { [key: string]: unknown }
}
```

A forma dos flashcards vem de `FlashcardsContent`, em `backend/app/services/content_schemas.py`:

```python
class Flashcard(StrictModel):
    front: Text  # 1 caractere ou mais
    back: Text
    hint: Text | None = None


class FlashcardsContent(StrictModel):
    introduction: Text
    cards: list[Flashcard]  # de 8 a 12
```

### O que este ticket muda

`frontend/src/components/Course/readers/FlashcardsReader.tsx` continua a exportar `FlashcardsReader(props: ReaderProps)`. Não mude o nome, a assinatura nem o caminho.

## Comportamento esperado

### Conteúdo no formato dos flashcards

Use `zod` para validar os campos que o leitor usa em `FlashcardsContent`. Exija os tipos indicados, textos com ao menos um caractere após `trim()` e de 8 a 12 cartões. Aceite `hint` ausente ou nulo. Ignore campos extras no leitor.

Com `content` válido, o leitor mostra, de cima para baixo:

1. A introdução, alinhada com o cartão abaixo. Use 16 px, altura de linha 1,5, `text-muted-foreground` e 24 px abaixo.
2. Um `Card` centralizado, com borda de 1 px, raio de 12 px, fundo `bg-card` e largura máxima de 900 px:
    - Na parte de cima, com padding de 24 px:
        - o rótulo "CARTÃO N DE T", em que N é a posição atual, a partir de 1, e T é o total. Use a regra dos rótulos em caixa alta de T18: 12 px, peso 600, espaçamento de 0,08 em, `text-foreground-tertiary`;
        - uma barra de posição de 4 px de altura, com fundo `bg-muted` e a parte cheia `bg-foreground`, na largura N/T. Use `role="progressbar"`, `aria-valuemin=1`, `aria-valuemax=T`, `aria-valuenow=N`, `aria-valuetext="Cartão N de T"` e o nome acessível "Posição no conjunto";
        - o cartão.
    - Na parte de baixo, uma faixa com padding de 24 px, linha superior de 1 px e fundo `bg-muted/50`, com "Anterior" à esquerda e "Próximo" à direita. Os dois são `Button` com `variant="outline"`, altura mínima de 48 px e peso 600.

### O cartão

O cartão é um `Button` que ocupa a largura, com altura mínima de 280 px, borda de 2 px `border-info`, raio de 12 px, fundo `bg-card` e padding de 32 px. O texto fica alinhado à esquerda e quebra linha.

| Lado | O que mostra |
| --- | --- |
| Frente, ao abrir o cartão | Um `Badge` "PERGUNTA" (`bg-info/10 text-info`, 12 px, peso 600). A `front`, em Space Grotesk (`font-heading`), 26 px, peso 700. No pé, o ícone `RefreshCw` de 18 px e o texto "Clique no cartão para ver a resposta", 15 px, peso 600, `text-info`. |
| Verso, depois do clique | Um `Badge` "RESPOSTA", no mesmo estilo. O `back`, 18 px, altura de linha 1,5, `text-foreground`. No pé, o ícone `RefreshCw` e o texto "Clique no cartão para ver a pergunta". |

- O clique no cartão, ou Enter e Espaço com o foco nele, troca o lado.
- O botão tem o nome acessível fixo "Virar cartão" e `aria-pressed="true"` quando mostra o verso.
- Use uma região `aria-live="polite"` que já está montada para anunciar o lado novo.

### A dica

Quando a frente do cartão tem `hint`, mostre abaixo um `Button` com `variant="ghost"`, o ícone `Lightbulb` e o texto "Mostrar dica". Ao acionar o botão, mostre a dica no lugar dele, com o prefixo "Dica: ", fonte de 15 px e `text-muted-foreground`. Leve o foco ao texto da dica. Ao virar ou trocar o cartão, esconda a dica.

### Navegação

- "Anterior" fica desabilitado no primeiro cartão. "Próximo" fica desabilitado no último.
- Trocar de cartão mostra a frente do cartão novo, sem a dica.
- A posição fica no componente. Recarregar a página ou receber outro conjunto de cartões abre a frente do primeiro cartão, com a dica fechada. Uma atualização automática com o mesmo conteúdo preserva a posição e o lado.

### Conteúdo fora do formato

Quando `content` não passa no schema, por exemplo `{}`, o leitor mostra um `Alert` com o texto "Não foi possível mostrar este conteúdo, porque ele não está no formato esperado." e nada mais. A frase é a mesma de T08 e T10. Cada leitor tem a sua cópia, para os três tickets rodarem ao mesmo tempo sem conflito.

## Onde o design e a especificação divergem

| Elemento | Telas finais | Este ticket | Motivo |
| --- | --- | --- | --- |
| Coluna à esquerda com o nome de cada cartão e marcas de visto | Tela F1 | Sai | O formato não tem um nome curto por cartão: a frente é uma pergunta inteira. As marcas de visto são progresso, que o esquema não guarda. O contador e a barra já mostram a posição. |
| Selo "Flashcards" no cabeçalho com o ícone `Copy` | Tela F1 | Selo de T18, com o ícone `Layers` | T18 já decidiu os ícones. |
| Dica | Não aparece | Botão "Mostrar dica" abaixo do cartão. Proposta. | `conteudos-e-formatos.md` e `telas.md` pedem a dica. |
| Verso do cartão | Não aparece | Selo "RESPOSTA" e o texto do verso. Proposta. | A captura mostra só a frente. |
| Aviso de conteúdo fora do formato | Não aparece | `Alert` com a frase acima. Proposta. | `telas.md`: uma mensagem de erro diz o que aconteceu. |

## Testes que mudam

Em `frontend/tests/course.spec.ts`, no teste "mantém o conteúdo publicado legível durante falha ou geração", preencha o `content` dos flashcards `running` com um conjunto válido. Depois do aviso "Gerando. A tela se atualiza sozinha.", troque `readerPlaceholder` pelo texto da frente do primeiro cartão.

T08 atualiza os casos de tutorial. Depois do `rebase`, o último dos dois tickets apaga `readerPlaceholder` se a constante ficar sem uso.

## Detalhes técnicos

- Use o `zod` 4 já instalado (`4.6.5` no `bun.lock`). Defina o schema dentro de `FlashcardsReader.tsx`.
- Use componentes shadcn onde houver: `Card`, `Badge`, `Button` e `Alert` já existem em `frontend/src/components/ui/`. Este ticket não acrescenta dependência: `frontend/package.json` e `bun.lock` não mudam.
- Use só as variáveis de cor de `frontend/src/index.css`. Não escreva valor hexadecimal.
- Não edite `ContentReader.tsx`, `ContentView.tsx`, `readers/types.ts`, os outros leitores nem `frontend/tests/utils/`.
- Este ticket não cria rota. `frontend/src/routeTree.gen.ts` não pode aparecer no diff.
- Nos testes, use uma sessão vazia, crie o usuário com `createUser`, crie o curso com `createCourse` e entre com `logInUser`, como em `course.spec.ts`. O seed permite criar flashcards `succeeded` com `content` válido ou inválido para testar a tela real.

## Critérios de aceite

- [x] Um conjunto válido mostra a introdução e um cartão por vez, com "CARTÃO N DE T" e a barra de posição.
- [x] O clique no cartão, ou Enter e Espaço, mostra o verso, e um novo clique volta à frente.
- [x] A dica aparece só no cartão que tem dica, depois do clique em "Mostrar dica".
- [x] "Anterior" e "Próximo" ficam desabilitados nas pontas, e trocar de cartão mostra a frente.
- [x] Um `content` fora do formato mostra o aviso, sem erro no console.
- [x] `course.spec.ts` confirma que os flashcards publicados continuam legíveis durante nova geração.
- [x] Nenhum componente tem valor hexadecimal.
- [x] Os testes Playwright que já existem passam.
- [x] `bun run lint` e `bun run build` passam.

## Cenários de teste

Em `frontend/tests/flashcards-reader.spec.ts`, com um usuário novo por teste e um curso com um só conteúdo de flashcards, que abre direto em `/courses/{id}`. O conjunto tem 8 cartões. Só o primeiro tem `hint`.

1. A tela mostra a introdução, "CARTÃO 1 DE 8", a frente do primeiro cartão, "PERGUNTA" e "Clique no cartão para ver a resposta". O verso não aparece. "Anterior" está desabilitado.
2. O clique no cartão mostra "RESPOSTA" e o verso, e o cartão fica com `aria-pressed="true"`. Um novo clique volta à frente.
3. Com o foco no cartão, Espaço mostra o verso e Enter volta à frente.
4. No primeiro cartão, o clique em "Mostrar dica" mostra "Dica: " e o texto da dica. Virar o cartão esconde a dica.
5. "Próximo" leva a "CARTÃO 2 DE 8" e mostra a frente do segundo cartão. O segundo cartão não tem o botão "Mostrar dica". A barra tem `aria-valuenow="2"`.
6. Depois de virar o cartão 2, "Próximo" e depois "Anterior" mostram a frente do cartão 2, não o verso.
7. No cartão 8, "Próximo" está desabilitado.
8. Um conteúdo com 3 cartões. A tela mostra só o aviso no lugar do leitor, sem emitir erro no console.
9. Com o cartão 12 aberto em um conteúdo `running`, intercepte uma consulta automática do curso e devolva um conjunto válido com 8 cartões. O leitor abre na frente do primeiro cartão novo.

## Verificação do aceite

- PR revisado: [#35](https://github.com/No-Country-simulation/g10_equipe1_novamente/pull/35), integrado no commit `62b69f3`.
- CI do PR: todos os checks obrigatórios passaram, com escopo dentro de `touches`.
- Revisão automática: um achado, nenhum teste usava `hint: null`, o formato publicado de um cartão sem dica. O commit `7dd6080` corrigiu.
- Depois do rebase sobre T08, a constante `readerPlaceholder` ficou sem uso e saiu de `course.spec.ts`.
- Testes: 83 testes Playwright passaram no Chromium. `bun run lint`, `bun run build` e os hooks passaram.
