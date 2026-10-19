# Analisador Léxico para COBOL — Relatório da Entrega 1

**Disciplina:** Construção de Compiladores\
**Integrantes:** Filipe Valeriano Batista de Oliveira - 14570701\
Felipe Teixeira Rodrigues - 13672213\
Pedro Henrique Resnitzky Barbedo - 14657691\
**Repositório (público):** <https://github.com/valiryo/Construcao-de-Compiladores>\
**Data:** outubro de 2026

---

## 1. Introdução

### 1.1 O COBOL

O COBOL (*COmmon Business-Oriented Language*) foi definido em 1959 pelo comitê CODASYL (*Conference on Data Systems Languages*), reunido por iniciativa do Departamento de Defesa dos EUA para criar uma linguagem comum de processamento de dados comerciais. O projeto partiu principalmente da FLOW-MATIC, de Grace Hopper, e da COMTRAN, da IBM, e a primeira especificação foi publicada em 1960 (COBOL-60). A linguagem foi padronizada pela ANSI em 1968, 1974 e 1985 e pela ISO/IEC em 2002 (que introduziu orientação a objetos e o formato livre), 2014 e 2023.

O objetivo era descrever o trabalho típico de um centro de processamento de dados: ler arquivos de registros, fazer cálculos monetários e emitir relatórios, com programas que pudessem ser lidos por quem não era programador. Daí a sintaxe próxima do inglês (`ADD 1 TO WRK-A`, `MOVE WRK-VALOR1 TO WRK-VALOR2`) e a organização do programa em quatro divisões: `IDENTIFICATION`, `ENVIRONMENT`, `DATA` e `PROCEDURE`.

### 1.2 Por que o COBOL ainda é usado

- **Aritmética decimal exata.** Os dados numéricos são declarados com máscaras como `PIC S9(05)V99` (sinal, cinco dígitos inteiros e duas casas decimais) e calculados em decimal de ponto fixo, sem os erros de arredondamento do ponto flutuante binário — requisito central em sistemas financeiros.
- **Processamento de registros e arquivos.** Registros hierárquicos (níveis `01`, `02`, `03`), tabelas com `OCCURS` e arquivos sequenciais e indexados fazem parte da linguagem, como mostram `prog004_folha_pgto.cob`, `prog006_files.cob` e `prog007_loja.cob`.
- **Compatibilidade retroativa.** O padrão evolui de forma conservadora, e programas escritos há décadas continuam compilando. Isso protege o investimento em sistemas que concentram regras de negócio acumuladas por muitos anos.
- **Plataforma consolidada.** Boa parte desse código roda em *mainframes* IBM Z, integrado a monitores de transação (CICS) e bancos de dados (Db2), com alta disponibilidade e grande vazão em processamento em lote.
- **Custo e risco da migração.** Reescrever sistemas grandes, críticos e pouco documentados é caro e arriscado. Estimativas divulgadas pela Reuters em 2017 indicavam cerca de 220 bilhões de linhas de COBOL em uso, presentes em 43% dos sistemas bancários e responsáveis por 95% das operações em caixas eletrônicos nos EUA. Em 2020, durante a pandemia, estados americanos como Nova Jersey pediram publicamente programadores COBOL para manter os sistemas de seguro-desemprego, sobrecarregados.

### 1.3 Dificuldades para a análise léxica

Nas linguagens mais comuns, o lexer pode ignorar espaços e quebras de linha. No COBOL isso não vale, e várias decisões dependem da posição na linha ou do contexto:

1. **Formato fixo orientado a colunas.** Herdado dos cartões perfurados, o formato divide cada linha em áreas:

   | Colunas | Área | Uso |
   | --- | --- | --- |
   | 1–6 | Sequência | Numeração da linha; ignorada pelo compilador |
   | 7 | Indicador | `*` ou `/` = comentário; `-` = continuação; `D` = depuração |
   | 8–11 | Área A | Divisões, seções, parágrafos e níveis `01`/`77` |
   | 12–72 | Área B | Comandos e demais declarações |
   | 73–80 | Identificação | Ignorada pelo compilador |

   Deslocar o código uma coluna para a esquerda muda o significado da linha: a primeira letra passa a ser lida como indicador.
2. **Linhas de continuação.** Um `-` na coluna 7 indica que a linha continua a anterior, e um token pode ser dividido no meio. Em `prog004_folha_pgto.cob`, o identificador `TAB-TRABALHADOR` começa com `T` na coluna 72 da linha 27 e termina em `AB-TRABALHADOR` na linha 28. O lexer precisa reconstruir o token e ainda informar a posição física correta.
3. **Comentários definidos por coluna, não por delimitador.** O mesmo `*` é comentário na coluna 7, operador de multiplicação no código e metade do operador de potência `**`. O `/` também é comentário (com salto de página) na coluna 7 e divisão no código.
4. **Hífen ambíguo.** O `-` aparece dentro de nomes (`WKS-NUM-1`), como operador de subtração, como sinal de literal (`-1`) e em máscaras (`-ZZZZZZZZZ9.99`). Como o COBOL exige espaços em torno do operador, `WRK-A-WRK-B` é um único identificador, e não uma subtração.
5. **Ponto ambíguo.** O `.` termina sentenças, separa casas decimais (`437.4675`), faz parte de máscaras (`ZZ9.99`) e pode aparecer logo depois de uma máscara: em `PIC -ZZZZZZZZZ9.99.`, o primeiro ponto pertence à máscara e o segundo encerra a declaração.
6. **Máscaras `PICTURE` formam uma sublinguagem.** Fora do contexto de `PIC`, `X(10)` seria um identificador seguido de parênteses e de um número; depois de `PIC`, é uma única máscara. O lexer precisa guardar estado sobre o token anterior.
7. **Palavras que começam com dígitos.** Nomes de parágrafo como `00001-DISPLAY-TRABALHADOR` são válidos. Para distingui-los de números como `00001`, é preciso ler a palavra inteira antes de classificá-la.
8. **Vocabulário extenso e sem distinção de caixa.** O padrão reserva algumas centenas de palavras, muitas com hífen (`END-IF`, `WORKING-STORAGE`) e com sinônimos (`ZERO`, `ZEROS`, `ZEROES`). Relações podem ser escritas com símbolos (`>`) ou por extenso (`GREATER THAN`), e `display` e `DISPLAY` são a mesma palavra.
9. **Literais.** Strings aceitam aspas simples ou duplas, usam aspas duplicadas como escape (`"ELE DISSE ""OI"""`) e também podem continuar na linha seguinte.
10. **Dialetos e pré-processamento.** IBM Enterprise COBOL, GnuCOBOL e Micro Focus diferem em detalhes. O formato livre (desde 2002), os comentários de fim de linha `*>` e a expansão de `COPY`/`REPLACE`, que ocorre antes da análise léxica, ampliam ainda mais o problema.

---

## 2. Implementação

### 2.1 Estratégia

O lexer foi escrito **à mão em Python 3.11**, usando apenas a biblioteca padrão. **Não usamos geradores de analisadores léxicos** (flex, JFlex, PLY, ANTLR) pelos seguintes motivos:

- O formato fixo exige um pré-processamento por colunas (descartar 1–6 e 73+, interpretar a coluna 7 e unir continuações) que precisaria ser escrito à parte de qualquer maneira.
- O reconhecimento de máscaras `PIC` depende do token anterior; no flex, isso exigiria *start conditions* controladas manualmente.
- Com o laço de varredura explícito, fica simples controlar a recuperação de erros e associar cada diagnóstico à linha e coluna físicas, inclusive em tokens que atravessam linhas.

O resultado tem cerca de 400 linhas de código, sem dependências externas.

O processamento ocorre em duas fases:

```text
arquivo .cob
   │  read_fixed_lines()     descarta colunas 1–6 e 73+; separa o indicador (coluna 7)
   ▼
linhas físicas (FixedLine)
   │  read_logical_lines()   descarta comentários e linhas D; valida TAB e indicador;
   │                         une continuações mantendo um mapa de posições
   ▼
linhas lógicas (LogicalLine: código + posição física de cada caractere)
   │  CobolLexer._scan_code()  reconhecimento por prioridade, com contexto de PIC
   ▼
LexerResult = tokens + diagnósticos  →  CLI (texto, --stream ou --json)
```

### 2.2 Organização do código

| Módulo | Responsabilidade |
| --- | --- |
| `cobol_lexer/fixed_format.py` | Leitura do formato fixo, validação da coluna 7 e de TAB, união de continuações e mapa de posições |
| `cobol_lexer/scanner.py` | Classe `CobolLexer`: palavras reservadas, expressões regulares e reconhecimento dos tokens |
| `cobol_lexer/model.py` | Estruturas `Token`, `Diagnostic` e `LexerResult` |
| `cobol_lexer/__main__.py` | Interface de linha de comando |
| `tests/` | 56 testes automatizados (`unittest`) |
| `examples/ebasso/` | Os sete programas de teste fornecidos, sem alterações |
| `examples/erros/` | Cópias dos programas de teste com erros inseridos (seção 4) |

### 2.3 Fase 1: leitura do formato fixo

Cada linha física é recortada nas colunas 8–72, e a coluna 7 é interpretada como indicador. Linhas de comentário (`*`, `/`) e de depuração (`D`, a menos que se use `--debug-lines`) são descartadas antes de qualquer outra validação. Linhas com TAB ou indicador desconhecido geram diagnóstico e são descartadas.

Uma linha com `-` na coluna 7 é anexada à linha lógica anterior, sem a indentação. Se houver uma string aberta, a aspa repetida no início da continuação também é removida. Para cada caractere da linha lógica, o leitor guarda o par (linha, coluna) de origem. Assim, um token reconstruído informa onde começa e onde termina no arquivo original:

```json
{
  "kind": "IDENTIFIER",
  "lexeme": "TAB-TRABALHADOR",
  "value": "TAB-TRABALHADOR",
  "line": 27,
  "column": 72,
  "area": "B",
  "end_line": 28,
  "end_column": 21
}
```

### 2.4 Fase 2: reconhecimento dos tokens

O scanner percorre a linha lógica e, em cada posição, testa as alternativas **nesta ordem de prioridade**, que resolve as ambiguidades descritas na seção 1.3:

1. **Espaço:** separador, é descartado.
2. **Contexto de `PIC`:** se a palavra anterior foi `PIC` ou `PICTURE` (com `IS` opcional), lê até o próximo espaço e remove o ponto, a vírgula ou o ponto-e-vírgula final, que são separadores. Em seguida, valida o texto como máscara e emite um único token `PICTURE`.
3. **Aspas:** literal alfanumérico; aspas duplicadas viram uma aspa no valor.
4. **Pontuação:** `.`, `,`, `;`, `(` e `)`.
5. **Número com sinal:** `+` ou `-` seguido de dígitos, desde que esteja no início da linha ou depois de espaço, `(`, vírgula ou operador. Assim, `-1` é um literal, enquanto em `COUNT+1` o `+` é operador.
6. **Operadores, pelo maior casamento:** `**`, `<=`, `>=` e `<>` são testados antes de `*`, `<` e `>`.
7. **Palavra** (`[A-Za-z0-9_-]+`, pelo maior casamento):
   - só dígitos (opcionalmente com parte decimal) → `NUMBER`;
   - presente na tabela de palavras reservadas → `KEYWORD`;
   - caso contrário → `IDENTIFIER`, desde que não comece nem termine com hífen ou underscore e tenha até 30 caracteres.
8. **Qualquer outro caractere:** diagnóstico `INVALID_CHARACTER`.

Como a palavra é lida inteira antes da classificação, `00001-DISPLAY-TRABALHADOR` é identificador, `00001` é número e `WKS-NUM-1` não é quebrado em uma subtração.

| Padrão | Expressão regular |
| --- | --- |
| Palavra | `[A-Za-z0-9_-]+` |
| Número com sinal | `[+-][0-9]+(?:\.[0-9]+)?` |
| Número decimal | `[0-9]+\.[0-9]+` |
| Máscara `PIC` | `(?:(?:CR\|DB\|[AX9SVPZ0B/,.+*$-])(?:\([0-9]+\))?)+` (sem distinção de caixa; repetições devem ser maiores que zero) |

**Tipos de token emitidos:**

| Tipo | Exemplos |
| --- | --- |
| `KEYWORD` | `IDENTIFICATION`, `PROGRAM-ID`, `MOVE`, `END-IF`, `ZEROS` |
| `IDENTIFIER` | `WRK-VALOR1`, `PROG007_LOJA`, `00001-PEDIR-DADOS` |
| `NUMBER` | `77`, `0`, `-1`, `123.45` |
| `STRING` | `"Hello world"`, `'TEXTO'` |
| `PICTURE` | `X(10)`, `S9(05)V99`, `-ZZZZZZZZZ9.99` |
| Pontuação | `PERIOD`, `COMMA`, `SEMICOLON`, `LPAREN`, `RPAREN` |
| Operadores | `PLUS`, `MINUS`, `MULTIPLY`, `DIVIDE`, `POWER`, `EQUAL`, `LESS_THAN`, `GREATER_THAN`, `LESS_EQUAL`, `GREATER_EQUAL`, `NOT_EQUAL` |

Cada token registra `kind`, `lexeme` (texto lido), `value` (palavras normalizadas em maiúsculas e strings sem as aspas), posição inicial e final e a área (A ou B) em que começa.

### 2.5 Decisões de projeto

- Palavras reservadas e identificadores não diferenciam maiúsculas de minúsculas.
- Linhas `D` são ignoradas por padrão e analisadas com `--debug-lines`.
- Além das 14 palavras reservadas da especificação, o vocabulário foi ampliado com as palavras usadas pelos programas de teste (`PIC`, `VALUE`, `COMPUTE`, `INSPECT`, `EVALUATE`, `READ`, `WRITE` etc.).
- Aceitamos underscore no interior de identificadores (`PROG007_LOJA`) para analisar os programas de teste sem modificá-los. É uma extensão à especificação, que prevê apenas letras, dígitos e hífen.
- A área (A ou B) é registrada como metadado. A validação de quais declarações podem aparecer em cada área fica para o parser.
- `COPY`/`REPLACE`, o formato livre e os comentários `*>` estão fora do escopo desta entrega.

A lista completa, com justificativas, está no `README.md` do repositório.

### 2.6 Testes automatizados

A suíte em `tests/` tem **56 testes** (`python -m unittest discover -s tests -v`). Eles cobrem:

- palavras reservadas, identificadores, números, strings, pontuação, operadores e máscaras;
- descarte de colunas, comentários e linhas de depuração;
- continuação de strings, palavras, números e máscaras, com verificação das posições físicas;
- cada código de erro e a recuperação após o erro;
- integração pela CLI com os sete programas de teste (todos sem diagnósticos);
- integração com as sete cópias com erros (seção 4), conferindo código, linha e coluna de cada diagnóstico;
- formato da saída `--stream`.

### 2.7 Ferramentas utilizadas

| Ferramenta | Uso |
| --- | --- |
| Python 3.11 (`re`, `dataclasses`, `argparse`, `json`) | Implementação do lexer e da CLI |
| `unittest` | Testes automatizados |
| Git e GitHub | Versionamento; integrações por *pull request* |
| Visual Studio Code | Edição do código |
| Guia do GnuCOBOL | Consulta sobre o formato fixo e `PICTURE` (o compilador não foi usado) |
| Claude Code (Anthropic) | Assistente de IA (seção 2.8) |

### 2.8 Uso de ferramentas de IA

Usamos o **Claude Code**, assistente de programação da Anthropic baseado nos modelos Claude. Ele roda no terminal e na extensão do VS Code e tem acesso ao repositório: lê arquivos, executa comandos e testes e propõe ou aplica alterações. O uso foi de **apoio**. As decisões de projeto e a responsabilidade pelo código são do grupo, e nenhuma alteração foi integrada sem passar pela suíte de testes.

| Atividade | O que a IA fez | Como validamos |
| --- | --- | --- |
| **Revisão de código** | Revisou os *diffs* antes da integração, como o PR #1, que ampliou o lexer para os programas de teste. Apontou casos-limite não tratados e inconsistências entre o código, o README e a especificação. | Cada apontamento aceito virou primeiro um teste de regressão e só depois foi corrigido. |
| **Esclarecimento de regras do COBOL** | Explicou o formato fixo (áreas, indicadores, continuação) e os símbolos de `PICTURE`. | Conferimos com a seção 2 da especificação e com o guia do GnuCOBOL; em caso de divergência, prevaleceu a especificação. |
| **Diagnóstico dos programas de teste** | Classificou por causa os 33 diagnósticos que a primeira versão gerava em seis dos sete programas: palavras reservadas ausentes, operadores, máscaras `PIC`, underscore e continuação de palavras. | A classificação orientou a ampliação do lexer. O critério de aceite foi zero diagnósticos nos sete programas, sem alterar os fontes. |
| **Sugestão de casos de teste** | Propôs entradas-limite: identificadores com 30 e 31 caracteres, aspas duplicadas, continuação com aspa repetida, comentários entre linhas continuadas. | O grupo escolheu quais adotar e conferiu o resultado esperado de cada teste com a especificação. |
| **Documentação** | Revisou o README, as mensagens de *commit* e a redação deste relatório (estrutura e clareza). | Revisão humana do texto final. Os números e as saídas foram copiados de execuções reais. |
| **Preparação desta entrega** | Implementou a opção `--stream`. Gerou as cópias com erros por um script que confere a linha original antes de alterá-la, escreveu os testes de regressão desses arquivos e coletou as saídas mostradas nas seções 3 e 4. | Execução da suíte completa e conferência de cada diagnóstico com a alteração correspondente. |

Exemplos de problemas encontrados na revisão de código, cada um coberto por um teste de regressão:

- **Comentários com TAB eram rejeitados**, porque a validação de TAB ocorria antes do descarte das linhas de comentário (`test_comments_with_tabs_ignored`).
- **Comentários e linhas `D` entre as partes de um token continuado** interrompiam a continuação (`test_comments_and_debug_lines_between_continuations`, `test_ignored_lines_between_continuations`).
- **O limite de 30 caracteres** precisava ser verificado depois da união das continuações, e não em cada linha física (`test_continued_word_length_is_validated_after_joining`).
- **O estado de contexto de `PIC`** não podia vazar de uma chamada de `tokenize` para a seguinte (`test_picture_context_does_not_leak`).
- **Dígitos Unicode** como `١` satisfazem `str.isdigit()`, mas não a expressão `[0-9]`, o que podia provocar falha após um sinal (`test_unicode_digit_after_sign_does_not_crash`).
- **Separador depois da máscara:** em `PIC 9(5)V99, VALUE 1`, a vírgula era incorporada à máscara. O problema foi encontrado e corrigido durante a preparação desta entrega (`test_separator_after_picture_is_not_part_of_mask`).

**Cuidados adotados.** Tratamos as respostas da IA como sugestões a verificar, nunca como fonte de verdade sobre o COBOL: afirmações sobre a linguagem foram conferidas com a especificação e o guia do GnuCOBOL. O código proposto só foi aceito depois de lido e de passar nos testes.

---

## 3. Resultados dos testes

Os sete programas de [ebasso/cobol-exemplos](https://github.com/ebasso/cobol-exemplos) estão em `examples/ebasso/`, sem nenhuma alteração. Os fluxos abaixo foram gerados em 19/10/2026 (Python 3.11.9, Windows 11) com:

```bash
python -m cobol_lexer examples/ebasso/<programa>.cob --stream
```

Todos os sete programas foram analisados **sem nenhum erro léxico** (código de saída 0). O exemplo mínimo `examples/hello.cob` também passa (16 tokens).

| Programa | Linhas físicas | Linhas com tokens | Tokens | Palavras reservadas | Identificadores | Números | Strings | Máscaras | Pontuação | Operadores | Erros |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `prog001_divisoes` | 58 | 18 | 76 | 25 | 24 | 0 | 2 | 0 | 25 | 0 | 0 |
| `prog002_operacoes` | 100 | 74 | 320 | 115 | 60 | 35 | 38 | 6 | 66 | 0 | 0 |
| `prog003_calculadora` | 83 | 63 | 229 | 92 | 49 | 11 | 21 | 7 | 39 | 10 | 0 |
| `prog004_folha_pgto` | 77 | 53 | 221 | 71 | 43 | 15 | 22 | 4 | 64 | 2 | 0 |
| `prog005_strings` | 75 | 49 | 236 | 95 | 41 | 9 | 42 | 4 | 45 | 0 | 0 |
| `prog006_files` | 76 | 49 | 225 | 74 | 48 | 22 | 7 | 12 | 61 | 1 | 0 |
| `prog007_loja` | 228 | 167 | 566 | 248 | 107 | 51 | 45 | 19 | 87 | 9 | 0 |
| **Total** | **697** | **473** | **1873** | **720** | **372** | **143** | **177** | **52** | **387** | **22** | **0** |

**Como ler os fluxos:**

- Cada linha mostra `NNNN | <TIPO, lexema> ...`, em que `NNNN` é a linha física onde o token começa. Linhas iniciadas só por `|` continuam a anterior; a quebra é apenas visual.
- Pontuação e operadores aparecem só com o tipo (`<PERIOD>`, `<EQUAL>`), porque o lexema é fixo.
- Comentários e linhas em branco não produzem tokens e por isso não aparecem.
- Um token continuado aparece na linha em que começa.

### 3.1 `prog001_divisoes.cob`

Mostra as quatro divisões e os parágrafos opcionais da `IDENTIFICATION DIVISION`. Das 58 linhas, 40 são comentários ou estão em branco e foram descartadas. O texto livre de `AUTHOR`, `INSTALLATION`, `DATE-WRITTEN`, `SECURITY` e `REMARKS` é tokenizado como palavras comuns: `ebasso(dot)net` gera identificadores e parênteses, e `2018-02-24` é uma palavra válida (começa com dígito e contém hífens). Um compilador completo trataria esse texto como *comment-entry*; neste programa, a tokenização comum não gera erros. A linha 56 mostra a insensibilidade a maiúsculas (`display`).

```text
  15 | <KEYWORD, IDENTIFICATION> <KEYWORD, DIVISION> <PERIOD>
  16 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, PROG0001> <PERIOD>
  19 | <KEYWORD, AUTHOR> <PERIOD> <IDENTIFIER, Enio> <IDENTIFIER, Basso> <PERIOD>
  20 | <KEYWORD, INSTALLATION> <PERIOD> <IDENTIFIER, ebasso> <LPAREN> <IDENTIFIER, dot> <RPAREN>
     | <IDENTIFIER, net> <PERIOD>
  21 | <KEYWORD, DATE-WRITTEN> <PERIOD> <IDENTIFIER, 2018-02-24> <PERIOD>
  22 | <KEYWORD, DATE-COMPILED> <PERIOD> <IDENTIFIER, 2018-02-24> <PERIOD>
  23 | <KEYWORD, SECURITY> <PERIOD> <IDENTIFIER, O> <IDENTIFIER, programa> <IDENTIFIER, usa>
     | <IDENTIFIER, criptografia> <IDENTIFIER, XPTO> <PERIOD>
  24 | <KEYWORD, REMARKS> <PERIOD> <IDENTIFIER, O> <IDENTIFIER, programa> <IDENTIFIER, recebe>
     | <IDENTIFIER, um> <IDENTIFIER, valor> <IDENTIFIER, e> <IDENTIFIER, imprime>
     | <IDENTIFIER, na> <IDENTIFIER, tela> <PERIOD>
  27 | <KEYWORD, ENVIRONMENT> <KEYWORD, DIVISION> <PERIOD>
  29 | <KEYWORD, CONFIGURATION> <KEYWORD, SECTION> <PERIOD>
  37 | <KEYWORD, INPUT-OUTPUT> <KEYWORD, SECTION> <PERIOD>
  46 | <KEYWORD, DATA> <KEYWORD, DIVISION> <PERIOD>
  53 | <KEYWORD, PROCEDURE> <KEYWORD, DIVISION> <PERIOD>
  54 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  55 | <KEYWORD, DISPLAY> <STRING, "Hello world">
  56 | <KEYWORD, display> <STRING, "Enio Basso - 2">
  57 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
  58 | <KEYWORD, END> <KEYWORD, PROGRAM> <IDENTIFIER, PROG0001> <PERIOD>

76 tokens; 0 erros léxicos.
```

### 3.2 `prog002_operacoes.cob`

Mostra os níveis `77`, `01` e `05` (emitidos como `NUMBER`), as máscaras `9(10)` e `9(2)` e os comandos aritméticos por extenso (`ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE ... REMAINDER`, `ON SIZE ERROR`). Nas linhas 38 e 39, a string termina na linha 38 e a linha de continuação traz apenas `WRK-VALOR2.`; os tokens da continuação recebem a posição da linha 39. As strings contêm `-->`, `=`, `;` e `.`, que não são confundidos com operadores ou pontuação.

```text
  11 | <KEYWORD, IDENTIFICATION> <KEYWORD, DIVISION> <PERIOD>
  12 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, YOUR-PROGRAM-NAME> <PERIOD>
  13 | <KEYWORD, DATA> <KEYWORD, DIVISION> <PERIOD>
  14 | <KEYWORD, FILE> <KEYWORD, SECTION> <PERIOD>
  15 | <KEYWORD, WORKING-STORAGE> <KEYWORD, SECTION> <PERIOD>
  16 | <NUMBER, 77> <IDENTIFIER, WRK-VALOR1> <KEYWORD, PIC> <PICTURE, 9(10)> <KEYWORD, VALUES>
     | <NUMBER, 10> <PERIOD>
  17 | <NUMBER, 77> <IDENTIFIER, WRK-VALOR2> <KEYWORD, PIC> <PICTURE, 9(10)> <KEYWORD, VALUES>
     | <KEYWORD, ZEROS> <PERIOD>
  18 | <NUMBER, 77> <IDENTIFIER, WRK-A> <KEYWORD, PIC> <PICTURE, 9(2)> <KEYWORD, VALUES>
     | <NUMBER, 1> <PERIOD>
  19 | <NUMBER, 77> <IDENTIFIER, WRK-B> <KEYWORD, PIC> <PICTURE, 9(2)> <KEYWORD, VALUES>
     | <NUMBER, 1> <PERIOD>
  20 | <NUMBER, 77> <IDENTIFIER, WRK-C> <KEYWORD, PIC> <PICTURE, 9(2)> <KEYWORD, VALUES>
     | <KEYWORD, ZEROS> <PERIOD>
  22 | <NUMBER, 01> <IDENTIFIER, WRK-TOTAIS> <PERIOD>
  23 | <NUMBER, 05> <IDENTIFIER, WRK-TOTAL> <KEYWORD, PIC> <PICTURE, 9(10)> <KEYWORD, VALUE>
     | <NUMBER, 19> <PERIOD>
  25 | <KEYWORD, PROCEDURE> <KEYWORD, DIVISION> <PERIOD>
  26 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  27 | <KEYWORD, DISPLAY> <STRING, "===== start ======="> <PERIOD>
  28 | <KEYWORD, MOVE> <NUMBER, 20> <KEYWORD, TO> <IDENTIFIER, WRK-VALOR2> <PERIOD>
  29 | <KEYWORD, DISPLAY> <STRING, "MOVE 20 TO WRK-VALOR2 -->"> <IDENTIFIER, WRK-VALOR2>
     | <PERIOD>
  31 | <KEYWORD, MOVE> <IDENTIFIER, WRK-VALOR1> <KEYWORD, TO> <IDENTIFIER, WRK-VALOR2> <PERIOD>
  32 | <KEYWORD, DISPLAY> <STRING, "MOVE WRK-VALOR1 TO WRK-VALOR2 -->"> <IDENTIFIER, WRK-VALOR2>
     | <PERIOD>
  34 | <KEYWORD, MOVE> <NUMBER, 70> <KEYWORD, TO> <IDENTIFIER, WRK-VALOR1>
     | <IDENTIFIER, WRK-VALOR2> <PERIOD>
  35 | <KEYWORD, DISPLAY> <STRING, "MOVE 70 TO WRK-VALOR1 WRK-VALOR2 -->">
     | <IDENTIFIER, WRK-VALOR2> <PERIOD>
  37 | <KEYWORD, MOVE> <IDENTIFIER, WRK-TOTAL> <KEYWORD, OF> <IDENTIFIER, WRK-TOTAIS>
     | <KEYWORD, TO> <IDENTIFIER, WRK-VALOR2> <PERIOD>
  38 | <KEYWORD, DISPLAY> <STRING, "MOVE WRK-TOTAL OF WRK-TOTAIS TO WRK-VALOR2. -->">
  39 | <IDENTIFIER, WRK-VALOR2> <PERIOD>
  41 | <KEYWORD, DISPLAY> <STRING, "--------"> <PERIOD>
  42 | <KEYWORD, DISPLAY> <STRING, "A = 1, B = 1, C = 1"> <PERIOD>
  44 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  45 | <KEYWORD, ADD> <NUMBER, 1> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WRK-A> <PERIOD>
  46 | <KEYWORD, DISPLAY> <STRING, "ADD B C TO A (A = B + C + A) -->"> <IDENTIFIER, WRK-A>
     | <PERIOD>
  48 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WRK-A> <PERIOD>
  49 | <KEYWORD, ADD> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WRK-A> <IDENTIFIER, WRK-B> <PERIOD>
  50 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  51 | <KEYWORD, DISPLAY> <STRING, "ADD 1 TO A B (A = A + 1; B = B + 1) -->">
  52 | <KEYWORD, DISPLAY> <STRING, "A= "> <IDENTIFIER, WRK-A> <STRING, " , B= ">
     | <IDENTIFIER, WRK-B> <PERIOD>
  54 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  55 | <KEYWORD, ADD> <NUMBER, 1> <NUMBER, 1> <KEYWORD, GIVING> <IDENTIFIER, WRK-A> <PERIOD>
  56 | <KEYWORD, DISPLAY> <STRING, "ADD B C GIVING A (A = B + C) -->"> <IDENTIFIER, WRK-A>
     | <PERIOD>
  58 | <KEYWORD, DISPLAY> <STRING, "============ SUBTRACT ============= "> <PERIOD>
  59 | <KEYWORD, MOVE> <NUMBER, 99> <KEYWORD, TO> <IDENTIFIER, WRK-A> <PERIOD>
  60 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WRK-B> <PERIOD>
  61 | <KEYWORD, DISPLAY> <STRING, "A= 99, B= 0"> <PERIOD>
  62 | <KEYWORD, SUBTRACT> <NUMBER, 30> <NUMBER, 23> <KEYWORD, FROM> <IDENTIFIER, WRK-A>
  63 | <KEYWORD, GIVING> <IDENTIFIER, WRK-B> <PERIOD>
  64 | <KEYWORD, DISPLAY> <STRING, "SUBTRACT 30 23 FROM A GIVING B.-->">
  65 | <KEYWORD, DISPLAY> <STRING, "A= "> <IDENTIFIER, WRK-A> <STRING, " , B= ">
     | <IDENTIFIER, WRK-B> <PERIOD>
  67 | <KEYWORD, DISPLAY> <STRING, "============ MULTIPLY ============= "> <PERIOD>
  68 | <KEYWORD, MOVE> <NUMBER, 40> <KEYWORD, TO> <IDENTIFIER, WRK-A> <PERIOD>
  69 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WRK-B> <PERIOD>
  70 | <KEYWORD, DISPLAY> <STRING, "A= 40, B= 0"> <PERIOD>
  71 | <KEYWORD, MULTIPLY> <NUMBER, 2> <KEYWORD, BY> <IDENTIFIER, WRK-A> <PERIOD>
  72 | <KEYWORD, DISPLAY> <STRING, "MULTIPLY A BY 2 -->">
  73 | <KEYWORD, DISPLAY> <STRING, "A= "> <IDENTIFIER, WRK-A> <STRING, " , B= ">
     | <IDENTIFIER, WRK-B> <PERIOD>
  75 | <KEYWORD, DISPLAY> <STRING, "============ MULTIPLY ============= "> <PERIOD>
  76 | <KEYWORD, MOVE> <NUMBER, 40> <KEYWORD, TO> <IDENTIFIER, WRK-A> <PERIOD>
  77 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WRK-B> <PERIOD>
  78 | <KEYWORD, DISPLAY> <STRING, "A= 40, B= 0"> <PERIOD>
  79 | <KEYWORD, MULTIPLY> <NUMBER, 2> <KEYWORD, BY> <IDENTIFIER, WRK-A> <KEYWORD, GIVING>
     | <IDENTIFIER, WRK-B> <PERIOD>
  80 | <KEYWORD, DISPLAY> <STRING, "MULTIPLY A BY 2 GIVING B.-->">
  81 | <KEYWORD, DISPLAY> <STRING, "A= "> <IDENTIFIER, WRK-A> <STRING, " , B= ">
     | <IDENTIFIER, WRK-B> <PERIOD>
  83 | <KEYWORD, DISPLAY> <STRING, "============ DIVIDE ============="> <PERIOD>
  84 | <KEYWORD, MOVE> <NUMBER, 81> <KEYWORD, TO> <IDENTIFIER, WRK-A> <PERIOD>
  85 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WRK-B> <PERIOD>
  86 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WRK-C> <PERIOD>
  87 | <KEYWORD, DISPLAY> <STRING, "A= 80, B= 0"> <PERIOD>
  88 | <KEYWORD, DIVIDE> <IDENTIFIER, WRK-A> <KEYWORD, BY> <NUMBER, 2> <KEYWORD, GIVING>
     | <IDENTIFIER, WRK-B> <KEYWORD, REMAINDER> <IDENTIFIER, WRK-C> <PERIOD>
  89 | <KEYWORD, DISPLAY> <STRING, "DIVIDE A BY 2 GIVING B REMAINDER C .-->">
  90 | <KEYWORD, DISPLAY> <STRING, "A= "> <IDENTIFIER, WRK-A> <STRING, " , B= ">
     | <IDENTIFIER, WRK-B> <STRING, " , C= "> <IDENTIFIER, WRK-C> <PERIOD>
  93 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  94 | <KEYWORD, MOVE> <NUMBER, 99> <KEYWORD, TO> <IDENTIFIER, WRK-A> <PERIOD>
  95 | <KEYWORD, ADD> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WRK-A>
  96 | <KEYWORD, ON> <KEYWORD, SIZE> <KEYWORD, ERROR>
  97 | <KEYWORD, DISPLAY> <STRING, "ON SIZE ERROR -->"> <IDENTIFIER, WRK-A> <PERIOD>
  99 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
 100 | <KEYWORD, END> <KEYWORD, PROGRAM> <IDENTIFIER, YOUR-PROGRAM-NAME> <PERIOD>

320 tokens; 0 erros léxicos.
```

### 3.3 `prog003_calculadora.cob`

Concentra as máscaras mais variadas: `S9(05)V99`, `S9(05)V9(02)`, `A(01)` e `-ZZZZZZZZZ9.99`, esta seguida do ponto final da declaração (linha 22). Também tem nomes de parágrafo que começam com dígitos (`00000-CALCULADORA`), a chamada `FUNCTION UPPER-CASE(WKS-OPCAO)`, o operador relacional `=` e o operador de potência `**` (linha 70).

```text
  11 | <KEYWORD, IDENTIFICATION> <KEYWORD, DIVISION> <PERIOD>
  12 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, CALCULADORA> <PERIOD>
  13 | <KEYWORD, DATA> <KEYWORD, DIVISION> <PERIOD>
  14 | <KEYWORD, FILE> <KEYWORD, SECTION> <PERIOD>
  15 | <KEYWORD, WORKING-STORAGE> <KEYWORD, SECTION> <PERIOD>
  16 | <NUMBER, 77> <IDENTIFIER, WKS-NUM-1> <KEYWORD, PIC> <PICTURE, S9(05)V99>
     | <KEYWORD, VALUES> <NUMBER, 0> <PERIOD>
  17 | <NUMBER, 77> <IDENTIFIER, WKS-NUM-2> <KEYWORD, PIC> <PICTURE, S9(05)V9(02)>
     | <KEYWORD, VALUES> <NUMBER, 0> <PERIOD>
  18 | <NUMBER, 77> <IDENTIFIER, WKS-RESULTADO> <KEYWORD, PIC> <PICTURE, S9(10)V99>
     | <KEYWORD, VALUES> <KEYWORD, ZEROS> <PERIOD>
  19 | <NUMBER, 77> <IDENTIFIER, WKS-RESTO> <KEYWORD, PIC> <PICTURE, 9(2)> <KEYWORD, VALUES>
     | <KEYWORD, ZEROS> <PERIOD>
  20 | <NUMBER, 77> <IDENTIFIER, WKS-OPCAO> <KEYWORD, PIC> <PICTURE, A(01)> <PERIOD>
  21 | <NUMBER, 77> <IDENTIFIER, WKS-SAIR> <KEYWORD, PIC> <PICTURE, 9(1)> <KEYWORD, VALUES>
     | <KEYWORD, ZEROS> <PERIOD>
  22 | <NUMBER, 77> <IDENTIFIER, WKS-RESULT-FORMAT> <KEYWORD, PIC> <PICTURE, -ZZZZZZZZZ9.99>
     | <PERIOD>
  24 | <KEYWORD, PROCEDURE> <KEYWORD, DIVISION> <PERIOD>
  25 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  27 | <KEYWORD, PERFORM> <IDENTIFIER, 00000-CALCULADORA> <KEYWORD, UNTIL>
     | <IDENTIFIER, WKS-SAIR> <EQUAL> <NUMBER, 2> <PERIOD>
  29 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
  31 | <IDENTIFIER, 00000-CALCULADORA> <PERIOD>
  32 | <KEYWORD, DISPLAY> <STRING, "============ CALCULADORA ============= "> <PERIOD>
  33 | <KEYWORD, DISPLAY> <STRING, "1-. USAR CALCULADORA, 2-. SAIR"> <PERIOD>
  34 | <KEYWORD, ACCEPT> <IDENTIFIER, WKS-SAIR> <PERIOD>
  36 | <KEYWORD, IF> <IDENTIFIER, WKS-SAIR> <EQUAL> <NUMBER, 1>
  37 | <KEYWORD, PERFORM> <IDENTIFIER, 00001-PEDIR-DADOS>
  38 | <KEYWORD, PERFORM> <IDENTIFIER, 00002-EXECUTAR-OPERACOES>
  39 | <KEYWORD, END-IF> <PERIOD>
  41 | <IDENTIFIER, 00001-PEDIR-DADOS> <PERIOD>
  42 | <KEYWORD, DISPLAY> <STRING, "OPERACAO: "> <PERIOD>
  43 | <KEYWORD, DISPLAY> <STRING, "(S)oma, s(U)btracao, (M)ultiplicacao e (D)ivisao"> <PERIOD>
  44 | <KEYWORD, DISPLAY> <STRING, "(P)otencia"> <PERIOD>
  45 | <KEYWORD, DISPLAY> <STRING, "==>"> <PERIOD>
  46 | <KEYWORD, ACCEPT> <IDENTIFIER, WKS-OPCAO> <PERIOD>
  48 | <KEYWORD, DISPLAY> <STRING, "VALOR 1:"> <PERIOD>
  49 | <KEYWORD, ACCEPT> <IDENTIFIER, WKS-NUM-1> <PERIOD>
  51 | <KEYWORD, DISPLAY> <STRING, "VALOR 2:"> <PERIOD>
  52 | <KEYWORD, ACCEPT> <IDENTIFIER, WKS-NUM-2> <PERIOD>
  54 | <IDENTIFIER, 00002-EXECUTAR-OPERACOES> <PERIOD>
  55 | <KEYWORD, MOVE> <KEYWORD, FUNCTION> <KEYWORD, UPPER-CASE> <LPAREN>
     | <IDENTIFIER, WKS-OPCAO> <RPAREN> <KEYWORD, TO> <IDENTIFIER, WKS-OPCAO> <PERIOD>
  56 | <KEYWORD, IF> <IDENTIFIER, WKS-OPCAO> <EQUAL> <STRING, "S"> <KEYWORD, OR> <STRING, "s">
  57 | <KEYWORD, ADD> <IDENTIFIER, WKS-NUM-1> <KEYWORD, TO> <IDENTIFIER, WKS-NUM-2>
     | <KEYWORD, GIVING> <IDENTIFIER, WKS-RESULTADO>
  58 | <KEYWORD, ELSE>
  59 | <KEYWORD, IF> <IDENTIFIER, WKS-OPCAO> <EQUAL> <STRING, "U">
  60 | <KEYWORD, SUBTRACT> <IDENTIFIER, WKS-NUM-1> <KEYWORD, FROM> <IDENTIFIER, WKS-NUM-2>
     | <KEYWORD, GIVING> <IDENTIFIER, WKS-RESULTADO>
  61 | <KEYWORD, ELSE>
  62 | <KEYWORD, IF> <IDENTIFIER, WKS-OPCAO> <EQUAL> <STRING, "M">
  63 | <KEYWORD, MULTIPLY> <IDENTIFIER, WKS-NUM-1> <KEYWORD, BY> <IDENTIFIER, WKS-NUM-2>
     | <KEYWORD, GIVING> <IDENTIFIER, WKS-RESULTADO>
  64 | <KEYWORD, ELSE>
  65 | <KEYWORD, IF> <IDENTIFIER, WKS-OPCAO> <EQUAL> <STRING, "D">
  66 | <KEYWORD, DIVIDE> <IDENTIFIER, WKS-NUM-1> <KEYWORD, BY> <IDENTIFIER, WKS-NUM-2>
     | <KEYWORD, GIVING> <IDENTIFIER, WKS-RESULTADO>
  67 | <KEYWORD, REMAINDER> <IDENTIFIER, WKS-RESTO>
  68 | <KEYWORD, ELSE>
  69 | <KEYWORD, IF> <IDENTIFIER, WKS-OPCAO> <EQUAL> <STRING, "P">
  70 | <KEYWORD, COMPUTE> <IDENTIFIER, WKS-RESULTADO> <EQUAL> <IDENTIFIER, WKS-NUM-1> <POWER>
     | <IDENTIFIER, WKS-NUM-2>
  71 | <KEYWORD, ELSE>
  72 | <KEYWORD, DISPLAY> <STRING, "OPCAO INVALIDA">
  73 | <KEYWORD, END-IF>
  74 | <KEYWORD, END-IF>
  75 | <KEYWORD, END-IF>
  76 | <KEYWORD, END-IF>
  77 | <KEYWORD, END-IF> <PERIOD>
  78 | <KEYWORD, IF> <IDENTIFIER, WKS-OPCAO> <EQUAL> <STRING, "S"> <KEYWORD, OR> <STRING, "U">
     | <KEYWORD, OR> <STRING, "M"> <KEYWORD, OR> <STRING, "D"> <KEYWORD, OR> <STRING, "P">
  79 | <KEYWORD, MOVE> <IDENTIFIER, WKS-RESULTADO> <KEYWORD, TO> <IDENTIFIER, WKS-RESULT-FORMAT>
  80 | <KEYWORD, DISPLAY> <STRING, "Resultado: "> <IDENTIFIER, WKS-RESULT-FORMAT>
  81 | <KEYWORD, END-IF> <PERIOD>
  83 | <KEYWORD, END> <KEYWORD, PROGRAM> <IDENTIFIER, CALCULADORA> <PERIOD>

229 tokens; 0 erros léxicos.
```

### 3.4 `prog004_folha_pgto.cob`

Usa tabelas com `OCCURS ... INDEXED BY` e subscritos com vírgula (`DPTO(IDX,1)`). Nas linhas 27 e 28 está o caso mais delicado dos programas de teste: o identificador `TAB-TRABALHADOR` foi dividido entre as duas linhas (`T` na coluna 72 e `AB-TRABALHADOR` na continuação). O lexer emite **um único** `IDENTIFIER`, que começa em 27:72 e termina em 28:21; o ponto final fica na linha 28.

```text
  11 | <KEYWORD, IDENTIFICATION> <KEYWORD, DIVISION> <PERIOD>
  12 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, FOLHA-PGTO> <PERIOD>
  13 | <KEYWORD, DATA> <KEYWORD, DIVISION> <PERIOD>
  14 | <KEYWORD, FILE> <KEYWORD, SECTION> <PERIOD>
  15 | <KEYWORD, WORKING-STORAGE> <KEYWORD, SECTION> <PERIOD>
  17 | <NUMBER, 01> <IDENTIFIER, TAB-TRABALHADOR> <PERIOD>
  18 | <NUMBER, 02> <IDENTIFIER, TRABALHADOR> <KEYWORD, OCCURS> <NUMBER, 3> <KEYWORD, TIMES>
     | <KEYWORD, INDEXED> <KEYWORD, BY> <IDENTIFIER, TID> <PERIOD>
  19 | <NUMBER, 03> <IDENTIFIER, NOME> <KEYWORD, PIC> <PICTURE, X(5)> <PERIOD>
  20 | <NUMBER, 03> <IDENTIFIER, SALARIO> <KEYWORD, PIC> <PICTURE, 9(5)V99> <PERIOD>
  21 | <NUMBER, 03> <IDENTIFIER, DPTO> <KEYWORD, PIC> <PICTURE, X(2)> <KEYWORD, VALUES>
     | <KEYWORD, SPACES> <KEYWORD, OCCURS> <NUMBER, 2> <KEYWORD, TIMES> <PERIOD>
  23 | <NUMBER, 77> <IDENTIFIER, IDX> <KEYWORD, PIC> <PICTURE, 9(1)> <PERIOD>
  25 | <KEYWORD, PROCEDURE> <KEYWORD, DIVISION> <PERIOD>
  26 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  27 | <KEYWORD, MOVE> <STRING, "JOSEA1111111A1A4MARIA2222222A2  FABIO3333333A2A3">
     | <KEYWORD, TO> <IDENTIFIER, TAB-TRABALHADOR>
  28 | <PERIOD>
  29 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  30 | <KEYWORD, DISPLAY> <STRING, "====TAB-TRABALHADOR===="> <PERIOD>
  31 | <KEYWORD, DISPLAY> <STRING, "INITIAL VALUE"> <PERIOD>
  32 | <KEYWORD, DISPLAY> <IDENTIFIER, TAB-TRABALHADOR> <PERIOD>
  34 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, IDX> <PERIOD>
  35 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  36 | <KEYWORD, DISPLAY> <STRING, "====00001-DISPLAY-TRABALHADOR===="> <PERIOD>
  37 | <KEYWORD, PERFORM> <IDENTIFIER, 00001-DISPLAY-TRABALHADOR> <KEYWORD, UNTIL>
     | <IDENTIFIER, IDX> <GREATER_THAN> <NUMBER, 3> <PERIOD>
  39 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  40 | <KEYWORD, DISPLAY> <STRING, "====00002-DISPLAY-BY-SEARCH===="> <PERIOD>
  41 | <KEYWORD, PERFORM> <IDENTIFIER, 00002-DISPLAY-BY-SEARCH> <PERIOD>
  43 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  44 | <KEYWORD, DISPLAY> <STRING, "====00003-REMOVE-TRABALHADOR===="> <PERIOD>
  45 | <KEYWORD, PERFORM> <IDENTIFIER, 00003-REMOVE-TRABALHADOR> <PERIOD>
  47 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
  49 | <IDENTIFIER, 00001-DISPLAY-TRABALHADOR> <PERIOD>
  50 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  52 | <KEYWORD, DISPLAY> <STRING, "IDX="> <IDENTIFIER, IDX> <PERIOD>
  53 | <KEYWORD, DISPLAY> <STRING, "TRABALHADOR(IDX)="> <IDENTIFIER, TRABALHADOR> <LPAREN>
     | <IDENTIFIER, IDX> <RPAREN> <PERIOD>
  54 | <KEYWORD, DISPLAY> <STRING, "NOME(IDX)="> <IDENTIFIER, NOME> <LPAREN> <IDENTIFIER, IDX>
     | <RPAREN> <PERIOD>
  55 | <KEYWORD, DISPLAY> <STRING, "SALARIO(IDX)="> <IDENTIFIER, SALARIO> <LPAREN>
     | <IDENTIFIER, IDX> <RPAREN> <PERIOD>
  56 | <KEYWORD, DISPLAY> <STRING, "DPTO(IDX,1)="> <IDENTIFIER, DPTO> <LPAREN> <IDENTIFIER, IDX>
     | <COMMA> <NUMBER, 1> <RPAREN> <PERIOD>
  57 | <KEYWORD, DISPLAY> <STRING, "DPTO(IDX,2)="> <IDENTIFIER, DPTO> <LPAREN> <IDENTIFIER, IDX>
     | <COMMA> <NUMBER, 2> <RPAREN> <PERIOD>
  58 | <KEYWORD, ADD> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, IDX> <PERIOD>
  60 | <IDENTIFIER, 00002-DISPLAY-BY-SEARCH> <PERIOD>
  62 | <KEYWORD, SET> <IDENTIFIER, TID> <KEYWORD, TO> <NUMBER, 1> <PERIOD>
  63 | <KEYWORD, SEARCH> <IDENTIFIER, TRABALHADOR>
  64 | <KEYWORD, AT> <KEYWORD, END> <KEYWORD, DISPLAY> <STRING, "TRABALHADOR NOT FOUND">
  65 | <KEYWORD, WHEN> <IDENTIFIER, NOME> <LPAREN> <IDENTIFIER, TID> <RPAREN> <EQUAL>
     | <STRING, "MARIA">
  66 | <KEYWORD, DISPLAY> <STRING, "'WHEN NOME(TID) = MARIA'">
  67 | <KEYWORD, DISPLAY> <STRING, "TID="> <IDENTIFIER, TID>
  68 | <KEYWORD, DISPLAY> <STRING, "TRABALHADOR(TID)="> <IDENTIFIER, TRABALHADOR> <LPAREN>
     | <IDENTIFIER, TID> <RPAREN>
  69 | <KEYWORD, END-SEARCH> <PERIOD>
  72 | <IDENTIFIER, 00003-REMOVE-TRABALHADOR> <PERIOD>
  73 | <KEYWORD, SET> <IDENTIFIER, TID> <KEYWORD, TO> <NUMBER, 2> <PERIOD>
  74 | <KEYWORD, MOVE> <KEYWORD, LOW-VALUES> <KEYWORD, TO> <IDENTIFIER, TRABALHADOR> <LPAREN>
     | <IDENTIFIER, TID> <RPAREN>
  75 | <KEYWORD, DISPLAY> <IDENTIFIER, TAB-TRABALHADOR> <PERIOD>
  77 | <KEYWORD, END> <KEYWORD, PROGRAM> <IDENTIFIER, FOLHA-PGTO> <PERIOD>

221 tokens; 0 erros léxicos.
```

### 3.5 `prog005_strings.cob`

Trata de manipulação de strings (`INSPECT ... TALLYING`, `REPLACING`, `CONVERTING`). Muitas strings delimitadas por aspas duplicadas contêm aspas simples (`"SAUX='"`, `" - FOR ALL 'L'"`), que fazem parte do texto e não abrem um novo literal.

```text
  11 | <KEYWORD, IDENTIFICATION> <KEYWORD, DIVISION> <PERIOD>
  12 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, PROG008_STRING> <PERIOD>
  13 | <KEYWORD, DATA> <KEYWORD, DIVISION> <PERIOD>
  14 | <KEYWORD, FILE> <KEYWORD, SECTION> <PERIOD>
  15 | <KEYWORD, WORKING-STORAGE> <KEYWORD, SECTION> <PERIOD>
  17 | <NUMBER, 77> <IDENTIFIER, SAUX> <KEYWORD, PIC> <PICTURE, X(15)> <PERIOD>
  18 | <NUMBER, 77> <IDENTIFIER, CONT> <KEYWORD, PIC> <PICTURE, 9(2)> <PERIOD>
  19 | <NUMBER, 77> <IDENTIFIER, YESNO> <KEYWORD, PIC> <PICTURE, 9> <PERIOD>
  21 | <NUMBER, 77> <IDENTIFIER, IDX> <KEYWORD, PIC> <PICTURE, 9(1)> <PERIOD>
  23 | <KEYWORD, PROCEDURE> <KEYWORD, DIVISION> <PERIOD>
  24 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  25 | <KEYWORD, MOVE> <STRING, "HELLO WORLD 123!!"> <KEYWORD, TO> <IDENTIFIER, SAUX> <PERIOD>
  27 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  28 | <KEYWORD, DISPLAY> <STRING, "==== EXEMPLO 1 ===="> <PERIOD>
  29 | <KEYWORD, DISPLAY> <STRING, "SAUX='"> <IDENTIFIER, SAUX> <STRING, "'"> <PERIOD>
  31 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, CONT> <PERIOD>
  32 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, TALLYING> <IDENTIFIER, CONT>
     | <KEYWORD, FOR> <KEYWORD, CHARACTERS> <PERIOD>
  33 | <KEYWORD, DISPLAY> <STRING, "CONT="> <IDENTIFIER, CONT> <STRING, " - FOR CHARACTERS">
     | <PERIOD>
  35 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, CONT> <PERIOD>
  36 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, TALLYING> <IDENTIFIER, CONT>
     | <KEYWORD, FOR> <KEYWORD, ALL> <STRING, "L"> <PERIOD>
  37 | <KEYWORD, DISPLAY> <STRING, "CONT="> <IDENTIFIER, CONT> <STRING, " - FOR ALL 'L'">
     | <PERIOD>
  39 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, CONT> <PERIOD>
  40 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, TALLYING> <IDENTIFIER, CONT>
  41 | <KEYWORD, FOR> <KEYWORD, CHARACTERS> <KEYWORD, BEFORE> <KEYWORD, INITIAL> <STRING, " ">
     | <PERIOD>
  42 | <KEYWORD, DISPLAY> <STRING, "CONT="> <IDENTIFIER, CONT> <STRING, " - BEFORE INITIAL ' '">
     | <PERIOD>
  44 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, CONT> <PERIOD>
  45 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, TALLYING> <IDENTIFIER, CONT>
  46 | <KEYWORD, FOR> <KEYWORD, CHARACTERS> <KEYWORD, AFTER> <KEYWORD, INITIAL> <STRING, " ">
     | <PERIOD>
  47 | <KEYWORD, DISPLAY> <STRING, "CONT="> <IDENTIFIER, CONT> <STRING, " - AFTER INITIAL ' '">
     | <PERIOD>
  49 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, YESNO> <PERIOD>
  50 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, TALLYING> <IDENTIFIER, YESNO>
  51 | <KEYWORD, FOR> <KEYWORD, LEADING> <STRING, "H"> <PERIOD>
  52 | <KEYWORD, DISPLAY> <STRING, "YESNO="> <IDENTIFIER, YESNO>
     | <STRING, " - FOR LEADING 'H' 0=N / 1=Y"> <PERIOD>
  54 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, REPLACING> <KEYWORD, FIRST> <STRING, "E">
     | <KEYWORD, BY> <STRING, "A"> <PERIOD>
  55 | <KEYWORD, DISPLAY> <STRING, "SAUX='"> <IDENTIFIER, SAUX>
     | <STRING, "' - REPLACING FIRST 'E' BY 'A'"> <PERIOD>
  57 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, REPLACING> <KEYWORD, ALL> <STRING, "LLO">
     | <KEYWORD, BY> <STRING, "PPY"> <PERIOD>
  58 | <KEYWORD, DISPLAY> <STRING, "SAUX='"> <IDENTIFIER, SAUX>
     | <STRING, "' - REPLACING ALL 'LLO' BY 'PPY'"> <PERIOD>
  60 | <KEYWORD, MOVE> <STRING, " HOLA-DAY"> <KEYWORD, TO> <IDENTIFIER, SAUX> <PERIOD>
  61 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, REPLACING> <KEYWORD, ALL>
     | <STRING, "HOLA"> <KEYWORD, BY> <STRING, "GOOD">
  62 | <KEYWORD, AFTER> <KEYWORD, INITIAL> <STRING, " "> <KEYWORD, BEFORE> <KEYWORD, INITIAL>
     | <STRING, "-"> <PERIOD>
  63 | <KEYWORD, DISPLAY> <STRING, "SAUX='"> <IDENTIFIER, SAUX>
     | <STRING, "' - HOLA-DAY TO GOOD-DAY'"> <PERIOD>
  65 | <KEYWORD, MOVE> <STRING, "HELLO WORLD"> <KEYWORD, TO> <IDENTIFIER, SAUX> <PERIOD>
  66 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, CONVERTING>
     | <STRING, "ABCDEFGHIJKLMNOPQRSTUVWXZ">
  67 | <KEYWORD, TO> <STRING, "abcdefghijklmnopqrstuvwxz"> <PERIOD>
  68 | <KEYWORD, DISPLAY> <STRING, "SAUX='"> <IDENTIFIER, SAUX> <STRING, "' - CONVERTING'">
     | <PERIOD>
  70 | <KEYWORD, INSPECT> <IDENTIFIER, SAUX> <KEYWORD, REPLACING> <KEYWORD, CHARACTERS>
     | <KEYWORD, BY> <STRING, "F"> <PERIOD>
  71 | <KEYWORD, DISPLAY> <STRING, "SAUX='"> <IDENTIFIER, SAUX> <STRING, "' - REPLACING ">
     | <PERIOD>
  73 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
  75 | <KEYWORD, END> <KEYWORD, PROGRAM> <IDENTIFIER, PROG008_STRING> <PERIOD>

236 tokens; 0 erros léxicos.
```

### 3.6 `prog006_files.cob`

Introduz a `ENVIRONMENT DIVISION` com `FILE-CONTROL`, `SELECT ... ASSIGN TO`, a descrição de arquivo (`FD`) e os comandos `OPEN OUTPUT`, `WRITE` e `CLOSE`. A divisão de `TAB-TRABALHADOR` se repete nas linhas 48 e 49 e é reconstruída da mesma forma.

```text
  11 | <KEYWORD, IDENTIFICATION> <KEYWORD, DIVISION> <PERIOD>
  12 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, PROG006_FILES> <PERIOD>
  13 | <KEYWORD, ENVIRONMENT> <KEYWORD, DIVISION> <PERIOD>
  14 | <KEYWORD, INPUT-OUTPUT> <KEYWORD, SECTION> <PERIOD>
  16 | <KEYWORD, FILE-CONTROL> <PERIOD>
  17 | <KEYWORD, SELECT> <IDENTIFIER, MY-FILE> <KEYWORD, ASSIGN> <KEYWORD, TO>
     | <STRING, "DADOS.TXT"> <PERIOD>
  19 | <KEYWORD, DATA> <KEYWORD, DIVISION> <PERIOD>
  20 | <KEYWORD, FILE> <KEYWORD, SECTION> <PERIOD>
  23 | <KEYWORD, FD> <IDENTIFIER, MY-FILE> <PERIOD>
  24 | <NUMBER, 01> <IDENTIFIER, RC-TRABALHADOR> <PERIOD>
  25 | <NUMBER, 02> <IDENTIFIER, RC-TID> <KEYWORD, PIC> <PICTURE, 9(5)> <PERIOD>
  26 | <NUMBER, 02> <IDENTIFIER, RC-NOME> <KEYWORD, PIC> <PICTURE, X(10)> <PERIOD>
  27 | <NUMBER, 02> <IDENTIFIER, RC-SALARIO> <KEYWORD, PIC> <PICTURE, 9(10)V99> <PERIOD>
  28 | <NUMBER, 02> <IDENTIFIER, RC-DPTO-1> <KEYWORD, PIC> <PICTURE, X(2)> <PERIOD>
  29 | <NUMBER, 02> <IDENTIFIER, RC-DPTO-2> <KEYWORD, PIC> <PICTURE, X(2)> <PERIOD>
  31 | <KEYWORD, WORKING-STORAGE> <KEYWORD, SECTION> <PERIOD>
  33 | <NUMBER, 01> <IDENTIFIER, TAB-TRABALHADOR> <PERIOD>
  34 | <NUMBER, 02> <IDENTIFIER, TRABALHADOR> <KEYWORD, OCCURS> <NUMBER, 3> <KEYWORD, TIMES>
     | <KEYWORD, INDEXED> <KEYWORD, BY> <IDENTIFIER, TID> <PERIOD>
  35 | <NUMBER, 03> <IDENTIFIER, NOME> <KEYWORD, PIC> <PICTURE, X(5)> <PERIOD>
  36 | <NUMBER, 03> <IDENTIFIER, SALARIO> <KEYWORD, PIC> <PICTURE, 9(5)V99> <PERIOD>
  37 | <NUMBER, 03> <IDENTIFIER, DPTO> <KEYWORD, PIC> <PICTURE, X(2)> <KEYWORD, VALUES>
     | <KEYWORD, SPACES> <KEYWORD, OCCURS> <NUMBER, 2> <KEYWORD, TIMES> <PERIOD>
  39 | <NUMBER, 77> <IDENTIFIER, SAUX> <KEYWORD, PIC> <PICTURE, X(15)> <PERIOD>
  40 | <NUMBER, 77> <IDENTIFIER, CONT> <KEYWORD, PIC> <PICTURE, 9(2)> <PERIOD>
  41 | <NUMBER, 77> <IDENTIFIER, YESNO> <KEYWORD, PIC> <PICTURE, 9> <PERIOD>
  43 | <NUMBER, 77> <IDENTIFIER, IDX> <KEYWORD, PIC> <PICTURE, 9(1)> <PERIOD>
  45 | <KEYWORD, PROCEDURE> <KEYWORD, DIVISION> <PERIOD>
  46 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  48 | <KEYWORD, MOVE> <STRING, "JOSEA1111111A1A4MARIA2222222A2  FABIO3333333A2A3">
     | <KEYWORD, TO> <IDENTIFIER, TAB-TRABALHADOR>
  49 | <PERIOD>
  51 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  52 | <KEYWORD, DISPLAY> <STRING, "====00001-DISPLAY-TRABALHADOR===="> <PERIOD>
  53 | <KEYWORD, OPEN> <KEYWORD, OUTPUT> <IDENTIFIER, MY-FILE> <PERIOD>
  55 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, IDX> <PERIOD>
  56 | <KEYWORD, PERFORM> <IDENTIFIER, 00001-WRITE-TO-FILE> <KEYWORD, UNTIL> <IDENTIFIER, IDX>
     | <GREATER_THAN> <NUMBER, 3> <PERIOD>
  58 | <KEYWORD, CLOSE> <IDENTIFIER, MY-FILE> <PERIOD>
  60 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
  62 | <IDENTIFIER, 00001-WRITE-TO-FILE> <PERIOD>
  63 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
  65 | <KEYWORD, MOVE> <KEYWORD, LOW-VALUES> <KEYWORD, TO> <IDENTIFIER, RC-TRABALHADOR> <PERIOD>
  66 | <KEYWORD, DISPLAY> <STRING, "IDX="> <IDENTIFIER, IDX> <PERIOD>
  67 | <KEYWORD, DISPLAY> <STRING, "TRABALHADOR(IDX)="> <IDENTIFIER, TRABALHADOR> <LPAREN>
     | <IDENTIFIER, IDX> <RPAREN> <PERIOD>
  68 | <KEYWORD, MOVE> <IDENTIFIER, IDX> <KEYWORD, TO> <IDENTIFIER, RC-TID> <PERIOD>
  69 | <KEYWORD, MOVE> <IDENTIFIER, NOME> <LPAREN> <IDENTIFIER, IDX> <RPAREN> <KEYWORD, TO>
     | <IDENTIFIER, RC-NOME> <PERIOD>
  70 | <KEYWORD, MOVE> <IDENTIFIER, SALARIO> <LPAREN> <IDENTIFIER, IDX> <RPAREN> <KEYWORD, TO>
     | <IDENTIFIER, RC-SALARIO> <PERIOD>
  71 | <KEYWORD, MOVE> <IDENTIFIER, DPTO> <LPAREN> <IDENTIFIER, IDX> <COMMA> <NUMBER, 1>
     | <RPAREN> <KEYWORD, TO> <IDENTIFIER, RC-DPTO-1> <PERIOD>
  72 | <KEYWORD, MOVE> <IDENTIFIER, DPTO> <LPAREN> <IDENTIFIER, IDX> <COMMA> <NUMBER, 2>
     | <RPAREN> <KEYWORD, TO> <IDENTIFIER, RC-DPTO-2> <PERIOD>
  73 | <KEYWORD, WRITE> <IDENTIFIER, RC-TRABALHADOR> <PERIOD>
  74 | <KEYWORD, ADD> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, IDX> <PERIOD>
  76 | <KEYWORD, END> <KEYWORD, PROGRAM> <IDENTIFIER, PROG006_FILES> <PERIOD>

225 tokens; 0 erros léxicos.
```

### 3.7 `prog007_loja.cob`

É o maior programa (566 tokens): arquivo indexado (`ORGANIZATION INDEXED`, `ACCESS MODE DYNAMIC`, `RECORD KEY IS`), a palavra reservada com hífen `I-O`, `EVALUATE ... WHEN OTHER`, `WITH NO ADVANCING` e `INVALID KEY`/`NOT INVALID KEY`. O bloco de comentários das linhas 36–44 contém expressões como `27998/64 => 437.4675`, que são descartadas sem gerar tokens.

```text
  11 | <KEYWORD, IDENTIFICATION> <KEYWORD, DIVISION> <PERIOD>
  12 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, PROG007_LOJA> <PERIOD>
  14 | <KEYWORD, ENVIRONMENT> <KEYWORD, DIVISION> <PERIOD>
  15 | <KEYWORD, INPUT-OUTPUT> <KEYWORD, SECTION> <PERIOD>
  17 | <KEYWORD, FILE-CONTROL> <PERIOD>
  18 | <KEYWORD, SELECT> <IDENTIFIER, FD-PRODUTOS> <KEYWORD, ASSIGN> <KEYWORD, TO>
     | <IDENTIFIER, WS-PROD-FILENAME>
  19 | <KEYWORD, ORGANIZATION> <KEYWORD, INDEXED>
  20 | <KEYWORD, ACCESS> <KEYWORD, MODE> <KEYWORD, DYNAMIC>
  21 | <KEYWORD, RECORD> <KEYWORD, KEY> <KEYWORD, IS> <IDENTIFIER, RP-PID>
  22 | <KEYWORD, ALTERNATE> <KEYWORD, RECORD> <KEYWORD, KEY> <KEYWORD, IS> <IDENTIFIER, RP-NOME>
  23 | <KEYWORD, FILE> <KEYWORD, STATUS> <IDENTIFIER, WS-FILE-STATUS-PROD> <PERIOD>
  26 | <KEYWORD, SELECT> <IDENTIFIER, FD-PRODUTOS-KEY> <KEYWORD, ASSIGN> <KEYWORD, TO>
     | <STRING, "PROG10-001.KEY">
  27 | <KEYWORD, FILE> <KEYWORD, STATUS> <IDENTIFIER, WS-FILE-STATUS-PROD-KEY> <PERIOD>
  29 | <KEYWORD, DATA> <KEYWORD, DIVISION> <PERIOD>
  30 | <KEYWORD, FILE> <KEYWORD, SECTION> <PERIOD>
  33 | <KEYWORD, FD> <IDENTIFIER, FD-PRODUTOS>
  34 | <KEYWORD, BLOCK> <KEYWORD, CONTAINS> <NUMBER, 874> <KEYWORD, RECORDS>
  35 | <KEYWORD, RECORD> <KEYWORD, CONTAINS> <NUMBER, 64> <KEYWORD, CHARACTERS> <PERIOD>
  46 | <NUMBER, 01> <IDENTIFIER, REG-PRODUTO> <PERIOD>
  47 | <NUMBER, 02> <IDENTIFIER, RP-PID> <KEYWORD, PIC> <PICTURE, 9(10)> <PERIOD>
  48 | <NUMBER, 02> <IDENTIFIER, RP-NOME> <KEYWORD, PIC> <PICTURE, X(10)> <PERIOD>
  49 | <NUMBER, 02> <IDENTIFIER, RP-VALOR> <KEYWORD, PIC> <PICTURE, 9(10)V9(02)> <PERIOD>
  50 | <NUMBER, 02> <IDENTIFIER, RP-QTD> <KEYWORD, PIC> <PICTURE, 9(10)V9(02)> <PERIOD>
  51 | <NUMBER, 02> <IDENTIFIER, RP-DESCRICAO> <KEYWORD, PIC> <PICTURE, X(20)> <PERIOD>
  54 | <KEYWORD, FD> <IDENTIFIER, FD-PRODUTOS-KEY> <PERIOD>
  55 | <NUMBER, 01> <IDENTIFIER, REGISTRO-CHAVE> <KEYWORD, PIC> <PICTURE, 9(10)> <PERIOD>
  59 | <KEYWORD, WORKING-STORAGE> <KEYWORD, SECTION> <PERIOD>
  62 | <NUMBER, 01> <IDENTIFIER, WS-PROD-FILENAME> <PERIOD>
  63 | <NUMBER, 02> <IDENTIFIER, NAME> <KEYWORD, PIC> <PICTURE, X(7)> <KEYWORD, VALUES>
     | <STRING, "PROG10-"> <PERIOD>
  64 | <NUMBER, 02> <IDENTIFIER, NUM> <KEYWORD, PIC> <PICTURE, 9(3)> <KEYWORD, VALUES>
     | <NUMBER, 1> <PERIOD>
  65 | <NUMBER, 02> <IDENTIFIER, EXT> <KEYWORD, PIC> <PICTURE, X(4)> <KEYWORD, VALUES>
     | <STRING, ".DAT"> <PERIOD>
  67 | <NUMBER, 77> <IDENTIFIER, WS-FILE-STATUS-PROD> <KEYWORD, PIC> <PICTURE, 9(02)> <PERIOD>
  68 | <NUMBER, 77> <IDENTIFIER, WS-FILE-STATUS-PROD-KEY> <KEYWORD, PIC> <PICTURE, 9(02)>
     | <PERIOD>
  70 | <NUMBER, 01> <IDENTIFIER, WS-PRODUTO> <PERIOD>
  71 | <NUMBER, 02> <IDENTIFIER, WS-PID> <KEYWORD, PIC> <PICTURE, 9(10)> <PERIOD>
  72 | <NUMBER, 02> <IDENTIFIER, WS-NOME> <KEYWORD, PIC> <PICTURE, X(10)> <PERIOD>
  73 | <NUMBER, 02> <IDENTIFIER, WS-VALOR> <KEYWORD, PIC> <PICTURE, 9(10)V9(02)> <PERIOD>
  74 | <NUMBER, 02> <IDENTIFIER, WS-QTD> <KEYWORD, PIC> <PICTURE, 9(10)V9(02)> <PERIOD>
  75 | <NUMBER, 02> <IDENTIFIER, WS-DESCRICAO> <KEYWORD, PIC> <PICTURE, X(20)> <PERIOD>
  78 | <NUMBER, 77> <IDENTIFIER, WS-OPCAO> <KEYWORD, PIC> <PICTURE, 9(01)> <PERIOD>
  79 | <NUMBER, 77> <IDENTIFIER, WS-ULTIMO-PID> <KEYWORD, PIC> <PICTURE, 9(10)> <PERIOD>
  80 | <NUMBER, 77> <IDENTIFIER, WS-EXIT> <KEYWORD, PIC> <PICTURE, 9(01)> <KEYWORD, VALUES>
     | <KEYWORD, ZERO> <PERIOD>
  84 | <KEYWORD, PROCEDURE> <KEYWORD, DIVISION> <PERIOD>
  85 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  87 | <KEYWORD, DISPLAY> <STRING, "PERFORM 00000-OPEN-FILE-PRODUTOS-KEY"> <PERIOD>
  88 | <KEYWORD, PERFORM> <IDENTIFIER, 00000-OPEN-FILE-PRODUTOS-KEY> <PERIOD>
  90 | <KEYWORD, IF> <IDENTIFIER, WS-EXIT> <EQUAL> <NUMBER, 0>
  91 | <KEYWORD, DISPLAY> <STRING, "PERFORM 00000-OPEN-FILE-PRODUTOS">
  92 | <KEYWORD, PERFORM> <IDENTIFIER, 00000-OPEN-FILE-PRODUTOS>
  93 | <KEYWORD, END-IF> <PERIOD>
  95 | <KEYWORD, PERFORM> <IDENTIFIER, 00001-MENU-OPCOES> <KEYWORD, UNTIL> <IDENTIFIER, WS-EXIT>
     | <EQUAL> <NUMBER, 1> <PERIOD>
  97 | <KEYWORD, WRITE> <IDENTIFIER, REGISTRO-CHAVE> <KEYWORD, FROM> <IDENTIFIER, WS-ULTIMO-PID>
     | <PERIOD>
  98 | <KEYWORD, CLOSE> <IDENTIFIER, FD-PRODUTOS-KEY> <PERIOD>
  99 | <KEYWORD, CLOSE> <IDENTIFIER, FD-PRODUTOS> <PERIOD>
 100 | <KEYWORD, DISPLAY> <STRING, "BYE">
 101 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
 103 | <IDENTIFIER, 00000-OPEN-FILE-PRODUTOS-KEY> <PERIOD>
 105 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WS-FILE-STATUS-PROD-KEY> <PERIOD>
 106 | <KEYWORD, OPEN> <KEYWORD, INPUT> <IDENTIFIER, FD-PRODUTOS-KEY> <PERIOD>
 107 | <KEYWORD, IF> <IDENTIFIER, WS-FILE-STATUS-PROD-KEY> <EQUAL> <NUMBER, 0>
 108 | <KEYWORD, DISPLAY> <STRING, "-- PROG10-001.KEY FOUND">
 109 | <KEYWORD, READ> <IDENTIFIER, FD-PRODUTOS-KEY> <KEYWORD, INTO> <IDENTIFIER, WS-ULTIMO-PID>
 110 | <KEYWORD, ELSE>
 111 | <KEYWORD, IF> <IDENTIFIER, WS-FILE-STATUS-PROD-KEY> <EQUAL> <NUMBER, 35>
 112 | <KEYWORD, DISPLAY> <STRING, "-- PROG10-001.KEY NOT FOUND - CREATING NEW">
 113 | <KEYWORD, OPEN> <KEYWORD, OUTPUT> <IDENTIFIER, FD-PRODUTOS-KEY>
 114 | <KEYWORD, IF> <IDENTIFIER, WS-FILE-STATUS-PROD-KEY> <EQUAL> <NUMBER, 0>
 115 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WS-ULTIMO-PID>
 116 | <KEYWORD, ELSE>
 117 | <KEYWORD, DISPLAY> <STRING, "-- ERRO AO CRIAR ARQUIVO DE CHAVES -->">
 118 | <IDENTIFIER, WS-FILE-STATUS-PROD-KEY>
 119 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-EXIT>
 120 | <KEYWORD, ELSE>
 121 | <KEYWORD, DISPLAY> <STRING, "-- ERRO AO ABRIR ARQUIVO DE CHAVES -->">
 122 | <IDENTIFIER, WS-FILE-STATUS-PROD-KEY>
 123 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-EXIT> <PERIOD>
 125 | <IDENTIFIER, 00000-OPEN-FILE-PRODUTOS> <PERIOD>
 126 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WS-FILE-STATUS-PROD> <PERIOD>
 127 | <KEYWORD, OPEN> <KEYWORD, I-O> <IDENTIFIER, FD-PRODUTOS> <PERIOD>
 129 | <KEYWORD, IF> <IDENTIFIER, WS-FILE-STATUS-PROD> <EQUAL> <NUMBER, 35>
 130 | <KEYWORD, DISPLAY> <STRING, "-- PROG10-001.DAT NOT FOUND - CREATING NEW">
 131 | <KEYWORD, OPEN> <KEYWORD, OUTPUT> <IDENTIFIER, FD-PRODUTOS>
 132 | <KEYWORD, IF> <IDENTIFIER, WS-FILE-STATUS-PROD> <EQUAL> <NUMBER, 0>
 133 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WS-ULTIMO-PID>
 134 | <KEYWORD, ELSE>
 135 | <KEYWORD, DISPLAY> <STRING, "-- ERRO AO CRIAR ARQUIVO DE DADOS -->">
 136 | <IDENTIFIER, WS-FILE-STATUS-PROD>
 137 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-EXIT>
 138 | <KEYWORD, ELSE>
 139 | <KEYWORD, IF> <IDENTIFIER, WS-FILE-STATUS-PROD> <EQUAL> <NUMBER, 0>
 140 | <KEYWORD, DISPLAY> <STRING, "-- PROG10-001.DAT FOUND">
 141 | <KEYWORD, IF> <IDENTIFIER, WS-ULTIMO-PID> <EQUAL> <NUMBER, 0>
 142 | <KEYWORD, MOVE> <NUMBER, 0> <KEYWORD, TO> <IDENTIFIER, WS-ULTIMO-PID>
 143 | <KEYWORD, ELSE>
 144 | <KEYWORD, MOVE> <IDENTIFIER, WS-ULTIMO-PID> <KEYWORD, TO> <IDENTIFIER, RP-PID>
 146 | <KEYWORD, START> <IDENTIFIER, FD-PRODUTOS> <KEYWORD, KEY> <KEYWORD, EQUAL>
     | <IDENTIFIER, RP-PID>
 147 | <KEYWORD, INVALID> <KEYWORD, KEY>
 148 | <KEYWORD, DISPLAY> <STRING, "ERRO AO REGISTRO">
 149 | <KEYWORD, ELSE>
 150 | <KEYWORD, DISPLAY> <STRING, "-- ERRO AO ABRIR ARQUIVO DE PRODUTOS">
 151 | <IDENTIFIER, WS-FILE-STATUS-PROD>
 152 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-EXIT> <PERIOD>
 155 | <IDENTIFIER, 00001-MENU-OPCOES> <PERIOD>
 156 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
 157 | <KEYWORD, DISPLAY> <STRING, "====00001-MENU-OPCOES===="> <PERIOD>
 158 | <KEYWORD, DISPLAY> <STRING, "OPCOES:"> <PERIOD>
 159 | <KEYWORD, DISPLAY> <STRING, "1) ADICIONA PRODUTO"> <PERIOD>
 160 | <KEYWORD, DISPLAY> <STRING, "2) REMOVE PRODUTO - NOT IMPLEMENTED"> <PERIOD>
 161 | <KEYWORD, DISPLAY> <STRING, "3) ATUALIZA PRODUTO - NOT IMPLEMENTED"> <PERIOD>
 162 | <KEYWORD, DISPLAY> <STRING, "4) CONSULTA PRODUTO"> <PERIOD>
 163 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
 164 | <KEYWORD, DISPLAY> <STRING, "5) SAIR DO PROGRAMA"> <PERIOD>
 165 | <KEYWORD, ACCEPT> <IDENTIFIER, WS-OPCAO> <PERIOD>
 167 | <KEYWORD, EVALUATE> <IDENTIFIER, WS-OPCAO>
 168 | <KEYWORD, WHEN> <NUMBER, 1> <KEYWORD, PERFORM> <IDENTIFIER, 00002-CREATE-PRODUTO>
 169 | <KEYWORD, WHEN> <NUMBER, 2>
 170 | <KEYWORD, DISPLAY> <STRING, "DELETE">
 171 | <KEYWORD, WHEN> <NUMBER, 3>
 172 | <KEYWORD, DISPLAY> <STRING, "UPDATE">
 173 | <KEYWORD, WHEN> <NUMBER, 4> <KEYWORD, PERFORM> <IDENTIFIER, 00002-SELECT-PRODUTO>
 174 | <KEYWORD, WHEN> <NUMBER, 5>
 175 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-EXIT>
 176 | <KEYWORD, WHEN> <KEYWORD, OTHER>
 177 | <KEYWORD, DISPLAY> <STRING, "OPCAO INVALIDA.">
 178 | <KEYWORD, END-EVALUATE> <PERIOD>
 180 | <IDENTIFIER, 00002-CREATE-PRODUTO> <PERIOD>
 181 | <KEYWORD, DISPLAY> <STRING, "CRIA UM NOVO PRODUTO"> <PERIOD>
 182 | <KEYWORD, DISPLAY> <STRING, "NOME: "> <KEYWORD, WITH> <KEYWORD, NO> <KEYWORD, ADVANCING>
     | <PERIOD>
 183 | <KEYWORD, ACCEPT> <IDENTIFIER, WS-NOME> <PERIOD>
 184 | <KEYWORD, DISPLAY> <STRING, "VALOR: "> <KEYWORD, WITH> <KEYWORD, NO> <KEYWORD, ADVANCING>
     | <PERIOD>
 185 | <KEYWORD, ACCEPT> <IDENTIFIER, WS-VALOR> <PERIOD>
 186 | <KEYWORD, DISPLAY> <STRING, "QUANTIDADE: "> <KEYWORD, WITH> <KEYWORD, NO>
     | <KEYWORD, ADVANCING> <PERIOD>
 187 | <KEYWORD, ACCEPT> <IDENTIFIER, WS-QTD> <PERIOD>
 188 | <KEYWORD, DISPLAY> <STRING, "DESCRICAO: "> <KEYWORD, WITH> <KEYWORD, NO>
     | <KEYWORD, ADVANCING> <PERIOD>
 189 | <KEYWORD, ACCEPT> <IDENTIFIER, WS-DESCRICAO> <PERIOD>
 191 | <KEYWORD, ADD> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-ULTIMO-PID> <PERIOD>
 192 | <KEYWORD, MOVE> <IDENTIFIER, WS-ULTIMO-PID> <KEYWORD, TO> <IDENTIFIER, WS-PID> <PERIOD>
 194 | <KEYWORD, DISPLAY> <STRING, "--------------">
 195 | <KEYWORD, DISPLAY> <IDENTIFIER, WS-PRODUTO> <PERIOD>
 196 | <KEYWORD, DISPLAY> <STRING, "--------------">
 198 | <KEYWORD, WRITE> <IDENTIFIER, REG-PRODUTO> <KEYWORD, FROM> <IDENTIFIER, WS-PRODUTO>
 199 | <KEYWORD, INVALID> <KEYWORD, KEY>
 200 | <KEYWORD, DISPLAY> <STRING, "CODIGO DE PRODUTO JAH EXISTE"> <IDENTIFIER, WS-ULTIMO-PID>
 201 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-EXIT>
 202 | <KEYWORD, NOT> <KEYWORD, INVALID> <KEYWORD, KEY>
 203 | <KEYWORD, DISPLAY> <STRING, "PRODUTO ARMAZENADO"> <PERIOD>
 205 | <IDENTIFIER, 00002-SELECT-PRODUTO> <PERIOD>
 206 | <KEYWORD, DISPLAY> <STRING, "CONSULTA PRODUTO"> <PERIOD>
 207 | <KEYWORD, DISPLAY> <STRING, "WS-ULTIMO-PID --> "> <IDENTIFIER, WS-ULTIMO-PID> <PERIOD>
 208 | <KEYWORD, DISPLAY> <STRING, "PID: "> <PERIOD>
 209 | <KEYWORD, ACCEPT> <IDENTIFIER, WS-PID> <PERIOD>
 211 | <KEYWORD, MOVE> <IDENTIFIER, WS-PID> <KEYWORD, TO> <IDENTIFIER, RP-PID> <PERIOD>
 213 | <KEYWORD, READ> <IDENTIFIER, FD-PRODUTOS> <KEYWORD, RECORD> <KEYWORD, KEY>
     | <IDENTIFIER, RP-PID>
 214 | <KEYWORD, INVALID> <KEYWORD, KEY>
 215 | <KEYWORD, DISPLAY> <STRING, "ERRO AO LOCALIZAR REGISTRO">
 216 | <KEYWORD, NOT> <KEYWORD, INVALID> <KEYWORD, KEY>
 217 | <KEYWORD, MOVE> <IDENTIFIER, REG-PRODUTO> <KEYWORD, TO> <IDENTIFIER, WS-PRODUTO>
 218 | <KEYWORD, DISPLAY> <STRING, " ">
 219 | <KEYWORD, DISPLAY> <STRING, "NOME: "> <KEYWORD, WITH> <KEYWORD, NO> <KEYWORD, ADVANCING>
 220 | <KEYWORD, DISPLAY> <IDENTIFIER, WS-NOME>
 221 | <KEYWORD, DISPLAY> <STRING, "VALOR: "> <KEYWORD, WITH> <KEYWORD, NO> <KEYWORD, ADVANCING>
 222 | <KEYWORD, DISPLAY> <IDENTIFIER, WS-VALOR>
 223 | <KEYWORD, DISPLAY> <STRING, "QUANTIDADE: "> <KEYWORD, WITH> <KEYWORD, NO>
     | <KEYWORD, ADVANCING>
 224 | <KEYWORD, DISPLAY> <IDENTIFIER, WS-QTD>
 225 | <KEYWORD, DISPLAY> <STRING, "DESCRICAO: "> <KEYWORD, WITH> <KEYWORD, NO>
     | <KEYWORD, ADVANCING>
 226 | <KEYWORD, DISPLAY> <IDENTIFIER, WS-DESCRICAO> <PERIOD>
 228 | <KEYWORD, END> <KEYWORD, PROGRAM> <IDENTIFIER, PROG007_LOJA> <PERIOD>

566 tokens; 0 erros léxicos.
```

---

## 4. Resultados de erros

### 4.1 Estratégia de tratamento de erros

O lexer **não interrompe a análise no primeiro erro**. Cada erro gera um diagnóstico com código, mensagem, linha e coluna físicas, e a varredura continua. É uma recuperação em **modo pânico**: descartamos a menor unidade que contém o erro e retomamos a análise no ponto seguinte. A unidade descartada depende do erro:

| Código | Condição | Unidade descartada / recuperação |
| --- | --- | --- |
| `INVALID_CHARACTER` | Caractere fora do alfabeto da linguagem | O caractere; a análise continua no seguinte |
| `INVALID_IDENTIFIER` | Palavra que começa ou termina com hífen ou underscore | A palavra inteira |
| `IDENTIFIER_TOO_LONG` | Palavra com mais de 30 caracteres | A palavra inteira |
| `INVALID_WORD` | Número com sinal colado a letras (`+12AB`) | A palavra inteira |
| `INVALID_PICTURE` | Máscara com símbolo inválido, parênteses desbalanceados ou repetição nula | A máscara; o ponto final continua sendo emitido |
| `UNTERMINATED_STRING` | Aspa aberta sem fechamento nem continuação | Do início do literal até o fim da linha lógica |
| `TAB_IN_SOURCE` | TAB nas colunas 1–72 de uma linha analisada | A linha física inteira |
| `INVALID_INDICATOR` | Caractere desconhecido na coluna 7 | A linha física inteira |
| `UNEXPECTED_CONTINUATION` | `-` na coluna 7 sem linha de código anterior | A linha física inteira |

Os diagnósticos são ordenados por posição. Quando há erro, a CLI termina com código de saída 1, para que um script ou o futuro parser possa detectar a falha. TAB e indicador inválido descartam a linha toda porque, nesses casos, as colunas deixam de ser confiáveis: a largura de um TAB depende do editor, e um indicador errado geralmente significa código deslocado.

### 4.2 Erros inseridos

Inserimos **15 erros** em cópias dos sete programas de teste, salvas em `examples/erros/` com o sufixo `_erros.cob`. Cada alteração substitui uma linha, de modo que a numeração continua igual à do original. Os erros imitam enganos plausíveis: TAB do editor, aspas tipográficas coladas de um processador de texto, acentos, sintaxe de outras linguagens (`!=`, `[ ]`) e a letra `O` no lugar do zero. O teste `test_error_examples_report_every_inserted_error` confere código, linha e coluna de cada diagnóstico.

| # | Arquivo : linha | Erro inserido | Diagnóstico (linha:coluna) |
| ---: | --- | --- | --- |
| 1 | `prog001_divisoes_erros` : 55 | Indentação com TAB | `TAB_IN_SOURCE` (55:1) |
| 2 | `prog001_divisoes_erros` : 56 | Aspa de fechamento removida | `UNTERMINATED_STRING` (56:21) |
| 3 | `prog002_operacoes_erros` : 25 | `PROCEDURE DIVISION` deslocada para a coluna 7 | `INVALID_INDICATOR` (25:7) |
| 4 | `prog002_operacoes_erros` : 28 | `+2O` (letra O no lugar do zero) | `INVALID_WORD` (28:17) |
| 5 | `prog003_calculadora_erros` : 36 | Operador `!=` de C/Java | `INVALID_CHARACTER` (36:24) |
| 6 | `prog003_calculadora_erros` : 70 | Subtração sem espaço: `WKS-NUM-1- WKS-NUM-2` | `INVALID_IDENTIFIER` (70:39) |
| 7 | `prog004_folha_pgto_erros` : 19 | Parêntese não fechado: `PIC X(5.` | `INVALID_PICTURE` (19:37) |
| 8 | `prog004_folha_pgto_erros` : 20 | Acento em identificador: `SALÁRIO` | `INVALID_CHARACTER` (20:20) |
| 9 | `prog004_folha_pgto_erros` : 53 | Subscrito com colchetes: `TRABALHADOR[IDX]` | `INVALID_CHARACTER` (53:51) e (53:55) |
| 10 | `prog005_strings_erros` : 11 | `-` na coluna 7 da primeira linha de código | `UNEXPECTED_CONTINUATION` (11:7) |
| 11 | `prog005_strings_erros` : 25 | Aspas trocadas: abre com `"` e fecha com `'` | `UNTERMINATED_STRING` (25:18) |
| 12 | `prog006_files_erros` : 17 | Aspas tipográficas `“DADOS.TXT”` | `INVALID_CHARACTER` (17:37) e (17:47) |
| 13 | `prog006_files_erros` : 39 | Identificador com 34 caracteres | `IDENTIFIER_TOO_LONG` (39:11) |
| 14 | `prog007_loja_erros` : 49 | Repetição nula na máscara: `9(10)V9(0)` | `INVALID_PICTURE` (49:38) |
| 15 | `prog007_loja_erros` : 117–118 | String quebrada em duas linhas sem `-` na coluna 7 | `UNTERMINATED_STRING` (117:26) e (118:39) |

Os 15 erros produzem **18 diagnósticos**: os erros 9, 12 e 15 geram dois cada. Todos os nove códigos de erro do lexer aparecem. As saídas abaixo foram obtidas com `python -m cobol_lexer examples/erros/<arquivo> --stream`; em todos os casos, o código de saída foi 1.

### 4.3 `prog001_divisoes_erros.cob` — erros 1 e 2

```diff
-            DISPLAY "Hello world"
-            display "Enio Basso - 2"
+⇥⇥DISPLAY "Hello world"
+            display "Enio Basso - 2
```

(`⇥` representa um caractere TAB.)

```text
  54 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  55 | ERRO 55:1 TAB_IN_SOURCE: TAB não permitido em formato fixo; use espaços.
  56 | <KEYWORD, display>
     | ERRO 56:21 UNTERMINATED_STRING: Literal não terminado; a continuação exige '-' na coluna 7.
  57 | <KEYWORD, STOP> <KEYWORD, RUN> <PERIOD>
```

- **Erro 1 — `TAB_IN_SOURCE`.** No formato fixo, a posição de cada caractere define seu papel, e um TAB pode valer de 1 a 8 colunas conforme o editor. Em vez de adivinhar a largura, o lexer rejeita a linha 55 inteira e informa a coluna do primeiro TAB. Os tokens dessa linha (`DISPLAY "Hello world"`) não são emitidos.
- **Erro 2 — `UNTERMINATED_STRING`.** O literal aberto na coluna 21 chega ao fim da linha sem aspa de fechamento e sem continuação na linha seguinte. O lexer descarta o literal e retoma na linha 57, que é analisada normalmente (`STOP RUN.`).

### 4.4 `prog002_operacoes_erros.cob` — erros 3 e 4

```text
         1111111111222
1234567890123456789012     ← colunas
       PROCEDURE DIVISION. ← original: "P" na coluna 8 (área A)
      PROCEDURE DIVISION.  ← alterado: "P" na coluna 7 (indicador)
```

```diff
-           MOVE 20 TO WRK-VALOR2.
+           MOVE +2O TO WRK-VALOR2.
```

```text
  25 | ERRO 25:7 INVALID_INDICATOR: Indicador 'P' desconhecido na coluna 7.
  26 | <IDENTIFIER, MAIN-PROCEDURE> <PERIOD>
  27 | <KEYWORD, DISPLAY> <STRING, "===== start ======="> <PERIOD>
  28 | <KEYWORD, MOVE> <KEYWORD, TO> <IDENTIFIER, WRK-VALOR2> <PERIOD>
     | ERRO 28:17 INVALID_WORD: Palavra inválida: '+2O'.
```

- **Erro 3 — `INVALID_INDICATOR`.** Com o código deslocado uma coluna para a esquerda, o `P` de `PROCEDURE` cai na coluna 7, que só aceita espaço, `*`, `/`, `-` ou `D`. A linha é descartada, e por isso `PROCEDURE DIVISION.` não aparece no fluxo. O parser vai notar a ausência da divisão.
- **Erro 4 — `INVALID_WORD`.** `+2` seria um número com sinal, mas vem colado à letra `O`. O lexer não separa silenciosamente `+2` de `O`: descarta a palavra inteira `+2O` e continua com `TO WRK-VALOR2.`.

### 4.5 `prog003_calculadora_erros.cob` — erros 5 e 6

```diff
-           IF WKS-SAIR = 1
+           IF WKS-SAIR != 1
-              COMPUTE WKS-RESULTADO = WKS-NUM-1 ** WKS-NUM-2
+              COMPUTE WKS-RESULTADO = WKS-NUM-1- WKS-NUM-2
```

```text
  36 | <KEYWORD, IF> <IDENTIFIER, WKS-SAIR> <EQUAL> <NUMBER, 1>
     | ERRO 36:24 INVALID_CHARACTER: Caractere '!' não reconhecido.
  37 | <KEYWORD, PERFORM> <IDENTIFIER, 00001-PEDIR-DADOS>
  70 | <KEYWORD, COMPUTE> <IDENTIFIER, WKS-RESULTADO> <EQUAL> <IDENTIFIER, WKS-NUM-2>
     | ERRO 70:39 INVALID_IDENTIFIER: Identificador não pode iniciar/terminar com hífen ou underscore: 'WKS-NUM-1-'.
```

- **Erro 5 — `INVALID_CHARACTER`.** `!` não pertence ao alfabeto do COBOL; a desigualdade se escreve `<>` ou `NOT =`. O lexer descarta só o `!` e reconhece o `=` seguinte como `EQUAL`. O fluxo restante (`IF WKS-SAIR = 1`) fica sintaticamente válido, mas com o sentido oposto ao pretendido, e por isso o diagnóstico é indispensável.
- **Erro 6 — `INVALID_IDENTIFIER`.** Como o hífen pode fazer parte de nomes, `WKS-NUM-1-` é lido como uma única palavra, e uma palavra não pode terminar com hífen. O lexer descarta a palavra e continua com `WKS-NUM-2`. Se o programador tivesse escrito `WKS-NUM-1-WKS-NUM-2`, sem espaço algum, o resultado seria um identificador válido (veja a seção 4.10).

### 4.6 `prog004_folha_pgto_erros.cob` — erros 7, 8 e 9

```diff
-             03 NOME            PIC X(5).
-             03 SALARIO         PIC 9(5)V99.
+             03 NOME            PIC X(5.
+             03 SALÁRIO         PIC 9(5)V99.
-           DISPLAY "TRABALHADOR(IDX)=" TRABALHADOR(IDX).
+           DISPLAY "TRABALHADOR(IDX)=" TRABALHADOR[IDX].
```

```text
  19 | <NUMBER, 03> <IDENTIFIER, NOME> <KEYWORD, PIC> <PERIOD>
     | ERRO 19:37 INVALID_PICTURE: Máscara PIC inválida: 'X(5'.
  20 | <NUMBER, 03> <IDENTIFIER, SAL> <IDENTIFIER, RIO> <KEYWORD, PIC> <PICTURE, 9(5)V99>
     | <PERIOD>
     | ERRO 20:20 INVALID_CHARACTER: Caractere 'Á' não reconhecido.
  53 | <KEYWORD, DISPLAY> <STRING, "TRABALHADOR(IDX)="> <IDENTIFIER, TRABALHADOR>
     | <IDENTIFIER, IDX> <PERIOD>
     | ERRO 53:51 INVALID_CHARACTER: Caractere '[' não reconhecido.
     | ERRO 53:55 INVALID_CHARACTER: Caractere ']' não reconhecido.
```

- **Erro 7 — `INVALID_PICTURE`.** Depois de `PIC`, o lexer lê `X(5`, retira o ponto final e não encontra o fecho da repetição. A máscara é descartada, mas o `PERIOD` continua sendo emitido, preservando o fim da declaração para o parser.
- **Erro 8 — `INVALID_CHARACTER`.** O alfabeto de identificadores é ASCII, e `Á` gera erro. Como a recuperação descarta apenas o caractere, sobram dois identificadores espúrios, `SAL` e `RIO`. Esta é uma limitação da estratégia: uma alternativa seria descartar a palavra inteira quando o caractere inválido estiver entre letras.
- **Erro 9 — `INVALID_CHARACTER` (×2).** Colchetes não existem em COBOL; subscritos usam parênteses. Cada colchete gera um diagnóstico, e o identificador `IDX` entre eles é preservado.

### 4.7 `prog005_strings_erros.cob` — erros 10 e 11

```text
1234567890123456789
       IDENTIFICATION DIVISION.  ← original
      -IDENTIFICATION DIVISION.  ← alterado: "-" na coluna 7
```

```diff
-            MOVE "HELLO WORLD 123!!" TO SAUX.
+            MOVE "HELLO WORLD 123!!' TO SAUX.
```

```text
  11 | ERRO 11:7 UNEXPECTED_CONTINUATION: Continuação sem linha de código anterior.
  12 | <KEYWORD, PROGRAM-ID> <PERIOD> <IDENTIFIER, PROG008_STRING> <PERIOD>
  25 | <KEYWORD, MOVE>
     | ERRO 25:18 UNTERMINATED_STRING: Literal não terminado; a continuação exige '-' na coluna 7.
  27 | <KEYWORD, DISPLAY> <STRING, " "> <PERIOD>
```

- **Erro 10 — `UNEXPECTED_CONTINUATION`.** As linhas 1 a 10 são comentários. Portanto, a linha 11 é a primeira linha de código e não há o que continuar. A linha é descartada, e a análise segue normalmente a partir de `PROGRAM-ID` na linha 12.
- **Erro 11 — `UNTERMINATED_STRING`.** O literal abre com aspa dupla, e a aspa simples no fim não o fecha. O literal consome o resto da linha, inclusive `TO SAUX.`, que se perde. A análise volta ao normal na linha 27. Esse é o custo de recuperar no fim da linha lógica: o que vem depois da aspa aberta na mesma linha não pode ser recuperado com segurança.

### 4.8 `prog006_files_erros.cob` — erros 12 e 13

```diff
-           SELECT MY-FILE ASSIGN TO "DADOS.TXT".
+           SELECT MY-FILE ASSIGN TO “DADOS.TXT”.
-       77 SAUX            PIC X(15).
+       77 SAUX-AUXILIAR-PARA-MANIPULAR-TEXTO PIC X(15).
```

```text
  17 | <KEYWORD, SELECT> <IDENTIFIER, MY-FILE> <KEYWORD, ASSIGN> <KEYWORD, TO>
     | <IDENTIFIER, DADOS> <PERIOD> <IDENTIFIER, TXT> <PERIOD>
     | ERRO 17:37 INVALID_CHARACTER: Caractere '“' não reconhecido.
     | ERRO 17:47 INVALID_CHARACTER: Caractere '”' não reconhecido.
  39 | <NUMBER, 77> <KEYWORD, PIC> <PICTURE, X(15)> <PERIOD>
     | ERRO 39:11 IDENTIFIER_TOO_LONG: Identificador contém 34 caracteres (máximo 30).
```

- **Erro 12 — `INVALID_CHARACTER` (×2).** Aspas tipográficas (`“` e `”`, U+201C e U+201D) aparecem quando se copia código de um processador de texto ou de uma página web. Como não são delimitadores de string, o conteúdo `DADOS.TXT` é tokenizado como código (`DADOS`, `.`, `TXT`). O diagnóstico aponta a coluna exata de cada aspa.
- **Erro 13 — `IDENTIFIER_TOO_LONG`.** O nome tem 34 caracteres, e o limite é 30. Truncar o nome poderia criar colisões silenciosas com outro identificador, por isso a palavra inteira é descartada. O restante da declaração (`77 PIC X(15).`) continua sendo emitido.

### 4.9 `prog007_loja_erros.cob` — erros 14 e 15

```diff
-           02 RP-VALOR           PIC 9(10)V9(02).
+           02 RP-VALOR           PIC 9(10)V9(0).
-                 DISPLAY "-- ERRO AO CRIAR ARQUIVO DE CHAVES -->"
-                         WS-FILE-STATUS-PROD-KEY
+                 DISPLAY "-- ERRO AO CRIAR ARQUIVO
+                         DE CHAVES -->" WS-FILE-STATUS-PROD-KEY
```

```text
  49 | <NUMBER, 02> <IDENTIFIER, RP-VALOR> <KEYWORD, PIC> <PERIOD>
     | ERRO 49:38 INVALID_PICTURE: Máscara PIC inválida: '9(10)V9(0)'.
 116 | <KEYWORD, ELSE>
 117 | <KEYWORD, DISPLAY>
     | ERRO 117:26 UNTERMINATED_STRING: Literal não terminado; a continuação exige '-' na coluna 7.
 118 | <IDENTIFIER, DE> <IDENTIFIER, CHAVES> <MINUS> <MINUS> <GREATER_THAN>
     | ERRO 118:39 UNTERMINATED_STRING: Literal não terminado; a continuação exige '-' na coluna 7.
 119 | <KEYWORD, MOVE> <NUMBER, 1> <KEYWORD, TO> <IDENTIFIER, WS-EXIT>
```

- **Erro 14 — `INVALID_PICTURE`.** A máscara tem símbolos válidos, mas a repetição `(0)` é nula. O lexer exige repetições positivas (zeros à esquerda, como em `(02)`, são aceitos).
- **Erro 15 — `UNTERMINATED_STRING` (×2): erro em cascata.** O programador quebrou o literal em duas linhas sem marcar a continuação com `-` na coluna 7. A linha 117 termina com a string aberta e gera o primeiro diagnóstico. A linha 118 é lida como código novo: `DE` e `CHAVES` viram identificadores, `-->` vira `MINUS MINUS GREATER_THAN`, e a aspa de fechamento original passa a *abrir* um novo literal, que também não termina. Um único engano gera dois diagnósticos e cinco tokens espúrios. A partir da linha 119, a análise está ressincronizada.

### 4.10 Erros que o analisador léxico não detecta

Alguns enganos produzem uma sequência de tokens lexicamente válida e só podem ser detectados nas fases seguintes. Conferimos o comportamento do lexer nestes casos:

| Entrada | Tokens produzidos | Quem deve detectar |
| --- | --- | --- |
| Continuação de `T` / `AB-TRABALHADOR` sem o `-` na coluna 7 | `<IDENTIFIER, T>` e `<IDENTIFIER, AB-TRABALHADOR>` | Parser e análise semântica (nomes não declarados) |
| Comentário com `*` na coluna 8 em vez da 7 | `<MULTIPLY>` seguido das palavras do comentário como identificadores | Parser |
| `data division.` deslocada para a coluna 7 | Nenhum: o `d` torna a linha uma linha de depuração, ignorada por padrão | Parser (divisão ausente) |
| Código que ultrapassa a coluna 72 | Texto a partir da coluna 73 descartado; `WRK-VALOR2` vira `<IDENTIFIER, W>` | Análise semântica |
| `COMPUTE WRK-C = WRK-A-WRK-B.` sem espaços | `<IDENTIFIER, WRK-A-WRK-B>` (um único nome, como manda a linguagem) | Análise semântica (nome não declarado) |

Uma melhoria possível seria emitir **avisos** (sem interromper a análise) para os casos mais suspeitos, como uma linha `D` cujo conteúdo começa com uma palavra reservada ou um token cortado exatamente na coluna 72.

---

## 5. Considerações finais

O lexer reconhece os sete programas de teste sem erros e trata os 15 erros inseridos com diagnósticos posicionados e recuperação local. A principal dificuldade não foi reconhecer os tokens em si, mas lidar com o que é próprio do COBOL: a semântica das colunas, os tokens divididos entre linhas, o hífen e o ponto ambíguos e o contexto exigido pelas máscaras `PICTURE`. Separar a leitura do formato fixo do reconhecimento dos tokens, com um mapa de posições entre as duas fases, deixou cada parte simples de testar.

Ficam para as próximas etapas: o parser, que validará a estrutura das divisões e as regras de área A/B; o tratamento de *comment-entries*; a expansão de `COPY`; e o suporte ao formato livre.

## Referências

- BASSO, E. *cobol-exemplos*. GitHub, 2018. Disponível em: <https://github.com/ebasso/cobol-exemplos>.
- GNUCOBOL. *GnuCOBOL Programmer's Guide*. Disponível em: <https://gnucobol.sourceforge.io/HTML/gnucobpg.html>.
