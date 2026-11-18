# Backend C11, runtime e execução — Etapa 4

O pipeline executável é **COPY → lexer → parser → AST → semântica/layout → C11 +
runtime próprio → GCC → executável nativo**. O gerador visita a AST validada e
consome seus vínculos semânticos. Não há IR de instruções, interpretador Python,
bytecode, reanálise do fonte em execução nem dependência de libgmp/libcob.
GnuCOBOL participa somente de comparações independentes nos testes.

## Resultado e requisitos

São necessários Python 3.11+ e GCC com suporte a C11. As interfaces estáticas
continuam funcionando sem GCC. GnuCOBOL é opcional para reproduzir o oráculo.

Os 68 programas semanticamente válidos do corpus foram submetidos ao backend:
**60 compilam (53 executáveis e sete objetos)**, seis dependem de chamadas
externas indisponíveis e dois usam posicionamento de terminal ainda não suportado.
Os 60 incluem os sete oficiais, PROGDATA e 52 complementares. Compilação não
comprova comportamento: **11 programas foram executados e validados em 30
cenários**, incluindo os sete oficiais, PROGDATA e três complementares.
Dos 29 cenários comparáveis, todos coincidem com GnuCOBOL 3.2.0 em stdout, stderr,
retorno e bytes dos arquivos. O cenário restante exige nosso erro de divisor zero.

A execução integral passou com **326 testes**, preservando os 245 anteriores. Os
[resultados por fonte e cenário](auditoria-backend.md) e o
[JSON com evidências](auditoria-backend.json) distinguem análise, geração,
compilação, execução e validação funcional.

## Compilar e executar

```bash
python compiler.py examples/oficiais/CALCMD01.cbl \
  -o build/calcmd01 --emit-c build/calcmd01.c
printf '10\n20\n30\n3\n' | ./build/calcmd01

python compiler.py examples/corrigidos/CAD0005A.cbl -o build/agenda
python compiler.py examples/oficiais/PROG024A.cbl \
  -I examples/dependencias --source examples/dependencias/PROGDATA.cbl \
  -o build/biblioteca --keep-c
```

O programa acessa os arquivos de dados relativos ao diretório de execução.
PROG024A exige `BIBLIOTECA.dat` e `BIBLIOTECA.txt` existentes; OPEN EXTEND de
arquivo ausente produz status 35. Para um ensaio vazio em diretório isolado:

```bash
mkdir -p build/ensaio-biblioteca
touch build/ensaio-biblioteca/BIBLIOTECA.dat build/ensaio-biblioteca/BIBLIOTECA.txt
(cd build/ensaio-biblioteca && \
  printf '9\n' | COBOL_DATETIME=2026-11-17T12:34:56 ../biblioteca)
```

Esses arquivos são preparação explícita do ensaio; o compilador não os cria nem
executa COBOL durante a compilação. Nenhum fonte original foi modificado.
CAD0005A usa a cópia corrigida já existente: o original contém conflito Git.

`python compiler.py` compila por padrão. `python -m cobol_compiler` preserva o
padrão de verificação sintática; `-o`, `--emit-c`, `--keep-c` ou `--module` ativam
a compilação. As opções estáticas `--check-syntax`, `--dump-ast`, `--check`,
`--dump-symbols` e `--dump-layout` continuam disponíveis.

| Opção | Efeito |
|---|---|
| `-I diretório` | Busca configurada de COPY; repetível |
| `--source arquivo` | Unidade COBOL adicional para CALL; repetível |
| `-o caminho` | Executável ou objeto; padrão é o nome do fonte em minúsculas, sem extensão |
| `--emit-c caminho` | Preserva o C gerado e compila |
| `--keep-c` | Preserva C em `<saída>.c` e compila |
| `--module` | Produz objeto sem main para programa chamável |
| `--check-backend` | Verifica geração e dependências, sem GCC nem artefato |
| `--strict` | Exige VALUE conforme contrato semântico estrito |

Erros léxicos, sintáticos, semânticos, de suporte ou ligação impedem GCC. O driver
usa `subprocess.run` com lista de argumentos, timeout e flags `-std=c11 -Wall
-Wextra`. C/objetos temporários ficam junto à saída durante a construção; somente
o artefato bem-sucedido substitui a saída por `os.replace`. Uma falha preserva o
executável anterior. Se GCC falhar sem C explicitamente preservado, o driver grava
`<saída>.failed.c`, captura stderr e emite `GCC_FAILED`. Fontes COBOL, COPY e runtime
são protegidos contra colisões com os caminhos de saída. Sucesso retorna 0;
falha de compilação retorna 1. O compilador não baixa dependências.

## API Python e módulos chamáveis

```python
from cobol_compiler.driver import compile_file

result = compile_file(
    "examples/oficiais/PROG024A.cbl", "build/biblioteca",
    include_dirs=["examples/dependencias"],
    source_paths=["examples/dependencias/PROGDATA.cbl"],
    emit_c="build/biblioteca.c",
)
for diagnostic in result.diagnostics:
    print(diagnostic.format())
if not result.success:
    print(result.gcc_stderr)
```

`compile_result(semantic_result, ...)` usa uma análise já concluída.
`CompilationResult` mantém análise, geração, diagnósticos, comando GCC,
stdout/stderr, caminho do C e artefato final. `check_backend=True` testa geração
sem invocar GCC. `semantic.backend_ready` é uma propriedade estática: não promete
suporte do backend, disponibilidade de GCC ou comportamento funcional.

CAD0002A é um subprograma com PROCEDURE DIVISION USING, sem entrada independente:

```bash
python compiler.py examples/oficiais/CAD0002A.cbl -I examples/dependencias \
  --module -o build/cad0002a.o --keep-c
python -m tools.comparar_gnucobol
```

O objeto exporta uma função C com nome estável derivado do PROGRAM-ID por
`c_codegen.function_name`, assinatura
`int programa(cb_runtime *, cb_field *, size_t)`. Um host inicializa
`cb_runtime_init`, fornece views com tamanhos corretos, chama a função e encerra
com `cb_runtime_destroy`; deve ligar os três arquivos do runtime. O teste de ABI
inclui um host C real. A ferramenta de cenários usa um driver **COBOL** que aloca
COPY002A-REGISTRO, chama o CAD0002A original e verifica as alterações após GOBACK.
O objeto não inventa main nem armazenamento local para LINKAGE.

## Armazenamento, números e conversões

`cb_field` é uma view `{ponteiro, comprimento, descritor}`. Grupos, tabelas,
REDEFINES e LINKAGE compartilham áreas contíguas descritas pelo layout semântico.
Não se usa NUL para medir campos COBOL. MOVE alfanumérico/de grupo copia bytes,
preenche espaços e trunca à direita; comparações alfanuméricas consideram padding.
MOVE captura a origem antes de escrever destinos sobrepostos. INITIALIZE ignora
FILLER e aliases REDEFINES e aplica as conversões REPLACING resolvidas.

| Representação | Contrato |
|---|---|
| DISPLAY numérico | Dígitos de largura fixa, escala implícita e sinal overpunch no último byte |
| COMP/BINARY | Little-endian, complemento de dois quando assinado; largura definida pelo layout (2/4/8 bytes até 4/9/18 dígitos, ampliada para campos maiores) |
| COMP-3 | Packed decimal, dois nibbles por byte e sinal C/D; F aceito na leitura |
| PIC editado | Supressão Z, dígitos obrigatórios, sinais fixos e separadores de acordo com DECIMAL-POINT; zero em máscara só Z vira espaços |
| Expressão numérica | Racional exato, numerador/denominador em vetores de dígitos; conversão somente ao armazenar |

Campos aceitam até **128 dígitos**; cada inteiro intermediário tem capacidade
checada de **512 dígitos**. `(1 / 3) * 3` permanece exato antes do armazenamento;
PIC 9(28) não passa por int64 ou ponto flutuante. Atribuição trunca na escala do
receptor; ROUNDED arredonda à metade afastando de zero. ON SIZE ERROR detecta
overflow/divisão por zero e conserva o receptor afetado; sem tratamento, erros
aritméticos fatais terminam com diagnóstico. MOVE numérico fora da largura aplica
truncamento de dígitos conforme o contrato testado. IS NUMERIC examina a
representação física, inclusive packed/overpunch, sem conversão permissiva.

As áreas têm limite de **64 MiB**. Subscritos base 1, quantidade ativa de OCCURS
DEPENDING ON, refmod e comprimentos são checados. Uma violação dinâmica termina
com código, caminho, linha e coluna do comando COBOL. Cada caso do dispatcher
emite `cb_origin`; o C preservado contém esse mapa. GCC continua reportando suas
próprias linhas de C em stderr quando a construção falha.

## Controle e chamadas

Cada programa tem um dispatcher C com posição e pilha explícita de retorno/limite
de PERFORM. A visita da AST emite os casos e transições diretamente. Parágrafos
preservam a ordem e o fall-through; PERFORM de seção retorna no limite da seção,
inclusive em chamadas aninhadas e recursivas da própria seção. EXIT isolado é
no-op. GO TO transfere a posição; GOBACK retorna ao chamador e STOP RUN encerra a
unidade de execução. EXIT PROGRAM retorna em subprograma e é no-op no principal.
TIMES, UNTIL, TEST BEFORE/AFTER, VARYING/AFTER e saídas de loop têm testes próprios.
As pilhas de controle têm limite checado de 4096 entradas e CALL de 16 ativações.

WORKING-STORAGE persiste entre chamadas; LOCAL-STORAGE é inicializado por
ativação; LINKAGE aponta para a área do chamador. BY REFERENCE compartilha bytes,
BY CONTENT copia e BY VALUE numérico converte para o descritor formal. RETURN-CODE
é independente por ativação e o retorno da chamada atualiza o chamador. Literais
usam temporários com ABI conhecida. Dependências devem ser fornecidas por
`--source`; chamadas não resolvidas e PROGRAM-ID duplicado falham antes de GCC,
sem stubs ou assinaturas inventadas. A implementação não promete chamadas
concorrentes ao mesmo armazenamento estático de programa.

## Terminal, arquivos, intrínsecas e relógio

Dados internos e registros usam **ISO-8859-1**, coerente com o comprimento em bytes
do layout. Literais Unicode precisam ser representáveis nessa codificação.
Por padrão, ACCEPT/DISPLAY convertem UTF-8 na fronteira do terminal;
`COBOL_TERMINAL_ENCODING=latin1` seleciona bytes brutos. Entrada Unicode não
representável, NUL e EOF inesperado recebem erros explícitos. NO ADVANCING faz
flush. ACCEPT numérico respeita o separador decimal do programa; dados inválidos
podem ser examinados por IS NUMERIC antes de uma operação aritmética.

Handles de arquivo são separados dos registros. LINE SEQUENTIAL lê até LF,
remove CR quando parte de CRLF, preenche registros curtos e detecta excesso;
escreve todos os bytes do registro, incluindo espaços finais, seguidos de LF.
SEQUENTIAL fixo usa bytes sem delimitador. OPEN INPUT/OUTPUT/EXTEND, READ INTO,
WRITE e CLOSE mantêm status e EOF. INPUT e EXTEND exigem arquivo existente;
OUTPUT cria/trunca. Erros sem FILE STATUS/tratamento são fatais.

| FILE STATUS | Significado |
|---|---|
| 00 / 04 | Sucesso / comprimento de registro divergente |
| 10 / 30 / 35 | EOF / falha de I/O / arquivo ausente |
| 41 / 42 | Já aberto / não aberto |
| 47 / 48 | Modo incompatível com leitura / escrita |

REVERSE e LENGTH preservam padding/tamanho físico; ORD é base 1; INTEGER e MOD
usam piso. Datas gregorianas abrangem 1601–9999. UPPER/LOWER-CASE tratam Latin-1.
RANDOM usa LCG de 32 bits e resultado racional exato; sua sequência é contrato do
projeto e não promete igualdade com outros compiladores. Potência aceita expoente
inteiro até módulo 4096. SEARCH ALL valida ordenação e usa busca linear equivalente
no subconjunto de chave única; não promete custo de busca binária.

DATE, DAY, DAY-OF-WEEK e TIME usam relógio local; para testes:
`COBOL_DATETIME=2026-11-17T12:34:56`. O driver PROGDATA também verifica os campos
que o fonte deixa inicializados, sem preencher valores ausentes artificialmente.

## Testes reproduzíveis e limites

```bash
python -m unittest discover -s tests -v
python -m tools.auditar_backend --write
python -m tools.comparar_gnucobol
python -m tools.auditar_backend --write --no-oracle
```

As ferramentas preparam fixtures em diretórios temporários e aplicam timeout de
execução. O oráculo usa os mesmos bytes, entrada e relógio, com
`COB_CURRENT_DATE=20261117123456`, `COB_LS_FIXED=Y`, `COB_LS_NULLS=N` e
`COB_LS_VALIDATE=N`. Não se removem espaços nem se normalizam saídas para obter
igualdade. Os cenários ainda verificam expectativas próprias sem GnuCOBOL.

Os 81 testes novos são: 13 provas do runtime C, 34 programas/contratos de geração,
30 cenários oficiais/complementares, uma comparação opcional e três testes da
auditoria. O runtime é compilado com `-Wall -Wextra -Werror` nas provas. Há casos
de overflow, divisor zero, bounds, EOF, arquivo ausente e falhas reais de leitura
e escrita. A tentativa com ASan/UBSan não chegou a executar: as bibliotecas
`libasan.so.8.0.0` e `libubsan.so.1.0.0` faltavam no ambiente. Não se declara
validação por sanitizadores; `sanitize=True` permanece opção da API para ambiente
que disponha dessas bibliotecas.

Recursos já rejeitados pela semântica incluem SCREEN, ALTER, SORT, START,
INDEXED/RELATIVE, acesso DYNAMIC/RANDOM, COMP-1/2 e POINTER. SQL/CICS e extensões
fora da gramática permanecem diagnosticadas. O backend também rejeita antes de
GCC: DISPLAY posicionado, SELECT OPTIONAL, WRITE ADVANCING, máscaras editadas com
0/B/barra/asterisco/moeda, INSPECT com múltiplos padrões de substituição,
UNSTRING sem delimitador, SEARCH complexo/aninhado ou com chave composta,
LENGTH de grupo variável, LENGTH numérico sem armazenamento, expressões
fracionárias em contextos textuais sem receptor numérico e GO TO saindo de
PERFORM inline. ROUNDED com REMAINDER é recusado. Limites de capacidade e dados
inválidos dependentes da entrada produzem diagnósticos do runtime.

O fonte corrigido de CAD0005A oferece adicionar/listar, sem opção de exclusão. A exclusão de
registro sequencial foi ensaiada no complementar PROG039A; os outros adicionais
são PROG012A (refmod/texto) e PROG020A (SEARCH ALL). Esses três ensaios não
substituem os três exemplos que serão escolhidos pelo professor. Os demais
programas apenas compilados precisam de novas fixtures para validação funcional.
