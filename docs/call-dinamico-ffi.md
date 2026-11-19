# CALL dinâmico, módulos compartilhados e funções C

O perfil `--dialect gnucobol` gera executáveis com CALLs ainda sem implementação. O runtime tenta resolver cada chamada quando o fluxo chega a ela. O perfil `project` exige resolução no build para executáveis e objetos por padrão. `--dynamic-call` seleciona a resolução em execução nesse perfil, e `--static-call` exige definições COBOL fornecidas via `--source` em ambos os perfis. Módulos compartilhados aceitam resolução em execução por padrão.

O comportamento foi comparado com GnuCOBOL 3.2 nos testes de instalação posterior de módulos, CALL por variável, tratadores e retorno inteiro de funções C. Os módulos próprios usam a interface do runtime do projeto. Veja a [documentação de ligação dinâmica do GnuCOBOL](https://gnucobol.sourceforge.io/doc/gnucobol.html#Dynamic-linking).

## Resolução e execução

1. Um CALL literal ligado a uma definição conhecida usa a função C gerada para aquele programa. O analisador verifica a aridade e os layouts antes de GCC.
2. Para outros CALLs, o runtime consulta as entradas COBOL da unidade, as integradas ao executável e as já carregadas. A busca por PROGRAM-ID usa caixa alta ASCII. Espaços finais do campo com o nome são removidos.
3. Um contrato de FFI explícito para a grafia exata liga o destino à biblioteca C declarada ou a um símbolo visível no processo. `dlopen` usa `RTLD_NOW | RTLD_LOCAL`. O runtime mantém a biblioteca aberta até o fim da unidade de execução.
4. Para descobrir um módulo COBOL no disco, o runtime procura `PROGRAM-ID.so`, com o nome em caixa alta e caracteres ASCII alfanuméricos, hífen ou sublinhado. Usa os diretórios `--module-dir` da unidade, os do executável e então as entradas de `COBOL_MODULE_PATH`, separadas por dois-pontos. Entradas vazias são ignoradas. O primeiro arquivo encontrado precisa ter o descritor e a entrada solicitada.
5. Uma função encontrada no processo ou nas bibliotecas explicitamente listadas por `--library` requer assinatura para ser invocada. Ela gera `CALL_SIGNATURE_REQUIRED` sem contrato. `CALL_NOT_FOUND` indica alvo ausente. Um literal como `ncurses_wrapper.c` representa um nome de CALL e continua sujeito às regras de resolução, sem selecionar um arquivo C para compilar.

Use diretórios e bibliotecas de confiança. Carregar uma biblioteca nativa pode executar seus inicializadores. A compilação gera C e chama GCC com argumentos separados. A busca e a carga ocorrem no processo do executável.

`ON EXCEPTION` executa quando a resolução ou o contrato falha, e `NOT ON EXCEPTION` executa após uma chamada concluída. Uma falha de resolução deixa o receptor de `RETURNING` e `RETURN-CODE` intactos. Sem tratador, o runtime informa o código do diagnóstico, a posição COBOL e o alvo, e termina com status 1. Uma falha fatal dentro do subprograma mantém sua própria posição e diagnóstico. Um retorno C como -1 continua sendo valor de retorno da função.

No perfil gnucobol, `CALL ... RETURNING` preenche o receptor explícito, preservando `RETURN-CODE`. Sem receptor explícito, um resultado inteiro atualiza `RETURN-CODE`. Resultados C ponteiro ou void podem ser descartados. `GOBACK` e `EXIT PROGRAM` retornam o código ao chamador e aceitam `RETURNING` inteiro. `STOP RUN` termina a unidade de execução. O perfil project conserva a regra anterior de atualizar também `RETURN-CODE` em um CALL inteiro com `RETURNING`.

## Módulo compartilhado próprio

```bash
python compiler.py MAIN.cbl --dialect gnucobol --module-dir build/modules -o build/main
python compiler.py SUBPROG.cbl --module -o build/modules/SUBPROG.so
./build/main
```

O primeiro comando funciona antes de `SUBPROG.so` existir. Uma chamada a `SUBPROG` com o módulo ausente segue a política de exceção. Depois da instalação, o mesmo binário usa o módulo. `--shared` seleciona explicitamente a saída compartilhada e usa por padrão o nome em caixa alta com extensão `.so`. `--module -o subprog.o` continua produzindo um objeto convencional. `COBOL_MODULE_PATH=/caminho/de/modulos ./build/main` configura a busca em execução. A variável `COB_LIBRARY_PATH` pertence ao GnuCOBOL.

O GCC gera o módulo com `-fPIC -shared`. Ele exporta `cobol_project_module_v1`, um descritor com versão, tamanho de `cb_runtime`, nomes canônicos, entradas e metadados de USING. O executável exporta os símbolos do runtime do projeto e fornece um único contexto para os módulos. Os arquivos compartilhados precisam da mesma ABI do executável. Um objeto de outra implementação, uma versão incompatível ou um módulo sem a entrada pedida recebe diagnóstico. A API C dos objetos convencionais continua usando `cb_runtime *`, `cb_field *` e aridade. Recompile o hospedeiro e seus objetos com o header desta etapa, que acrescenta o estado do carregador a `cb_runtime`.

A chamada conserva a memória de WORKING-STORAGE em acessos repetidos ao mesmo módulo, e cada programa tem sua própria área. LINKAGE aponta para os argumentos do chamador. BY REFERENCE compartilha os bytes. BY CONTENT cria uma cópia que pode ser recebida por USING BY REFERENCE. BY VALUE converte o número ao descritor formal em uma área temporária. O runtime valida aridade, modos e layout antes de entrar na unidade carregada. Para grupos, compara uma impressão digital das folhas, offsets, dimensões e representações. As dependências transitivas podem usar programas integrados ao executável ou outros módulos descobertos pela mesma busca.

## Assinaturas C

Use `--ffi-manifest contrato.json` para gerar adaptadores com protótipos C. O manifesto é uma lista JSON. Adicione `library` para escolher um SONAME ou um caminho. Caminhos com barra são resolvidos relativamente ao manifesto. A ausência de `library` escolhe os símbolos visíveis no processo. A opção repetível `--library` aceita caminhos, SONAMEs e o conjunto de assinaturas `ncurses`. O Linux resolve SONAMEs de acordo com sua configuração de bibliotecas. O build não requer libffi ou a biblioteca escolhida.

```json
[
  {"name":"ajustar", "library":"./libdados.so", "returns":"int", "params":["int","raw:32"]},
  {"name":"obter_contexto", "library":"./libdados.so", "returns":"pointer", "params":[]},
  {"name":"consultar", "library":"./libdados.so", "returns":"int", "params":["pointer","cstring"]},
  {"name":"printf", "returns":"int", "params":["cstring"], "varargs":["int","cstring"], "format":"printf"}
]
```

```bash
gcc -std=c11 -shared -fPIC dados.c -o libdados.so
python compiler.py MAIN.cbl --dialect gnucobol --ffi-manifest contrato.json -o build/main
python compiler.py examples/complementares/NCURSESDEMO.cbl --dialect gnucobol --library ncurses -o build/ncursesdemo
```

| Tipo no contrato | Tipo C | Argumento COBOL |
|---|---|---|
| `int` | `int` de 32 bits | BY VALUE inteiro na faixa |
| `bool` | `_Bool` | BY VALUE 0 ou 1, em parâmetros fixos |
| `pointer` | `void *` | BY VALUE de USAGE POINTER. O retorno usa `RETURNING` de USAGE POINTER |
| `cstring` | `const char *` | Campo textual ou literal, por referência ou conteúdo. A cópia terminada em NUL inclui os bytes e o padding Latin-1 |
| `raw:N` | `void *` | Região COBOL de pelo menos N bytes. BY REFERENCE fornece endereço e bytes originais. BY CONTENT fornece a cópia |
| `out-int` | `int *` | BY REFERENCE para campo inteiro. O adaptador passa um temporário C com alinhamento correto e converte o resultado |
| `void` | `void` | Só no retorno |

O manifesto aceita `"abi":"c"` para a convenção nativa. `varargs` declara uma sequência exata de tipos adicionais com as promoções já aplicadas. Com `format:"printf"`, o adaptador valida `%d`, `%s` e `%%`. Com `format:"scanf"`, aceita `%d` para cada `out-int` declarado e `%%`. O formato é o último argumento fixo. Em scanf, os primeiros destinos convertidos são copiados de volta de acordo com a contagem retornada. Use apenas entradas válidas para o domínio numérico da biblioteca. Para outras funções variádicas, o contrato de aridade e tipos é responsabilidade do autor da assinatura.

Todos os buffers de chamada são emprestados. A C string, os literais copiados, o BY CONTENT e o temporário de saída duram apenas durante o CALL. Use um wrapper C confiável para APIs que retêm a memória, exigem cópia persistente, alocam resultados que precisam de uma função de liberação ou usam estruturas C específicas. Os ponteiros retornados são opacos e sua propriedade segue a função nativa. Os adaptadores GCC suportam a convenção C de Linux e os tipos da tabela. Floats, structs por valor, callbacks, chamadas de convenções alternativas e formatos de varargs arbitrários exigem extensão. Os testes usam uma biblioteca C real e exercitam tanto símbolos do processo quanto bibliotecas compartilhadas.

## ncurses e os seis originais

`--library ncurses` seleciona a ABI Linux `libncurses.so.6`. Inclui `initscr` com retorno `WINDOW *`, `keypad` com ponteiro e controle booleano, `getch` com retorno inteiro e as operações básicas de tela. `mvprintw` aceita, por padrão, formato sem conversões. As assinaturas de `scanw` e `mvscanw` precisam de destinos explicitamente declarados no manifesto para efetuar conversões. O ensaio positivo em PTY testa janela, tecla `Q`, valor ASCII 81 e restauração do terminal. Consulte as assinaturas de [initscr](https://invisible-island.net/ncurses/man/curs_initscr.3x.html), [keypad](https://invisible-island.net/ncurses/man/curs_inopts.3x.html), [getch](https://invisible-island.net/ncurses/man/curs_getch.3x.html), [printw](https://invisible-island.net/ncurses/man/curs_printw.3x.html) e [scanw](https://invisible-island.net/ncurses/man/curs_scanw.3x.html).

Os três casos ncurses originais compilam. NCURSESDEMO e PROGTEST3 chegam a `scanw` sem destino de conversão. PROGTEST2 chega a `keypad` e o adaptador recusa o inteiro passado como janela. São exercitados com TTY isolado e encerramento da sessão ncurses. Os três outros casos chegam a CALLs ausentes no runtime. CAD0001A usa as dependências existentes e chega a SORT001A após a leitura e o cadastro. `main` chega a `exibir_tela`, e `ncurses_demo` chega ao primeiro CALL, `ncurses_wrapper.c`.

A auditoria registra a construção de todos os originais, tentativas de ligação estática no GnuCOBOL e os probes de execução. Nenhum dos seis probes conta como validação funcional integral. [Auditoria de compatibilidade](compatibilidade-gnucobol.md) · [Evidências por programa](compatibilidade-gnucobol.json).

```bash
python -m unittest discover -s tests -v
python -m tools.auditar_compatibilidade --write
```
