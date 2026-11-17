# Inventário gerado do corpus COBOL Dicas

Gerado por `python -m tools.auditar_corpus`; não editar manualmente.

Commit de referência: `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`.

O [JSON completo](auditoria-lexer-depois.json) registra por arquivo todos os lexemas,
valores, frequências, primeiras posições, categorias, dependências, máscaras,
palavras reclassificadas e diagnósticos antes/depois. Não expande COPY.

## Programas oficiais (CAD0005A corrigido)

| Programa | Tokens antes → depois | Erros antes → depois | PIC |
|---|---:|---:|---|
| [BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) | 208 → 208 | 0 → 0 | `9(02)`, `9(11)`, `X(01)`, `X(30)` |
| [CAD0002A.cbl](../examples/oficiais/CAD0002A.cbl) | 864 → 868 | 4 → 0 | `9(02)`, `9(03)`, `9(04)`, `9(08)`, `9(09)`, `X(01)`, `X(02)`, `X(20)`, `X(30)`, `X(50)` |
| [CAD0004A.cbl](../examples/oficiais/CAD0004A.cbl) | 133 → 133 | 0 → 0 | `9(03)`, `X(1)`, `X(14)`, `X(30)` |
| [CAD0005A.cbl](../examples/corrigidos/CAD0005A.cbl) | 516 → 516 | 0 → 0 | `9(01)`, `9(02)`, `X(01)`, `X(02)`, `X(15)`, `X(30)` |
| [CAIXAREG.cbl](../examples/oficiais/CAIXAREG.cbl) | 390 → 390 | 0 → 0 | `9(05)V99`, `9(06)V99`, `X(01)`, `ZZZ.ZZZ.ZZZ,ZZ` |
| [CALCMD01.cbl](../examples/oficiais/CALCMD01.cbl) | 285 → 285 | 0 → 0 | `9(02)`, `9(06)V99`, `9(08)V9999`, `X(01)` |
| [PROG024A.cbl](../examples/oficiais/PROG024A.cbl) | 1397 → 1397 | 0 → 0 | `9(002)`, `9(004)`, `9(01)`, `9(02)`, `9(05)`, `S9(4)`, `X(001)`, `X(01)`, `X(10)`, `X(20)`, `X(40)` |

## Todos os fontes importados e a cópia corrigida

Zero erros significa apenas tokenização bem formada; não atesta suporte sintático/semântico.

| Arquivo | Tokens | Diagnósticos por código | Observações |
|---|---:|---|---|
| [ASCII001.cbl](../examples/complementares/ASCII001.cbl) | 40 | 0 |  |
| [CAD0001A.cbl](../examples/complementares/CAD0001A.cbl) | 286 | 0 |  |
| [CBREAKEX.cbl](../examples/complementares/CBREAKEX.cbl) | 607 | INVALID_INDICATOR: 38 |  |
| [CLIESQL01.cbl](../examples/complementares/CLIESQL01.cbl) | 0 | 0 | arquivo vazio; sucesso léxico não representa programa |
| [GAMESNAK.cbl](../examples/complementares/GAMESNAK.cbl) | 1028 | 0 | terminal/tela (runtime futuro) |
| [GRAV001A.cbl](../examples/complementares/GRAV001A.cbl) | 203 | 0 |  |
| [LER0001A.cbl](../examples/complementares/LER0001A.cbl) | 223 | 0 |  |
| [LER0002A.cbl](../examples/complementares/LER0002A.cbl) | 138 | 0 |  |
| [LOGIN01A.cbl](../examples/complementares/LOGIN01A.cbl) | 289 | 0 |  |
| [MINICALC.cbl](../examples/complementares/MINICALC.cbl) | 371 | 0 |  |
| [NCURSESDEMO.cbl](../examples/complementares/NCURSESDEMO.cbl) | 166 | 0 | biblioteca externa ncurses/ABI C |
| [PROG001A.cbl](../examples/complementares/PROG001A.cbl) | 236 | 0 |  |
| [PROG002A.cbl](../examples/complementares/PROG002A.cbl) | 856 | MERGE_CONFLICT: 3 |  |
| [PROG003A.cbl](../examples/complementares/PROG003A.cbl) | 501 | 0 |  |
| [PROG004A.cbl](../examples/complementares/PROG004A.cbl) | 177 | 0 |  |
| [PROG005A.cbl](../examples/complementares/PROG005A.cbl) | 212 | 0 |  |
| [PROG006A.cbl](../examples/complementares/PROG006A.cbl) | 79 | 0 | CICS (fora do subconjunto) |
| [PROG007A.cbl](../examples/complementares/PROG007A.cbl) | 55 | 0 |  |
| [PROG008A.cbl](../examples/complementares/PROG008A.cbl) | 108 | 0 |  |
| [PROG009A.cbl](../examples/complementares/PROG009A.cbl) | 137 | 0 |  |
| [PROG010A.cbl](../examples/complementares/PROG010A.cbl) | 364 | MERGE_CONFLICT: 30 |  |
| [PROG011A.cbl](../examples/complementares/PROG011A.cbl) | 61 | 0 |  |
| [PROG012A.cbl](../examples/complementares/PROG012A.cbl) | 111 | 0 |  |
| [PROG014A.cbl](../examples/complementares/PROG014A.cbl) | 59 | 0 |  |
| [PROG015A.cbl](../examples/complementares/PROG015A.cbl) | 90 | 0 |  |
| [PROG016A.cbl](../examples/complementares/PROG016A.cbl) | 172 | 0 |  |
| [PROG017A.cbl](../examples/complementares/PROG017A.cbl) | 193 | 0 |  |
| [PROG018A.cbl](../examples/complementares/PROG018A.cbl) | 50 | 0 |  |
| [PROG019A.cbl](../examples/complementares/PROG019A.cbl) | 185 | 0 |  |
| [PROG020A.cbl](../examples/complementares/PROG020A.cbl) | 186 | 0 |  |
| [PROG021A.cbl](../examples/complementares/PROG021A.cbl) | 184 | 0 |  |
| [PROG022A.cbl](../examples/complementares/PROG022A.cbl) | 283 | 0 |  |
| [PROG023A.cbl](../examples/complementares/PROG023A.cbl) | 807 | 0 |  |
| [PROG023B.cbl](../examples/complementares/PROG023B.cbl) | 1144 | 0 |  |
| [PROG023C.cbl](../examples/complementares/PROG023C.cbl) | 1651 | MERGE_CONFLICT: 3 |  |
| [PROG023D.cbl](../examples/complementares/PROG023D.cbl) | 1818 | 0 |  |
| [PROG023E.cbl](../examples/complementares/PROG023E.cbl) | 2048 | 0 |  |
| [PROG025A.cbl](../examples/complementares/PROG025A.cbl) | 1264 | 0 |  |
| [PROG027A.cbl](../examples/complementares/PROG027A.cbl) | 775 | 0 |  |
| [PROG028A.cbl](../examples/complementares/PROG028A.cbl) | 755 | 0 |  |
| [PROG029A.cbl](../examples/complementares/PROG029A.cbl) | 250 | 0 |  |
| [PROG033A.cbl](../examples/complementares/PROG033A.cbl) | 145 | 0 |  |
| [PROG034A.cbl](../examples/complementares/PROG034A.cbl) | 239 | 0 |  |
| [PROG035A.cbl](../examples/complementares/PROG035A.cbl) | 197 | 0 |  |
| [PROG036A.cbl](../examples/complementares/PROG036A.cbl) | 587 | 0 |  |
| [PROG037A.cbl](../examples/complementares/PROG037A.cbl) | 462 | 0 |  |
| [PROG038A.cbl](../examples/complementares/PROG038A.cbl) | 422 | 0 |  |
| [PROG039A.cbl](../examples/complementares/PROG039A.cbl) | 315 | 0 |  |
| [PROG040A.cbl](../examples/complementares/PROG040A.cbl) | 224 | 0 |  |
| [PROG041A.cbl](../examples/complementares/PROG041A.cbl) | 201 | 0 |  |
| [PROG042A.cbl](../examples/complementares/PROG042A.cbl) | 895 | IDENTIFIER_TOO_LONG: 2 |  |
| [PROG042B.cbl](../examples/complementares/PROG042B.cbl) | 410 | 0 |  |
| [PROG043A.cbl](../examples/complementares/PROG043A.cbl) | 422 | 0 |  |
| [PROG044A.cbl](../examples/complementares/PROG044A.cbl) | 291 | 0 |  |
| [PROG045A.cbl](../examples/complementares/PROG045A.cbl) | 562 | 0 |  |
| [PROGTEST.cbl](../examples/complementares/PROGTEST.cbl) | 123 | 0 | terminal/tela (runtime futuro) |
| [PROGTEST2.cbl](../examples/complementares/PROGTEST2.cbl) | 185 | 0 | biblioteca externa ncurses/ABI C |
| [PROGTEST3.cbl](../examples/complementares/PROGTEST3.cbl) | 206 | 0 | biblioteca externa ncurses/ABI C |
| [PROGTEST4.cbl](../examples/complementares/PROGTEST4.cbl) | 172 | 0 |  |
| [PROGTIME.cbl](../examples/complementares/PROGTIME.cbl) | 116 | 0 |  |
| [PROGVSAM.cbl](../examples/complementares/PROGVSAM.cbl) | 353 | 0 |  |
| [REL0001A.cbl](../examples/complementares/REL0001A.cbl) | 732 | 0 |  |
| [REL0002A.cbl](../examples/complementares/REL0002A.cbl) | 690 | 0 |  |
| [SORT001A.cbl](../examples/complementares/SORT001A.cbl) | 522 | MERGE_CONFLICT: 3 |  |
| [SORT002A.cbl](../examples/complementares/SORT002A.cbl) | 480 | 0 |  |
| [TELABMS.cbl](../examples/complementares/TELABMS.cbl) | 88 | INVALID_CHARACTER: 2 | BMS, não é fonte COBOL apesar da extensão; terminal/tela (runtime futuro) |
| [TESTE002.cbl](../examples/complementares/TESTE002.cbl) | 67 | 0 | terminal/tela (runtime futuro) |
| [VALCNPJ.cbl](../examples/complementares/VALCNPJ.cbl) | 753 | 0 |  |
| [VALCPF01.cbl](../examples/complementares/VALCPF01.cbl) | 276 | 0 |  |
| [VALIDA1A.cbl](../examples/complementares/VALIDA1A.cbl) | 452 | 0 |  |
| [VALIDA1B.cbl](../examples/complementares/VALIDA1B.cbl) | 1060 | MERGE_CONFLICT: 27 |  |
| [clientes-sql.cbl](../examples/complementares/clientes-sql.cbl) | 99 | 0 | SQL embutido (fora do subconjunto) |
| [main.cbl](../examples/complementares/main.cbl) | 46 | 0 |  |
| [meu_programa.cob](../examples/complementares/meu_programa.cob) | 29 | 0 |  |
| [ncurses_demo.cbl](../examples/complementares/ncurses_demo.cbl) | 36 | 0 |  |
| [CAD0005A.cbl](../examples/corrigidos/CAD0005A.cbl) | 516 | 0 |  |
| [COD001A.cpy](../examples/dependencias/COD001A.cpy) | 69 | 0 |  |
| [COPY002A.cpy](../examples/dependencias/COPY002A.cpy) | 89 | 0 |  |
| [PROGDATA.cbl](../examples/dependencias/PROGDATA.cbl) | 253 | 0 |  |
| [BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) | 208 | 0 |  |
| [CAD0002A.cbl](../examples/oficiais/CAD0002A.cbl) | 868 | 0 |  |
| [CAD0004A.cbl](../examples/oficiais/CAD0004A.cbl) | 133 | 0 |  |
| [CAD0005A.cbl](../examples/oficiais/CAD0005A.cbl) | 518 | MERGE_CONFLICT: 3 |  |
| [CAIXAREG.cbl](../examples/oficiais/CAIXAREG.cbl) | 390 | 0 |  |
| [CALCMD01.cbl](../examples/oficiais/CALCMD01.cbl) | 285 | 0 |  |
| [PROG024A.cbl](../examples/oficiais/PROG024A.cbl) | 1397 | 0 |  |

## Dependências por fonte

ASSIGN lista destinos físicos; não implica arquivo de entrada existente. CALL dinâmico
e dependências de EXEC SQL/CICS exigem análise específica. A tabela é inventário léxico.

| Fonte | Tipo | Alvo | Linha | Resolução |
|---|---|---|---:|---|
| CAD0001A.cbl | COPY | `COD001A` | 25 | examples/dependencias/COD001A.cpy |
| CAD0001A.cbl | COPY | `COPY002A` | 28 | examples/dependencias/COPY002A.cpy |
| CAD0001A.cbl | CALL | `PROGDATA` | 57 | examples/dependencias/PROGDATA.cbl |
| CAD0001A.cbl | CALL | `CAD0002A` | 81 | examples/oficiais/CAD0002A.cbl |
| CAD0001A.cbl | CALL | `LER0001A` | 99 | examples/complementares/LER0001A.cbl |
| CAD0001A.cbl | CALL | `GRAV001A` | 117 | examples/complementares/GRAV001A.cbl |
| CAD0001A.cbl | CALL | `REL0001A` | 134 | examples/complementares/REL0001A.cbl |
| CAD0001A.cbl | CALL | `SORT001A` | 155 | examples/complementares/SORT001A.cbl |
| GRAV001A.cbl | ASSIGN | `SEQSAI02.dat` | 13 | não fornecido / externo |
| GRAV001A.cbl | COPY | `COPY002A` | 40 | examples/dependencias/COPY002A.cpy |
| LER0001A.cbl | ASSIGN | `SEQENT01.dat` | 13 | não fornecido / externo |
| LER0001A.cbl | COPY | `COPY002A` | 40 | examples/dependencias/COPY002A.cpy |
| LER0002A.cbl | ASSIGN | `CADASTRO2.dat` | 13 | não fornecido / externo |
| LOGIN01A.cbl | ASSIGN | `USUARIO.dat` | 17 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `initscr` | 12 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `cbreak` | 13 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `noecho` | 14 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `clear` | 15 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 18 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 22 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `refresh` | 24 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `scanw` | 25 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 28 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `refresh` | 30 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `scanw` | 31 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `clear` | 34 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 35 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 37 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 39 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 41 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `mvprintw` | 43 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `refresh` | 47 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `getch` | 50 | não fornecido / externo |
| NCURSESDEMO.cbl | CALL | `endwin` | 51 | não fornecido / externo |
| PROG005A.cbl | ASSIGN | `SEQENT02.dat` | 7 | não fornecido / externo |
| PROG008A.cbl | ASSIGN | `SEQENT01.dat` | 7 | não fornecido / externo |
| PROG009A.cbl | ASSIGN | `SEQSAI01.dat` | 7 | não fornecido / externo |
| PROG010A.cbl | ASSIGN | `SEQENT02.dat` | 12 | não fornecido / externo |
| PROG010A.cbl | ASSIGN | `SEQSAI03.dat` | 15 | não fornecido / externo |
| PROG010A.cbl | ASSIGN | `SEQSAI05.dat` | 20 | não fornecido / externo |
| PROG016A.cbl | COPY | `COD001A` | 21 | examples/dependencias/COD001A.cpy |
| PROG016A.cbl | CALL | `PROGDATA` | 25 | examples/dependencias/PROGDATA.cbl |
| PROG016A.cbl | CALL | `PROGTIME` | 42 | examples/complementares/PROGTIME.cbl |
| PROG021A.cbl | ASSIGN | `USUARIO.dat` | 7 | não fornecido / externo |
| PROG023A.cbl | ASSIGN | `ESTOQUE.dat` | 17 | não fornecido / externo |
| PROG023B.cbl | ASSIGN | `ESTOQUE.dat` | 18 | não fornecido / externo |
| PROG023C.cbl | ASSIGN | `ESTOQUE.dat` | 19 | não fornecido / externo |
| PROG023C.cbl | ASSIGN | `ARQLOG1.dat` | 22 | não fornecido / externo |
| PROG023C.cbl | COPY | `COD001A` | 96 | examples/dependencias/COD001A.cpy |
| PROG023C.cbl | CALL | `PROGDATA` | 658 | examples/dependencias/PROGDATA.cbl |
| PROG023C.cbl | CALL | `PROGTIME` | 683 | examples/complementares/PROGTIME.cbl |
| PROG023D.cbl | ASSIGN | `ESTOQUE.dat` | 19 | não fornecido / externo |
| PROG023D.cbl | ASSIGN | `ARQLOG1.dat` | 22 | não fornecido / externo |
| PROG023D.cbl | COPY | `COD001A` | 99 | examples/dependencias/COD001A.cpy |
| PROG023D.cbl | CALL | `PROGDATA` | 724 | examples/dependencias/PROGDATA.cbl |
| PROG023D.cbl | CALL | `PROGTIME` | 749 | examples/complementares/PROGTIME.cbl |
| PROG023E.cbl | ASSIGN | `ESTOQUE.dat` | 23 | não fornecido / externo |
| PROG023E.cbl | ASSIGN | `ARQLOG1.dat` | 26 | não fornecido / externo |
| PROG023E.cbl | COPY | `COD001A` | 109 | examples/dependencias/COD001A.cpy |
| PROG023E.cbl | CALL | `PROGDATA` | 790 | examples/dependencias/PROGDATA.cbl |
| PROG023E.cbl | CALL | `PROGTIME` | 815 | examples/complementares/PROGTIME.cbl |
| PROG025A.cbl | ASSIGN | `TITULOS.dat` | 17 | não fornecido / externo |
| PROG025A.cbl | ASSIGN | `PARAMETROS.dat` | 20 | não fornecido / externo |
| PROG025A.cbl | ASSIGN | `BOLETOS.dat` | 23 | não fornecido / externo |
| PROG025A.cbl | COPY | `COD001A` | 187 | examples/dependencias/COD001A.cpy |
| PROG025A.cbl | CALL | `PROGDATA` | 220 | examples/dependencias/PROGDATA.cbl |
| PROG027A.cbl | ASSIGN | `PRODUTOS.dat` | 17 | não fornecido / externo |
| PROG027A.cbl | ASSIGN | `NOTAFISCAL.dat` | 20 | não fornecido / externo |
| PROG027A.cbl | COPY | `COD001A` | 126 | examples/dependencias/COD001A.cpy |
| PROG027A.cbl | CALL | `PROGDATA` | 160 | examples/dependencias/PROGDATA.cbl |
| PROG028A.cbl | ASSIGN | `FUNCIONARIO.dat` | 17 | não fornecido / externo |
| PROG028A.cbl | ASSIGN | `PONTO.dat` | 20 | não fornecido / externo |
| PROG028A.cbl | COPY | `COD001A` | 65 | examples/dependencias/COD001A.cpy |
| PROG028A.cbl | CALL | `PROGDATA` | 190 | examples/dependencias/PROGDATA.cbl |
| PROG028A.cbl | CALL | `PROGTIME` | 219 | examples/complementares/PROGTIME.cbl |
| PROG033A.cbl | CALL | `PROG034A` | 88 | examples/complementares/PROG034A.cbl |
| PROG033A.cbl | CALL | `PROG035A` | 106 | examples/complementares/PROG035A.cbl |
| PROG034A.cbl | ASSIGN | `CADENT001.dat` | 17 | não fornecido / externo |
| PROG034A.cbl | ASSIGN | `CADASTRO1.dat` | 19 | não fornecido / externo |
| PROG035A.cbl | ASSIGN | `CADASTRO1.dat` | 17 | não fornecido / externo |
| PROG036A.cbl | ASSIGN | `CLASSENT.dat` | 17 | não fornecido / externo |
| PROG036A.cbl | ASSIGN | `CADASTRO1.dat` | 19 | não fornecido / externo |
| PROG037A.cbl | ASSIGN | `ALTENT01.dat` | 17 | não fornecido / externo |
| PROG037A.cbl | ASSIGN | `CADASTRO1.dat` | 19 | não fornecido / externo |
| PROG038A.cbl | ASSIGN | `ALTCONS01.dat` | 17 | não fornecido / externo |
| PROG038A.cbl | ASSIGN | `CADASTRO1.dat` | 19 | não fornecido / externo |
| PROG038A.cbl | ASSIGN | `ALTRET01.dat` | 21 | não fornecido / externo |
| PROG039A.cbl | ASSIGN | `CADASTRO1.dat` | 17 | não fornecido / externo |
| PROG040A.cbl | ASSIGN | `CADASTRO2.dat` | 17 | não fornecido / externo |
| PROG041A.cbl | ASSIGN | `CADASTRO2.dat` | 17 | não fornecido / externo |
| PROG042A.cbl | ASSIGN | `CADASTRO1.dat` | 17 | não fornecido / externo |
| PROG042A.cbl | ASSIGN | `CADASTRO2.dat` | 20 | não fornecido / externo |
| PROG042A.cbl | ASSIGN | `PEDENT01.dat` | 23 | não fornecido / externo |
| PROG042A.cbl | ASSIGN | `CADASTRO3.dat` | 26 | não fornecido / externo |
| PROG042A.cbl | CALL | `PROG042B` | 349 | examples/complementares/PROG042B.cbl |
| PROG042B.cbl | ASSIGN | `CADASTRO3.dat` | 18 | não fornecido / externo |
| PROG043A.cbl | ASSIGN | `PRODCONS01.dat` | 17 | não fornecido / externo |
| PROG043A.cbl | ASSIGN | `CADASTRO2.dat` | 19 | não fornecido / externo |
| PROG043A.cbl | ASSIGN | `PRODRET01.dat` | 21 | não fornecido / externo |
| PROG044A.cbl | ASSIGN | `CADASTRO3.dat` | 17 | não fornecido / externo |
| PROG045A.cbl | ASSIGN | `PEDDET01.dat` | 17 | não fornecido / externo |
| PROG045A.cbl | ASSIGN | `CADASTRO3.dat` | 20 | não fornecido / externo |
| PROG045A.cbl | ASSIGN | `CADASTRO4.dat` | 23 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `initscr` | 16 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `keypad` | 17 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `noecho` | 18 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `clear` | 19 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 22 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 24 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 26 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `refresh` | 30 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvscanw` | 31 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvscanw` | 33 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `clear` | 37 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 38 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 40 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 42 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 44 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `mvprintw` | 46 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `refresh` | 49 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `getch` | 50 | não fornecido / externo |
| PROGTEST2.cbl | CALL | `endwin` | 53 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `initscr` | 14 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `clear` | 15 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 17 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 19 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `refresh` | 21 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `scanw` | 22 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 24 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `refresh` | 26 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `scanw` | 27 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `clear` | 37 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 38 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 40 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 42 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 44 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `mvprintw` | 46 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `refresh` | 53 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `getch` | 57 | não fornecido / externo |
| PROGTEST3.cbl | CALL | `endwin` | 59 | não fornecido / externo |
| PROGTIME.cbl | COPY | `COD001A` | 14 | examples/dependencias/COD001A.cpy |
| PROGVSAM.cbl | ASSIGN | `clientes.dat` | 8 | não fornecido / externo |
| REL0001A.cbl | ASSIGN | `REL0001A.txt` | 13 | não fornecido / externo |
| REL0001A.cbl | COPY | `COD001A` | 103 | examples/dependencias/COD001A.cpy |
| REL0001A.cbl | COPY | `COPY002A` | 107 | examples/dependencias/COPY002A.cpy |
| REL0001A.cbl | CALL | `PROGDATA` | 153 | examples/dependencias/PROGDATA.cbl |
| REL0001A.cbl | CALL | `PROGTIME` | 166 | examples/complementares/PROGTIME.cbl |
| REL0002A.cbl | ASSIGN | `CADASTRO3.dat` | 17 | não fornecido / externo |
| REL0002A.cbl | ASSIGN | `REL0002A.txt` | 20 | não fornecido / externo |
| REL0002A.cbl | COPY | `COD001A` | 108 | examples/dependencias/COD001A.cpy |
| REL0002A.cbl | CALL | `PROGDATA` | 156 | examples/dependencias/PROGDATA.cbl |
| REL0002A.cbl | CALL | `PROGTIME` | 169 | examples/complementares/PROGTIME.cbl |
| SORT001A.cbl | COPY | `COPY002A` | 42 | examples/dependencias/COPY002A.cpy |
| SORT002A.cbl | ASSIGN | `CADASTRO3.dat` | 17 | não fornecido / externo |
| main.cbl | CALL | `exibir_tela` | 13 | não fornecido / externo |
| ncurses_demo.cbl | CALL | `ncurses_wrapper.c` | 10 | não fornecido / externo |
| ncurses_demo.cbl | CALL | `mostrar_mensagem` | 12 | não fornecido / externo |
| ncurses_demo.cbl | CALL | `esperar_tecla` | 14 | não fornecido / externo |
| ncurses_demo.cbl | CALL | `finalizar_ncurses` | 16 | não fornecido / externo |
| CAD0005A.cbl | ASSIGN | `CADAGENDA.dat` | 18 | não fornecido / externo |
| PROGDATA.cbl | COPY | `COD001A` | 19 | examples/dependencias/COD001A.cpy |
| BUSCA01A.cbl | ASSIGN | `CADASTRO2.dat` | 17 | não fornecido / externo |
| CAD0002A.cbl | COPY | `COPY002A` | 50 | examples/dependencias/COPY002A.cpy |
| CAD0004A.cbl | ASSIGN | `CADASTRO.dat` | 13 | não fornecido / externo |
| CAD0005A.cbl | ASSIGN | `CADAGENDA.dat` | 18 | não fornecido / externo |
| PROG024A.cbl | ASSIGN | `BIBLIOTECA.dat` | 17 | não fornecido / externo |
| PROG024A.cbl | ASSIGN | `BIBLIOTECA.txt` | 20 | não fornecido / externo |
| PROG024A.cbl | COPY | `COD001A` | 93 | examples/dependencias/COD001A.cpy |
| PROG024A.cbl | CALL | `PROGDATA` | 574 | examples/dependencias/PROGDATA.cbl |
