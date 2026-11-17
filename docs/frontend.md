# Front-end COBOL — Etapas 2 e 3

Implementação em Python 3.11+, sem bibliotecas externas. O pré-processador e o
parser utilizam o lexer existente. A Etapa 3 acrescenta análise semântica e layout
com tabelas laterais, detalhados em [semantica.md](semantica.md). Runtime, geração C
e chamada ao GCC continuam futuros.

## Usar a CLI

```bash
python -m cobol_compiler examples/oficiais/CALCMD01.cbl --check-syntax
python -m cobol_compiler examples/corrigidos/CAD0005A.cbl --dump-ast
python -m cobol_compiler examples/oficiais/CAD0002A.cbl \
    -I examples/dependencias --check-syntax
python -m cobol_compiler examples/oficiais/PROG024A.cbl \
    -I examples/dependencias --dump-ast > /tmp/prog024a-ast.json
python -m cobol_compiler examples/dependencias/COPY002A.cpy --dump-ast
python -m tools.auditar_parser --write
python -m unittest discover -s tests -v
```

`--check-syntax` é o padrão. `--dump-ast` imprime JSON com o tipo de cada nó e
seus atributos/filhos. `-I` pode se repetir. `.cpy` é analisado automaticamente
como `DataFragment`; `--copybook` força esse modo em outra extensão. `--debug-lines`
habilita as linhas D do formato fixo.

Códigos de saída: 0 para sucesso, 1 para erro léxico/sintático/COPY ou construção
não suportada, 2 para falha de leitura/encoding. A CLI escreve diagnósticos em
stderr e não imprime uma AST válida quando há erros. A verificação sintática
continua independente da semântica. `--check`, `--dump-symbols` e `--dump-layout`
ativam a semântica; `--source` fornece unidades de CALL e `--strict` exige VALUE.
Chamadas sem assinatura disponível ficam pendentes para ligação, preservando
a validade local; nenhuma biblioteca é carregada ou executada.

O comando de auditoria lê todo o inventário da etapa léxica e faz nova execução do
front-end. `--write` regenera [auditoria-parser.md](auditoria-parser.md) e
[auditoria-parser.json](auditoria-parser.json). Todos os 86 arquivos são visitados,
inclusive os nove negativos léxicos. Todos os 77 anteriormente aceitos são
submetidos ao parser. O comando termina com erro se surgir uma falha inesperada
nessa coorte; arquivo vazio e SQL/CICS são expectativas individuais documentadas,
não exclusões. Atualizar essas expectativas exige atualizar testes e relatório.

## Organização e contratos Python

| Módulo | Responsabilidade |
|---|---|
| `source.py` | SourceLocation, SourceSpan, IncludeSite, LocatedToken |
| `diagnostics.py` | Código, fase, severidade, esperado/encontrado e pilha de inclusão |
| `preprocessor.py` | Resolver/expandir COPY, mapear origem e tokenizar no contexto final |
| `ast.py` | Dataclasses tipadas, visitante walk, serialização e invariantes de árvore |
| `parser.py` | Divisões, configuração, arquivos, hierarquia de dados, sentenças e recuperação |
| `expressions.py` | Referências, primários, precedência e condições abreviadas |
| `statements.py` | Rotinas por comando, delimitadores e tratadores aninhados |
| `validation.py` | Verificação independente de spans/intervalos e cobertura dos comandos |
| `frontend.py` | parse_file, parse_source e FrontendResult |
| `types.py`, `symbols.py`, `layout.py`, `semantic.py` | PIC, namespaces, descritores físicos e análise semântica da AST |
| `__main__.py` | Interfaces sintática e semântica, sem backend |

```python
from cobol_compiler import parse_file
from cobol_compiler.ast import Program, walk, to_dict
from cobol_compiler.validation import validate_ast

result = parse_file(
    "examples/oficiais/PROG024A.cbl",
    include_dirs=["examples/dependencias"],
)
if result.success:
    assert isinstance(result.ast, Program)
    validation = validate_ast(result.ast, result.preprocessed.tokens)
    assert validation.success
    for node in walk(result.ast):
        pass  # inspeção sintática; check_file executa a semântica
else:
    for diagnostic in result.diagnostics:
        print(diagnostic.format())
```

`parse_source(text, filename=..., include_dirs=..., copybook=False)` atende testes
e integrações sem arquivo de entrada. `Parser(tokens).parse(copybook=False)`
também é público. A API histórica `CobolLexer().tokenize(source)` continua igual.

`FrontendResult` expõe `preprocessed`, `parsed`, `diagnostics`, `ast` e `success`.
`PreprocessResult` tem os tokens localizados, as linhas expandidas, diagnósticos e
dependências COPY. `ParseResult` informa tokens consumidos, tokens pulados em
recuperação e erros estruturais. `ast` só existe em sucesso; `partial_ast` é
exclusivamente uma árvore de recuperação para depuração, nunca entrada válida
para a próxima fase.

## COPY e origem física

A resolução procura primeiro o diretório do incluindo e depois os diretórios
`-I`, na ordem fornecida. O nome exato tem prioridade; nomes sem extensão também
tentam `.cpy`, `.cbl` e `.cob`. Uma correspondência de caixa diferente é aceita se
única, para que `COPY COD001A` não dependa do sistema operacional. Caminhos com
subdiretórios usam a grafia indicada. Não há download ou busca global no disco.

A passagem preliminar usa tokens do próprio lexer para localizar COPY fora de
strings/comentários. A expansão intercala linhas físicas, mascarando apenas a
diretiva, e a tokenização definitiva ocorre sobre o texto expandido inteiro.
Isso mantém a configuração decimal e PIC do programa incluindo; o copybook pode
até fornecer uma máscara após PIC. O único ajuste adicional no lexer nesta etapa
permite reconhecer COPY quando uma máscara ainda é esperada; a API e os resultados
dos corpora léxicos anteriores permanecem iguais.

`LocatedToken.token` mantém lexema, kind, valor e coordenadas físicas mapeadas;
`LocatedToken.span` acrescenta os caminhos e a pilha de inclusão. Cada
`SourceLocation` tem `file`, `line`, `column` e `inclusion_stack`. Tokens
continuados mantêm os dois extremos originais. Um SourceSpan pode atravessar
arquivos/inclusões: não inferir tamanho subtraindo linhas de arquivos distintos.
Os caminhos da API são absolutos (ou o nome virtual informado); a auditoria
normaliza caminhos internos para relativos, tornando seus artefatos reproduzíveis.

Os caracteres inválidos dentro de uma diretiva removida também são propagados;
expandir COPY não apaga erros léxicos. COPY ausente, ciclo, profundidade excessiva,
falha de leitura e sintaxe inválida têm códigos próprios. A profundidade padrão é
128. COPY REPLACING não ocorre no snapshot; sua presença é rejeitada com
`UNSUPPORTED_COPY_REPLACING`, sem substituição parcial ou aceitação de pseudotexto.

## AST e sintaxe

A [EBNF implementada](gramatica-cobol.ebnf) descreve as formas disponíveis.
Programas e copybooks são raízes distintas: `Program` e `DataFragment`. Os nós
possuem `span` físico e intervalo de tokens `[token_start, token_end)`.

Dados preservam a lista ordenada de cláusulas e a árvore de níveis. `DataItem`
inclui o nome (None para FILLER/itens SCREEN anônimos), nível, filhos, span total
e `declaration_span` da declaração própria. Níveis 88 são filhos do item ao qual
pertencem. FD/SD contêm seus registros. OCCURS guarda mínimo/máximo, DEPENDING,
índices e chaves; PIC preserva máscara e lexema, sem interpretar tipos/tamanhos na fase sintática. A semântica os guarda em tabelas laterais.

`ProcedureDivision.body` mantém sentenças de entrada, seções e parágrafos em ordem.
Cada seção mantém suas sentenças e parágrafos; cada parágrafo mantém sentenças;
cada sentença mantém comandos. Não se cria uma função por parágrafo nem se
descarta fall-through, pois a geração C ainda precisará desses limites.

Referências possuem qualificadores, subscritos e ReferenceModification separados.
Expressões têm nós Literal, Reference, Unary, Binary, Group, Comparison,
ClassCondition, FunctionCall e LengthOf. As condições abreviadas preservam operador,
lado direito e o span do sujeito herdado, em vez de virar números booleanos C.
O sujeito mais recente é herdado no mesmo nível; parênteses abrem contexto próprio.
A semântica resolve referências isoladas a condition-names e vincula sujeitos herdados.

Cada comando e cláusula possui tipo próprio. Por exemplo, READ contém arquivo,
receptor, chave e tratadores; CALL contém parâmetros com modos de passagem;
PERFORM distingue alvo/corpo, THRU, TIMES, UNTIL, VARYING e TEST; EVALUATE mantém
sujeitos e alternativas WHEN. `DISPLAY.operands` intercala posicionamento e
operandos sem reordená-los. Não há `RawStatement`, texto bruto de comandos ou
catch-all que aceite construções desconhecidas. Somente parágrafos descritivos de
identificação, como AUTHOR, guardam palavras de prosa.

O parser exige cabeçalhos de divisão, PROGRAM-ID e seções do ambiente/dados na
área A e reconhece rótulos de procedimentos nessa área. Preserva a posição dos
demais elementos; não impõe uma proibição geral a subitens/comandos na área A,
política compatível com a variação de indentação dos exemplos. Regras adicionais
de estilo estrito podem ser adicionadas por opção, sem deslocar o fonte.

## Diagnósticos e validação

Mensagens incluem arquivo, linha/coluna, construção inesperada, expectativa e
pilha de inclusão. O scanner original continua emitindo seus códigos; o front-end
os adapta com fase `lexer`. COPY usa `preprocessor`; sintaxe usa `parser`.
Erros E/S invalidam a AST pública da respectiva fase. A semântica usa I para
pendências externas e inclui notas de declarações relacionadas, com campos
opcionais compatíveis com a API anterior.

A recuperação sincroniza em pontos, rótulos e novos níveis de declaração. Blocos
EXEC não suportados podem ser saltados até END-EXEC para continuar diagnosticando,
mas sempre registram erro, não criam um nó de extensão válido e nunca contam como
sucesso. Tokens pulados são contabilizados. Delimitadores externos ficam visíveis
a blocos aninhados, como um IF dentro de READ antes de NOT AT END.

Uma AST só é aceita após consumo integral, zero tokens pulados e validação
estrutural. A validação confere intervalos, origem, contenção dos filhos e, de
forma independente, se cada início de comando reconhecido nos tokens tem
exatamente um Statement. Testes removem um comando da árvore para confirmar que
essa verificação acusa a perda.

Isso não substitui semântica. A Etapa 3 verifica referências, tipos, combinações
de cláusulas, FILE STATUS, layouts, assinaturas de intrínsecas, REDEFINES, chamadas
e alvos de controle. A API sintática preserva sua independência dessas verificações.
STRING/UNSTRING, SORT e tela cobrem somente as formas documentadas na EBNF;
diretivas gerais, COPY REPLACING, programas aninhados e EXEC SQL/CICS ficam fora.

## Testes e cobertura obtida

**245 testes passaram** ao fim da Etapa 3: os 149 da Etapa 2 abaixo mais
96 testes semânticos descritos em [semantica.md](semantica.md). A Etapa 2 partiu
dos 80 existentes:

- `test_preprocessor.py`: 12 testes de COPY, caminhos, caixa, inclusão aninhada,
  ciclos/limite, formato fixo, origem e propagação de erros.
- `test_parser.py`: 45 testes de estrutura, expressões, comandos, variantes,
  negativos, recuperação, mutações de entrada e CLI.
- `test_parser_corpus.py`: 12 testes sobre toda a coorte, oficiais, famílias
  complementares, invariantes e consistência dos relatórios.
- Os 80 testes anteriores continuam verificando lexer, CLI léxica, exemplos
  inválidos, manifesto/hashes e a correção isolada do CAD0005A.

As contagens de nós/comandos dos oficiais são verificadas junto com atributos e
relações concretas: linkage/COPY, tabela de 50 em COPY002A, tabela de 10 na agenda,
quatro referências modificadas no CAD0002A, READ com ambos tratadores, dois FD no
PROG024A e CALL PROGDATA com área compartilhada. O corpus complementar é executado
inteiro e não fica limitado a três exemplos escolhidos para passar.

O [relatório de cobertura](auditoria-parser.md) separa **72 programas completos**,
**dois fragmentos**, um arquivo vazio, duas extensões não suportadas e nove
negativos léxicos. Os 77 aceitos anteriormente foram todos submetidos ao parser.
Nenhum resultado exige bibliotecas externas, dados `.dat`, rede ou compilador C.

## Integração semântica e próxima etapa

Consumir `result.ast` somente após `result.success`. Usar visitantes sobre os
nós tipados e tabelas laterais por identidade do nó para símbolos, tipos e layout.
Não refazer análise de strings nem inferir fluxo a partir do nome dos parágrafos.
Preservar os spans e pilhas nas mensagens semânticas, inclusive para declarações
vindas dos copybooks. Condições relativas devem ser vinculadas ao sujeito de
EVALUATE ou à comparação antecedente indicada pela AST.

Implementar na sequência: escopos/qualificações; interpretação PIC/USAGE e layout
de grupos/tabelas/linkage; tipos/conversões; vínculos de arquivos, parágrafos e
CALL; depois runtime e backend C diretamente da AST. A disponibilidade de dados,
bibliotecas e chamadas externas precisa de testes próprios na etapa executável.
