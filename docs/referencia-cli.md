# Referência da linha de comando

Execute os comandos da raiz do repositório. `python compiler.py fonte` compila por padrão. `python -m cobol_compiler fonte` verifica sintaxe por padrão. Ambos aceitam as mesmas opções. As opções de saída ativam a compilação também na entrada por módulo.

## Opções

| Opção e argumento | Padrão | Finalidade e exemplo |
|---|---|---|
| `file` | Obrigatório | Fonte principal, por exemplo `examples/oficiais/CALCMD01.cbl`. |
| `-h`, `--help` | Desativado | Exibe a ajuda. Exemplo `python compiler.py --help`. |
| `--source-format fixed` ou `free` | `fixed` | Seleciona formato físico. Use `--source-format free` para CBREAKEX. |
| `--dialect project` ou `gnucobol` | `project` | Seleciona o [perfil de recursos](recursos-suportados.md#perfis). Exemplo `--dialect gnucobol`. |
| `-I DIR`, `--include-dir DIR` | Só a busca local ao fonte que inclui | Acrescenta diretórios para COPY, em ordem e de forma repetível. Exemplo `-I examples/dependencias`. |
| `--source ARQUIVO` | Nenhuma unidade adicional | Integra fonte de outro programa. Repetível. Exemplo `--source examples/dependencias/PROGDATA.cbl`. |
| `--check-syntax` | Ativo na entrada por módulo sem outra ação | Expande COPY, analisa léxico e sintaxe e valida a AST. |
| `--dump-ast` | Desativado | Faz a análise sintática e escreve a AST tipada em JSON. |
| `--check` | Desativado | Verifica semântica e layout sem gerar o executável. |
| `--dump-symbols` | Desativado | Emite tabela de símbolos e vínculos em JSON. |
| `--dump-layout` | Desativado | Emite o layout físico, áreas e campos em JSON. |
| `--check-backend` | Desativado | Verifica geração C e os requisitos de resolução do modo escolhido, sem invocar GCC. |
| `--strict` | Desativado | Exige VALUE nos campos elementares abrangidos pelo contrato estrito. Use `--check --strict`. |
| `--copybook` | Automático para `.cpy` na análise sintática | Analisa o arquivo como fragmento de declarações. Útil com `--dump-ast`. |
| `--debug-lines` | Desativado | Analisa linhas D na coluna 7 do formato fixo. |
| `-o CAMINHO`, `--output CAMINHO` | Nome do fonte em minúsculas, sem extensão | Define o artefato. Exemplo `-o build/calcmd01`. Com `--shared`, o padrão é PROGRAM-ID em maiúsculas com `.so`, quando o nome permite. |
| `--emit-c CAMINHO` | C temporário | Compila e preserva o C indicado. Exemplo `--emit-c build/calcmd01.c`. |
| `--keep-c` | Desativado | Compila e guarda o C em `<saída>.c`. |
| `--module` | Executável principal | Produz objeto chamável sem main. Com `-o build/PROGDATA.so`, produz módulo compartilhado. |
| `--shared` | Desativado | Seleciona um módulo compartilhado. Exemplo `--shared -o build/modulos/PROGDATA.so`. |
| `--static-call` | Padrão de executáveis e objetos no perfil `project` | Exige destinos resolvidos no build. Forneça os fontes com `--source`. |
| `--dynamic-call` | Padrão no perfil `gnucobol` e para módulos compartilhados | Adia chamadas pendentes até a execução. Também funciona no perfil `project`. |
| `--module-dir DIR` | Nenhum diretório embutido | Acrescenta diretório para módulos COBOL. Repetível. Exemplo `--module-dir build/modulos`. |
| `--library NOME` | Nenhuma biblioteca C explícita | Aceita caminho, SONAME ou o conjunto de contratos `ncurses`. Repetível. Exemplo `--library ncurses`. |
| `--ffi-manifest ARQUIVO` | Nenhum manifesto | Lê assinaturas C em JSON. Repetível. Exemplo `--ffi-manifest build/ffi.json`. |

Use uma ação de verificação ou dump por vez. `--static-call` e `--dynamic-call` são mutuamente exclusivos. Para verificar e gerar um binário, faça invocações separadas.

```bash
python -m cobol_lexer examples/oficiais/CALCMD01.cbl --json
python -m cobol_compiler examples/oficiais/CALCMD01.cbl --dump-ast
python -m cobol_compiler examples/oficiais/CAD0002A.cbl -I examples/dependencias --dump-symbols
python -m cobol_compiler examples/oficiais/CAD0002A.cbl -I examples/dependencias --dump-layout
python -m cobol_compiler examples/dependencias/COD001A.cpy --copybook --dump-ast
python -m cobol_compiler examples/complementares/CBREAKEX.cbl --dialect gnucobol --source-format free --check-backend
```

O lexer isolado trabalha em formato fixo. `--json` emite tokens e diagnósticos e `--stream` agrupa tokens por linha. Sem essas opções, imprime o resumo. `--debug-lines` inclui linhas D.

Diagnósticos saem em stderr. Sucesso retorna 0, erro de compilação retorna 1 e erro de uso retorna 2. Na entrada de verificação, erros de leitura também podem retornar 2. Se GCC falhar, o driver conserva o artefato anterior e guarda `<saída>.failed.c` quando o C ainda não foi preservado.

## Busca em tempo de execução

| Variável | Padrão | Efeito e exemplo |
|---|---|---|
| `COBOL_MODULE_PATH` | Vazia | Lista de diretórios separados por `:` para módulos próprios. Exemplo `COBOL_MODULE_PATH=../modulos` no diretório de dados do exemplo da biblioteca. |
| `COBOL_TERMINAL_ENCODING` | UTF-8 na fronteira do terminal | `COBOL_TERMINAL_ENCODING=latin1` seleciona bytes Latin-1 brutos. |
| `COBOL_DATETIME` | Relógio local | Fixa a data e hora do runtime. Exemplo `COBOL_DATETIME=2026-11-17T12:34:56`. |
| `TERM` | Herdado do terminal | Usado pela biblioteca ncurses quando chamada. O comparador fixa `TERM=ansi` em PTY. |

O carregador procura `PROGRAM-ID.so` em maiúsculas nos diretórios passados com `--module-dir` pela unidade, depois nos do executável e em `COBOL_MODULE_PATH`. Componentes vazios são ignorados. O primeiro arquivo encontrado precisa oferecer o descritor da ABI própria e a entrada solicitada. Para instalar o módulo depois do build, conserve esse nome no diretório de busca. `COB_LIBRARY_PATH` pertence ao GnuCOBOL.

Os caminhos de dados relativos de SELECT partem do diretório de execução. Veja no [README](../README.md#copy-arquivos-e-módulos) como preparar os dados e rodar um chamador com módulo separado.

## Manifesto FFI

O manifesto é uma lista JSON. Cada assinatura exige `name`, `returns` e `params`. `library` aceita SONAME ou caminho. Um caminho relativo com barra parte do diretório do manifesto. Sem biblioteca, o adaptador busca um símbolo no processo. `abi` aceita `c`, o padrão. `varargs` indica a sequência exata de tipos adicionais já promovidos. `format` pode validar o último argumento fixo como `printf` ou `scanf`.

| Tipo | Contrato |
|---|---|
| `int` | Inteiro C de 32 bits. Argumento BY VALUE dentro da faixa. |
| `bool` | `_Bool`. Argumento fixo BY VALUE com valor 0 ou 1. |
| `pointer` | `void *` opaco. Argumento BY VALUE ou receptor RETURNING de USAGE POINTER. |
| `cstring` | Cópia de texto em Latin-1, com padding e terminador NUL. Argumento por referência ou conteúdo. |
| `raw:N` | Buffer com pelo menos N bytes. BY REFERENCE passa os bytes originais e BY CONTENT passa a cópia. |
| `out-int` | Temporário `int *` para atualizar campo inteiro BY REFERENCE. A função precisa retornar `int`. |
| `void` | Válido somente como retorno. |

Os retornos do manifesto são `int`, `pointer`, `window` ou `void`. A lista aceita até 64 argumentos fixos e adicionais somados. A validação de `printf` abrange `%d`, `%s` e `%%`. A de `scanf` aceita `%d` com destino `out-int` declarado e `%%`. O contrato precisa corresponder ao protótipo real. Veja [ABI e duração de buffers](arquitetura.md#call-linkage-e-abi).

Exemplo com o símbolo `abs` da libc, disponível no processo:

```bash
mkdir -p build
cat > build/ffi.json <<'JSON'
[{"name":"abs","returns":"int","params":["int"]}]
JSON
cat > build/ffi.cbl <<'COBOL'
IDENTIFICATION DIVISION.
PROGRAM-ID. DEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 ANSWER PIC 99.
PROCEDURE DIVISION.
    CALL 'abs' USING BY VALUE -42 RETURNING ANSWER
    DISPLAY ANSWER
    STOP RUN.
COBOL
python compiler.py build/ffi.cbl --source-format free --dialect gnucobol \
  --ffi-manifest build/ffi.json -o build/ffi
./build/ffi
```

O exemplo imprime `42`. Para os contratos predefinidos de ncurses, use `--library ncurses`. A resolução ocorre no binário, com `libncurses.so.6` disponível no sistema.

## Validação reproduzível

```bash
python -m tools.auditar_funcional --officials --no-oracle
python -m tools.auditar_compatibilidade --compile-only --write
python -m tools.auditar_compatibilidade --execution-gaps --write
```

O primeiro comando roda os cenários oficiais com expectativas próprias. O segundo reconstrói a matriz de compilação comparada. O terceiro repete a divisão por zero e os seis casos de CALL externo, incluindo os prefixos seguros de ncurses. Ambos os modos de comparação requerem GnuCOBOL. `--write` gera JSON e Markdown em `build/`. Execute `python -m tools.auditar_compatibilidade --write` para o conjunto completo e `--help` nos validadores para ver as opções de seleção e salvamento.
