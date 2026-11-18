# Plano técnico do compilador COBOL final

## Objetivo e estado após a Etapa 7

Implementar em Python 3.11+ um compilador com pipeline:

```text
COBOL fixo/livre → expansão COPY → lexer → parser → AST
             → análise semântica → C + runtime → GCC → executável
```

A AST é a entrada direta do gerador C, sem uma IR de instruções separada.
GCC compila o C produzido por este projeto com runtime próprio. GnuCOBOL compara
resultados exclusivamente como oráculo independente de testes.

Corpus e lexer foram concluídos na Etapa 1: 58 testes iniciais e 80 após as
melhorias, conforme [auditoria-lexer.md](auditoria-lexer.md). A **Etapa 2 implementa
COPY, parser descendente recursivo, AST tipada e CLI de sintaxe**, com **149 testes
passando** e os sete oficiais completos. Todos os 77 arquivos anteriormente
aceitos pelo lexer foram submetidos ao parser: 72 programas e dois copybooks
passam; um arquivo vazio e dois exemplos SQL/CICS ficam separados. Os nove
negativos léxicos também foram revisitados. A **Etapa 3 implementa semântica e
layout**, com **245 testes passando**. Os sete
oficiais foram validados; todos os 72 programas parseáveis foram analisados, com
68 válidos (seis com pendências externas), três erros reais e um caso de tela
parcialmente suportado. Os copybooks são verificados no contexto de COPY.
A **Etapa 4 implementa runtime C, geração C11 e driver GCC**, com **326 testes**.
Dos 68 programas semanticamente válidos, 60 compilam (53 executáveis e sete
objetos), seis dependem de chamadas externas e dois usam terminal posicionado.
Na Etapa 4, os sete oficiais, PROGDATA e três complementares foram executados e validados
em 30 cenários; os 29 comparáveis coincidem integralmente com GnuCOBOL 3.2.0.
A **Etapa 5 valida os 60 compilados em 140 cenários**, incluindo os 49 antes
pendentes e seus cinco módulos. A suíte reúne **476 testes**. Os sete oficiais
foram recompilados do zero nos 25 cenários originais. Há 136 comparações idênticas,
três diferenças previstas da ABI com expectativas completas e nenhuma divergência
inesperada; um cenário de divisor zero verifica a política do projeto. Duas falhas
comprovadas foram corrigidas: separador decimal em MOVE/UNSTRING e padding de
literais continuados no frontend. Os
[inventários por fonte](inventario-corpus.md) e
[dados completos](auditoria-lexer-depois.json) fixam o escopo conhecido ao commit
`1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295` do COBOL Dicas.

Os resultados reproduzíveis estão em [auditoria-parser.md](auditoria-parser.md),
a semântica em [auditoria-semantica.md](auditoria-semantica.md),
a gramática em [gramatica-cobol.ebnf](gramatica-cobol.ebnf) e a API/CLI em
[frontend.md](frontend.md) e [semantica.md](semantica.md). Os fontes originais
permanecem intactos. A [auditoria do backend](auditoria-backend.md) registra
geração, GCC, execução e validação por fonte; [backend.md](backend.md) documenta
uso, ABI, capacidades e limites. A [auditoria funcional](auditoria-funcional.md) e
[guia de reprodução](validacao-funcional.md) documentam inventário, isolamento,
proveniência e verificação dos 60 programas.

A **Etapa 7** muda a meta para os originais que GnuCOBOL constrói intactos:
**64/70 (91,43%)**, com **57/63 principais e 7/7 subprogramas**. O perfil explícito
`--dialect gnucobol` acrescenta formato livre configurável, identificadores de
63 posições, FD DATA RECORD(S), PIC de sinal flutuante e terminal/SCREEN no
subconjunto documentado. Foram ampliados cinco originais sem alterações nos
fontes. Os 140 cenários anteriores e os sete oficiais passaram novamente; há
12 novos cenários e 522 testes na suíte. Dos originais, 60 coincidem nos cenários
completos, três têm diferenças ABI conhecidas e GAMESNAK tem comparação parcial.
As seis pendências são CALL externo, sem stubs; custos e arquitetura proposta
estão na [auditoria de compatibilidade](compatibilidade-gnucobol.md), com
[comandos e dados reproduzíveis](compatibilidade-gnucobol.json). Não há plano de
recuperar fontes inválidos nem criar novas cópias corrigidas. As metas anteriores
abaixo são históricas; a Etapa 7 prevalece sobre propostas antigas de recuperação.

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
implementada. Os três ensaios adicionais são PROG012A (texto/refmod), PROG020A
(SEARCH ALL) e PROG039A (exclusão em arquivo sequencial). Não há garantia de
suporte a toda extensão do repositório; os três escolhidos pelo professor ainda
deverão ser executados na avaliação.

## Componentes implementados

| Componente | Estado, responsabilidade e saída |
|---|---|
| `frontend.py`, `__main__.py` | Implementados: API/CLI sintática e semântica, diagnósticos, JSON de AST/símbolos/layout |
| `compiler.py`, `cobol_compiler/driver.py` | Driver C11/GCC, objetos, temporários e publicação atômica |
| `source.py`, `preprocessor.py` | Implementados: COPY, caminhos, origem física e detecção de ciclos |
| `cobol_lexer/` existente | Colunas/continuação, tokens e diagnósticos léxicos, API preservada |
| `source.py`, `diagnostics.py` | Implementados: LocatedToken e diagnósticos por fase/severidade/inclusão |
| `ast.py`, `parser.py`, `expressions.py`, `statements.py` | Implementados: AST tipada, descendente recursivo, expressões e comandos |
| `validation.py`, `tools/auditar_parser.py` | Implementados: invariantes da AST e auditoria integral |
| `symbols.py`, `types.py`, `semantic.py`, `layout.py` | Implementados: resolução, PIC/tipos, layout e vínculos em tabelas laterais da AST |
| `c_codegen.py` | Visitante da AST validada, dispatcher C e origem COBOL por comando |
| `runtime/cobol_runtime.h`, `decimal.c`, `fields.c`, `files.c` | Campos, decimal exato, MOVE, edição, terminal, arquivos, controle e chamadas |
| `tests/test_preprocessor.py`, `test_parser.py`, `test_parser_corpus.py` | Implementados: unitários, oficiais e corpus completo |
| Testes semânticos e auditoria | Implementados: 96 testes novos, sete oficiais e todos os 72 programas parseáveis |
| Runtime e integração executável | 81 testes novos; sete oficiais, PROGDATA, três complementares e oráculo opcional |
| `tools/auditar_backend.py` | Todos os 68 semanticamente válidos; 60 compilados e classificação de cada limite |
| `tools/auditar_funcional.py`, `functional_execution.py`, `functional_scenarios.py` | Descoberta dos 49 pendentes, construção limpa, 140 cenários, logs binários, seleção e repetição de falhas |
| `tools/auditar_compatibilidade.py`, `compatibility_corpus.py`, `compatibility_scenarios.py`, `terminal_probe.py` | Todo original intacto, GnuCOBOL por fase, perfil explícito, novas fixtures e PTY com evidências brutas |

A **Etapa 6** audita os 26 arquivos fora da coorte compilada, sem mudanças no
compilador/runtime nem nos originais. A [auditoria dos pendentes](auditoria-pendentes.md)
e o [plano de recuperação](recuperacao-pendentes.md) separam nove casos simples
(oito identidades novas), quatro moderados, sete complexos, quatro fora do escopo
e dois fragmentos. Dez fontes chegam ao GCC em cópias experimentais; isso não
altera os 60 funcionalmente validados. Seis verificações novas preservam a suíte
anterior, totalizando 482 testes ao fim daquela etapa. A Etapa 7 substitui sua
proposta de recuperação pelo critério de originais intactos compiláveis pelo
GnuCOBOL e implementa terminal e edição flutuante nos casos comprovados.

Os módulos Python estão em `cobol_compiler/` e o runtime em `runtime/`.
Os comandos não são representados por tokens de texto
concatenados. Os nós mantêm SourceSpan; o analisador semântico vincula referências a
símbolos e layouts; o gerador consome essas anotações sem repetir resolução.

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
virar palavras reservadas globais. O parser reconhece frases por tokens
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
  preservada; tipos e layouts são interpretados pela semântica em tabelas laterais.
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

## Análise semântica e layout — implementados

A [API e ABI documentadas](semantica.md) detalham os contratos atuais, inclusive
comprimentos em bytes ISO-8859-1, COMP/COMP-3, inicialização, chamadas pendentes e
limites explícitos. O [relatório por fonte](auditoria-semantica.md) separa validade
local, dependências externas, erros do corpus e recursos bloqueados.


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
hierarquia qualificável. O modo de compatibilidade com o corpus permite
VALUE ausente, com inicialização documentada/testada; o modo `--strict` emite
o diagnóstico exigido pelo texto da disciplina. Não exigir VALUE em todo item
para conseguir executar os oficiais sem alterar seus fontes. O resolvedor deve
tratar a ambiguidade do nome TAB-ENT-LINHA em dois níveis do PROG024A pela
hierarquia, diagnosticando apenas referências realmente ambíguas.

Diagnósticos semânticos têm fase, severidade I/W/E/S, caminho e span, com notas
para declarações relacionadas e inclusão COPY. Qualquer E/S bloqueia GCC e
linkedição. Evoluir o modelo por adaptador/campos opcionais com defaults, mantendo
a integração atual do lexer e seus códigos testados.

## Geração C e runtime — implementados no subconjunto

O gerador produz C11 com nomes internos baseados no símbolo resolvido e literais
escapados. O executável liga somente nosso runtime e a biblioteca padrão C.

| Recurso | Estratégia |
|---|---|
| Strings | Buffers com comprimento explícito e espaços finais; sem depender de NUL; MOVE preenche/trunca, comparação considera padding |
| Numérico DISPLAY | Dígitos em largura fixa, sinal e escala no descritor; leitura/escrita por helpers; IS NUMERIC examina representação, não conversão permissiva de atoi |
| Decimais | Racional exato com vetores de dígitos para numerador/denominador; truncamento/arredondamento na escala do receptor |
| Capacidade | 128 dígitos por campo, 512 por inteiro intermediário, checks de capacidade; PIC 9(28) não usa int64/float como representação lógica |
| COMP | Armazenamento binário com largura definida pelo ABI do projeto e conversões por descritor; layouts compartilhados de CALL consistentes |
| PIC editado | Formatação Z, sinais, inserções e separadores conforme DECIMAL-POINT; zero suppression e casas fixas testadas |
| Grupos/tabelas | Área contígua com offsets e strides calculados; subscritos base 1; REDEFINES e linkage como views |
| ACCEPT/DISPLAY | stdin/stdout, largura e conversões COBOL; NO ADVANCING com flush; fontes DATE/DAY/TIME via contexto de runtime |
| Arquivos | Handles separados dos registros, LINE SEQUENTIAL, modos INPUT/OUTPUT/EXTEND, preenchimento de registro, EOF e FILE STATUS |
| Intrínsecas | REVERSE/LENGTH, UPPER/LOWER-CASE, datas, MOD/ORD/INTEGER e RANDOM com contrato explícito |
| CALL/GOBACK | Função por programa com contexto e slices de parâmetros, armazenamento de working-storage e RETURN-CODE; linkage aponta para área do chamador |

Os arquivos de entrada exigem fixtures explícitas, criadas somente pelos testes.
O relógio pode ser fixado por COBOL_DATETIME. Registros e armazenamento usam
ISO-8859-1; o terminal usa UTF-8 por padrão, com conversão na fronteira. Comprimentos
PIC são bytes da ABI. `COBOL_TERMINAL_ENCODING=latin1` ativa terminal bruto.

### Controle de fluxo sem reescrever a arquitetura por exemplo

Um PERFORM de seção retorna ao fim de sua seção; `EXIT.` isolado é no-op, não
`return`. Um programa pode cair no próximo parágrafo, executar GO TO e chamar
PERFORM dentro de PERFORM. Nos oficiais há também repetição por chamada da
própria seção. Traduzir cada parágrafo ingenuamente para função C com return final
altera esses comportamentos.

Cada programa usa dispatcher C com contador de posição e pilha explícita dos
retornos/limites de PERFORM. Rótulos e transições são emitidos diretamente
durante a visita da AST com as anotações semânticas, sem IR de instruções separada.
GO TO transfere a posição e a pilha controla retorno no limite
performado. STOP RUN encerra a unidade de execução inteira; GOBACK retorna ao
chamador ou ao host quando principal. Esse contrato tem testes pequenos e cenários
de menus recursivos. GO TO para fora de PERFORM inline é diagnosticado antes de GCC.
ALTER já tem nó tipado e teste baseado no PROG018A. Fica fora da primeira versão
executável; a semântica já emite diagnóstico explícito quando ele é selecionado.

## Driver e CLI implementados

Já disponíveis nesta etapa:

```bash
python -m cobol_compiler examples/oficiais/CALCMD01.cbl --check-syntax
python -m cobol_compiler examples/oficiais/CAD0002A.cbl -I examples/dependencias --dump-ast
python -m tools.auditar_parser --write
python -m cobol_compiler examples/oficiais/CALCMD01.cbl --check
python -m cobol_compiler examples/oficiais/CAD0002A.cbl -I examples/dependencias --dump-layout
python -m cobol_compiler examples/oficiais/PROG024A.cbl -I examples/dependencias \
    --source examples/dependencias/PROGDATA.cbl --dump-symbols
python -m tools.auditar_semantica --write
```

Compilação nativa:

```bash
python compiler.py examples/oficiais/CALCMD01.cbl -o calcmd01
./calcmd01

python compiler.py examples/corrigidos/CAD0005A.cbl -o cad0005a
python compiler.py examples/oficiais/PROG024A.cbl \
    -I examples/dependencias --source examples/dependencias/PROGDATA.cbl \
    -o biblioteca --emit-c build/biblioteca.c
```

`compiler.py` compila por padrão; `python -m cobol_compiler` mantém sintaxe como
padrão. `--check` verifica semântica e `--check-backend` verifica suporte/ligação
sem GCC. `--emit-c` e `--keep-c` preservam o C durante a compilação; `--module`
gera objeto sem main para CAD0002A e outros subprogramas. O driver usa temporários,
`subprocess.run([...])` sem shell e flags C11/Wall/Wextra. A saída só é publicada
após sucesso, preservando executáveis anteriores em caso de falha. stderr do GCC
é capturado e o C contém origem COBOL por comando. GCC é requisito da compilação
nativa. Dependências são configuradas, sem downloads ou execução durante compilação.

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
3. **Semântica/layout — concluído no subconjunto documentado:** símbolos e
   operações dos sete oficiais resolvidos; 245 testes totais. Todos os 72
   programas parseáveis analisados; 68 válidos, com seis pendências externas,
   três fontes inválidos e um caso SCREEN parcialmente suportado. COPY002A tem
   registro de 10552 bytes, contador de 2 e 50 ocorrências de stride 211; LINKAGE
   é externo, REDEFINES compartilha storage e 88 não recebe bytes. CALL PROGDATA
   valida a ABI das folhas do COD001A. A auditoria registra 2480 símbolos, 4257
   referências e 1490 layouts. SCREEN, ALTER, SORT, START, arquivos indexados e
   usos listados na documentação permanecem bloqueados explicitamente. Isso
   comprova análise estática, sem geração ou execução.
4. **Runtime e C — concluído no subconjunto:** strings, decimal exato, edição,
   dispatcher, tabelas, arquivos e CALL têm testes pequenos e cenários de integração.
   Todos os 68 válidos foram submetidos ao backend; 60 compilam, seis ficam
   bloqueados por chamadas externas e dois por tela posicionada. Overflow, EOF,
   arquivo ausente, bounds, divisor zero e erros reais de I/O foram exercitados.
5. **Integração dos sete + três — ensaios concluídos:** 30 cenários validam os
   sete, PROGDATA e três complementares. Os 29 comparáveis coincidem com GnuCOBOL.
   A suíte total tem 326 testes. Na avaliação ainda será necessário executar os
   três efetivamente escolhidos pelo professor. Ampliar fixtures dos outros
   programas compilados foi concluído na Etapa 5, nos cenários documentados.
6. **Validação funcional de toda a coorte — concluída nos cenários:** 60 programas
   executados, incluindo todos os 49 antes pendentes; 140 cenários, 136 comparações
   idênticas e três diferenças previstas da ABI verificadas integralmente. Há
   476 testes na suíte e nenhuma divergência inesperada. O executor compartilha
   cenários com o oráculo, verifica regeneração de C/GCC/binário e isola cada
   conjunto de fixtures. Novas entradas/ramos e os três escolhidos pelo professor
   continuam como ampliação de cobertura; os seis externos e dois de tela permanecem
   bloqueados explicitamente.

| Programa | Cenários executáveis validados |
|---|---|
| BUSCA01A | CPF primeiro/último, ausente e arquivo vazio; conferir contador e término no EOF |
| CAD0002A | Driver com COPY002A compartilhado; entradas válidas/inválidas e FIM; verificar alterações na área do chamador e GOBACK |
| CAD0004A | Um e vários cadastros, resposta N; bytes e largura do arquivo de saída |
| CAD0005A corrigido | Agenda vazia/preenchida, adicionar/listar, duplicado, FIM, opção inválida e persistência após reabrir; o fonte não tem exclusão, ensaiada em PROG039A |
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
