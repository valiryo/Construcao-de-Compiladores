# Análise semântica e armazenamento — Etapa 3

O front-end implementa COPY → lexer → parser → AST → semântica/layout em Python
3.11+, sem dependências externas. Os sete oficiais são semanticamente válidos;
CAD0005A usa a cópia corrigida já documentada. A auditoria visita os 86 arquivos
do snapshot, analisa os 72 programas parseáveis e valida 68 deles, dos quais seis
têm pendências externas. Os dois copybooks são analisados nas inclusões.

Os números e as justificativas por fonte estão na
[auditoria reproduzível](auditoria-semantica.md) e em seu
[JSON completo](auditoria-semantica.json). Ao fim da Etapa 3 eram **245 testes**:
149 anteriores e 96 novos. Esses resultados atestam análise estática. A Etapa 4
acrescenta [runtime e compilação C/GCC](backend.md), com
[auditoria de execução separada](auditoria-backend.md).

## Perfil de compatibilidade — Etapa 7

`check_file` e `check_source` propagam `source_format` e `dialect`; os padrões
anteriores permanecem. Em `dialect="gnucobol"`, FD DATA RECORD(S) resolve referências
que devem pertencer ao próprio FD. PIC com sequência inicial de + ou -, inclusive
agrupamento, ganha precisão/layout sem float; misturas com Z, *, moeda ou uso
binário/packed são rejeitadas. SCREEN permite PIC textual/inteiro sem sinal ou
escala, USING gravável, LINE/COLUMN e BLANK SCREEN. CURSOR exige 4/6 posições e
CRT STATUS um inteiro de pelo menos quatro dígitos. As referências continuam
vinculadas nas tabelas laterais e o gerador consome os símbolos resolvidos.
Os diagnósticos padrão e os layouts/strides existentes são preservados.

Veja a [auditoria da Etapa 7](compatibilidade-gnucobol.md) para métricas, limites
e comandos; as contagens anteriores desta página são históricas.

## API e CLI

```bash
python -m cobol_compiler examples/oficiais/CALCMD01.cbl --check
python -m cobol_compiler examples/oficiais/CAD0002A.cbl \
  -I examples/dependencias --dump-layout
python -m cobol_compiler examples/oficiais/PROG024A.cbl \
  -I examples/dependencias --source examples/dependencias/PROGDATA.cbl \
  --dump-symbols > /tmp/prog024a-symbols.json
python -m tools.auditar_semantica --write
python -m unittest discover -s tests -v
```

`--source` e `-I` podem se repetir. O compilador só analisa os caminhos fornecidos;
não procura implementações de CALL em disco ou na rede. O auditor escolhe fontes
dentro do inventário fixado, por PROGRAM-ID e fechamento das chamadas literais.
`--strict` exige VALUE em itens elementares. O padrão da CLI continua sendo
`--check-syntax`; `--dump-ast` e a API de parsing continuam independentes da semântica.

```python
from cobol_compiler import check_file
from cobol_compiler.ast import Reference, walk

result = check_file(
    "examples/oficiais/PROG024A.cbl",
    include_dirs=["examples/dependencias"],
    source_paths=["examples/dependencias/PROGDATA.cbl"],
)
assert result.success and result.backend_ready
for node in walk(result.ast):
    if isinstance(node, Reference):
        binding = result.annotation(node)
        if binding.symbol_id:
            symbol = result.table.symbols[binding.symbol_id]
            layout = result.layout.items.get(binding.layout_id)
```

`analyze(frontend, sources=[outros_frontends], strict=False)` recebe resultados de
`parse_file`/`parse_source`. `check_source(text, filename=..., sources=...)` combina
parsing e semântica em memória. `SemanticResult` expõe:

| Atributo | Contrato |
|---|---|
| `frontend` | Parsing original, inclusive AST para depuração de falhas semânticas |
| `success` | Front-end válido e nenhum diagnóstico E/S nas unidades fornecidas |
| `ast` | AST pública somente quando `success`; nunca árvore de recuperação |
| `backend_ready` | Validade estática e nenhuma dependência de chamada pendente; não indica existência de backend |
| `table.symbols` | Símbolos por identidade; `table.candidates` consulta nomes/qualificações para depuração |
| `layout.items`, `layout.areas` | Descritores físicos e capacidades máximas, incluindo áreas externas |
| `annotation(node)` | Tipo, símbolo, escrita, layout, conversões, checks e vínculos do nó |
| `files`, `calls`, `controls`, `parameters` | Associações e contratos já resolvidos |
| `source_results` | Resultados das outras unidades; referências entre resultados podem formar ciclos |
| `pending_externals` | Chamadas externas/dinâmicas ou com dependências transitivas pendentes |
| `diagnostics` | Diagnósticos do front-end e da semântica, inclusive fontes adicionais |
| `dump_symbols()`, `dump_layout()` | Estruturas JSON, sem serializar recursivamente `source_results` |

Dumps com erros continuam disponíveis para inspeção, identificados por
`success: false`; a CLI retorna 1. Falha de leitura retorna 2; sucesso retorna 0,
inclusive validade local com chamada externa informativa. Nenhum comando invoca GCC.

## Passagens e tabelas laterais

1. Enumerar nós em pré-ordem (`n0`, `n1`...) e declarar símbolos (`s0`, `s1`...).
   Os IDs são estáveis para a mesma AST e locais à unidade, sem modificar os nós.
2. Construir hierarquias, PIC/USAGE, armazenamento e parâmetros formais de todas
   as unidades antes de analisar seus corpos. Isso permite referências futuras.
3. Vincular SELECT/FD, chaves/status, expressões, destinos, rótulos e chamadas;
   validar condições, comandos e tratadores aninhados.
4. Propagar falhas e pendências de dependências. Conferir independentemente que
   todo Expr tem tipo/papel e todo Statement foi visitado. Nós sem implementação
   recebem erro explícito.

`symbols.py` contém as tabelas e a resolução; `types.py`, PIC e tipos;
`layout.py`, os descritores físicos; `semantic.py`, a coordenação e validações.
Não há IR de instruções. O gerador C consome a AST e suas anotações, sem
resolver nomes nem inferir tipos novamente.

Os namespaces são programa, dados (grupos e campos), arquivos, seções, parágrafos,
condições 88, índices e registradores especiais. FILLER tem identidade e layout,
mas nenhum nome utilizável. Caixa é normalizada para busca; a grafia original e
a declaração são preservadas. Qualificadores OF/IN correspondem a ancestrais na
ordem informada e podem omitir níveis intermediários. Duplicatas no mesmo escopo
são erros; homônimos em hierarquias diferentes exigem qualificação se ambíguos.

Os dois TAB-ENT-LINHA do PROG024A são pai/filho válidos, sem referência ambígua
usada pelo programa. Parágrafos homônimos em seções distintas também permitem
qualificação. Rótulos guardam limites de tokens, entrada, pai e fall-through.
PERFORM guarda alvo, limite THRU e retorno ao sucessor do próprio comando para a
pilha explícita do backend. EXIT isolado é no-op; GOBACK e STOP RUN têm efeitos distintos.

## PIC e ABI do projeto

`CobolType` separa categoria, comprimento físico em bytes, precisão/escala/sinal,
edição, máscara original/expandida, convenção decimal, USAGE e representação.
Tipos de expressões numéricas usam precisão arbitrária; não existe conversão para
float/int64 durante a análise. Soma/subtração reservam carry e alinham escalas;
produto soma precisões e escalas. Divisão e potência mantêm limites não determinados
(`None`) e representação exata até a atribuição ao receptor. Não são cálculos dos
valores do programa. ROUNDED, escala do receptor e verificação de capacidade ficam
anotados para o runtime.

| Representação | Bytes e regras |
|---|---|
| X/A/DISPLAY | Um byte ISO-8859-1 por posição; sem NUL e sem padding de alinhamento |
| 9/S/V | Dígitos físicos; S é overpunch no dígito final, V implícito, sem bytes adicionais |
| Z, sinais e separadores editados | Símbolos físicos preservados, precisão e escala separadas; DECIMAL-POINT altera o separador decimal |
| COMP/COMP-4/BINARY/COMPUTATIONAL | Little-endian, 2 bytes até 4 dígitos, 4 até 9, 8 até 18; acima, mínimo de bytes para os dígitos e um bit de sinal |
| COMP-5 | Mesmas larguras explícitas de COMP neste ABI, sem depender do host |
| COMP-3/PACKED-DECIMAL | `ceil((dígitos + 1)/2)` bytes, nibble final de sinal |
| INDEX/INDEXED BY | Inteiro de 8 bytes, ordinal de base 1, associado à tabela, inicialização em 1 |
| RETURN-CODE/SORT-RETURN | Registradores especiais numéricos S9(9) COMP; o backend terá acesso próprio a eles |

Esta é uma ABI definida pelo projeto, não uma promessa de interoperabilidade
binária com compiladores externos. COMP-1/2, POINTER, edição flutuante de
sinais/moedas repetidos e símbolos PIC fora do subconjunto recebem diagnóstico.
A expansão de PIC é limitada a 100000 posições; OCCURS, a 1000000 entradas.
O gerador ainda deverá testar o código de overpunch, packed e conversões exatas.

O arquivo fonte continua sendo UTF-8 lido pelo front-end. Para dados/literais, a
política inicial é ISO-8859-1: caracteres acentuados representáveis ocupam um byte;
literais não representáveis são rejeitados. Não se usa `len(texto Python)` como
largura de um buffer UTF-8 gerado. O runtime aplica essa codificação e converte UTF-8 na fronteira do terminal.

## Armazenamento e inicialização

`StorageLayout` guarda área, offset da primeira ocorrência, tamanho unitário,
tamanho total, pai, dimensões, alias e política inicial. Cada dimensão guarda
mínimo/máximo, stride, base 1 e símbolo DEPENDING. Subscrever um campo anota seus
índices e a fórmula de endereço por dimensões; não recalcula nomes no backend.

Grupos são contíguos. A reserva de OCCURS é a capacidade máxima, mesmo quando
DEPENDING limita o número ativo; bounds ativos são verificados em runtime.
REDEFINES usa o mesmo offset e reserva a maior extensão entre as views. Não há
alinhamento implícito. Registros alternativos de um FD começam em zero na mesma
área de arquivo, que reserva o maior registro. Níveis 77 são elementares; níveis
88 são condições do campo anterior e não recebem layout próprio.

Cada raiz LINKAGE é uma área externa independente, exceto aliases REDEFINES.
`local=false` proíbe tratá-la como working-storage; USING vincula as raízes formais
às áreas do chamador. A raiz COPY002A-HEADER não é parâmetro de CAD0002A e deve ser
fornecida por mecanismo de ligação apropriado se vier a ser acessada; não se
inventa armazenamento local para ela. Os oficiais atuais usam COPY002A-REGISTRO.

Sem VALUE, armazenamento local recebe política `zero` para numéricos e `spaces`
para texto; grupos contêm as políticas de seus filhos. VALUE referencia o nó
sintático para aplicar a constante exata; aliases não reinicializam bytes e
LINKAGE preserva o conteúdo externo. INITIALIZE lista receptores elementares,
ignora FILLER e views REDEFINES e guarda conversões de REPLACING. Não há escrita
real em memória nesta etapa.

`LENGTH OF` de item com OCCURS mede uma ocorrência, conforme a
[referência IBM](https://www.ibm.com/docs/en/i/7.5.0?topic=statement-length-special-register).
Anotações distinguem comprimento constante, máximo e dimensões variáveis de grupos;
comprimentos dependentes de execução não são dobrados em constantes. Índices de
outra tabela só são aceitos com quantidade e stride compatíveis, segundo o
[contrato de indexação](https://www.ibm.com/docs/en/cobol-zos/6.5.0?topic=table-indexing).

## Operações, arquivos e chamadas

MOVE valida destinos e categorias, com a proibição PIC A → numérico exigida pelo
professor. MOVE de grupo guarda cópia por bytes; conversões numéricas/textuais,
preenchimento e truncamento são anotados por receptor. CORRESPONDING guarda pares
já resolvidos de folhas, respeitando nomes e hierarquia e excluindo tabelas/views.
Condições abreviadas e testes WHEN relativos apontam ao sujeito efetivo. Condition-names
88 são booleanos e somente SET pode alterar a condição via campo associado.

Subscritagem exige número correto de índices inteiros; constantes fora dos
limites são erros, expressões dinâmicas recebem checks. Refmod valida categoria,
início/comprimento e resultado alfanumérico. Divisão, datas, capacidade numérica,
STRING/UNSTRING e modo de arquivo têm checks próprios. REVERSE, UPPER/LOWER-CASE,
LENGTH, MOD, ORD, INTEGER, INTEGER-OF-DATE, DATE-OF-INTEGER e RANDOM têm assinaturas
e tipos; funções desconhecidas bloqueiam a unidade. SEARCH ALL aceita igualdade
simples com uma chave ordenada e guarda índices/chaves e contrato de ordenação.

Arquivos associam SELECT, ASSIGN, FD/SD, registros, organização, acesso, status e
cláusulas de chave. ASSIGN com nome externo não é confundido com variável não
declarada. READ/WRITE/OPEN/CLOSE vinculam arquivo/registro; FILE STATUS exige dois
bytes DISPLAY. Um READ em programa que só declara OPEN OUTPUT é incompatível;
a ordem e o estado de OPEN em cada caminho permanecem checks de runtime, sem
simular entradas. Não se abre nenhum arquivo de dados nesta etapa.

CALL disponível verifica quantidade, modos, bytes, tipos elementares e ABI das
folhas de grupos, sem comparar seus nomes. Passagem de ocorrência de tabela
considera apenas as dimensões não consumidas. Literais por referência usam
metadados de temporário; BY VALUE numérico usa o descritor formal para conversão.
O vínculo guarda símbolos formais/atuais e modos. Chamadas externas/dinâmicas
mantêm nome original, argumentos e pendência de assinatura; não recebem assinatura
inventada. Erros em fontes adicionais bloqueiam o resultado; pendências são
propagadas transitivamente. A análise estática não faz ligação nem executa subprogramas; o driver da Etapa 4
rejeita pendências antes de GCC e liga somente implementações fornecidas.

## Diagnósticos, cobertura e próxima etapa

Diagnósticos mantêm fase, severidade I/W/E/S, SourceSpan, inclusão COPY e notas de
declarações relacionadas. Códigos `UNDEFINED_SYMBOL`, `AMBIGUOUS_REFERENCE`,
`CALL_LAYOUT_MISMATCH`, `VALUE_OUT_OF_RANGE` e similares indicam erros no fonte;
`UNSUPPORTED_*` indica limite do compilador; `EXTERNAL_CALL_PENDING` é informativo.
Qualquer E/S impede a AST semântica pública e `backend_ready`.

A classificação dos 72 programas é: 62 válidos com dependências disponíveis,
seis válidos com chamadas externas, três inválidos por erros no fonte e um
parcialmente suportado. Os demais 14 arquivos são dois copybooks contextuais,
dois SQL/CICS e dez negativos anteriores (incluindo o vazio). Nenhum erro foi
resolvido alterando um original ou relaxando a verificação de nomes/tipos.

Os 96 testes semânticos cobrem PIC/ABI (14), resolução/operações/layout (47),
arquivos/chamadas/CLI (25) e integração/auditoria completa (10). Os 149 testes
anteriores continuam passando. A auditoria registra também 2480 símbolos,
4257 referências vinculadas e 1490 layouts nos programas visitados.

SCREEN, ALTER, SORT, START, arquivos INDEXED/RELATIVE/acesso DYNAMIC ou RANDOM,
COMP-1/2 e POINTER ficam explicitamente bloqueados. Formas complexas de SEARCH ALL,
funções não listadas, SQL/CICS e extensões fora da gramática também são diagnosticadas.
Isso não impede analisar suas referências disponíveis e conservar layouts para
inspeção; esses resultados nunca são tratados como programas válidos.

A Etapa 4 implementa runtime decimal/string/edição, checks dinâmicos, dispatcher
e pilha de PERFORM, linkage e CALL, I/O e relógio controlável, geração C direta
da AST e driver GCC. Seus testes cobrem os sete oficiais, PROGDATA e três
complementares, overflow, EOF, erros de I/O, bytes e acentos; os resultados estão
na [auditoria do backend](auditoria-backend.md). GnuCOBOL é somente oráculo opcional.

O auditor termina com código 1 se um programa antes parseável regredir ou apresentar
uma falha semântica inesperada. Os quatro casos negativos novos são expectativas
individuais documentadas, sem impedir a visita de qualquer fonte.
