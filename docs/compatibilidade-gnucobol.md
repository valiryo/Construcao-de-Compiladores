# Compatibilidade com GnuCOBOL — Etapa 8

Gerado por `python -m tools.auditar_compatibilidade --write`. A revisão de execução pode ser refeita isoladamente. [Dados completos e comandos](compatibilidade-gnucobol.json).
Snapshot `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`; **85 arquivos originais**, bytes e hashes preservados. Modo: `compilation-and-functional`.
A cópia corrigida de CAD0005A continua nos testes oficiais, mas não entra no denominador dos originais. Não foram criadas novas versões corrigidas.

## Cobertura de compilação

| Unidades comparáveis | Nosso C + GCC | GnuCOBOL | Cobertura |
|---|---:|---:|---:|
| Todas | 70 | 70 | 100.00% |
| Principais | 63 | 63 | 100.00% |
| Subprogramas (-c / objeto) | 7 | 7 | 100.00% |

O perfil padrão compila 59 originais. O perfil `--dialect gnucobol` chega a 70, com seis a mais que os 64 da Etapa 7. A derivada CAD0005A continua validada separadamente.
A comparação de compilação inclui os seis programas com CALL adiado. A execução dos seis registra os três alvos ausentes e os três contratos ncurses rejeitados.

## Execução e comparação

Os **140 cenários anteriores passaram novamente** (140 válidos, 7 oficiais). Os 136 resultados idênticos, três diferenças conhecidas da ABI e um erro próprio permanecem preservados.
Há **7 cenários batch novos e 5 de terminal**, todos com expectativas satisfeitas. Total: 152 cenários, incluindo a comparação parcial do jogo.
O conjunto funcional das etapas anteriores executa 64 originais. **60/70 (85.71%)** coincidem nos cenários completos: 58 em bytes e dois em células de texto. Outros três têm diferenças de ABI conhecidas e expectativas independentes completas; GAMESNAK tem somente comparação parcial.
CBREAKEX confere entrada vazia, mudanças de cidade/estado, totais, zero e valores negativos, todos os bytes dos registros de 80 posições. PROG042A confere inclusão, reabertura, cliente/produto ausente e quantidade zero, ligando PROG042B intacto.
PROGTEST confere Backspace, Tab, entrada parcial numérica (7 em PIC 99 resulta em 70), nome de 30 posições e zero. TESTE002 confere CRT STATUS/posição. GAMESNAK exercita saída por Q, moldura e conclusão; RANDOM produz comida em posições diferentes e não há ensaio completo de jogabilidade.
No terminal, os protocolos ANSI brutos diferem e ficam preservados em base64. A comparação usa todas as células de texto de um PTY 40x100, incluindo padding; não remove espaços, valores ou posições. Atributos visuais não são objeto da equivalência de texto. Um escape desconhecido falha a interpretação.
O levantamento geral registrou **535 testes descobertos**. A suíte unittest é executada separadamente pelo comando de reprodução abaixo.

## Incompatibilidades corrigidas

- **CBREAKEX**: Formato livre explícito; FD DATA RECORD; edição numérica com sinal flutuante.
- **PROG042A**: Perfil de identificadores até 63 posições, mantendo o nome original de 31; CALL PROG042B existente.
- **PROGTEST**: SCREEN SECTION com LINE/COLUMN, BLANK SCREEN, PIC e USING; edição em terminal real.
- **TESTE002**: DISPLAY posicionado e CRT STATUS.
- **GAMESNAK**: DISPLAY/ACCEPT posicionados e CURSOR; execução de saída, com RANDOM comparado parcialmente.

## Matriz de todo o corpus

Análise, construção e ligação ficam em campos distintos do JSON. Os seis probes de CALL adiado têm resultado de execução próprio. `both_compiled_functional_difference` distingue os três contratos ABI conhecidos e a diferença parcial do jogo.

| Programa | GnuCOBOL | Nosso compilador | Causa da diferença | Ação |
|---|---|---|---|---|
| [examples/complementares/ASCII001.cbl](../examples/complementares/ASCII001.cbl) | rejeitado | bloqueado | source_rejected; not_run; UNDEFINED_SYMBOL | Registrar diagnóstico; não alterar fonte original. |
| [examples/oficiais/BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/CAD0001A.cbl](../examples/complementares/CAD0001A.cbl) | executável | C/GCC OK | both_compiled; missing_at_runtime | Carrega as dependências COBOL disponíveis. CALL SORT001A falha quando alcançado. O único SORT001A do snapshot contém conflitos. |
| [examples/oficiais/CAD0002A.cbl](../examples/oficiais/CAD0002A.cbl) | objeto | objeto | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/oficiais/CAD0004A.cbl](../examples/oficiais/CAD0004A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/oficiais/CAD0005A.cbl](../examples/oficiais/CAD0005A.cbl) | rejeitado | bloqueado | source_rejected; not_run; MERGE_CONFLICT | Registrar diagnóstico; não alterar fonte original. |
| [examples/oficiais/CAIXAREG.cbl](../examples/oficiais/CAIXAREG.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/oficiais/CALCMD01.cbl](../examples/oficiais/CALCMD01.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/CBREAKEX.cbl](../examples/complementares/CBREAKEX.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Formato livre explícito; FD DATA RECORD; edição numérica com sinal flutuante. |
| [examples/complementares/CLIESQL01.cbl](../examples/complementares/CLIESQL01.cbl) | rejeitado | bloqueado | source_rejected; not_run; SYNTAX_ERROR | Registrar diagnóstico; não alterar fonte original. |
| [examples/dependencias/COD001A.cpy](../examples/dependencias/COD001A.cpy) | contexto COPY | contexto COPY | contextual_fragment; not_run | Registrar diagnóstico; não alterar fonte original. |
| [examples/dependencias/COPY002A.cpy](../examples/dependencias/COPY002A.cpy) | contexto COPY | contexto COPY | contextual_fragment; not_run | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/GAMESNAK.cbl](../examples/complementares/GAMESNAK.cbl) | executável | C/GCC OK | both_compiled_functional_difference; partial_random_difference | DISPLAY/ACCEPT posicionados e CURSOR; execução de saída, com RANDOM comparado parcialmente. |
| [examples/complementares/GRAV001A.cbl](../examples/complementares/GRAV001A.cbl) | objeto | objeto | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/LER0001A.cbl](../examples/complementares/LER0001A.cbl) | objeto | objeto | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/LER0002A.cbl](../examples/complementares/LER0002A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/LOGIN01A.cbl](../examples/complementares/LOGIN01A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/MINICALC.cbl](../examples/complementares/MINICALC.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/NCURSESDEMO.cbl](../examples/complementares/NCURSESDEMO.cbl) | executável | C/GCC OK | both_compiled; native_contract_rejected | Liga ncurses no GnuCOBOL. O runtime próprio executa a inicialização e a escrita, depois rejeita scanw sem destinos de conversão. |
| [examples/complementares/PROG001A.cbl](../examples/complementares/PROG001A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG002A.cbl](../examples/complementares/PROG002A.cbl) | rejeitado | bloqueado | source_rejected; not_run; MERGE_CONFLICT | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/PROG003A.cbl](../examples/complementares/PROG003A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG004A.cbl](../examples/complementares/PROG004A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG005A.cbl](../examples/complementares/PROG005A.cbl) | executável | C/GCC OK | both_compiled_functional_difference; known_abi_difference | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG006A.cbl](../examples/complementares/PROG006A.cbl) | rejeitado | bloqueado | external_extension_unavailable; not_run; UNSUPPORTED_EXEC | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/PROG007A.cbl](../examples/complementares/PROG007A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG008A.cbl](../examples/complementares/PROG008A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG009A.cbl](../examples/complementares/PROG009A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG010A.cbl](../examples/complementares/PROG010A.cbl) | rejeitado | bloqueado | source_rejected; not_run; MERGE_CONFLICT | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/PROG011A.cbl](../examples/complementares/PROG011A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG012A.cbl](../examples/complementares/PROG012A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG014A.cbl](../examples/complementares/PROG014A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG015A.cbl](../examples/complementares/PROG015A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG016A.cbl](../examples/complementares/PROG016A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG017A.cbl](../examples/complementares/PROG017A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG018A.cbl](../examples/complementares/PROG018A.cbl) | rejeitado | bloqueado | source_rejected; not_run; INVALID_ALTER_TARGET, UNSUPPORTED_ALTER | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/PROG019A.cbl](../examples/complementares/PROG019A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG020A.cbl](../examples/complementares/PROG020A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG021A.cbl](../examples/complementares/PROG021A.cbl) | executável | C/GCC OK | both_compiled_functional_difference; known_abi_difference | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG022A.cbl](../examples/complementares/PROG022A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG023A.cbl](../examples/complementares/PROG023A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG023B.cbl](../examples/complementares/PROG023B.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG023C.cbl](../examples/complementares/PROG023C.cbl) | rejeitado | bloqueado | source_rejected; not_run; MERGE_CONFLICT | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/PROG023D.cbl](../examples/complementares/PROG023D.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG023E.cbl](../examples/complementares/PROG023E.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/oficiais/PROG024A.cbl](../examples/oficiais/PROG024A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG025A.cbl](../examples/complementares/PROG025A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG027A.cbl](../examples/complementares/PROG027A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG028A.cbl](../examples/complementares/PROG028A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG029A.cbl](../examples/complementares/PROG029A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG033A.cbl](../examples/complementares/PROG033A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG034A.cbl](../examples/complementares/PROG034A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG035A.cbl](../examples/complementares/PROG035A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG036A.cbl](../examples/complementares/PROG036A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG037A.cbl](../examples/complementares/PROG037A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG038A.cbl](../examples/complementares/PROG038A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG039A.cbl](../examples/complementares/PROG039A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG040A.cbl](../examples/complementares/PROG040A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG041A.cbl](../examples/complementares/PROG041A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG042A.cbl](../examples/complementares/PROG042A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Perfil de identificadores até 63 posições, mantendo o nome original de 31; CALL PROG042B existente. |
| [examples/complementares/PROG042B.cbl](../examples/complementares/PROG042B.cbl) | objeto | objeto | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG043A.cbl](../examples/complementares/PROG043A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG044A.cbl](../examples/complementares/PROG044A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROG045A.cbl](../examples/complementares/PROG045A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/dependencias/PROGDATA.cbl](../examples/dependencias/PROGDATA.cbl) | objeto | objeto | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROGTEST.cbl](../examples/complementares/PROGTEST.cbl) | executável | C/GCC OK | both_compiled; text_cells_equal | SCREEN SECTION com LINE/COLUMN, BLANK SCREEN, PIC e USING; edição em terminal real. |
| [examples/complementares/PROGTEST2.cbl](../examples/complementares/PROGTEST2.cbl) | executável | C/GCC OK | both_compiled; native_contract_rejected | Liga ncurses no GnuCOBOL. O runtime próprio recusa o inteiro usado no lugar de WINDOW* em keypad. |
| [examples/complementares/PROGTEST3.cbl](../examples/complementares/PROGTEST3.cbl) | executável | C/GCC OK | both_compiled; native_contract_rejected | Liga ncurses no GnuCOBOL. O runtime próprio rejeita scanw sem destinos de conversão. |
| [examples/complementares/PROGTEST4.cbl](../examples/complementares/PROGTEST4.cbl) | executável | C/GCC OK | both_compiled_functional_difference; known_abi_difference | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROGTIME.cbl](../examples/complementares/PROGTIME.cbl) | objeto | objeto | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/PROGVSAM.cbl](../examples/complementares/PROGVSAM.cbl) | rejeitado | bloqueado | source_rejected; not_run; UNSUPPORTED_FILE_ORGANIZATION, KEY_ON_SEQUENTIAL_FILE, INVALID_FILE_ACCESS, INVALID_FILE_MODE, INVALID_FILE_HANDLER | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/REL0001A.cbl](../examples/complementares/REL0001A.cbl) | objeto | objeto | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/REL0002A.cbl](../examples/complementares/REL0002A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/SORT001A.cbl](../examples/complementares/SORT001A.cbl) | rejeitado | bloqueado | source_rejected; not_run; MERGE_CONFLICT | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/SORT002A.cbl](../examples/complementares/SORT002A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/TELABMS.cbl](../examples/complementares/TELABMS.cbl) | rejeitado | bloqueado | external_extension_unavailable; not_run; INVALID_CHARACTER | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/TESTE002.cbl](../examples/complementares/TESTE002.cbl) | executável | C/GCC OK | both_compiled; text_cells_equal | DISPLAY posicionado e CRT STATUS. |
| [examples/complementares/VALCNPJ.cbl](../examples/complementares/VALCNPJ.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/VALCPF01.cbl](../examples/complementares/VALCPF01.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/VALIDA1A.cbl](../examples/complementares/VALIDA1A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/VALIDA1B.cbl](../examples/complementares/VALIDA1B.cbl) | rejeitado | bloqueado | source_rejected; not_run; MERGE_CONFLICT | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/clientes-sql.cbl](../examples/complementares/clientes-sql.cbl) | rejeitado | bloqueado | external_extension_unavailable; not_run; UNSUPPORTED_EXEC | Registrar diagnóstico; não alterar fonte original. |
| [examples/complementares/main.cbl](../examples/complementares/main.cbl) | executável | C/GCC OK | both_compiled; missing_at_runtime | CALL exibir_tela permanece no executável e falha por implementação ausente na execução. |
| [examples/complementares/meu_programa.cob](../examples/complementares/meu_programa.cob) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/ncurses_demo.cbl](../examples/complementares/ncurses_demo.cbl) | executável | C/GCC OK | both_compiled; missing_at_runtime | O CALL ncurses_wrapper.c e os demais CALLs permanecem no binário. O primeiro falha por implementação ausente. |

## Formatos, fases e dependências

- CBREAKEX usa `-free` e `--source-format free`. Os outros originais usam formato fixo. Não há reindentação automática, exclusão de instruções ou truncamento de nomes.
- GnuCOBOL usa `-std=default -fnot-reserved=ID -freserved=VALUES:VALUE`; são opções de vocabulário, sem ignorar erros. O limite de 63 posições é opt-in no nosso perfil; o padrão continua em 30.
- Primeiro `cobc -fsyntax-only`; depois objeto `-c` para cada unidade; por fim `-x` para principais. Para principais aceitos há tentativa adicional `-fstatic-call`, fornecendo as dependências encontradas pelo PROGRAM-ID. No perfil gnucobol, o CALL externo é resolvido em execução. Use --static-call para exigir fontes resolvidos antes de GCC.
- Cada compilação de referência recebe TMPDIR exclusivo no seu build. Uma execução concorrente da suíte e auditoria expôs colisão de nomes temporários cob<PID> entre namespaces; o isolamento foi corrigido e verificado com processos concorrentes.
- GnuCOBOL liga NCURSESDEMO, PROGTEST2 e PROGTEST3 com `-l:libncurses.so.6 -l:libtinfo.so.6`. O executável próprio usa `--library ncurses` e carrega o SONAME durante o CALL. O probe PTY registra saída, retorno e restauração do terminal.
- CAD0001A depende do SORT001A original com conflitos; main depende de exibir_tela ausente; ncurses_demo depende de wrappers ausentes. O manifesto e a árvore upstream da Etapa 6 não contêm essas implementações. GnuCOBOL permite CALL dinâmico adiado; ligação estática confirma a pendência.
- Registros continuam ISO-8859-1, números exatos e ABI própria. CBREAKEX é comparado com `-fsign=EBCDIC` no oráculo para selecionar o mesmo overpunch; os bytes fornecidos são idênticos. Isso não muda a codificação textual. As três diferenças antigas (inicialização de FD e acentos/padding) continuam registradas, sem alterar a ABI.


## Execução dos seis CALLs adiados

| Original | CALL alcançado | Diagnóstico próprio | Retorno próprio | Retorno GnuCOBOL |
|---|---|---|---:|---:|
| CAD0001A | SORT001A | CALL_NOT_FOUND | 1 | 1 |
| NCURSESDEMO | scanw | CALL_NATIVE_FORMAT | 1 | — |
| PROGTEST2 | keypad | CALL_NATIVE_ARGUMENT | 1 | — |
| PROGTEST3 | scanw | CALL_NATIVE_FORMAT | 1 | — |
| main | exibir_tela | CALL_NOT_FOUND | 1 | 1 |
| ncurses_demo | ncurses_wrapper.c | CALL_NOT_FOUND | 1 | 1 |

Os casos ncurses atingiram a verificação de argumentos em terminal isolado. O retorno do GnuCOBOL aparece apenas nos casos de módulo ausente. Os logs JSON incluem os bytes, estado do terminal e sinal quando aplicável.

## Revisão final das lacunas de execução

Oráculo `cobc (GnuCOBOL) 3.2.0`. A revisão inclui o divisor zero e reexecuta os seis CALLs adiados. GAMESNAK ficou fora desta rodada.

| Programa | Ponto observado | stdout | stderr | Arquivos | Retorno próprio / GnuCOBOL |
|---|---|---|---|---|---:|
| CAD0001A | Até `SORT001A` ausente | igual | diferente | igual | 1 / 1 |
| CALCMD01 | Divisor zero | diferente | diferente | igual | 1 / 0 |
| NCURSESDEMO | Antes de `scanw`, linha 25 | igual | igual | igual | 77 / 77 |
| PROGTEST2 | Antes de `keypad`, linha 17 | igual | igual | igual | 77 / 77 |
| PROGTEST3 | Antes de `scanw`, linha 22 | igual | igual | igual | 77 / 77 |
| main | Até `exibir_tela` ausente | igual | diferente | igual | 1 / 1 |
| ncurses_demo | Até `ncurses_wrapper.c` ausente | igual | diferente | igual | 1 / 1 |

Em CALCMD01, as saídas coincidem até o total. O próprio aborta na divisão por zero. O GnuCOBOL prossegue até exibir a média `00000006,0000`.
Os três destinos ausentes produziram diagnósticos com redações próprias de cada runtime. A execução com as implementações disponíveis permanece sem verificação.
O ensaio ncurses compila, nos dois compiladores, cópias temporárias do prefixo original até a linha indicada. Depois do prefixo, a cópia chama `endwin` e sai com o marcador 77. Esse retorno é do ensaio. A chamada incompatível e a execução subsequente ficam fora da comparação. Os fontes originais do corpus permanecem intactos.
A saída do executável próprio original, encerrado pelo diagnóstico e com o terminal restaurado, coincidiu com a saída do prefixo em 3/3 casos.
Os três casos com diferenças conhecidas de ABI já têm comparação de saída na auditoria funcional e ficaram fora desta rodada.
O JSON guarda os comandos de compilação, hashes, entradas, saídas brutas do PTY, arquivos e os bytes usados na derivação do prefixo. A revisão complementa os 152 cenários registrados acima.

## Fontes excluídos da meta executável

Dez originais têm erros reais: seis conflitos (PROG002A, PROG010A, PROG023C, SORT001A, VALIDA1B e CAD0005A), ASCII001 com referência inexistente, CLIESQL01 vazio, PROG018A com destino inválido de ALTER e PROGVSAM com organização LINE SEQUENTIAL contraditória com chaves. GnuCOBOL também os rejeita; nenhum foi reparado.
PROG006A (CICS), clientes-sql (SQL) e TELABMS (macro BMS) exigem ferramentas externas indisponíveis. COPY002A e COD001A são copybooks, validados nos consumidores e excluídos da contagem de programas.

## Contratos das chamadas externas

O runtime aceita módulos COBOL com descritor próprio e invoca símbolos C com adaptadores gerados a partir de assinaturas explícitas. A busca, os modos de passagem e a política de erros estão no [guia de CALL e FFI](call-dinamico-ffi.md).
scanw e mvscanw recebem um formato C. Uma conversão precisa de destino explícito. getch devolve um inteiro e keypad exige WINDOW*. Os ensaios próprios usam PTY isolado e recusam a operação inválida antes de invocá-la. A compilação e a ligação GnuCOBOL foram verificadas separadamente. O SIGSEGV de PROGTEST2 registrado na Etapa 7 é evidência histórica.

## Contratos do perfil novo

Formato livre preserva coordenadas físicas, COPY e comentários inline; não implementa todas as continuações de literais do formato livre. FD DATA RECORD(S) mantém referências tipadas e valida que pertencem ao FD. PIC flutuante aceita uma sequência inicial de + ou -, com agrupamento, dígitos obrigatórios e decimal; combinações com moeda, Z, *, COMP e COMP-3 são rejeitadas.
Terminal usa ANSI/POSIX próprio, sem ncurses/GnuCOBOL. Requer TTY, coordenadas base 1 e limites da janela. SCREEN suporta LINE/COLUMN, BLANK SCREEN, VALUE, PIC textual ou inteiro sem sinal/escala e USING. Limites: 1024 campos editáveis, 4096 bytes por campo. Teclas básicas, Enter, Backspace, Tab e navegação são tratadas; sequências desconhecidas dão diagnóstico explícito. ECHO/ICANON são restaurados na confirmação, erro e SIGINT/SIGTERM. Um DISPLAY posicionado aplica a posição ao operando imediatamente anterior, conforme os probes completos.
Essas extensões dependem de `--dialect gnucobol`; o perfil padrão, suas rejeições e a suíte anterior são preservados. O nome do perfil indica o subconjunto documentado, sem prometer toda a linguagem GnuCOBOL.

## Reprodução

```bash
python -m unittest discover -s tests -v
python -m tools.auditar_compatibilidade --write
python -m tools.auditar_compatibilidade --execution-gaps --write
python -m tools.auditar_compatibilidade --compile-only --report /tmp/compat-compilacao.json
python compiler.py examples/complementares/CBREAKEX.cbl --source-format free --dialect gnucobol -o build/cbreak
python compiler.py examples/complementares/PROG042A.cbl --dialect gnucobol --source examples/complementares/PROG042B.cbl -o build/pedidos
python compiler.py examples/complementares/PROGTEST.cbl --dialect gnucobol -o build/tela
```

Os comandos GCC/cobc efetivamente executados, diagnósticos completos, hashes de fontes/COPY/runtime, opções, entradas, saídas brutas e arquivos estão no JSON. `$REPO`, `$BUILD`, `$RUN`, `$SCREEN` e `$GAPS` representam diretórios declarados e temporários novos; os comandos podem ser refeitos substituindo essas raízes. O compilador não executa COBOL durante a compilação nem gera fixtures. GnuCOBOL continua exclusivamente oráculo.
