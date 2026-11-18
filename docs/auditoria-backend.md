# Auditoria do backend C e runtime

Gerado por `python -m tools.auditar_backend --write`. O compilador não usa
GnuCOBOL para gerar ou executar seus programas. O oráculo é uma execução separada.
Snapshot do corpus: `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`. Fontes originais preservados.

## Métricas

- 86 arquivos classificados; todos os **68 programas semanticamente válidos** submetidos ao backend.
- **60 com C gerado; 60 compilados pelo GCC:** 53 executáveis e 7 objetos de subprogramas.
- **11 programas executados e validados nos cenários explícitos**, incluindo CAD0002A por harness COBOL; PROGDATA também executa como dependência de PROG024A.
- 3 complementares validados: texto/refmod, SEARCH ALL e arquivo sequencial com exclusão.
- 30 cenários executados; 30 satisfazem as expectativas de stdout, stderr, retorno e bytes dos arquivos.
- 29 cenários comparados integralmente com GnuCOBOL; 29 coincidem sem normalizar saídas.

Um cenário de divisor zero verifica o diagnóstico do nosso runtime e não exige
igualdade com políticas de recuperação de outro compilador. Compilar os demais
programas não comprova seu comportamento; eles não são executados sem fixtures.

| Estado do backend | Arquivos |
|---|---:|
| compiled | 60 |
| external_dependency_missing | 6 |
| not_run | 18 |
| unsupported_backend | 2 |

## Sete oficiais

| Programa | C / GCC | Execução e validação | Cenários |
|---|---|---|---:|
| BUSCA01A | compiled (executable) | validado | 4 |
| CAD0002A | compiled (module) | validado | 2 |
| CAD0004A | compiled (executable) | validado | 2 |
| CAD0005A corrigido | compiled (executable) | validado | 7 |
| CAIXAREG | compiled (executable) | validado | 2 |
| CALCMD01 | compiled (executable) | validado | 3 |
| PROG024A | compiled (executable) | validado | 5 |

CAD0002A é compilado como objeto chamável e executado por um driver que fornece
COPY002A-REGISTRO e confere seus campos após GOBACK. PROG024A liga PROGDATA e
usa data/hora determinística. Não há main artificial nos subprogramas.

## Cenários e oráculo

| Cenário | Programa | Retorno | Expectativas | GnuCOBOL |
|---|---|---:|---|---|
| busca-first | BUSCA01A | 0 | OK | igual |
| busca-last | BUSCA01A | 0 | OK | igual |
| busca-absent | BUSCA01A | 0 | OK | igual |
| busca-empty | BUSCA01A | 0 | OK | igual |
| cad2-fim | CAD0002A | 0 | OK | igual |
| cad2-validation-and-shared-record | CAD0002A | 0 | OK | igual |
| cad4-one | CAD0004A | 0 | OK | igual |
| cad4-two | CAD0004A | 0 | OK | igual |
| agenda-empty | CAD0005A | 0 | OK | igual |
| agenda-add | CAD0005A | 0 | OK | igual |
| agenda-reopen-add | CAD0005A | 0 | OK | igual |
| agenda-list | CAD0005A | 0 | OK | igual |
| agenda-duplicate | CAD0005A | 0 | OK | igual |
| agenda-fim | CAD0005A | 0 | OK | igual |
| agenda-invalid-option | CAD0005A | 0 | OK | igual |
| caixa-no-discount | CAIXAREG | 0 | OK | igual |
| caixa-retries-and-discount | CAIXAREG | 0 | OK | igual |
| calcmd-basic | CALCMD01 | 0 | OK | igual |
| calcmd-retry-and-fraction | CALCMD01 | 0 | OK | igual |
| calcmd-zero-divisor | CALCMD01 | 1 | OK | não comparado |
| extra-refmod-count | PROG012A | 0 | OK | igual |
| extra-search-found | PROG020A | 0 | OK | igual |
| extra-search-absent | PROG020A | 0 | OK | igual |
| biblioteca-empty | PROG024A | 0 | OK | igual |
| biblioteca-add-loan-return-query | PROG024A | 0 | OK | igual |
| biblioteca-reopen-list | PROG024A | 0 | OK | igual |
| biblioteca-absent | PROG024A | 0 | OK | igual |
| biblioteca-loan-unavailable | PROG024A | 0 | OK | igual |
| extra-sequential-delete | PROG039A | 0 | OK | igual |
| progdata-clock | PROGDATA | 0 | OK | igual |

Oráculo encontrado: `cobc (GnuCOBOL) 3.2.0`.
As comparações usam fixtures idênticas, `COB_CURRENT_DATE=20261117123456`,
`COB_LS_FIXED=Y`, `COB_LS_NULLS=N` e `COB_LS_VALIDATE=N`, preservando os
comprimentos físicos definidos pelo projeto. O nosso relógio usa
`COBOL_DATETIME=2026-11-17T12:34:56`. O log de BIBLIOTECA é preparado
explicitamente: OPEN EXTEND de arquivo ausente falha com status 35.

## Todo o corpus

| Fonte | Semântica | Backend | C | GCC | Artefato | Validado funcionalmente |
|---|---|---|---|---|---|---|
| [examples/complementares/ASCII001.cbl](../examples/complementares/ASCII001.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/CAD0001A.cbl](../examples/complementares/CAD0001A.cbl) | valid_pending_external | external_dependency_missing | não | not_run | executable | não |
| [examples/complementares/CBREAKEX.cbl](../examples/complementares/CBREAKEX.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/CLIESQL01.cbl](../examples/complementares/CLIESQL01.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/GAMESNAK.cbl](../examples/complementares/GAMESNAK.cbl) | semantic_valid | unsupported_backend | não | not_run | executable | não |
| [examples/complementares/GRAV001A.cbl](../examples/complementares/GRAV001A.cbl) | semantic_valid | compiled | sim | success | module | não |
| [examples/complementares/LER0001A.cbl](../examples/complementares/LER0001A.cbl) | semantic_valid | compiled | sim | success | module | não |
| [examples/complementares/LER0002A.cbl](../examples/complementares/LER0002A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/LOGIN01A.cbl](../examples/complementares/LOGIN01A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/MINICALC.cbl](../examples/complementares/MINICALC.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/NCURSESDEMO.cbl](../examples/complementares/NCURSESDEMO.cbl) | valid_pending_external | external_dependency_missing | não | not_run | executable | não |
| [examples/complementares/PROG001A.cbl](../examples/complementares/PROG001A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG002A.cbl](../examples/complementares/PROG002A.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/PROG003A.cbl](../examples/complementares/PROG003A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG004A.cbl](../examples/complementares/PROG004A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG005A.cbl](../examples/complementares/PROG005A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG006A.cbl](../examples/complementares/PROG006A.cbl) | unsupported_extension | not_run | não | not_run | — | não |
| [examples/complementares/PROG007A.cbl](../examples/complementares/PROG007A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG008A.cbl](../examples/complementares/PROG008A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG009A.cbl](../examples/complementares/PROG009A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG010A.cbl](../examples/complementares/PROG010A.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/PROG011A.cbl](../examples/complementares/PROG011A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG012A.cbl](../examples/complementares/PROG012A.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/complementares/PROG014A.cbl](../examples/complementares/PROG014A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG015A.cbl](../examples/complementares/PROG015A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG016A.cbl](../examples/complementares/PROG016A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG017A.cbl](../examples/complementares/PROG017A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG018A.cbl](../examples/complementares/PROG018A.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/PROG019A.cbl](../examples/complementares/PROG019A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG020A.cbl](../examples/complementares/PROG020A.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/complementares/PROG021A.cbl](../examples/complementares/PROG021A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG022A.cbl](../examples/complementares/PROG022A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG023A.cbl](../examples/complementares/PROG023A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG023B.cbl](../examples/complementares/PROG023B.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG023C.cbl](../examples/complementares/PROG023C.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/PROG023D.cbl](../examples/complementares/PROG023D.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG023E.cbl](../examples/complementares/PROG023E.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG025A.cbl](../examples/complementares/PROG025A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG027A.cbl](../examples/complementares/PROG027A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG028A.cbl](../examples/complementares/PROG028A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG029A.cbl](../examples/complementares/PROG029A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG033A.cbl](../examples/complementares/PROG033A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG034A.cbl](../examples/complementares/PROG034A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG035A.cbl](../examples/complementares/PROG035A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG036A.cbl](../examples/complementares/PROG036A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG037A.cbl](../examples/complementares/PROG037A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG038A.cbl](../examples/complementares/PROG038A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG039A.cbl](../examples/complementares/PROG039A.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/complementares/PROG040A.cbl](../examples/complementares/PROG040A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG041A.cbl](../examples/complementares/PROG041A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG042A.cbl](../examples/complementares/PROG042A.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/PROG042B.cbl](../examples/complementares/PROG042B.cbl) | semantic_valid | compiled | sim | success | module | não |
| [examples/complementares/PROG043A.cbl](../examples/complementares/PROG043A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG044A.cbl](../examples/complementares/PROG044A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROG045A.cbl](../examples/complementares/PROG045A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROGTEST.cbl](../examples/complementares/PROGTEST.cbl) | partially_supported | not_run | não | not_run | — | não |
| [examples/complementares/PROGTEST2.cbl](../examples/complementares/PROGTEST2.cbl) | valid_pending_external | external_dependency_missing | não | not_run | executable | não |
| [examples/complementares/PROGTEST3.cbl](../examples/complementares/PROGTEST3.cbl) | valid_pending_external | external_dependency_missing | não | not_run | executable | não |
| [examples/complementares/PROGTEST4.cbl](../examples/complementares/PROGTEST4.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/PROGTIME.cbl](../examples/complementares/PROGTIME.cbl) | semantic_valid | compiled | sim | success | module | não |
| [examples/complementares/PROGVSAM.cbl](../examples/complementares/PROGVSAM.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/REL0001A.cbl](../examples/complementares/REL0001A.cbl) | semantic_valid | compiled | sim | success | module | não |
| [examples/complementares/REL0002A.cbl](../examples/complementares/REL0002A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/SORT001A.cbl](../examples/complementares/SORT001A.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/SORT002A.cbl](../examples/complementares/SORT002A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/TELABMS.cbl](../examples/complementares/TELABMS.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/TESTE002.cbl](../examples/complementares/TESTE002.cbl) | semantic_valid | unsupported_backend | não | not_run | executable | não |
| [examples/complementares/VALCNPJ.cbl](../examples/complementares/VALCNPJ.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/VALCPF01.cbl](../examples/complementares/VALCPF01.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/VALIDA1A.cbl](../examples/complementares/VALIDA1A.cbl) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/VALIDA1B.cbl](../examples/complementares/VALIDA1B.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/complementares/clientes-sql.cbl](../examples/complementares/clientes-sql.cbl) | unsupported_extension | not_run | não | not_run | — | não |
| [examples/complementares/main.cbl](../examples/complementares/main.cbl) | valid_pending_external | external_dependency_missing | não | not_run | executable | não |
| [examples/complementares/meu_programa.cob](../examples/complementares/meu_programa.cob) | semantic_valid | compiled | sim | success | executable | não |
| [examples/complementares/ncurses_demo.cbl](../examples/complementares/ncurses_demo.cbl) | valid_pending_external | external_dependency_missing | não | not_run | executable | não |
| [examples/corrigidos/CAD0005A.cbl](../examples/corrigidos/CAD0005A.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/dependencias/COD001A.cpy](../examples/dependencias/COD001A.cpy) | copybook_context_only | not_run | não | not_run | — | não |
| [examples/dependencias/COPY002A.cpy](../examples/dependencias/COPY002A.cpy) | copybook_context_only | not_run | não | not_run | — | não |
| [examples/dependencias/PROGDATA.cbl](../examples/dependencias/PROGDATA.cbl) | semantic_valid | compiled | sim | success | module | sim |
| [examples/oficiais/BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/oficiais/CAD0002A.cbl](../examples/oficiais/CAD0002A.cbl) | semantic_valid | compiled | sim | success | module | sim |
| [examples/oficiais/CAD0004A.cbl](../examples/oficiais/CAD0004A.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/oficiais/CAD0005A.cbl](../examples/oficiais/CAD0005A.cbl) | invalid_source | not_run | não | not_run | — | não |
| [examples/oficiais/CAIXAREG.cbl](../examples/oficiais/CAIXAREG.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/oficiais/CALCMD01.cbl](../examples/oficiais/CALCMD01.cbl) | semantic_valid | compiled | sim | success | executable | sim |
| [examples/oficiais/PROG024A.cbl](../examples/oficiais/PROG024A.cbl) | semantic_valid | compiled | sim | success | executable | sim |

## Falhas e limitações identificadas

| Fonte | Motivo |
|---|---|
| examples/complementares/CAD0001A.cbl | `LINK_UNRESOLVED_CALL`: Implementação ausente para CALL SORT001A. |
| examples/complementares/GAMESNAK.cbl | `UNSUPPORTED_BACKEND_SCREEN_POSITION`: Backend não implementado: SCREEN_POSITION. |
| examples/complementares/NCURSESDEMO.cbl | `LINK_UNRESOLVED_CALL`: Implementação ausente para CALL initscr.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL cbreak.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL noecho.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL clear.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL scanw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL scanw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL clear.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL getch.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL endwin. |
| examples/complementares/PROGTEST2.cbl | `LINK_UNRESOLVED_CALL`: Implementação ausente para CALL initscr.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL keypad.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL noecho.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL clear.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvscanw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvscanw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL clear.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL getch.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL endwin. |
| examples/complementares/PROGTEST3.cbl | `LINK_UNRESOLVED_CALL`: Implementação ausente para CALL initscr.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL clear.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL scanw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL scanw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL clear.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mvprintw.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL refresh.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL getch.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL endwin. |
| examples/complementares/TESTE002.cbl | `UNSUPPORTED_BACKEND_SCREEN_POSITION`: Backend não implementado: SCREEN_POSITION. |
| examples/complementares/main.cbl | `LINK_UNRESOLVED_CALL`: Implementação ausente para CALL exibir_tela. |
| examples/complementares/ncurses_demo.cbl | `LINK_UNRESOLVED_CALL`: Implementação ausente para CALL ncurses_wrapper.c.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL mostrar_mensagem.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL esperar_tecla.<br>`LINK_UNRESOLVED_CALL`: Implementação ausente para CALL finalizar_ncurses. |

## Contratos, limites e testes

- Runtime próprio: buffers/slices, decimal racional exato, DISPLAY/overpunch, COMP little-endian, COMP-3, edição, conversões, terminal, datas e arquivos.
- C11 gerado diretamente da AST/anotações. Dispatcher com pilha de limites/retornos preserva seções, parágrafos, fall-through, GO TO e PERFORM; não há interpretador ou bytecode.
- Até 128 dígitos por campo e capacidade checada de 512 dígitos por inteiro intermediário; áreas até 64 MiB. Exceder capacidade é erro explícito, sem conversão para float.
- Dados e registros usam ISO-8859-1; stdin/stdout usam UTF-8 na fronteira por padrão. `COBOL_TERMINAL_ENCODING=latin1` seleciona terminal bruto. Campos COBOL continuam com comprimento em bytes da ABI.
- Recursos sem backend são rejeitados antes de GCC: tela/posicionamento, arquivos opcionais, algumas formas complexas de INSPECT/SEARCH, comprimento variável de grupo e GO TO que sai de PERFORM inline. Os códigos efetivamente encontrados estão na tabela acima.
- SQL/CICS, ncurses, VSAM/INDEXED, ALTER, SORT e START continuam fora do subconjunto conforme a semântica; chamadas externas têm diagnóstico de ligação, sem stubs.
- O processo de compilação não executa o programa nem cria fixtures de dados. O driver publica saída por substituição atômica somente após GCC bem-sucedido e protege fontes/COPY/runtime de colisões.
- A suíte contém **326 testes**, preservando os 245 anteriores: runtime em C com `-Werror`, controle, arquivos, chamadas, CLI e cenários oficiais. O auditor conta os testes; a execução integral é independente, pelo comando abaixo. O resultado da entrega está em [runtime e uso](backend.md).
- Os três ensaios complementares não substituem os três programas escolhidos pelo professor. Demais programas compilados precisam de cenários adicionais antes de serem declarados funcionais.

## Reprodução

```bash
python -m unittest discover -s tests -v
python -m tools.auditar_backend --write
python -m tools.comparar_gnucobol
```

O [JSON completo](auditoria-backend.json) guarda diagnósticos, hashes e tamanhos
de stdout/arquivos, diferenças do oráculo e o estado de cada programa. `--no-oracle`
mantém os testes próprios e registra a ausência de comparação independente.
