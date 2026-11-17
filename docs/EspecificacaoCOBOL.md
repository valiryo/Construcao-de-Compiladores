# ESPECIFICAÇÃO TEXTUAL DO COMPILADOR COBOL (COBOL Compiler Specification)

## Arquitetura de Referência e Passos de Compilação

---

## 1. INTRODUÇÃO E OBJETIVO

Esta especificação define os requisitos textuais, gramaticais e estruturais para o desenvolvimento ou conformidade de um **Compilador COBOL** (Common Business-Oriented Language). O objetivo deste documento é mapear os componentes do pipeline de compilação, desde a leitura do código-fonte estruturado em colunas até a geração do código objeto executável ou código intermediário (como C ou Java).

---

## 2. ANÁLISE LÉXICA (LEXER)

O analisador léxico deve converter o fluxo de caracteres de entrada em um fluxo de tokens válidos, respeitando estritamente o formato de referência de colunas tradicional do COBOL (Fixed Format):

### 2.1 Estrutura de Colunas (Layout da Linha)

- **Colunas 1-6:** Indicador de Sequência (Sequence Number Area) — Ignorado ou usado para ordenação.
- **Coluna 7:** Indicador de Indicador (Indicator Area):
  - `*` ou `/`: Linha de comentário.
  - `-`: Continuação de literal string da linha anterior.
  - `D`: Linha de depuração (debugging line).
- **Colunas 8-11:** Área A (Área de início de divisões, seções, parágrafos e níveis lógicos de dados como `01` e `77`).
- **Colunas 12-72:** Área B (Área de comandos, frases, cláusulas e níveis de dados superiores).
- **Colunas 73-80:** Área do Programa (Program Name/Sequence Area) — Desprezada pelo compilador.

### 2.2 Tabela de Tokens (Categorias)

- **Palavras-Chave Reservadas:** `IDENTIFICATION`, `ENVIRONMENT`, `DATA`, `PROCEDURE`, `DIVISION`, `SECTION`, `DISPLAY`, `ACCEPT`, `PERFORM`, `STOP`, `RUN`, `IF`, `ELSE`, `MOVE`.
- **Literais:**
  - *Numéricos:* Cadeias de dígitos opcionalmente precedidas por sinal (`+` ou `-`) e com ponto decimal interno (ex.: `-123.45`).
  - *Alfanuméricos:* Strings delimitadas por aspas simples (`'`) ou duplas (`"`).
- **Identificadores (User-Defined Words):** Nomes de variáveis ou parágrafos (até 30 caracteres, contendo `A-Z`, `0-9` e hífen `-`, não podendo iniciar nem terminar com hífen).
- **Símbolos Especiais / Pontuação:** `.`, `,`, `;`, `(`, `)`. *Nota: O ponto final (`.`) é um token crítico que encerra sentenças e parágrafos.*

---

## 3. ANÁLISE SINTÁTICA (PARSER)

O analisador sintático valida a hierarquia de quatro divisões obrigatórias da linguagem. A gramática formal deve seguir estritamente esta ordem de derivação:

```ebnf
<Program> ::= <IdentificationDivision> [<EnvironmentDivision>] [<DataDivision>] <ProcedureDivision>
```

### 3.1 IDENTIFICATION DIVISION (Obrigatória)

- Define a identidade do programa.
- **Sintaxe Básica:**

```cobol
IDENTIFICATION DIVISION.
PROGRAM-ID. [NomeDoPrograma].
```

### 3.2 ENVIRONMENT DIVISION (Opcional / Reconfigurável)

- Mapeia o ambiente físico do hardware e os arquivos lógicos.
- **Sintaxe Básica:**

```cobol
ENVIRONMENT DIVISION.
CONFIGURATION SECTION.
    SOURCE-COMPUTER. [Nome].
    OBJECT-COMPUTER. [Nome].
INPUT-OUTPUT SECTION.
    FILE-CONTROL.
        SELECT [NomeArquivo] ASSIGN TO [DestinoFisico].
```

### 3.3 DATA DIVISION (Opcional / Estrutural)

- Declaração de todas as variáveis, registros de arquivos e estruturas de memória.
- **Níveis de Estrutura:**
  - `01`: Registro principal ou variável de grupo.
  - `02-49`: Subcampos subordinados (variáveis elementares).
  - `77`: Variáveis elementares independentes.
  - `88`: Condições lógicas (Condition-names).
- **Cláusulas Mandatórias por Item Elementar:**
  - `PICTURE` (ou `PIC`): Especifica o tipo e tamanho (`9` numérico, `X` alfanumérico, `A` alfabético).
  - `VALUE`: Inicialização de constante ou valor default.

### 3.4 PROCEDURE DIVISION (Obrigatória)

- Contém os algoritmos, a lógica de negócio e as declarações imperativas executáveis.
- Dividida em `SECTIONS` (opcionais), `PARAGRAPHS` (parágrafos), contendo `SENTENCES` (frases) compostas por `STATEMENTS` (instruções), obrigatoriamente finalizadas por ponto final (`.`).

---

## 4. ANÁLISE SEMÂNTICA (VERIFICAÇÕES)

O compilador deve impor as seguintes restrições de escopo e tipo durante a compilação:

1. **Compatibilidade de MOVE:** Impedir a movimentação de dados puramente alfabéticos (`PIC A`) para variáveis numéricas (`PIC 9`).
2. **Unicidade de Identificadores:** Variáveis globais na `DATA DIVISION` não podem ter nomes duplicados dentro do mesmo escopo, a menos que sejam qualificadas por hierarquia (`OF`).
3. **Validação de Destinos de Controle:** Instruções `PERFORM [Parágrafo]` ou `GO TO [Parágrafo]` devem referenciar parágrafos ou seções declarados explicitamente na `PROCEDURE DIVISION`.
4. **Associação de Arquivos:** Qualquer operação de `OPEN`, `READ`, `WRITE` ou `CLOSE` na `PROCEDURE DIVISION` exige a prévia declaração do arquivo no `FILE-CONTROL` e seu respectivo descritor `FD` na `DATA DIVISION`.

---

## 5. GERAÇÃO DE CÓDIGO INTERMEDIÁRIO / TRADUÇÃO

O compilador pode seguir duas abordagens principais de backend:

- **Tradução para Linguagem Alvo (Ex: GNU COBOL / Genio Cobol):** Traduz a árvore sintática abstrata (AST) do COBOL para código equivalente em **Linguagem C**, acionando posteriormente o compilador nativo da máquina (como `gcc`) para gerar o executável binário.
- **Geração Direta de Código Objeto / Bytecode:** Conversão para código de máquina direcionado a Mainframes (IBM z/OS) ou geração de Bytecode **Java** para execução multiplataforma em máquinas virtuais.

---

## 6. TRATAMENTO DE ERROS E DIRETIVAS DO COMPILADOR

- **Níveis de Severidade de Erro:**
  - `I` (Informational): Sugestões de estilo ou otimização.
  - `W` (Warning): Alertas de potenciais ambiguidades (não impedem a compilação).
  - `E` (Error): Erros sintáticos ou semânticos graves. A compilação falha e impede o passo de linkedição.
  - `S` (Severe/Severe Error): Falha catastrófica no processo de compilação.
- **Copybooks (Inclusão de código):** Suporte à diretiva `COPY [Nome]`, que interrompe momentaneamente a leitura do arquivo atual para incluir textualmente blocos de código externos (reutilização de layouts de dados ou procedures).

---

*Este documento atua como guia de especificação de engenharia de software para o desenvolvimento de ferramentas de conformidade e front-ends de compiladores legados.*
