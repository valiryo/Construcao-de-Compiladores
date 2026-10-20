# Compilador COBOL — Entrega 1: Analisador léxico

Primeira etapa do trabalho de Construção de Compiladores. Implementa o **lexer** para o subconjunto COBOL em **formato fixo** definido na seção 2 da [especificação do professor](docs/EspecificacaoCOBOL.pdf), com extensões para os programas de [ebasso/cobol-exemplos](examples/ebasso/README.md).

## Relatório da entrega

O **relatório da Entrega 1** está na pasta `docs/`: **[abrir o relatório completo](docs/relatorio-lexer.md)**.

O documento apresenta a introdução ao COBOL, a implementação e o uso de IA, os fluxos de tokens dos programas de teste e os resultados dos exemplos com erros léxicos.

## Requisitos

- Python **3.11+** (sem bibliotecas externas).
- Arquivos-fonte usando o **COBOL Fixed Format**, não o formato livre.

## Executar

Na raiz deste repositório, usando Terminal, PowerShell ou CMD:

```bash
python -m cobol_lexer examples/hello.cob
python -m cobol_lexer examples/hello.cob --json
python -m cobol_lexer examples/hello.cob --stream
python -m cobol_lexer examples/hello.cob --debug-lines
python -m cobol_lexer examples/ebasso/prog003_calculadora.cob --json
python -m cobol_lexer examples/erros/prog004_folha_pgto_erros.cob --stream
```

O programa lista os tokens, com linha e coluna (contadas desde 1), e os diagnósticos. Em caso de erro léxico, o processo termina com código 1; erro de leitura resulta no código 2; sucesso, 0. Com `--json`, a saída é adequada para integração futura com o parser. Com `--stream`, os tokens são agrupados por linha física no formato `<TIPO, lexema>`, com os erros intercalados na linha em que ocorrem; é o formato usado no [relatório](docs/relatorio-lexer.md).

## Executar testes

```bash
python -m unittest discover -s tests -v
```

No Windows, `py -3 -m cobol_lexer examples/hello.cob` também funciona caso `python` não esteja no PATH.

## Escopo implementado

> **Compatibilidade com os exemplos fornecidos pelo professor:** foi necessário
> aceitar underscore (`_`) no interior de identificadores, como `PROG007_LOJA`,
> para analisar os programas do repositório ebasso sem modificar seus fontes.
> Essa é uma extensão deliberada à seção 2.2 da especificação, que lista apenas
> letras, dígitos e hífen. O limite de 30 caracteres e a proibição de underscore
> no início ou no fim do identificador continuam válidos.

- **Colunas 1-6:** ignoradas; **7:** indicador; **8-11:** área A; **12-72:** área B; **73 em diante:** ignoradas.
- Comentários em linhas com `*` ou `/` na coluna 7; continuação de strings, palavras, números e máscaras `PIC` com `-` na coluna 7.
- Linha `D` de debugging: ignorada normalmente; opcionalmente analisada com `--debug-lines`.
- As **14 palavras reservadas** da seção 2.2 e palavras adicionais usadas nos exemplos, como `PROGRAM-ID`, `PIC`, `VALUE`, `COMPUTE`, `INSPECT`, `READ` e `END-IF`, sem diferenciar maiúsculas de minúsculas. A lista implementada está em `RESERVED_WORDS`, no módulo `scanner.py`.
- Números inteiros, decimais com ponto, sinais `+` e `-`.
- Strings entre aspas simples ou duplas; aspas duplicadas dentro do texto. Em continuação, aceitamos repetir a aspa de abertura no início da próxima linha.
- Identificadores com letras ASCII A-Z, números, hífen e underscore internos (até 30 caracteres).
- Pontuação: `.`, `,`, `;`, `(` e `)`.
- Operadores aritméticos `+`, `-`, `*`, `/`, `**` e relacionais `=`, `<`, `>`, `<=`, `>=`, `<>`, com preferência pelo operador mais longo.
- Máscaras após `PIC` ou `PICTURE`, com `IS` opcional, reconhecidas como um único token `PICTURE`: por exemplo, `X(10)`, `S9(05)V99` e `-ZZZZZZZZZ9.99`. O ponto final da declaração permanece um token `PERIOD` separado; da mesma forma, uma vírgula ou um ponto-e-vírgula logo após a máscara é emitido como separador.
- Diagnósticos com linha e coluna físicas; recuperação parcial após erro.

Linhas com até seis caracteres ocupam apenas a área de sequência e são
ignoradas, preservando a numeração física das linhas seguintes. Isso inclui
`000100` e também `MOVE` sem indentação: comandos precisam começar na área de
código do formato fixo.

Comentários identificados por `*` ou `/` na coluna 7 são descartados antes da
validação de TAB. Linhas `D` recebem o mesmo tratamento quando o debugging está
desabilitado; com `--debug-lines`, seu conteúdo é validado como código. TAB em
linhas analisadas continua gerando erro. Linhas ignoradas não interrompem
continuações de tokens.

Tipos (`kind`) de token: `KEYWORD`, `IDENTIFIER`, `NUMBER`, `STRING`, `PICTURE`, `PERIOD`, `COMMA`, `SEMICOLON`, `LPAREN`, `RPAREN`, `PLUS`, `MINUS`, `MULTIPLY`, `DIVIDE`, `POWER`, `EQUAL`, `LESS_THAN`, `GREATER_THAN`, `LESS_EQUAL`, `GREATER_EQUAL` e `NOT_EQUAL`.

Cada token inclui `kind`, `lexeme`, `value`, `line`, `column`, `area`, `end_line` e `end_column`. Os `value` de palavras-chave, identificadores e máscaras são normalizados para maiúsculas; os valores dos números são mantidos como strings para evitar perda de precisão. O `lexeme` de tokens continuados é reconstruído sem indicadores nem quebras de linha, mas as posições de início e fim referenciam o arquivo físico original.

Os sete programas importados e o exemplo inicial passam sem diagnósticos. A suíte inclui testes de integração que executam a CLI com `--json` em cada programa importado e verificações da reconstrução de identificadores divididos entre linhas.

Em `examples/erros/` há cópias dos sete programas com 15 erros léxicos inseridos, que cobrem os nove códigos de diagnóstico. Um teste de regressão confere código, linha e coluna de cada um. A descrição de cada erro e a recuperação correspondente estão na seção 4 do [relatório](docs/relatorio-lexer.md).

## Decisões a validar com o professor / testes oficiais

A especificação não detalha todos os seguintes aspectos. Por isso adotamos **decisões de implementação**, sem alegar que constam no documento:

1. **Case-insensitive** para palavras reservadas e identificadores (comportamento habitual do COBOL).
2. **Linhas de debugging `D`:** ignoradas por padrão e analisadas quando explicitamente habilitadas.
3. **Continuação:** o indicador `-` une o conteúdo à linha de código anterior, descartando espaços finais e a indentação da continuação. Em strings abertas, aceita a aspa de abertura repetida. Comentários e linhas de debugging desabilitadas podem aparecer entre as partes. Uma continuação sem linha de código anterior gera `UNEXPECTED_CONTINUATION`.
4. **Aspas duplicadas** geram uma aspa no valor da string.
5. **Vocabulário ampliado:** palavras como `PROGRAM-ID`, `PIC`, `VALUE` e `COPY` agora são emitidas como `KEYWORD`. Essa extensão e os novos tipos de token atendem aos exemplos importados e vão além da lista explícita da seção 2.2.
6. **Área A/B:** a posição é registrada como metadado. O parser futuro validará se uma declaração pode aparecer em cada área; o lexer não impõe regras sintáticas sobre divisão/seção/parágrafo.
7. A palavra com letras/dígitos/hífen/underscore é reconhecida como unidade, inclusive após unir continuações. Identificadores inválidos ou longos geram erro, em vez de fragmentação silenciosa. `PROG007_LOJA` é um identificador único; `_NAME` e `NAME_` geram `INVALID_IDENTIFIER`.
8. Não implementamos `COPY`/copybooks: a seção 6 os menciona, mas o pré-processamento não faz parte do escopo léxico mínimo definido na seção 2.
9. **Sinais e operadores:** sinais adjacentes a dígitos, no início do código ou após espaço, parêntese de abertura, vírgula ou operador, pertencem ao literal numérico (`-123.45`, `+8`). Em `COUNT+1`, o `+` é um operador. Hífens internos permanecem parte do identificador; escreva `COUNT - 1` para expressar subtração. Um hífen colado ao início de um nome (`-COUNT`) gera `INVALID_IDENTIFIER`, e a palavra inteira é descartada. Para o menos unário antes de um nome, use `- COUNT`; parênteses também podem delimitar o operador, como em `-(COUNT)` ou `(- COUNT)`.
10. **Máscaras `PIC`:** os símbolos e as repetições entre parênteses são verificados lexicalmente; repetições devem ser positivas, aceitando zeros à esquerda. Máscaras malformadas geram `INVALID_PICTURE`. A validade semântica da combinação dos símbolos ficará a cargo das etapas seguintes.

As extensões de continuação e máscaras usam como referência o [guia do GnuCOBOL](https://gnucobol.sourceforge.io/HTML/gnucobpg.html), nas seções de formato fixo e `PICTURE`. O projeto continua sendo um subconjunto, sem compatibilidade completa com esse compilador.

## Estrutura

```text
cobol_lexer/
  __init__.py       API para programas Python
  __main__.py       interface em linha de comando
  model.py          Token, Diagnostic e LexerResult
  fixed_format.py   leitor de colunas, indicadores e continuações com mapa de posições
  scanner.py        reconhecimento de lexemas
docs/EspecificacaoCOBOL.pdf especificação do professor
docs/relatorio-lexer.md relatório da entrega e resultados de validação
examples/hello.cob  exemplo em formato fixo
examples/ebasso/    sete programas importados, licença e resultados de validação
examples/erros/     cópias dos programas com erros léxicos inseridos
tests/test_lexer.py suíte de testes sem dependências
tests/test_extended_lexer.py testes das extensões e integração pela CLI
```

## Limites da entrega

**Não há parser nem análise semântica.** Um conjunto de tokens bem formado não garante que seja um programa COBOL sintaticamente válido. O lexer aceita o subconjunto da seção 2 com as extensões documentadas para os exemplos importados. Outros recursos, como formato livre, comentários inline, diretivas de compilação e expansão de `COPY`, ainda não são implementados.
