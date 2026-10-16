# Compilador COBOL — Entrega 1: Analisador léxico

Primeira etapa do trabalho de Construção de Compiladores. Implementa o **lexer** para o subconjunto COBOL em **formato fixo** definido na seção 2 de `EspecificacaoCOBOL.pdf` (documento do professor).

## Requisitos

- Python **3.11+** (sem bibliotecas externas).
- Arquivos-fonte usando o **COBOL Fixed Format**, não o formato livre.

## Executar

Na raiz deste repositório, usando Terminal, PowerShell ou CMD:

```bash
python -m cobol_lexer examples/hello.cob
python -m cobol_lexer examples/hello.cob --json
python -m cobol_lexer examples/hello.cob --debug-lines
```

O programa lista os tokens, com linha e coluna (contadas desde 1), e os diagnósticos. Em caso de erro léxico, o processo termina com código 1; erro de leitura resulta no código 2; sucesso, 0. Com `--json`, a saída é adequada para integração futura com o parser.

## Executar testes

```bash
python -m unittest discover -s tests -v
```

No Windows, `py -3 -m cobol_lexer examples/hello.cob` também funciona caso `python` não esteja no PATH.

## Escopo implementado

- **Colunas 1-6:** ignoradas; **7:** indicador; **8-11:** área A; **12-72:** área B; **73 em diante:** ignoradas.
- Comentários em linhas com `*` ou `/` na coluna 7; continuação de literal com `-` na coluna 7.
- Linha `D` de debugging: ignorada normalmente; opcionalmente analisada com `--debug-lines`.
- As **14 palavras reservadas** da seção 2.2, sem diferenciar maiúsculas de minúsculas.
- Números inteiros, decimais com ponto, sinais `+` e `-`.
- Strings entre aspas simples ou duplas; aspas duplicadas dentro do texto. Em continuação, aceitamos repetir a aspa de abertura no início da próxima linha.
- Identificadores com letras ASCII A-Z, números e hífen interno (até 30 caracteres).
- Pontuação: `.`, `,`, `;`, `(` e `)`.
- Diagnósticos com linha e coluna físicas; recuperação parcial após erro.

Tipos (`kind`) de token: `KEYWORD`, `IDENTIFIER`, `NUMBER`, `STRING`, `PERIOD`, `COMMA`, `SEMICOLON`, `LPAREN`, `RPAREN`.

Cada token inclui `kind`, `lexeme`, `value`, `line`, `column`, `area`, `end_line` e `end_column`. Os `value` de palavras-chave/identificadores são normalizados para maiúsculas; os valores dos números são mantidos como strings para evitar perda de precisão. `lexeme` de literais continuados é reconstruído, não o trecho físico original incluindo quebras de linha.

## Decisões a validar com o professor / testes oficiais

A especificação não detalha todos os seguintes aspectos. Por isso adotamos **decisões de implementação**, sem alegar que constam no documento:

1. **Case-insensitive** para palavras reservadas e identificadores (comportamento habitual do COBOL).
2. **Linhas de debugging `D`:** ignoradas por padrão e analisadas quando explicitamente habilitadas.
3. **Continuação de literais:** exige literal aberto e `-` na coluna 7; ignora indentação inicial, aceita aspa de abertura repetida e descarta espaços de preenchimento físico no fim da linha.
4. **Aspas duplicadas** geram uma aspa no valor da string.
5. As palavras `PROGRAM-ID`, `PIC`, `VALUE`, `COPY`, etc. não estão na **lista explícita de reservadas da seção 2.2** e são emitidas como `IDENTIFIER` até que haja uma especificação adicional.
6. **Área A/B:** a posição é registrada como metadado. O parser futuro validará se uma declaração pode aparecer em cada área; o lexer não impõe regras sintáticas sobre divisão/seção/parágrafo.
7. A palavra com letras/dígitos/hífen é reconhecida como unidade. Identificadores inválidos ou longos geram erro, em vez de fragmentação silenciosa.
8. Não implementamos `COPY`/copybooks: a seção 6 os menciona, mas o pré-processamento não faz parte do escopo léxico mínimo definido na seção 2.

## Estrutura

```text
cobol_lexer/
  __init__.py       API para programas Python
  __main__.py       interface em linha de comando
  model.py          Token, Diagnostic e LexerResult
  fixed_format.py   leitor de colunas e indicadores
  scanner.py        reconhecimento de lexemas
examples/hello.cob  exemplo em formato fixo
tests/test_lexer.py suíte de testes sem dependências
```

## Limites da entrega

**Não há parser nem análise semântica.** Um conjunto de tokens bem formado não garante que seja um programa COBOL sintaticamente válido. O lexer aceita apenas o subconjunto de tokens da seção 2, e não todos os recursos de COBOL real.
