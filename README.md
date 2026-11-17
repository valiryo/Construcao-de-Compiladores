# Compilador COBOL — Pré-processador, parser e AST

Trabalho de Construção de Compiladores em Python 3.11+. Implementa o **front-end** para
COBOL em **formato fixo** definido na seção 2 da [especificação do professor](docs/EspecificacaoCOBOL.md),
com extensões para os corpora [ebasso](examples/ebasso/README.md) e
[COBOL Dicas](examples/README.md): COPY → lexer → parser → AST. As próximas fases
serão análise semântica → C → GCC → executável nativo.

## Etapa 2: sintaxe e AST

Os sete oficiais produzem ASTs completas, com expansão dos copybooks necessários,
consumo integral dos tokens e verificação independente da representação de cada
comando. Dos 77 arquivos anteriormente aceitos pelo lexer, **72 programas e dois
copybooks passam**. Um fonte vazio e os exemplos SQL/CICS são diagnosticados
separadamente. A suíte completa passou com **149 testes**, incluindo os 80 anteriores.

```bash
python -m cobol_compiler examples/oficiais/CALCMD01.cbl --check-syntax
python -m cobol_compiler examples/oficiais/CAD0002A.cbl -I examples/dependencias --dump-ast
python -m tools.auditar_parser --write
```

- [Interface, arquitetura e testes](docs/frontend.md).
- [Auditoria sintática por arquivo](docs/auditoria-parser.md) e [dados JSON](docs/auditoria-parser.json).
- [Gramática implementada em EBNF](docs/gramatica-cobol.ebnf).

A AST usa nós tipados com origem física e pilha de inclusão. Não há comandos
armazenados como texto bruto nem aceitação genérica de tokens desconhecidos.
Os originais do corpus permanecem intactos; não há execução nativa nesta etapa.

## Consolidação léxica da Etapa 1

- [Auditoria léxica e resultados](docs/auditoria-lexer.md): **58 testes antes,
  80 depois**, com os sete programas oficiais sem erros léxicos indevidos.
- [Corpus e proveniência](examples/README.md): sete originais, dependências,
  CAD0005A corrigido e todos os 75 fontes complementares do commit fixado.
- [Inventário reproduzível](docs/inventario-corpus.md): tokens, máscaras,
  construções e dependências; nove arquivos externos ficam como casos negativos.
- [Plano técnico atualizado](docs/plano-implementacao-final.md): distingue o
  front-end concluído das etapas futuras de semântica, runtime e geração C.

Para os testes positivos, use `examples/corrigidos/CAD0005A.cbl`.
`examples/oficiais/CAD0005A.cbl` preserva o conflito upstream como teste negativo.

## Relatório da entrega

O **relatório da Entrega 1** está na pasta `docs/`: **[abrir o relatório completo](docs/relatorio-lexer.md)**.

O documento apresenta a introdução ao COBOL, a implementação e o uso de IA, os fluxos de tokens dos programas de teste e os resultados dos exemplos com erros léxicos.

## Requisitos

- Python **3.11+** (sem bibliotecas externas).
- Arquivos-fonte usando o **COBOL Fixed Format**, não o formato livre.

## Executar o lexer isoladamente

Na raiz deste repositório, usando Terminal, PowerShell ou CMD:

```bash
python -m cobol_lexer examples/hello.cob
python -m cobol_lexer examples/hello.cob --json
python -m cobol_lexer examples/hello.cob --stream
python -m cobol_lexer examples/hello.cob --debug-lines
python -m cobol_lexer examples/ebasso/prog003_calculadora.cob --json
python -m cobol_lexer examples/erros/prog004_folha_pgto_erros.cob --stream
python -m cobol_lexer examples/oficiais/CALCMD01.cbl --json
python -m cobol_lexer examples/corrigidos/CAD0005A.cbl --json
```

O programa lista os tokens, com linha e coluna (contadas desde 1), e os diagnósticos. Em caso de erro léxico, o processo termina com código 1; erro de leitura resulta no código 2; sucesso, 0. Com `--json`, a saída é adequada para integração futura com o parser. Com `--stream`, os tokens são agrupados por linha física no formato `<TIPO, lexema>`, com os erros intercalados na linha em que ocorrem; é o formato usado no [relatório](docs/relatorio-lexer.md).

## Executar testes

```bash
python -m unittest discover -s tests -v
python -m tools.auditar_corpus
python -m tools.auditar_parser --write
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
- Comentários em linhas com `*` ou `/` na coluna 7 e inline `*>` fora de strings; continuação de strings, palavras, números e máscaras `PIC` com `-` na coluna 7.
- Linha `D` de debugging: ignorada normalmente; opcionalmente analisada com `--debug-lines`.
- As **14 palavras reservadas** da seção 2.2 e palavras adicionais usadas nos exemplos, como `PROGRAM-ID`, `PIC`, `VALUE`, `COMPUTE`, `INSPECT`, `READ` e `END-IF`, sem diferenciar maiúsculas de minúsculas. A lista implementada está em `RESERVED_WORDS`, no módulo `scanner.py`.
- Números inteiros, decimais com ponto, sinais `+` e `-`; após `DECIMAL-POINT IS COMMA`, vírgula decimal, preservando o lexema e normalizando `value` para ponto.
- Strings entre aspas simples ou duplas; aspas duplicadas dentro do texto. Em continuação, aceitamos repetir a aspa de abertura no início da próxima linha.
- Identificadores com letras ASCII A-Z, números, hífen e underscore internos (até 30 caracteres).
- Pontuação: `.`, `,`, `;`, `(`, `)` e `:` (`COLON`, em referências modificadas).
- Operadores aritméticos `+`, `-`, `*`, `/`, `**` e relacionais `=`, `<`, `>`, `<=`, `>=`, `<>`, com preferência pelo operador mais longo.
- Máscaras após `PIC` ou `PICTURE`, com `IS` opcional, reconhecidas como um único token `PICTURE`: por exemplo, `X(10)`, `S9(05)V99` e `-ZZZZZZZZZ9.99`. O ponto final da declaração permanece um token `PERIOD` separado; da mesma forma, uma vírgula ou um ponto-e-vírgula logo após a máscara é emitido como separador.
- Diagnósticos com linha e coluna físicas; recuperação parcial após erro.
- Diagnóstico `MERGE_CONFLICT` para marcadores Git no código, inclusive antes do descarte da área de sequência.

Linhas com até seis caracteres ocupam apenas a área de sequência e são
ignoradas, preservando a numeração física das linhas seguintes. Isso inclui
`000100` e também `MOVE` sem indentação: comandos precisam começar na área de
código do formato fixo.

Comentários identificados por `*` ou `/` na coluna 7 são descartados antes da
validação de TAB. Linhas `D` recebem o mesmo tratamento quando o debugging está
desabilitado; com `--debug-lines`, seu conteúdo é validado como código. TAB em
linhas analisadas continua gerando erro. Linhas ignoradas não interrompem
continuações de tokens.

Tipos (`kind`) de token: `KEYWORD`, `IDENTIFIER`, `NUMBER`, `STRING`, `PICTURE`, `PERIOD`, `COMMA`, `SEMICOLON`, `LPAREN`, `RPAREN`, `COLON`, `PLUS`, `MINUS`, `MULTIPLY`, `DIVIDE`, `POWER`, `EQUAL`, `LESS_THAN`, `GREATER_THAN`, `LESS_EQUAL`, `GREATER_EQUAL` e `NOT_EQUAL`.

Cada token inclui `kind`, `lexeme`, `value`, `line`, `column`, `area`, `end_line` e `end_column`. Os `value` de palavras-chave, identificadores e máscaras são normalizados para maiúsculas; os valores dos números são mantidos como strings para evitar perda de precisão. O `lexeme` de tokens continuados é reconstruído sem indicadores nem quebras de linha, mas as posições de início e fim referenciam o arquivo físico original.

Os sete programas ebasso, o exemplo inicial e os sete oficiais COBOL Dicas (com
CAD0005A corrigido) passam sem diagnósticos. A suíte executa a CLI com `--json`
para ambos os conjuntos, verifica posições e identificadores continuados e analisa
todos os fontes complementares. O inventário atual abrange 86 arquivos COBOL Dicas:
77 sem erros léxicos e nove negativos documentados. Zero erros léxicos não garante
validade sintática, semântica ou disponibilidade de dependências externas.

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
8. O lexer isolado reconhece `COPY`, sem expandi-lo. A Etapa 2 implementa a expansão no pré-processador de `cobol_compiler`, preservando a API léxica. COPY REPLACING não ocorre no corpus e recebe diagnóstico explícito de recurso não implementado.
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
cobol_compiler/
  source.py         origem física e tokens localizados
  preprocessor.py   COPY, busca local/-I, ciclos e pilha de inclusão
  ast.py            nós tipados, visitante e serialização
  parser.py         divisões, declarações e recuperação
  expressions.py    referências, precedência e condições
  statements.py     rotinas específicas de comandos
  validation.py     invariantes e cobertura dos comandos na AST
  frontend.py       parse_file e parse_source
  __main__.py       --check-syntax e --dump-ast
docs/EspecificacaoCOBOL.pdf especificação do professor
docs/relatorio-lexer.md relatório da entrega e resultados de validação
examples/hello.cob  exemplo em formato fixo
examples/ebasso/    sete programas importados, licença e resultados de validação
examples/erros/     cópias dos programas com erros léxicos inseridos
tests/test_lexer.py suíte de testes sem dependências
tests/test_extended_lexer.py testes das extensões e integração pela CLI
tests/test_coboldicas_corpus.py corpus oficial/complementar, hashes e regressões
tests/test_preprocessor.py testes unitários de COPY
tests/test_parser.py gramática, negativos, AST e CLI
tests/test_parser_corpus.py sete oficiais e toda a coorte léxica
tools/auditar_corpus.py inventário offline reproduzível
tools/auditar_parser.py auditoria do front-end completo
examples/oficiais/ sete fontes originais COBOL Dicas
examples/corrigidos/ cópia de CAD0005A usada nos testes positivos
examples/dependencias/ copybooks e PROGDATA
examples/complementares/ demais fontes COBOL Dicas
docs/auditoria-lexer.md consolidação e limitações do corpus real
docs/plano-implementacao-final.md arquitetura das próximas fases
```

## Limites da entrega

**Ainda não há análise semântica completa, gerador C ou invocação do GCC.**
Sintaxe válida não garante tipos, símbolos, layouts ou comportamento corretos.
Formato livre, diretivas gerais, COPY REPLACING, programas aninhados e EXEC SQL/CICS
permanecem fora da gramática atual. CALL para bibliotecas C/ncurses é analisado,
mas sua execução depende de infraestrutura futura. As limitações individuais
estão na [auditoria do parser](docs/auditoria-parser.md).
