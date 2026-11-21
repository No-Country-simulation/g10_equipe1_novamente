# NovaMente — T12: consolidação e auditoria

**Data dos registros:** 16/11/2026 (UTC)  
**Origem:** `t12_resultados.zip`, fornecido pelo usuário.  
**Escopo:** somente leitura do ZIP; nenhum acesso à API Gemini e nenhuma alteração no repositório.

## Resumo

| Indicador | Total |
|---|---:|
| CSVs de origem | 6 |
| Execuções com registro CSV | 12 |
| Execuções `ok` | 7 |
| Execuções `erro` | 5 |
| Erros HTTP 503 | 5 |
| Arquivos TXT encontrados | 8 |
| Arquivos TXT com registro correspondente | 7 |
| Arquivos TXT sem registro correspondente | 1 |
| JSONs estruturados aprovados na validação local | 7 |
| Tokens de entrada registrados | 2.416 |
| Tokens de saída registrados | 2.949 |
| Tokens totais registrados | 5.365 |

## Resultado por modelo

| Modelo | OK | Erro | Cenários aprovados |
|---|---:|---:|---|
| gemini-3.5-flash-lite | 7 | 1 | simples, tutorial, flashcards e quiz |
| gemini-3.8-flash | 0 | 4 | nenhum no material examinado |

Todos os erros registrados são `ServerError`, HTTP 503, segundo os CSVs.
Esse diagnóstico não determina a causa do 503.

## Conteúdos encontrados

- **Tutorial:** 4 arquivos estruturados, todos com 3 seções e válidos pelo modelo Pydantic equivalente ao script.
- **Flashcards:** 2 arquivos, ambos com 8 cartões e válidos.
- **Quiz:** 1 arquivo, com 5 questões, cada uma com 4 alternativas distintas e índices corretos de 0 a 3.
- **Simples:** 1 arquivo de texto não estruturado.

O texto gerado está coerente, em revisão inicial, com o documento HTTP de exemplo que acompanhou os scripts originais.
O ZIP enviado não contém a fonte original, de modo que a fidelidade exata depende de ela não ter sido alterada localmente.

## Consumo de tokens — registros com métricas

| Cenário | Execuções com métrica | Tokens totais | Média por execução |
|---|---:|---:|---:|
| simples | 1 | 519 | 519 |
| tutorial | 4 | 3.068 | 767 |
| flashcards | 1 | 776 | 776 |
| quiz | 1 | 1.002 | 1.002 |
| **Total** | **7** | **5.365** | **766,4** |

Tokens não informados pelos registros de erro **não são considerados zero**: simplesmente não há medição disponível.

## Anomalias e tratamento

1. **Cinco valores de duração suspeitos:** os arquivos de origem registram `3141`, `28531`, `2405`, `2114` e `1993` onde provavelmente deveriam estar `3.141`, `28.531`, `2.405`, `2.114` e `1.993` segundos. Os três primeiros são conferíveis pelas capturas enviadas na conversa; os dois últimos foram **inferidos** pelo padrão. Valores brutos, fontes e método de ajuste estão em `auditoria_origens.csv` e na guia `Auditoria` do XLSX.
2. **Um TXT órfão:** `20261116T201118148258Z_gemini-3.5-flash-lite_flashcards.txt` contém um JSON válido, mas não há registro correspondente de execução nos CSVs. O arquivo foi preservado, sem criar medição fictícia.
3. **Sem duplicações nas medições:** os 12 valores de `data_utc` são distintos; nenhum registro foi excluído.
4. **Paths antigos:** referências absolutas e relativas de diferentes pastas foram normalizadas no CSV consolidado para `t12_resultados/<nome-do-arquivo>`.
5. **Cuidado com Excel em pt-BR:** a abertura e gravação automática de CSV pode interpretar pontos decimais como separadores de milhar. Para visualização e edição humana, use o XLSX; mantenha o CSV em UTF-8, com vírgula como separador de campos e **ponto** como separador decimal para o script.

## Arquivos

- `t12_resultados/medicoes.csv`: histórico consolidado com **as mesmas 15 colunas do script Python**; pronto para inclusão de novas linhas quando a pasta for colocada ao lado do script.
- `t12_resultados/auditoria_origens.csv`: trilha de proveniência dos 12 registros e valores de duração originais.
- `t12_resultados/inventario_respostas.csv`: inventário dos 8 arquivos TXT, validação local e identificação do arquivo sem registro.
- `t12_resultados/modelos.json`: resultado de descoberta original.
- `t12_resultados/*.txt`: os oito conteúdos de saída, preservados byte a byte.
- `T12_Gemini_consolidado.xlsx`: planilha para leitura com as guias Resumo, Medições, Respostas, Auditoria e Notas.

## Uso

1. **Faça backup** da pasta local `t12_resultados`, especialmente de `medicoes.csv`, antes de substituir qualquer arquivo.
2. Extraia o ZIP na pasta dos scripts, de modo que fique `./t12_resultados/medicoes.csv`.
3. Se novos resultados forem coletados, não substitua o CSV pela versão deste pacote sem reconciliar os registros posteriores.

## Limitações

A amostra é pequena, usa um texto-fonte curto e não permite inferir confiabilidade estatística, capacidade real de 12 chamadas por curso ou qualidade para documentos longos. O Gemini 3.8 Flash não possui resposta bem-sucedida neste conjunto. Quotas de RPM, RPD e TPM foram discutidas na conversa, mas não são derivadas destes CSVs.
