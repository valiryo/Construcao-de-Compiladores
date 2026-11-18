# Compatibilidade com GnuCOBOL — Etapa 7

Gerado por `python -m tools.auditar_compatibilidade --write`. [Dados completos e comandos](compatibilidade-gnucobol.json).
Snapshot `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`; **85 arquivos originais**, bytes e hashes preservados. Modo: `compilation-and-functional`.
A cópia corrigida de CAD0005A continua nos testes oficiais, mas não entra no denominador dos originais. Não foram criadas novas versões corrigidas.

## Cobertura de compilação

| Unidades comparáveis | Nosso C + GCC | GnuCOBOL | Cobertura |
|---|---:|---:|---:|
| Todas | 64 | 70 | 91.43% |
| Principais | 57 | 63 | 90.48% |
| Subprogramas (-c / objeto) | 7 | 7 | 100.00% |

O perfil padrão compila 59 originais; o perfil explícito `--dialect gnucobol` amplia para 64 (**+5**). Com a derivada CAD0005A preservada, são 65 unidades próprias; a derivada não aumenta a cobertura original.
Os 70 incluem três executáveis GnuCOBOL com chamadas dinâmicas ainda sem implementação disponível. Produzir um executável com resolução adiada não prova que ele execute. O denominador os conserva para não ocultar lacunas.

## Execução e comparação

Os **140 cenários anteriores passaram novamente** (140 válidos, 7 oficiais). Os 136 resultados idênticos, três diferenças conhecidas da ABI e um erro próprio permanecem preservados.
Há **7 cenários batch novos e 5 de terminal**, todos com expectativas satisfeitas. Total: 152 cenários, incluindo a comparação parcial do jogo.
Nos originais, 64 programas foram executados e comparados em algum nível. **60/70 (85.71%)** coincidem nos cenários completos: 58 em bytes e dois em células de texto. Outros três têm diferenças de ABI conhecidas e expectativas independentes completas; GAMESNAK tem somente comparação parcial. Portanto não há alegação de 64 programas funcionalmente equivalentes.
CBREAKEX confere entrada vazia, mudanças de cidade/estado, totais, zero e valores negativos, todos os bytes dos registros de 80 posições. PROG042A confere inclusão, reabertura, cliente/produto ausente e quantidade zero, ligando PROG042B intacto.
PROGTEST confere Backspace, Tab, entrada parcial numérica (7 em PIC 99 resulta em 70), nome de 30 posições e zero. TESTE002 confere CRT STATUS/posição. GAMESNAK exercita saída por Q, moldura e conclusão; RANDOM produz comida em posições diferentes e não há ensaio completo de jogabilidade.
No terminal, os protocolos ANSI brutos diferem e ficam preservados em base64. A comparação usa todas as células de texto de um PTY 40x100, incluindo padding; não remove espaços, valores ou posições. Atributos visuais não são objeto da equivalência de texto. Um escape desconhecido falha a interpretação.
A suíte contém **522 testes descobertos**. A auditoria executa os cenários, não a suíte unittest; executar a suíte pelo comando de reprodução abaixo.

## Incompatibilidades corrigidas

- **CBREAKEX**: Formato livre explícito; FD DATA RECORD; edição numérica com sinal flutuante.
- **PROG042A**: Perfil de identificadores até 63 posições, mantendo o nome original de 31; CALL PROG042B existente.
- **PROGTEST**: SCREEN SECTION com LINE/COLUMN, BLANK SCREEN, PIC e USING; edição em terminal real.
- **TESTE002**: DISPLAY posicionado e CRT STATUS.
- **GAMESNAK**: DISPLAY/ACCEPT posicionados e CURSOR; execução de saída, com RANDOM comparado parcialmente.

## Matriz de todo o corpus

Análise, construção e ligação ficam em campos distintos do JSON. As seis pendências de CALL continuam explícitas. `both_compiled_functional_difference` distingue os três contratos ABI conhecidos e a diferença parcial do jogo.

| Programa | GnuCOBOL | Nosso compilador | Causa da diferença | Ação |
|---|---|---|---|---|
| [examples/complementares/ASCII001.cbl](../examples/complementares/ASCII001.cbl) | rejeitado | bloqueado | source_rejected; not_run; UNDEFINED_SYMBOL | Registrar diagnóstico; não alterar fonte original. |
| [examples/oficiais/BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/CAD0001A.cbl](../examples/complementares/CAD0001A.cbl) | executável | bloqueado | external_dependency_unavailable; not_run; LINK_UNRESOLVED_CALL | CALL SORT001A permanece dinâmico no GnuCOBOL. O único SORT001A do snapshot contém conflitos e é rejeitado; não foi corrigido. |
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
| [examples/complementares/NCURSESDEMO.cbl](../examples/complementares/NCURSESDEMO.cbl) | executável | bloqueado | gnu_only; not_run; LINK_UNRESOLVED_CALL | Chamadas C/ncurses sem FFI tipada; bibliotecas do sistema permitem ligação GnuCOBOL. scanw recebe campo como formato, sem destinos de conversão. |
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
| [examples/complementares/PROGTEST2.cbl](../examples/complementares/PROGTEST2.cbl) | executável | bloqueado | gnu_only; not_run; LINK_UNRESOLVED_CALL | FFI ncurses pendente; keypad recebe 1 em lugar de WINDOW*. mvscanw usa campos como formato; getch é retorno, não parâmetro de saída. |
| [examples/complementares/PROGTEST3.cbl](../examples/complementares/PROGTEST3.cbl) | executável | bloqueado | gnu_only; not_run; LINK_UNRESOLVED_CALL | FFI ncurses pendente; scanw usa campos como formato; getch é retorno, não parâmetro de saída. |
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
| [examples/complementares/main.cbl](../examples/complementares/main.cbl) | executável | bloqueado | external_dependency_unavailable; not_run; LINK_UNRESOLVED_CALL | CALL exibir_tela sem implementação no snapshot; GnuCOBOL -x deixa resolução para execução. |
| [examples/complementares/meu_programa.cob](../examples/complementares/meu_programa.cob) | executável | C/GCC OK | both_compiled; raw_equal | Fonte preservado; manter os testes existentes. |
| [examples/complementares/ncurses_demo.cbl](../examples/complementares/ncurses_demo.cbl) | executável | bloqueado | external_dependency_unavailable; not_run; LINK_UNRESOLVED_CALL | ncurses_wrapper.c e funções de wrapper não existem no snapshot. Nome literal de arquivo C em CALL não fornece implementação. |

## Formatos, fases e dependências

- CBREAKEX usa `-free` e `--source-format free`. Os outros originais usam formato fixo. Não há reindentação automática, exclusão de instruções ou truncamento de nomes.
- GnuCOBOL usa `-std=default -fnot-reserved=ID -freserved=VALUES:VALUE`; são opções de vocabulário, sem ignorar erros. O limite de 63 posições é opt-in no nosso perfil; o padrão continua em 30.
- Primeiro `cobc -fsyntax-only`; depois objeto `-c` para cada unidade; por fim `-x` para principais. Para principais aceitos há tentativa adicional `-fstatic-call`, fornecendo as dependências encontradas pelo PROGRAM-ID. O nosso driver exige resolução antes de GCC.
- Cada compilação de referência recebe TMPDIR exclusivo no seu build. Uma execução concorrente da suíte e auditoria expôs colisão de nomes temporários cob<PID> entre namespaces; o isolamento foi corrigido e verificado com processos concorrentes.
- NCURSESDEMO, PROGTEST2 e PROGTEST3 ligam com `-l:libncurses.so.6 -l:libtinfo.so.6` presentes no ambiente. Isso evita confundir ausência dos nomes de desenvolvimento `-lncurses` com ausência da biblioteca. O probe PTY isolado conserva retorno, stderr e terminal restaurado, sem declarar suas chamadas corretas.
- CAD0001A depende do SORT001A original com conflitos; main depende de exibir_tela ausente; ncurses_demo depende de wrappers ausentes. O manifesto e a árvore upstream da Etapa 6 não contêm essas implementações. GnuCOBOL permite CALL dinâmico adiado; ligação estática confirma a pendência.
- Registros continuam ISO-8859-1, números exatos e ABI própria. CBREAKEX é comparado com `-fsign=EBCDIC` no oráculo para selecionar o mesmo overpunch; os bytes fornecidos são idênticos. Isso não muda a codificação textual. As três diferenças antigas (inicialização de FD e acentos/padding) continuam registradas, sem alterar a ABI.


### Probes das bibliotecas nativas

Ligação estática GnuCOBOL com as bibliotecas instaladas, seguida de PTY isolado com entrada finita `1\n2\nx\n`. Retorno zero não comprova conversão dos campos; não há destinos corretos nas chamadas scanw destes fontes.

| Original | Retorno GnuCOBOL | Timeout | Terminal restaurado |
|---|---:|---|---|
| NCURSESDEMO | 0 | False | True |
| PROGTEST2 | -11 | False | False |
| PROGTEST3 | 0 | False | True |

Retorno -11 indica SIGSEGV no ambiente observado. Retorno zero indica conclusão, sem prova de que os campos de entrada tenham sido preenchidos como pretendido. Esses resultados permanecem distintos da capacidade de compilar e ligar.

## Fontes excluídos da meta executável

Dez originais têm erros reais: seis conflitos (PROG002A, PROG010A, PROG023C, SORT001A, VALIDA1B e CAD0005A), ASCII001 com referência inexistente, CLIESQL01 vazio, PROG018A com destino inválido de ALTER e PROGVSAM com organização LINE SEQUENTIAL contraditória com chaves. GnuCOBOL também os rejeita; nenhum foi reparado.
PROG006A (CICS), clientes-sql (SQL) e TELABMS (macro BMS) exigem ferramentas externas indisponíveis. COPY002A e COD001A são copybooks, validados nos consumidores e excluídos da contagem de programas.

## Pendências e custo arquitetural

O limite real remanescente é CALL externo. Uma ampliação exige registro explícito de assinaturas C, tamanhos/promoções BY VALUE, ponteiros de retorno, buffers NUL versus slices COBOL, ownership, varargs e configuração de bibliotecas do linker. Importação dinâmica exigiria carregador e falhas de símbolo em runtime, sem stubs. A resolução de CALL COBOL existente e a ABI de LINKAGE devem ser preservadas.
Nos três exemplos ncurses há ainda contratos do próprio fonte: scanw/mvscanw recebem campos como formato e nenhum destino de conversão; getch devolve um int. PROGTEST2 passa 1 no lugar do ponteiro WINDOW* de keypad. Não se deve transformar essas chamadas silenciosamente em uma interface diferente. As assinaturas oficiais de [scanw](https://invisible-island.net/ncurses/man/curs_scanw.3x.html) e [getch](https://invisible-island.net/ncurses/man/curs_getch.3x.html) fundamentam essa distinção. Permanecem na meta de compilação enquanto GnuCOBOL os construir, ainda que a execução apresente problemas.
ALTER, SORT e INDEXED/RELATIVE/VSAM não são necessários a nenhum original adicional compilável identificado nesta execução. SQL/CICS requerem precompiladores; macros BMS são outra linguagem. Não foi introduzido um subsistema especulativo para esses exemplos rejeitados ou dependentes de ferramentas ausentes.

## Contratos do perfil novo

Formato livre preserva coordenadas físicas, COPY e comentários inline; não implementa todas as continuações de literais do formato livre. FD DATA RECORD(S) mantém referências tipadas e valida que pertencem ao FD. PIC flutuante aceita uma sequência inicial de + ou -, com agrupamento, dígitos obrigatórios e decimal; combinações com moeda, Z, *, COMP e COMP-3 são rejeitadas.
Terminal usa ANSI/POSIX próprio, sem ncurses/GnuCOBOL. Requer TTY, coordenadas base 1 e limites da janela. SCREEN suporta LINE/COLUMN, BLANK SCREEN, VALUE, PIC textual ou inteiro sem sinal/escala e USING. Limites: 1024 campos editáveis, 4096 bytes por campo. Teclas básicas, Enter, Backspace, Tab e navegação são tratadas; sequências desconhecidas dão diagnóstico explícito. ECHO/ICANON são restaurados na confirmação, erro e SIGINT/SIGTERM. Um DISPLAY posicionado aplica a posição ao operando imediatamente anterior, conforme os probes completos.
Essas extensões dependem de `--dialect gnucobol`; o perfil padrão, suas rejeições e a suíte anterior são preservados. O nome do perfil indica o subconjunto documentado, sem prometer toda a linguagem GnuCOBOL.

## Reprodução

```bash
python -m unittest discover -s tests -v
python -m tools.auditar_compatibilidade --write
python -m tools.auditar_compatibilidade --compile-only --report /tmp/compat-compilacao.json
python compiler.py examples/complementares/CBREAKEX.cbl --source-format free --dialect gnucobol -o build/cbreak
python compiler.py examples/complementares/PROG042A.cbl --dialect gnucobol --source examples/complementares/PROG042B.cbl -o build/pedidos
python compiler.py examples/complementares/PROGTEST.cbl --dialect gnucobol -o build/tela
```

Os comandos GCC/cobc efetivamente executados, diagnósticos completos, hashes de fontes/COPY/runtime, opções, entradas, saídas brutas e arquivos estão no JSON. `$REPO`, `$BUILD`, `$RUN` e `$SCREEN` representam diretórios declarados e temporários novos; os comandos podem ser refeitos substituindo essas raízes. O compilador não executa COBOL durante a compilação nem gera fixtures. GnuCOBOL continua exclusivamente oráculo.
