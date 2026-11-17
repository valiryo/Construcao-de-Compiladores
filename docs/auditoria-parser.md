# Auditoria do pré-processador, parser e AST

Relatório gerado por `python -m tools.auditar_parser --write`. O snapshot e os
fontes originais permanecem intactos; os hashes são verificados pela suíte léxica.

Referência: [COBOL Dicas no commit 1ffb3bf279bb](https://github.com/Coboldicas/codigo_fonte_cobol/tree/1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295).

## Métricas

- **86 arquivos analisados:** 85 originais + CAD0005A corrigido.
- **77 aceitos anteriormente pelo lexer; todos os 77 foram efetivamente submetidos ao parser.**
- **74 sucessos completos:** 72 programas e 2 fragmentos .cpy, com consumo integral, zero recuperação e AST validada.
- Três dos anteriormente aceitos ficam separados: arquivo vazio, EXEC CICS e EXEC SQL.
- Nove negativos léxicos são novamente processados e bloqueiam o parser, sem virar falsos sucessos sintáticos.

Sucesso sintático não inclui resolução de símbolos, validade de tipos, abertura de
arquivos, disponibilidade de bibliotecas ou execução. CALL para ncurses/wrappers é
uma construção sintaticamente reconhecida, mesmo que o runtime externo não exista.

## Sete oficiais

| Programa | Tokens expandidos/consumidos | Comandos representados | Nós AST | Itens de dados | Resultado |
|---|---:|---:|---:|---:|---|
| BUSCA01A.cbl | 208/208 | 23 | 135 | 9 | OK |
| CAD0002A.cbl | 954/954 | 153 | 657 | 47 | OK |
| CAD0004A.cbl | 133/133 | 16 | 77 | 8 | OK |
| CAD0005A.cbl (corrigido) | 516/516 | 87 | 366 | 15 | OK |
| CAIXAREG.cbl | 390/390 | 71 | 287 | 10 | OK |
| CALCMD01.cbl | 285/285 | 52 | 214 | 8 | OK |
| PROG024A.cbl | 1463/1463 | 194 | 998 | 65 | OK |

A diferença de tokens em CAD0002A e PROG024A é a expansão COPY, sem os tokens
das diretivas. Testes conferem os campos incluídos, a hierarquia e a origem,
além dos comandos esperados de cada programa. CAD0005A original continua negativo.

## Resultado individual de todo o corpus

PP = pré-processamento; AST inclui invariantes de intervalos, SourceSpan, filhos e
correspondência independente de cada início de comando com um nó Statement.

| Arquivo | Lexer anterior | PP | Parser | AST | Erros | Classificação |
|---|---|---|---|---|---:|---|
| [examples/complementares/ASCII001.cbl](../examples/complementares/ASCII001.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/CAD0001A.cbl](../examples/complementares/CAD0001A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/CBREAKEX.cbl](../examples/complementares/CBREAKEX.cbl) | erro | success | not_run | — | 38 | lexical_error |
| [examples/complementares/CLIESQL01.cbl](../examples/complementares/CLIESQL01.cbl) | OK | success | error | — | 1 | syntax_error |
| [examples/complementares/GAMESNAK.cbl](../examples/complementares/GAMESNAK.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/GRAV001A.cbl](../examples/complementares/GRAV001A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/LER0001A.cbl](../examples/complementares/LER0001A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/LER0002A.cbl](../examples/complementares/LER0002A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/LOGIN01A.cbl](../examples/complementares/LOGIN01A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/MINICALC.cbl](../examples/complementares/MINICALC.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/NCURSESDEMO.cbl](../examples/complementares/NCURSESDEMO.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG001A.cbl](../examples/complementares/PROG001A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG002A.cbl](../examples/complementares/PROG002A.cbl) | erro | success | not_run | — | 3 | lexical_error |
| [examples/complementares/PROG003A.cbl](../examples/complementares/PROG003A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG004A.cbl](../examples/complementares/PROG004A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG005A.cbl](../examples/complementares/PROG005A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG006A.cbl](../examples/complementares/PROG006A.cbl) | OK | success | error | — | 4 | unsupported_extension |
| [examples/complementares/PROG007A.cbl](../examples/complementares/PROG007A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG008A.cbl](../examples/complementares/PROG008A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG009A.cbl](../examples/complementares/PROG009A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG010A.cbl](../examples/complementares/PROG010A.cbl) | erro | success | not_run | — | 30 | lexical_error |
| [examples/complementares/PROG011A.cbl](../examples/complementares/PROG011A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG012A.cbl](../examples/complementares/PROG012A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG014A.cbl](../examples/complementares/PROG014A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG015A.cbl](../examples/complementares/PROG015A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG016A.cbl](../examples/complementares/PROG016A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG017A.cbl](../examples/complementares/PROG017A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG018A.cbl](../examples/complementares/PROG018A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG019A.cbl](../examples/complementares/PROG019A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG020A.cbl](../examples/complementares/PROG020A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG021A.cbl](../examples/complementares/PROG021A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG022A.cbl](../examples/complementares/PROG022A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG023A.cbl](../examples/complementares/PROG023A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG023B.cbl](../examples/complementares/PROG023B.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG023C.cbl](../examples/complementares/PROG023C.cbl) | erro | success | not_run | — | 3 | lexical_error |
| [examples/complementares/PROG023D.cbl](../examples/complementares/PROG023D.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG023E.cbl](../examples/complementares/PROG023E.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG025A.cbl](../examples/complementares/PROG025A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG027A.cbl](../examples/complementares/PROG027A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG028A.cbl](../examples/complementares/PROG028A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG029A.cbl](../examples/complementares/PROG029A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG033A.cbl](../examples/complementares/PROG033A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG034A.cbl](../examples/complementares/PROG034A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG035A.cbl](../examples/complementares/PROG035A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG036A.cbl](../examples/complementares/PROG036A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG037A.cbl](../examples/complementares/PROG037A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG038A.cbl](../examples/complementares/PROG038A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG039A.cbl](../examples/complementares/PROG039A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG040A.cbl](../examples/complementares/PROG040A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG041A.cbl](../examples/complementares/PROG041A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG042A.cbl](../examples/complementares/PROG042A.cbl) | erro | success | not_run | — | 2 | lexical_error |
| [examples/complementares/PROG042B.cbl](../examples/complementares/PROG042B.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG043A.cbl](../examples/complementares/PROG043A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG044A.cbl](../examples/complementares/PROG044A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROG045A.cbl](../examples/complementares/PROG045A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROGTEST.cbl](../examples/complementares/PROGTEST.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROGTEST2.cbl](../examples/complementares/PROGTEST2.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROGTEST3.cbl](../examples/complementares/PROGTEST3.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROGTEST4.cbl](../examples/complementares/PROGTEST4.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROGTIME.cbl](../examples/complementares/PROGTIME.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/PROGVSAM.cbl](../examples/complementares/PROGVSAM.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/REL0001A.cbl](../examples/complementares/REL0001A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/REL0002A.cbl](../examples/complementares/REL0002A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/SORT001A.cbl](../examples/complementares/SORT001A.cbl) | erro | success | not_run | — | 3 | lexical_error |
| [examples/complementares/SORT002A.cbl](../examples/complementares/SORT002A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/TELABMS.cbl](../examples/complementares/TELABMS.cbl) | erro | success | not_run | — | 2 | lexical_error |
| [examples/complementares/TESTE002.cbl](../examples/complementares/TESTE002.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/VALCNPJ.cbl](../examples/complementares/VALCNPJ.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/VALCPF01.cbl](../examples/complementares/VALCPF01.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/VALIDA1A.cbl](../examples/complementares/VALIDA1A.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/VALIDA1B.cbl](../examples/complementares/VALIDA1B.cbl) | erro | success | not_run | — | 27 | lexical_error |
| [examples/complementares/clientes-sql.cbl](../examples/complementares/clientes-sql.cbl) | OK | success | error | — | 4 | unsupported_extension |
| [examples/complementares/main.cbl](../examples/complementares/main.cbl) | OK | success | success | OK | 0 | program |
| [examples/complementares/meu_programa.cob](../examples/complementares/meu_programa.cob) | OK | success | success | OK | 0 | program |
| [examples/complementares/ncurses_demo.cbl](../examples/complementares/ncurses_demo.cbl) | OK | success | success | OK | 0 | program |
| [examples/corrigidos/CAD0005A.cbl](../examples/corrigidos/CAD0005A.cbl) | OK | success | success | OK | 0 | program |
| [examples/dependencias/COD001A.cpy](../examples/dependencias/COD001A.cpy) | OK | success | success | OK | 0 | data_fragment |
| [examples/dependencias/COPY002A.cpy](../examples/dependencias/COPY002A.cpy) | OK | success | success | OK | 0 | data_fragment |
| [examples/dependencias/PROGDATA.cbl](../examples/dependencias/PROGDATA.cbl) | OK | success | success | OK | 0 | program |
| [examples/oficiais/BUSCA01A.cbl](../examples/oficiais/BUSCA01A.cbl) | OK | success | success | OK | 0 | program |
| [examples/oficiais/CAD0002A.cbl](../examples/oficiais/CAD0002A.cbl) | OK | success | success | OK | 0 | program |
| [examples/oficiais/CAD0004A.cbl](../examples/oficiais/CAD0004A.cbl) | OK | success | success | OK | 0 | program |
| [examples/oficiais/CAD0005A.cbl](../examples/oficiais/CAD0005A.cbl) | erro | success | not_run | — | 3 | lexical_error |
| [examples/oficiais/CAIXAREG.cbl](../examples/oficiais/CAIXAREG.cbl) | OK | success | success | OK | 0 | program |
| [examples/oficiais/CALCMD01.cbl](../examples/oficiais/CALCMD01.cbl) | OK | success | success | OK | 0 | program |
| [examples/oficiais/PROG024A.cbl](../examples/oficiais/PROG024A.cbl) | OK | success | success | OK | 0 | program |

## Construções efetivamente implementadas

- Divisões, configuração/SPECIAL-NAMES, SELECT e cláusulas de arquivos, FD/SD, seções de dados e procedimentos, parágrafos e sentenças.
- Hierarquia de dados, FILLER, níveis 77/88, PIC/VALUE/ranges, OCCURS/DEPENDING/índices/chaves, REDEFINES, USAGE/COMP-3 e itens SCREEN sem nome.
- Referências qualificadas OF/IN, múltiplos subscritos, referência modificada e LENGTH OF; funções intrínsecas com argumentos estruturados.
- Expressões aritméticas com precedência/potência associativa à direita, sinais, comparações/classe, NOT/AND/OR e relações abreviadas com sujeito rastreado.
- IF aninhado e ELSE, EVALUATE/WHEN/ranges/ALSO/ANY/OTHER, PERFORM inline/alvo/THRU/TIMES/UNTIL/VARYING/TEST BEFORE/AFTER, GO TO, EXIT, CONTINUE, STOP RUN, GOBACK e NEXT SENTENCE.
- MOVE/CORRESPONDING, INITIALIZE REPLACING, ACCEPT de fontes de data/hora, DISPLAY/posicionamento/NO ADVANCING.
- ADD/SUBTRACT/MULTIPLY/DIVIDE/COMPUTE, GIVING/REMAINDER/ROUNDED e tratadores SIZE ERROR; READ/WRITE/OPEN/CLOSE/START e tratadores de fim/chave.
- CALL USING por referência/valor/conteúdo, retorno e exceções; INSPECT TALLYING/REPLACING/CONVERTING, STRING/UNSTRING, SEARCH/SET, ALTER e forma SORT USING/GIVING.

Os recursos fora dos exemplos reais também têm testes pequenos próprios; o reconhecimento
de um nó não implica implementação semântica. A [gramática](gramatica-cobol.ebnf)
e [contratos do front-end](frontend.md) descrevem as variantes e limites.

## Falhas, dependências e limites

| Arquivo/recurso | Evidência e tratamento |
|---|---|
| CLIESQL01.cbl | Zero bytes; diagnóstico em 1:1 por falta de IDENTIFICATION DIVISION. Erro real do fonte, não limitação de cobertura. |
| PROG006A.cbl | UNSUPPORTED_EXEC em 9:8, 13:12, 16:12 e 21:12. Inclui EXEC CICS DFLD RECEIVE dentro de WORKING-STORAGE; essa extensão e sua posição não foram validadas. MAP/MAPSET EXEMPLO não fornecido; LOGINMAP.bms é outro mapa. Não contabilizado como sintaticamente válido. |
| clientes-sql.cbl | EXEC SQL/SQLCA e banco externo; blocos embutidos não têm gramática implementada. UNSUPPORTED_EXEC, sem tratar SQL como texto bruto em um nó válido. |
| CAD0005A original, PROG002A, PROG010A, PROG023C, SORT001A, VALIDA1B | Conflitos Git preservados, impedem parsing. Só CAD0005A tem cópia corrigida autorizada. |
| CBREAKEX / PROG042A / TELABMS | Respectivamente formato incompatível, identificadores de 31 caracteres e macrofonte BMS. Negativos léxicos preservados; detalhes na auditoria anterior. |
| COPY REPLACING | Nenhum caso no corpus. Gera UNSUPPORTED_COPY_REPLACING com origem; não há substituição silenciosa nem promessa de suporte a pseudotexto. |
| Formato livre, programas aninhados, múltiplos programas por arquivo | Fora desta gramática; ordem inválida ou tokens após END PROGRAM são diagnosticados. |
| RENAMES e verbos não implementados | Diagnóstico explícito; não existe nó genérico de comando nem passagem de tokens desconhecidos como sucesso. |
| Arquivos .dat, SQLCA, bibliotecas C/ncurses e wrappers | Dependências de execução/semântica futuras, listadas no inventário léxico; não são necessárias para analisar sintaxe de CALL. |

Não restam falhas de parsing em exemplos batch/tela do subconjunto entre os
arquivos anteriormente aceitos. Isso não prova validade de todas as combinações
de cláusulas COBOL: validações de categoria, símbolos, compatibilidade e layouts
continuam para a análise semântica. O corpus é fixado por commit, não por HEAD remoto.

## Testes e reprodução

```bash
python -m unittest discover -s tests -v
python -m tools.auditar_parser --write
```

A suíte inicial desta etapa tinha 80 testes passando. Os testes novos cobrem COPY,
gramática, metadados, ASTs oficiais, corpus inteiro, diagnósticos, recuperação,
precedência, cláusulas adicionais e CLI. O resultado final e a organização dos
testes estão em [frontend.md](frontend.md). Nenhum teste invoca GCC ou GnuCOBOL.

O [JSON completo](auditoria-parser.json) registra por arquivo as fases, diagnósticos
com origem/inclusões, tokens consumidos, dependências, validação estrutural e
contagem de cada tipo de nó. Não editar as tabelas/JSON manualmente.

## Próxima etapa

Implementar tabela de símbolos, qualificações, interpretação de PIC/layout,
tipagem e associação SELECT/FD; vincular referências de controle e CALL.
Depois implementar runtime e geração C diretamente da AST. Os nós atuais
preservam cláusulas, ordem, limites e SourceSpan para essas verificações.
