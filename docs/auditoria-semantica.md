# Auditoria semântica e de layout

Gerado por `python -m tools.auditar_semantica --write`, sem rede, execução COBOL ou GCC.
Snapshot: `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`. Os fontes originais e hashes permanecem intactos.

## Métricas

- 86 arquivos revisitados; **72/72 programas aceitos pelo parser submetidos à semântica**.
- **68 programas semanticamente válidos**, incluindo pendências externas explicitadas abaixo.
- 2480 símbolos, 4257 referências vinculadas e 1490 descritores físicos.
- Dois copybooks são fragmentos; sua semântica é verificada nas inclusões, sem simular programas independentes.

| Classificação | Arquivos |
|---|---:|
| copybook_context_only | 2 |
| invalid_source | 13 |
| partially_supported | 1 |
| semantic_valid | 62 |
| unsupported_extension | 2 |
| valid_pending_external | 6 |

## Sete oficiais

| Programa | Estado | Símbolos | Referências | Layouts | Áreas e bytes máximos |
|---|---|---:|---:|---:|---|
| BUSCA01A.cbl | semantic_valid | 21 | 21 | 9 | FILE:s3=43; WORKING-STORAGE=26 |
| CAD0002A.cbl | semantic_valid | 68 | 150 | 47 | WORKING-STORAGE=238; LINKAGE:s32=13; LINKAGE:s35=10552 |
| CAD0004A.cbl | semantic_valid | 16 | 17 | 8 | FILE:s3=47; WORKING-STORAGE=48 |
| CAD0005A.cbl corrigido | semantic_valid | 37 | 76 | 15 | FILE:s3=45; WORKING-STORAGE=504 |
| CAIXAREG.cbl | semantic_valid | 33 | 63 | 10 | WORKING-STORAGE=61 |
| CALCMD01.cbl | semantic_valid | 23 | 39 | 8 | WORKING-STORAGE=41 |
| PROG024A.cbl | semantic_valid | 106 | 264 | 65 | FILE:s3=76; FILE:s4=113; WORKING-STORAGE=3980 |

CAD0005A original permanece negativo léxico. PROG024A usa PROGDATA disponível no
inventário, com parâmetros COD001A vinculados. A API/CLI exigem `--source` para fornecer
esse programa explicitamente. CAD0002A tem duas raízes externas de LINKAGE; somente
COPY002A-REGISTRO é parâmetro USING. Não há armazenamento local para essas raízes.

COPY002A-REGISTRO ocupa **10552 bytes**: contador de 2 bytes e 50 ocorrências de
**211 bytes**, com base 1 e primeiro registro no offset 2. O comentário histórico
`TAMANHO 02125` do copybook não determina o layout e não foi alterado. Os descritores
completos, offsets de cada campo e strides estão no JSON e em `--dump-layout`.

## Todos os arquivos

| Arquivo | Lexer | Parser | Semântica | Símbolos | Referências | Layouts | E/S | W | Classificação |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| [examples/complementares/ASCII001.cbl](../examples/complementares/ASCII001.cbl) | success | success | error | 4 | 2 | 1 | 2 | 0 | invalid_source |
| [examples/complementares/CAD0001A.cbl](../examples/complementares/CAD0001A.cbl) | success | success | success | 59 | 45 | 40 | 0 | 0 | valid_pending_external |
| [examples/complementares/CBREAKEX.cbl](../examples/complementares/CBREAKEX.cbl) | error | not_run | not_run | 0 | 0 | 0 | 38 | 0 | invalid_source |
| [examples/complementares/CLIESQL01.cbl](../examples/complementares/CLIESQL01.cbl) | success | error | not_run | 0 | 0 | 0 | 1 | 0 | invalid_source |
| [examples/complementares/GAMESNAK.cbl](../examples/complementares/GAMESNAK.cbl) | success | success | success | 56 | 182 | 37 | 0 | 0 | semantic_valid |
| [examples/complementares/GRAV001A.cbl](../examples/complementares/GRAV001A.cbl) | success | success | success | 48 | 16 | 34 | 0 | 0 | semantic_valid |
| [examples/complementares/LER0001A.cbl](../examples/complementares/LER0001A.cbl) | success | success | success | 46 | 26 | 34 | 0 | 0 | semantic_valid |
| [examples/complementares/LER0002A.cbl](../examples/complementares/LER0002A.cbl) | success | success | success | 17 | 17 | 5 | 0 | 0 | semantic_valid |
| [examples/complementares/LOGIN01A.cbl](../examples/complementares/LOGIN01A.cbl) | success | success | success | 30 | 34 | 12 | 0 | 0 | semantic_valid |
| [examples/complementares/MINICALC.cbl](../examples/complementares/MINICALC.cbl) | success | success | success | 29 | 56 | 8 | 0 | 0 | semantic_valid |
| [examples/complementares/NCURSESDEMO.cbl](../examples/complementares/NCURSESDEMO.cbl) | success | success | success | 6 | 5 | 3 | 0 | 0 | valid_pending_external |
| [examples/complementares/PROG001A.cbl](../examples/complementares/PROG001A.cbl) | success | success | success | 26 | 24 | 15 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG002A.cbl](../examples/complementares/PROG002A.cbl) | error | not_run | not_run | 0 | 0 | 0 | 3 | 0 | invalid_source |
| [examples/complementares/PROG003A.cbl](../examples/complementares/PROG003A.cbl) | success | success | success | 28 | 89 | 25 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG004A.cbl](../examples/complementares/PROG004A.cbl) | success | success | success | 14 | 27 | 11 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG005A.cbl](../examples/complementares/PROG005A.cbl) | success | success | success | 28 | 24 | 14 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG006A.cbl](../examples/complementares/PROG006A.cbl) | success | error | not_run | 0 | 0 | 0 | 4 | 0 | unsupported_extension |
| [examples/complementares/PROG007A.cbl](../examples/complementares/PROG007A.cbl) | success | success | success | 5 | 4 | 2 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG008A.cbl](../examples/complementares/PROG008A.cbl) | success | success | success | 10 | 13 | 5 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG009A.cbl](../examples/complementares/PROG009A.cbl) | success | success | success | 17 | 13 | 5 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG010A.cbl](../examples/complementares/PROG010A.cbl) | error | not_run | not_run | 0 | 0 | 0 | 30 | 0 | invalid_source |
| [examples/complementares/PROG011A.cbl](../examples/complementares/PROG011A.cbl) | success | success | success | 7 | 3 | 4 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG012A.cbl](../examples/complementares/PROG012A.cbl) | success | success | success | 11 | 10 | 8 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG014A.cbl](../examples/complementares/PROG014A.cbl) | success | success | success | 5 | 7 | 2 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG015A.cbl](../examples/complementares/PROG015A.cbl) | success | success | success | 6 | 14 | 3 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG016A.cbl](../examples/complementares/PROG016A.cbl) | success | success | success | 28 | 23 | 25 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG017A.cbl](../examples/complementares/PROG017A.cbl) | success | success | success | 10 | 27 | 5 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG018A.cbl](../examples/complementares/PROG018A.cbl) | success | success | error | 6 | 5 | 0 | 2 | 0 | invalid_source |
| [examples/complementares/PROG019A.cbl](../examples/complementares/PROG019A.cbl) | success | success | success | 13 | 24 | 8 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG020A.cbl](../examples/complementares/PROG020A.cbl) | success | success | success | 13 | 24 | 8 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG021A.cbl](../examples/complementares/PROG021A.cbl) | success | success | success | 17 | 22 | 11 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG022A.cbl](../examples/complementares/PROG022A.cbl) | success | success | success | 22 | 35 | 9 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG023A.cbl](../examples/complementares/PROG023A.cbl) | success | success | success | 52 | 141 | 20 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG023B.cbl](../examples/complementares/PROG023B.cbl) | success | success | success | 64 | 225 | 26 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG023C.cbl](../examples/complementares/PROG023C.cbl) | error | not_run | not_run | 0 | 0 | 0 | 3 | 0 | invalid_source |
| [examples/complementares/PROG023D.cbl](../examples/complementares/PROG023D.cbl) | success | success | success | 120 | 369 | 73 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG023E.cbl](../examples/complementares/PROG023E.cbl) | success | success | success | 128 | 431 | 79 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG025A.cbl](../examples/complementares/PROG025A.cbl) | success | success | success | 144 | 172 | 124 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG027A.cbl](../examples/complementares/PROG027A.cbl) | success | success | success | 107 | 93 | 86 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG028A.cbl](../examples/complementares/PROG028A.cbl) | success | success | success | 80 | 112 | 45 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG029A.cbl](../examples/complementares/PROG029A.cbl) | success | success | success | 27 | 31 | 12 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG033A.cbl](../examples/complementares/PROG033A.cbl) | success | success | success | 14 | 8 | 1 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG034A.cbl](../examples/complementares/PROG034A.cbl) | success | success | success | 26 | 28 | 13 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG035A.cbl](../examples/complementares/PROG035A.cbl) | success | success | success | 21 | 20 | 9 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG036A.cbl](../examples/complementares/PROG036A.cbl) | success | success | success | 40 | 114 | 19 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG037A.cbl](../examples/complementares/PROG037A.cbl) | success | success | success | 43 | 70 | 22 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG038A.cbl](../examples/complementares/PROG038A.cbl) | success | success | success | 42 | 58 | 24 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG039A.cbl](../examples/complementares/PROG039A.cbl) | success | success | success | 31 | 42 | 17 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG040A.cbl](../examples/complementares/PROG040A.cbl) | success | success | success | 23 | 23 | 7 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG041A.cbl](../examples/complementares/PROG041A.cbl) | success | success | success | 21 | 21 | 9 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG042A.cbl](../examples/complementares/PROG042A.cbl) | error | not_run | not_run | 0 | 0 | 0 | 2 | 0 | invalid_source |
| [examples/complementares/PROG042B.cbl](../examples/complementares/PROG042B.cbl) | success | success | success | 38 | 60 | 26 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG043A.cbl](../examples/complementares/PROG043A.cbl) | success | success | success | 42 | 58 | 24 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG044A.cbl](../examples/complementares/PROG044A.cbl) | success | success | success | 30 | 31 | 16 | 0 | 0 | semantic_valid |
| [examples/complementares/PROG045A.cbl](../examples/complementares/PROG045A.cbl) | success | success | success | 55 | 84 | 37 | 0 | 0 | semantic_valid |
| [examples/complementares/PROGTEST.cbl](../examples/complementares/PROGTEST.cbl) | success | success | error | 13 | 6 | 10 | 1 | 0 | partially_supported |
| [examples/complementares/PROGTEST2.cbl](../examples/complementares/PROGTEST2.cbl) | success | success | success | 7 | 5 | 3 | 0 | 0 | valid_pending_external |
| [examples/complementares/PROGTEST3.cbl](../examples/complementares/PROGTEST3.cbl) | success | success | success | 8 | 16 | 4 | 0 | 0 | valid_pending_external |
| [examples/complementares/PROGTEST4.cbl](../examples/complementares/PROGTEST4.cbl) | success | success | success | 12 | 21 | 8 | 0 | 0 | semantic_valid |
| [examples/complementares/PROGTIME.cbl](../examples/complementares/PROGTIME.cbl) | success | success | success | 26 | 15 | 15 | 0 | 0 | semantic_valid |
| [examples/complementares/PROGVSAM.cbl](../examples/complementares/PROGVSAM.cbl) | success | success | error | 20 | 51 | 12 | 6 | 0 | invalid_source |
| [examples/complementares/REL0001A.cbl](../examples/complementares/REL0001A.cbl) | success | success | success | 109 | 114 | 89 | 0 | 0 | semantic_valid |
| [examples/complementares/REL0002A.cbl](../examples/complementares/REL0002A.cbl) | success | success | success | 95 | 96 | 70 | 0 | 0 | semantic_valid |
| [examples/complementares/SORT001A.cbl](../examples/complementares/SORT001A.cbl) | error | not_run | not_run | 0 | 0 | 0 | 3 | 0 | invalid_source |
| [examples/complementares/SORT002A.cbl](../examples/complementares/SORT002A.cbl) | success | success | success | 33 | 83 | 15 | 0 | 0 | semantic_valid |
| [examples/complementares/TELABMS.cbl](../examples/complementares/TELABMS.cbl) | error | not_run | not_run | 0 | 0 | 0 | 2 | 0 | invalid_source |
| [examples/complementares/TESTE002.cbl](../examples/complementares/TESTE002.cbl) | success | success | success | 5 | 4 | 2 | 0 | 0 | semantic_valid |
| [examples/complementares/VALCNPJ.cbl](../examples/complementares/VALCNPJ.cbl) | success | success | success | 28 | 132 | 22 | 0 | 0 | semantic_valid |
| [examples/complementares/VALCPF01.cbl](../examples/complementares/VALCPF01.cbl) | success | success | success | 24 | 33 | 9 | 0 | 0 | semantic_valid |
| [examples/complementares/VALIDA1A.cbl](../examples/complementares/VALIDA1A.cbl) | success | success | success | 41 | 49 | 24 | 0 | 0 | semantic_valid |
| [examples/complementares/VALIDA1B.cbl](../examples/complementares/VALIDA1B.cbl) | error | not_run | not_run | 0 | 0 | 0 | 27 | 0 | invalid_source |
| [examples/complementares/clientes-sql.cbl](../examples/complementares/clientes-sql.cbl) | success | error | not_run | 0 | 0 | 0 | 4 | 0 | unsupported_extension |
| [examples/complementares/main.cbl](../examples/complementares/main.cbl) | success | success | success | 5 | 4 | 2 | 0 | 0 | valid_pending_external |
| [examples/complementares/meu_programa.cob](../examples/complementares/meu_programa.cob) | success | success | success | 4 | 1 | 1 | 0 | 0 | semantic_valid |
| [examples/complementares/ncurses_demo.cbl](../examples/complementares/ncurses_demo.cbl) | success | success | success | 4 | 1 | 1 | 0 | 0 | valid_pending_external |
| [examples/corrigidos/CAD0005A.cbl](../examples/corrigidos/CAD0005A.cbl) | success | success | success | 37 | 76 | 15 | 0 | 0 | semantic_valid |
| [examples/dependencias/COD001A.cpy](../examples/dependencias/COD001A.cpy) | success | success | not_run | 0 | 0 | 0 | 0 | 0 | copybook_context_only |
| [examples/dependencias/COPY002A.cpy](../examples/dependencias/COPY002A.cpy) | success | success | not_run | 0 | 0 | 0 | 0 | 0 | copybook_context_only |
| [examples/dependencias/PROGDATA.cbl](../examples/dependencias/PROGDATA.cbl) | success | success | success | 33 | 34 | 18 | 0 | 0 | semantic_valid |
| [examples/oficiais/BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) | success | success | success | 21 | 21 | 9 | 0 | 0 | semantic_valid |
| [examples/oficiais/CAD0002A.cbl](../examples/oficiais/CAD0002A.cbl) | success | success | success | 68 | 150 | 47 | 0 | 0 | semantic_valid |
| [examples/oficiais/CAD0004A.cbl](../examples/oficiais/CAD0004A.cbl) | success | success | success | 16 | 17 | 8 | 0 | 0 | semantic_valid |
| [examples/oficiais/CAD0005A.cbl](../examples/oficiais/CAD0005A.cbl) | error | not_run | not_run | 0 | 0 | 0 | 3 | 0 | invalid_source |
| [examples/oficiais/CAIXAREG.cbl](../examples/oficiais/CAIXAREG.cbl) | success | success | success | 33 | 63 | 10 | 0 | 0 | semantic_valid |
| [examples/oficiais/CALCMD01.cbl](../examples/oficiais/CALCMD01.cbl) | success | success | success | 23 | 39 | 8 | 0 | 0 | semantic_valid |
| [examples/oficiais/PROG024A.cbl](../examples/oficiais/PROG024A.cbl) | success | success | success | 106 | 264 | 65 | 0 | 0 | semantic_valid |

## Diagnósticos e justificativas individuais

Erro real no fonte prevalece na classificação quando também há recurso não suportado.
Pendência externa é informação (I), preserva a validade local e impede `backend_ready`.
Recursos fora do subconjunto são erros explícitos e nunca contam como sucesso.

| Arquivo | Posição/código e justificativa |
|---|---|
| examples/complementares/ASCII001.cbl | 10:20 E `UNDEFINED_SYMBOL`: WS-CODIGO não declarado em data/condition/index/special.<br>12:45 E `UNDEFINED_SYMBOL`: WS-CODIGO não declarado em data/condition/index/special. |
| examples/complementares/CAD0001A.cbl | 155:13 I `EXTERNAL_CALL_PENDING`: CALL SORT001A: assinatura pendente para ligação.<br>Fontes de ligação: examples/complementares/GRAV001A.cbl, examples/complementares/LER0001A.cbl, examples/complementares/PROGTIME.cbl, examples/complementares/REL0001A.cbl, examples/dependencias/PROGDATA.cbl, examples/oficiais/CAD0002A.cbl |
| examples/complementares/CBREAKEX.cbl | 2:7 E `INVALID_INDICATOR`: Indicador 'I' desconhecido na coluna 7.<br>3:7 E `INVALID_INDICATOR`: Indicador 'P' desconhecido na coluna 7.<br>4:7 E `INVALID_INDICATOR`: Indicador 'A' desconhecido na coluna 7.<br>5:7 E `INVALID_INDICATOR`: Indicador 'E' desconhecido na coluna 7.<br>7:7 E `INVALID_INDICATOR`: Indicador 'I' desconhecido na coluna 7.<br>8:7 E `INVALID_INDICATOR`: Indicador 'F' desconhecido na coluna 7.<br>9:7 E `INVALID_INDICATOR`: Indicador 'S' desconhecido na coluna 7.<br>10:7 E `INVALID_INDICATOR`: Indicador 'O' desconhecido na coluna 7.<br>12:7 E `INVALID_INDICATOR`: Indicador 'S' desconhecido na coluna 7.<br>13:7 E `INVALID_INDICATOR`: Indicador 'O' desconhecido na coluna 7.<br>15:7 E `INVALID_INDICATOR`: Indicador 'F' desconhecido na coluna 7.<br>17:7 E `INVALID_INDICATOR`: Indicador 'F' desconhecido na coluna 7.<br>18:7 E `INVALID_INDICATOR`: Indicador 'R' desconhecido na coluna 7.<br>20:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>27:7 E `INVALID_INDICATOR`: Indicador 'F' desconhecido na coluna 7.<br>29:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>32:7 E `INVALID_INDICATOR`: Indicador 'W' desconhecido na coluna 7.<br>33:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>40:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>43:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>57:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>62:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>67:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>74:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>85:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>99:7 E `INVALID_INDICATOR`: Indicador '0' desconhecido na coluna 7.<br>113:7 E `INVALID_INDICATOR`: Indicador 'P' desconhecido na coluna 7.<br>115:7 E `INVALID_INDICATOR`: Indicador 'P' desconhecido na coluna 7.<br>123:7 E `INVALID_INDICATOR`: Indicador 'P' desconhecido na coluna 7.<br>137:7 E `INVALID_INDICATOR`: Indicador 'P' desconhecido na coluna 7.<br>147:7 E `INVALID_INDICATOR`: Indicador 'M' desconhecido na coluna 7.<br>158:7 E `INVALID_INDICATOR`: Indicador 'S' desconhecido na coluna 7.<br>167:7 E `INVALID_INDICATOR`: Indicador 'C' desconhecido na coluna 7.<br>174:7 E `INVALID_INDICATOR`: Indicador 'C' desconhecido na coluna 7.<br>183:7 E `INVALID_INDICATOR`: Indicador 'G' desconhecido na coluna 7.<br>189:7 E `INVALID_INDICATOR`: Indicador 'S' desconhecido na coluna 7.<br>198:7 E `INVALID_INDICATOR`: Indicador 'C' desconhecido na coluna 7.<br>209:7 E `INVALID_INDICATOR`: Indicador 'S' desconhecido na coluna 7. |
| examples/complementares/CLIESQL01.cbl | 1:1 E `SYNTAX_ERROR`: Construção sintática inesperada. |
| examples/complementares/NCURSESDEMO.cbl | 12:12 I `EXTERNAL_CALL_PENDING`: CALL INITSCR: assinatura pendente para ligação.<br>13:12 I `EXTERNAL_CALL_PENDING`: CALL CBREAK: assinatura pendente para ligação.<br>14:12 I `EXTERNAL_CALL_PENDING`: CALL NOECHO: assinatura pendente para ligação.<br>15:12 I `EXTERNAL_CALL_PENDING`: CALL CLEAR: assinatura pendente para ligação.<br>18:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>22:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>24:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>25:12 I `EXTERNAL_CALL_PENDING`: CALL SCANW: assinatura pendente para ligação.<br>28:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>30:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>31:12 I `EXTERNAL_CALL_PENDING`: CALL SCANW: assinatura pendente para ligação.<br>34:12 I `EXTERNAL_CALL_PENDING`: CALL CLEAR: assinatura pendente para ligação.<br>35:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>37:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>39:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>41:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>43:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>47:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>50:12 I `EXTERNAL_CALL_PENDING`: CALL GETCH: assinatura pendente para ligação.<br>51:12 I `EXTERNAL_CALL_PENDING`: CALL ENDWIN: assinatura pendente para ligação. |
| examples/complementares/PROG002A.cbl | 1:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>171:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>313:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte. |
| examples/complementares/PROG006A.cbl | 9:8 E `UNSUPPORTED_EXEC`: SQL/CICS embutido ainda não é suportado.<br>13:12 E `UNSUPPORTED_EXEC`: EXEC SQL/CICS exige uma gramática de extensão ainda não implementada.<br>16:12 E `UNSUPPORTED_EXEC`: EXEC SQL/CICS exige uma gramática de extensão ainda não implementada.<br>21:12 E `UNSUPPORTED_EXEC`: EXEC SQL/CICS exige uma gramática de extensão ainda não implementada. |
| examples/complementares/PROG010A.cbl | 18:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>19:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>23:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>44:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>45:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>49:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>54:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>55:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>73:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>85:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>89:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>96:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>110:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>111:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>113:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>128:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>129:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>131:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>155:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>156:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>158:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>172:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>174:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>179:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>188:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>189:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>216:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>224:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>227:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>233:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte. |
| examples/complementares/PROG018A.cbl | 15:18 E `INVALID_ALTER_TARGET`: Parágrafo alterável deve conter somente GO TO.<br>15:12 E `UNSUPPORTED_ALTER`: Recurso fora do subconjunto semântico: ALTER. |
| examples/complementares/PROG023C.cbl | 163:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>165:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>167:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte. |
| examples/complementares/PROG042A.cbl | 219:20 E `IDENTIFIER_TOO_LONG`: Identificador contém 31 caracteres (máximo 30).<br>280:8 E `IDENTIFIER_TOO_LONG`: Identificador contém 31 caracteres (máximo 30). |
| examples/complementares/PROGTEST.cbl | 10:8 E `UNSUPPORTED_SCREEN`: Recurso fora do subconjunto semântico: SCREEN. |
| examples/complementares/PROGTEST2.cbl | 16:12 I `EXTERNAL_CALL_PENDING`: CALL INITSCR: assinatura pendente para ligação.<br>17:12 I `EXTERNAL_CALL_PENDING`: CALL KEYPAD: assinatura pendente para ligação.<br>18:12 I `EXTERNAL_CALL_PENDING`: CALL NOECHO: assinatura pendente para ligação.<br>19:12 I `EXTERNAL_CALL_PENDING`: CALL CLEAR: assinatura pendente para ligação.<br>22:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>24:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>26:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>30:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>31:12 I `EXTERNAL_CALL_PENDING`: CALL MVSCANW: assinatura pendente para ligação.<br>33:12 I `EXTERNAL_CALL_PENDING`: CALL MVSCANW: assinatura pendente para ligação.<br>37:12 I `EXTERNAL_CALL_PENDING`: CALL CLEAR: assinatura pendente para ligação.<br>38:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>40:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>42:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>44:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>46:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>49:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>50:12 I `EXTERNAL_CALL_PENDING`: CALL GETCH: assinatura pendente para ligação.<br>53:12 I `EXTERNAL_CALL_PENDING`: CALL ENDWIN: assinatura pendente para ligação. |
| examples/complementares/PROGTEST3.cbl | 14:12 I `EXTERNAL_CALL_PENDING`: CALL INITSCR: assinatura pendente para ligação.<br>15:12 I `EXTERNAL_CALL_PENDING`: CALL CLEAR: assinatura pendente para ligação.<br>17:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>19:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>21:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>22:12 I `EXTERNAL_CALL_PENDING`: CALL SCANW: assinatura pendente para ligação.<br>24:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>26:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>27:12 I `EXTERNAL_CALL_PENDING`: CALL SCANW: assinatura pendente para ligação.<br>37:12 I `EXTERNAL_CALL_PENDING`: CALL CLEAR: assinatura pendente para ligação.<br>38:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>40:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>42:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>44:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>46:12 I `EXTERNAL_CALL_PENDING`: CALL MVPRINTW: assinatura pendente para ligação.<br>53:12 I `EXTERNAL_CALL_PENDING`: CALL REFRESH: assinatura pendente para ligação.<br>57:12 I `EXTERNAL_CALL_PENDING`: CALL GETCH: assinatura pendente para ligação.<br>59:12 I `EXTERNAL_CALL_PENDING`: CALL ENDWIN: assinatura pendente para ligação. |
| examples/complementares/PROGVSAM.cbl | 8:12 E `UNSUPPORTED_FILE_ORGANIZATION`: Recurso fora do subconjunto semântico: FILE_ORGANIZATION.<br>8:12 E `KEY_ON_SEQUENTIAL_FILE`: RECORD KEY/ALTERNATE KEY exige arquivo INDEXED/RELATIVE.<br>8:12 E `INVALID_FILE_ACCESS`: Arquivo sequencial exige ACCESS SEQUENTIAL.<br>68:17 E `INVALID_FILE_MODE`: LINE SEQUENTIAL não admite I-O neste ABI.<br>73:20 E `INVALID_FILE_MODE`: LINE SEQUENTIAL não admite I-O neste ABI.<br>85:15 E `INVALID_FILE_HANDLER`: INVALID KEY não se aplica ao arquivo sequencial. |
| examples/complementares/SORT001A.cbl | 4:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>6:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>8:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte. |
| examples/complementares/TELABMS.cbl | 2:24 E `INVALID_CHARACTER`: Caractere '&' não reconhecido.<br>5:67 E `INVALID_CHARACTER`: Caractere '$' não reconhecido. |
| examples/complementares/VALIDA1B.cbl | 111:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>112:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>114:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>133:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>134:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>136:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>174:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>175:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>177:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>201:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>202:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>204:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>211:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>212:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>214:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>231:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>232:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>234:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>296:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>297:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>299:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>363:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>364:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>366:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>386:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>387:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>389:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte. |
| examples/complementares/clientes-sql.cbl | 6:8 E `UNSUPPORTED_EXEC`: SQL/CICS embutido ainda não é suportado.<br>8:8 E `UNSUPPORTED_EXEC`: SQL/CICS embutido ainda não é suportado.<br>11:8 E `UNSUPPORTED_EXEC`: SQL/CICS embutido ainda não é suportado.<br>15:8 E `UNSUPPORTED_EXEC`: EXEC SQL/CICS exige uma gramática de extensão ainda não implementada. |
| examples/complementares/main.cbl | 13:12 I `EXTERNAL_CALL_PENDING`: CALL EXIBIR_TELA: assinatura pendente para ligação. |
| examples/complementares/ncurses_demo.cbl | 10:12 I `EXTERNAL_CALL_PENDING`: CALL NCURSES_WRAPPER.C: assinatura pendente para ligação.<br>12:12 I `EXTERNAL_CALL_PENDING`: CALL MOSTRAR_MENSAGEM: assinatura pendente para ligação.<br>14:12 I `EXTERNAL_CALL_PENDING`: CALL ESPERAR_TECLA: assinatura pendente para ligação.<br>16:12 I `EXTERNAL_CALL_PENDING`: CALL FINALIZAR_NCURSES: assinatura pendente para ligação. |
| examples/oficiais/CAD0005A.cbl | 97:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>99:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte.<br>101:1 E `MERGE_CONFLICT`: Marcador de conflito Git não resolvido no fonte. |

## Contratos e limites

- PIC e tipos lógicos separam categoria, precisão, escala, sinal, edição e representação física. Operações usam metadados decimais exatos; divisão/potência mantêm precisão/escala não limitadas até o receptor.
- Não há padding implícito. COMP usa 2/4/8 bytes até 4/9/18 dígitos; acima, largura binária mínima com sinal. COMP-3 reserva nibbles de dígitos e sinal. DISPLAY S usa overpunch sem byte adicional. Ver [contrato semântico](semantica.md).
- REDEFINES e registros alternativos FD são views sobre a mesma área. OCCURS guarda tamanho máximo, mínimo, DEPENDING, stride e verificações dinâmicas.
- SCREEN, ALTER, SORT, START, arquivos INDEXED/RELATIVE/acesso DYNAMIC ou RANDOM, POINTER e COMP-1/2 permanecem fora do subconjunto semântico. As referências alcançáveis são ainda visitadas e os diagnósticos bloqueiam o programa.
- SEARCH ALL aceita condição simples de igualdade sobre chave ordenada e anota o contrato de ordenação; formas mais complexas recebem diagnóstico explícito.
- CALL externo conserva grafia, modos e argumentos, incluindo literais por referência em temporários. Unidades disponíveis validam assinatura e estrutura física; falhas do chamado bloqueiam o chamador.
- FILE STATUS, SELECT/FD e modos declarados são conferidos. O estado efetivo de OPEN em cada caminho é uma verificação de runtime anotada, sem simular entrada ou fluxo nesta etapa.
- ISO-8859-1 define bytes de literais/registros; UTF-8 do arquivo fonte continua decodificado pelo front-end. Valores não representáveis são diagnosticados.
- Ausência de VALUE usa zeros numéricos/espaços textuais em armazenamento local; LINKAGE preserva bytes do chamador. `--strict` exige VALUE sem alterar os fontes.
- SQL/CICS, vazio e negativos léxicos preservam suas classificações anteriores; não chegam artificialmente à semântica.

A classificação atesta análise estática deste subconjunto. Runtime, conversões reais,
geração C, dispatcher/PERFORM, I/O, passagem de parâmetros e GCC são a próxima etapa.
Nenhum resultado desta auditoria é uma prova de execução dos programas.

## Reprodução

```bash
python -m tools.auditar_semantica --write
python -m unittest discover -s tests -v
```

O [JSON completo](auditoria-semantica.json) inclui diagnósticos com origem/inclusão,
dependências, layouts por símbolo, parâmetros e vínculos de chamadas. Não editar as
tabelas ou JSON manualmente.
