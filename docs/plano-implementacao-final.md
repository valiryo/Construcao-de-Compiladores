# Plano técnico do compilador COBOL final

## Objetivo e estado após a Etapa 2

Implementar em Python 3.11+ um compilador com pipeline:

```text
COBOL fixo → expansão COPY → lexer → parser → AST
             → análise semântica → C + runtime → GCC → executável
```

A AST será a entrada direta do gerador C. Não se planeja MIPS, LLVM nem uma IR
separada. GCC compilará o C produzido por este projeto. GnuCOBOL poderá comparar
resultados, exclusivamente como oráculo de testes, nunca como backend.

Corpus e lexer foram concluídos na Etapa 1: 58 testes iniciais e 80 após as
melhorias, conforme [auditoria-lexer.md](auditoria-lexer.md). A **Etapa 2 implementa
COPY, parser descendente recursivo, AST tipada e CLI de sintaxe**, com **149 testes
passando** e os sete oficiais completos. Todos os 77 arquivos anteriormente
aceitos pelo lexer foram submetidos ao parser: 72 programas e dois copybooks
passam; um arquivo vazio e dois exemplos SQL/CICS ficam separados. Os nove
negativos léxicos também foram revisitados. Não há análise semântica completa,
runtime C, invocação GCC ou geração executável. Os
[inventários por fonte](inventario-corpus.md) e
[dados completos](auditoria-lexer-depois.json) fixam o escopo conhecido ao commit
`1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295` do COBOL Dicas.

Os resultados reproduzíveis estão em [auditoria-parser.md](auditoria-parser.md),
a gramática em [gramatica-cobol.ebnf](gramatica-cobol.ebnf) e a API/CLI em
[frontend.md](frontend.md). Os fontes originais permanecem intactos.

## Inventário que orienta a arquitetura

| Domínio | Oficiais/dependências | Ampliação identificada |
|---|---|---|
| Estrutura | IDENTIFICATION/ENVIRONMENT/DATA/PROCEDURE, PROGRAM-ID, seções e parágrafos, FILE-CONTROL, SPECIAL-NAMES | SCREEN, SD e programas chamados |
| Dados | Níveis 01/05/10/15, grupos, FILLER, PIC X/9/S/V/Z, VALUE, OCCURS 50, COMP, LINKAGE | Níveis 77/88, REDEFINES, INDEXED BY, índices, ASCENDING KEY, formatos editados com sinal, campos até 28 dígitos |
| Referências | OF, subscritos, CAMPO(início:comprimento), LENGTH OF, FUNCTION REVERSE | MOD, ORD, INTEGER, INTEGER-OF-DATE, RANDOM, múltiplas tabelas |
| Entrada/saída | ACCEPT, DISPLAY, WITH NO ADVANCING, DATE YYYYMMDD, DAY-OF-WEEK e DAY YYYYDDD em PROGDATA | TIME, SCREEN, LINE/COLUMN, CRT e teclas |
| Movimentação | MOVE inclusive de grupo e para vários destinos; INITIALIZE REPLACING ALPHANUMERIC/NUMERIC | CORR/CORRESPONDING, STRING/UNSTRING e DELIMITED |
| Cálculo | ADD, SUBTRACT, COMPUTE, + - * / e parênteses, valores decimais implícitos | MULTIPLY, DIVIDE/GIVING/REMAINDER, ROUNDED, SIZE ERROR, potência |
| Condições | IF/ELSE/END-IF, EQUAL/GREATER/LESS, operadores simbólicos, NOT/AND/OR, IS NUMERIC | Condições abreviadas, níveis 88 e TRUE/FALSE |
| Seleção | EVALUATE de campo, WHEN valor, WHEN LESS, WHEN IS NOT NUMERIC e WHEN OTHER | Seleções com condição composta conforme inventário |
| Controle | PERFORM seção/parágrafo, inline, UNTIL, VARYING FROM/BY, END-PERFORM, GO TO, EXIT, CONTINUE, STOP RUN, GOBACK | TIMES, SEARCH/END-SEARCH e SET, SORT, ALTER |
| Arquivos | SELECT/ASSIGN, FD, LINE SEQUENTIAL, OPEN INPUT/OUTPUT/EXTEND, READ INTO, AT END/NOT AT END, END-READ, WRITE/CLOSE | INDEXED/DYNAMIC, RECORD KEY/ALTERNATE KEY, DUPLICATES, FILE STATUS, START/INVALID KEY |
| Modularização | COPY002A, COD001A; CALL PROGDATA USING, RETURN-CODE | CALL entre outros fontes, BY REFERENCE/BY VALUE e bibliotecas externas |

O inventário detalhado prevalece sobre esta síntese. O parser reconhece as
construções batch/tela nas formas documentadas na EBNF. Uma construção conhecida
ainda sem backend deve produzir
diagnóstico explícito com posição, em vez de ser ignorada ou traduzida parcialmente.

EXEC SQL/CICS, macros BMS/JCL e wrappers C/ncurses merecem trilhas separadas.
ALTER e cláusulas de arquivos indexados já têm AST, mas sua execução não foi
implementada. Os três adicionais serão **semelhantes aos oficiais**;
não há garantia de suporte a toda extensão do repositório. Priorizar os adicionais
batch interativos, tabelas e arquivos sequenciais, mantendo a capacidade de
diagnosticar claramente recursos fora do subconjunto.

## Componentes existentes e futuros

| Componente | Estado, responsabilidade e saída |
|---|---|
| `frontend.py`, `__main__.py` | Implementados: API/CLI de sintaxe, diagnóstico e JSON da AST |
| `compiler.py`, `cobol_compiler/driver.py` | Futuro: driver de compilação e invocação GCC |
| `source.py`, `preprocessor.py` | Implementados: COPY, caminhos, origem física e detecção de ciclos |
| `cobol_lexer/` existente | Colunas/continuação, tokens e diagnósticos léxicos, API preservada |
| `source.py`, `diagnostics.py` | Implementados: LocatedToken e diagnósticos por fase/severidade/inclusão |
| `ast.py`, `parser.py`, `expressions.py`, `statements.py` | Implementados: AST tipada, descendente recursivo, expressões e comandos |
| `validation.py`, `tools/auditar_parser.py` | Implementados: invariantes da AST e auditoria integral |
| `symbols.py`, `semantic.py`, `layout.py` | Resolução, tipos, layout de armazenamento e vínculos em tabelas laterais da AST |
| `c_codegen.py` | Visitante da AST validada, C e mapeamento de diagnósticos para o fonte |
| `runtime/cobol_runtime.h`, `.c` | Campos, números decimais, MOVE, formatação, arquivos e chamadas |
| `tests/test_preprocessor.py`, `test_parser.py`, `test_parser_corpus.py` | Implementados: unitários, oficiais e corpus completo |
| Testes semânticos, runtime e integração executável | Futuros: tipos, layouts, C e cenários completos |

Os módulos implementados estão em `cobol_compiler/`; os componentes marcados como
futuros ainda são proposta. Os comandos não são representados por tokens de texto
concatenados. Os nós mantêm SourceSpan; o analisador semântico deverá vincular referências a
símbolos e layouts, e o gerador não deve repetir resolução por nomes.

### Origem e COPY — implementados

1. Resolver COPY sem aspas ou com literal usando diretório do fonte e opções `-I`,
   extensões .cpy/.cbl e política explícita para caixa. Não usar busca arbitrária
   no disco nem rede durante compilação. COPY REPLACING, se implementado, requer
   substituição de tokens/pseudotexto e testes próprios.
2. Preservar stack de inclusão, caminhos, linhas e colunas originais. Detectar
   ciclos e copybooks ausentes, com diagnóstico na diretiva e trilha de inclusão.
3. O adaptador `LocatedToken(token, span)` preserva caminhos, posições físicas e
   pilha de inclusão em SourceLocation; consumidores antigos de Token não mudam.
   Não perder a origem ao concatenar virtualmente linhas expandidas. A convenção
   decimal do programa deve valer também no texto incluído.
4. Manter tratamento de formato fixo em um único leitor. Não converter todo
   exemplo para formato livre nem deslocar código mal indentado automaticamente.
   As áreas A/B serão verificadas com contexto sintático, usando os metadados.

### Gramática e parser implementados

O descendente recursivo tem rotinas por divisão, declaração e comando, com
precedência de expressões e potência associativa à direita. A referência completa
é [gramatica-cobol.ebnf](gramatica-cobol.ebnf); o esboço abaixo resume a arquitetura,
sem substituir a gramática das formas efetivamente implementadas:

```ebnf
program       = identification, [environment], [data], procedure, [end_program] ;
identification = "IDENTIFICATION", "DIVISION", ".",
                 "PROGRAM-ID", ".", name, ".", {metadata_clause} ;
environment   = "ENVIRONMENT", "DIVISION", ".", {environment_section} ;
data          = "DATA", "DIVISION", ".", {data_section} ;
data_item     = level, (name | "FILLER"), {data_clause}, "." ;
data_clause   = picture | value | occurs | redefines | usage | condition_values ;
procedure     = "PROCEDURE", "DIVISION", ["USING", {parameter}], ".",
                {sentence | paragraph | procedure_section} ;
sentence      = {statement}, "." ;
statement     = move | initialize | accept | display | arithmetic | inspect
              | if | evaluate | perform | goto | exit | continue | stop
              | goback | open | read | write | close | call
              | string | unstring | search | set | sort ;
reference     = name, {("OF" | "IN"), name}, [subscripts], [refmod] ;
subscripts    = "(", expression, {separator, expression}, ")" ;
refmod        = "(", expression, ":", [expression], ")" ;
primary       = number | string_literal | figurative | reference
              | "FUNCTION", function_name, [arguments]
              | "LENGTH", "OF", reference | "(", expression, ")" ;
```

O esboço não é uma promessa de formas ausentes nem uma gramática completa: listas
de argumentos, alternativas de READ e condições abreviadas requerem regras
explícitas. Distinguir subscrito de referência modificada ao encontrar `:` dentro
dos parênteses e permitir uma referência de tabela seguida de refmod. Nomes de
programa/arquivo/parágrafo são tokens IDENTIFIER; funções contextuais não precisam
virar palavras reservadas globais. O parser deverá reconhecer frases por tokens
e contexto, sem comparar trechos de código por regex.

Precedência: potência, sinal unário (fixar sua interação com potência em testes),
produto/divisão, soma/subtração, comparação/classe, NOT, AND, OR. Construir nós
para condições abreviadas, evitando interpretar `A = 1 OR 2` como booleano numérico
C. `WHEN LESS 18` e `WHEN IS NOT NUMERIC` herdam o sujeito do EVALUATE.

Ponto encerra sentença e também escopos implícitos de comandos; END-IF,
END-EVALUATE, END-PERFORM e END-READ são delimitadores explícitos. Uma pilha de
terminadores e pontos de sincronização permite recuperar após erros, sem consumir
o início do próximo parágrafo/divisão. Falha sintática impede geração executável.
Validar ordem das divisões e requisitos de área A/B nesta fase.

### Nós da AST

- Estrutura: `Program`, `EnvironmentDivision`, `FileControlEntry`, `DataDivision`,
  `DataSection`, `ProcedureDivision`, `ProcedureSection`, `Paragraph`, `Sentence`.
- Dados: `DataItem(level, name, clauses, children)`, `PictureClause`, `ValueClause`,
  `OccursClause`, `RedefinesClause`, `UsageClause`, `FileDescriptor`, `CallParameter`.
  Níveis 88 são DataItem associados ao item anterior. A máscara original é
  preservada; a interpretação de tipo/layout ainda será implementada.
- Expressões: `Literal` (inclui constantes figurativas), `Reference(qualifiers,
  subscripts, refmod)`, `Unary`, `Binary`, `FunctionCall`, `LengthOf`,
  `Comparison`, `ClassCondition`, `AbbreviatedCondition`, `Group`. Operadores
  booleanos usam Binary/Unary; condition-names serão resolvidos pela semântica.
- Comandos: `Move`, `Initialize`, `Accept`, `Display`, `Arithmetic` (operação e
  destinos explícitos), `Inspect`, `If`, `Evaluate`/`When`, `Perform` (alvo ou corpo,
  TIMES/UNTIL/VARYING/TEST BEFORE/AFTER), `GoTo`, `Exit`, `Continue`, `StopRun`,
  `Goback`, `Call`, `Open`, `Read` (corpos AT END/NOT AT END), `Write`, `Close`.
  Extensões têm nós próprios: `String`, `Unstring`, `Search`, `Set`, `Sort`.

Preservar lista ordenada de seções/parágrafos e limites de sentença: a ordem do
fonte afeta fall-through e PERFORM. Os filhos de dados são construídos pela pilha
de níveis, sem transformar 77/88 em filhos regulares. Não usar dicionário simples
por nome para armazenar todos os campos, pois FILLER se repete e há qualificações.

## Análise semântica e layout

Analisar primeiro declarações, depois referências, permitindo destinos de PERFORM
declarados posteriormente. Separar namespaces de dados, arquivos, seções,
parágrafos, programas e condições. Normalizar caixa para resolução; preservar
grafia original para mensagens.

| Verificação | Critério |
|---|---|
| Declaração | Referência inexistente ou ambígua é erro; OF/IN resolve por hierarquia; duplicatas no mesmo escopo são rejeitadas |
| Hierarquia | Níveis válidos, 77 elementar, 88 associado a item, FILLER sem símbolo utilizável; grupos não têm PIC elementar |
| PIC/USAGE | Interpretar categoria, comprimento, sinal, escala e edição; validar combinações, COMP, limites e VALUE |
| MOVE/cálculo | Aplicar conversões definidas; rejeitar PIC A puramente alfabético para numérico, conforme especificação; destinos graváveis e operações numéricas |
| Tabelas/refmod | Número e tipo dos índices, base 1, bounds constantes; inserir verificação em runtime para limites dinâmicos; refmod válido para categoria e comprimento |
| Controle | Resolver PERFORM/GO TO, seção/parágrafo, limites de ranges e encerramento; comandos de saída corretos para contexto |
| Arquivos | SELECT e FD associados; READ/OPEN/CLOSE com arquivo declarado, WRITE com registro correto, modo/organização e FILE STATUS compatíveis |
| Chamadas | Programa resolvido, parâmetros de USING por referência, layouts/tamanhos compatíveis; área LINKAGE não é alocação independente |
| Condições/funções | Tipos de comparações, classe NUMERIC, assinatura de REVERSE/LENGTH/data e funções adicionais |

Dados devem ter representação de armazenamento independente de seu valor lógico:
offset, tamanho, categoria, escala, uso, pai e stride de OCCURS. REDEFINES cria
visões do mesmo armazenamento, não cópias. MOVE de grupo copia bytes com regras
de preenchimento/truncamento; acessos elementares interpretam a fatia apropriada.

Há duas divergências da especificação com o corpus que precisam ficar explícitas:
campos oficiais frequentemente omitem VALUE, e nomes iguais podem ocorrer em
hierarquia qualificável. O modo de compatibilidade com o corpus deverá permitir
VALUE ausente, com inicialização documentada/testada; um modo estrito pode emitir
o diagnóstico exigido pelo texto da disciplina. Não exigir VALUE em todo item
para conseguir executar os oficiais sem alterar seus fontes. O resolvedor deve
tratar a ambiguidade do nome TAB-ENT-LINHA em dois níveis do PROG024A pela
hierarquia, diagnosticando apenas referências realmente ambíguas.

Diagnósticos futuros terão fase, severidade I/W/E/S, caminho e span, com notas
para declarações relacionadas e inclusão COPY. Qualquer E/S bloqueia GCC e
linkedição. Evoluir o modelo por adaptador/campos opcionais com defaults, mantendo
a integração atual do lexer e seus códigos testados.

## Geração C e runtime

Gerar C11 portátil com nomes internos baseados no símbolo resolvido, nunca em
texto COBOL inserido diretamente no C. Escapar literais, proteger colisões de
nomes e garantir compilação sem dependência de um runtime GnuCOBOL.

| Recurso | Estratégia |
|---|---|
| Strings | Buffers com comprimento explícito e espaços finais; sem depender de NUL; MOVE preenche/trunca, comparação considera padding |
| Numérico DISPLAY | Dígitos em largura fixa, sinal e escala no descritor; leitura/escrita por helpers; IS NUMERIC examina representação, não conversão permissiva de atoi |
| Decimais | Coeficiente inteiro + escala, operações exatas e regras de arredondamento/truncamento; evitar float como representação padrão |
| Capacidade | Int64 somente com prova de faixa e operações checadas; corpus tem PIC 9(28), portanto prever vetor de dígitos para valores maiores e intermediários |
| COMP | Armazenamento binário com largura definida pelo ABI do projeto e conversões por descritor; layouts compartilhados de CALL consistentes |
| PIC editado | Formatação Z, sinais, inserções e separadores conforme DECIMAL-POINT; zero suppression e casas fixas testadas |
| Grupos/tabelas | Área contígua com offsets e strides calculados; subscritos base 1; REDEFINES e linkage como views |
| ACCEPT/DISPLAY | stdin/stdout, largura e conversões COBOL; NO ADVANCING com flush; fontes DATE/DAY/TIME via contexto de runtime |
| Arquivos | Handles separados dos registros, LINE SEQUENTIAL, modos INPUT/OUTPUT/EXTEND, preenchimento de registro, EOF e FILE STATUS |
| Intrínsecas | REVERSE/LENGTH sem remover padding; datas e MOD/ORD com contrato explícito, caso entrem no subconjunto |
| CALL/GOBACK | Função por programa com contexto e slices de parâmetros, armazenamento de working-storage e RETURN-CODE; linkage aponta para área do chamador |

Os arquivos de entrada ausentes exigem fixtures; não gerar dados fictícios dentro
do compilador. O relógio deve ser substituível nos testes de PROGDATA. Definir a
codificação dos registros e o tratamento de acentos antes de comparar comprimentos
de PIC X com strings UTF-8; caracteres Python e bytes C não são intercambiáveis.

### Controle de fluxo sem reescrever a arquitetura por exemplo

Um PERFORM de seção retorna ao fim de sua seção; `EXIT.` isolado é no-op, não
`return`. Um programa pode cair no próximo parágrafo, executar GO TO e chamar
PERFORM dentro de PERFORM. Nos oficiais há também repetição por chamada da
própria seção. Traduzir cada parágrafo ingenuamente para função C com return final
altera esses comportamentos.

Usar por programa um dispatcher C com contador de posição e pilha explícita dos
retornos/limites de PERFORM. Os rótulos e transições serão emitidos diretamente
durante a visita da AST com as anotações semânticas, sem introduzir uma IR de
instruções separada. Estruturas inline podem gerar blocos/loops C quando preservam
os mesmos limites; GO TO transfere a posição e a pilha controla retorno no limite
performado. STOP RUN encerra a unidade de execução inteira; GOBACK retorna ao
chamador ou ao host quando principal. Testar esse contrato antes de emitir menus.
ALTER já tem nó tipado e teste baseado no PROG018A. Fica fora da primeira versão
executável e precisará de diagnóstico semântico/backend claro se selecionado.

## Driver e CLI planejados

Já disponíveis nesta etapa:

```bash
python -m cobol_compiler examples/oficiais/CALCMD01.cbl --check-syntax
python -m cobol_compiler examples/oficiais/CAD0002A.cbl -I examples/dependencias --dump-ast
python -m tools.auditar_parser --write
```

Os comandos abaixo continuam futuros, para a etapa do backend:

```bash
python compiler.py examples/oficiais/CALCMD01.cbl -o calcmd01
./calcmd01

python compiler.py examples/corrigidos/CAD0005A.cbl -o cad0005a
python compiler.py examples/oficiais/PROG024A.cbl \
    -I examples/dependencias --source examples/dependencias/PROGDATA.cbl \
    -o biblioteca --emit-c build/biblioteca.c
```

São comandos futuros. Oferecer `--check` para front-end, `--emit-c` e `--keep-c`
para inspeção e compilação, diretório temporário para C/objetos e saída explícita.
COPY e fontes de CALL devem ser resolvidos por caminhos configurados; jamais
baixar dependências ou executar programas COBOL no processo de compilação.
Invocar GCC com `subprocess.run([...])`, sem shell; capturar stderr e manter mapa
entre C gerado e fonte para diagnosticar falhas. Usar flags C11 e warnings úteis;
não sobrescrever um executável anterior se a compilação falhar. Documentar GCC
como requisito apenas quando o backend existir.

## Entregas incrementais e critérios

1. **COPY e fonte localizado — concluído:** ambos copybooks, ciclos/ausência,
   pilha de inclusão, coordenadas físicas, decimal e PIC herdados. Os 80 testes
   léxicos foram preservados; COPY REPLACING não ocorre no corpus e é rejeitado
   explicitamente, sem implementação parcial.
2. **Gramática/AST — concluído no subconjunto documentado:** sete oficiais e
   dependências completos, 74 sucessos entre os 77 anteriormente aceitos. Todos
   os fontes são exercitados; vazio e SQL/CICS têm classificação individual.
   A suíte total tem 149 testes. A validação confere cada comando, spans,
   hierarquia e ausência de tokens descartados; não atesta execução.
3. **Semântica/layout:** resolver todos os símbolos oficiais e layouts; negativos
   para variável/arquivo/parágrafo ausentes, duplicatas, MOVE A→9, tipos,
   subscritos/refmod e CALL incompatível. Conferir tamanho/offset dos registros e
   dos 50 elementos de COPY002A. Separar problemas reais no fonte de recurso ausente.
4. **Runtime e C:** validar primeiro strings, decimal e controle com programas
   pequenos; depois interação, tabelas, READ/WRITE e CALL. Gerar C dos sete,
   compilar com GCC e executar em diretórios temporários. Recursos não suportados
   devem falhar antes de GCC. Testar overflow, EOF, arquivo ausente e erro de I/O.
5. **Integração dos sete + três:** scripts de entrada e resultados esperados,
   status, stdout e arquivos gerados; escolher três complementares semelhantes
   de famílias distintas para ensaio. Na avaliação, executar os três efetivamente
   escolhidos pelo professor; os ensaios não substituem essa exigência.

| Programa | Cenários executáveis mínimos futuros |
|---|---|
| BUSCA01A | CPF primeiro/último, ausente e arquivo vazio; conferir contador e término no EOF |
| CAD0002A | Driver com COPY002A compartilhado; entradas válidas/inválidas e FIM; verificar alterações na área do chamador e GOBACK |
| CAD0004A | Um e vários cadastros, resposta N; bytes e largura do arquivo de saída |
| CAD0005A corrigido | Agenda inicialmente vazia/preenchida, adicionar/listar/excluir conforme menu, opção inválida; persistência após reabrir |
| CAIXAREG | Itens válidos/zero, com/sem desconto; casas decimais e máscara editada exatas |
| CALCMD01 | Três valores, tentativa inválida e nova entrada; divisor e escala da média |
| PROG024A | Biblioteca vazia/preenchida, cadastrar/emprestar/devolver/consultar, gravar/reabrir, log e data determinística via PROGDATA |

A comparação opcional com GnuCOBOL deve usar fixtures idênticos e controlar
convenção decimal, data, encoding e espaços, registrando divergências. O resultado
avaliado será sempre o executável obtido de **nosso C via GCC**. Não normalizar
saídas a ponto de esconder truncamento, arredondamento ou padding incorreto.

Os snapshots originais, hashes e negativos de conflitos permanecem no repositório.
Qualquer correção adicional de fonte exige identificação da necessidade e cópia
separada documentada. Toda fase deve executar a suíte anterior e validar o corpus
inteiro, evitando decisões baseadas apenas no primeiro programa a compilar.
