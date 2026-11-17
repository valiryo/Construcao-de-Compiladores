# Consolidação léxica para a entrega final

## Base e método

Branch: `feat/compilador-cobol-final`. O estado inicial era `main`, sem modificações
rastreadas e com `docs/EspecificacaoCOBOL.md` e `docs/InstrucoesAdicionaisCOBOL.md`
não rastreados. Ambos foram lidos integralmente e preservados, assim como o README,
os módulos existentes e seus testes. Antes das alterações, o comando
`python -m unittest discover -s tests -v` passou **58 testes**.

A importação e sua proveniência estão em [examples/README.md](../examples/README.md).
O snapshot contém 85 fontes upstream: sete oficiais, três dependências e 75
complementares, além de seis arquivos de referência. Foi criada uma cópia corrigida
adicional. Todos os .cbl, .cob e .cpy rastreados no commit foram tokenizados e
inventariados, inclusive arquivos incompatíveis ou vazios.

- [Auditoria inicial](auditoria-lexer-antes.json): contagens, diagnósticos e
  identificadores produzidos pelo lexer anterior, incluindo a cópia corrigida.
- [Inventário legível](inventario-corpus.md): resultados por fonte, máscaras
  oficiais e dependências externas com linhas e resolução.
- [Auditoria atual completa](auditoria-lexer-depois.json): para cada arquivo,
  palavras reservadas, identificadores, literais, operadores, símbolos, PIC,
  lexemas originais, valores normalizados, frequências e primeiras posições.
  Contém também construções especiais, funções, reclassificações e antes/depois.
- `python -m tools.auditar_corpus`: reprodução offline do inventário atual.

Cada `Diagnostic` da API existente representa erro, sem campo de severidade.
Portanto, os relatórios registram zero avisos emitidos; isso não significa que
houve uma análise sintática, semântica ou de estilo sem avisos.

## Sete programas oficiais

| Programa | Tokens antes → depois | Diagnósticos antes → depois | Construções que orientam as próximas etapas |
|---|---:|---:|---|
| BUSCA01A | 208 → 208 | 0 → 0 | LINE SEQUENTIAL, FD, READ INTO, AT END/NOT AT END, END-READ, PERFORM de seção UNTIL, EXIT |
| CAD0002A | 864 → 868 | 4 → 0 | COPY, LINKAGE, USING, GOBACK, OCCURS no copybook, subscritos, referência modificada, VARYING, INITIALIZE REPLACING, NUMERIC, GO TO, INSPECT TALLYING, FUNCTION REVERSE e LENGTH OF |
| CAD0004A | 133 → 133 | 0 → 0 | Parágrafos sem SECTION, PERFORM UNTIL, OPEN OUTPUT, WRITE, registros de grupo, campos sem VALUE |
| CAD0005A corrigido | 516 → 516 | 0 → 0 | Agenda persistente, tabela de 10 registros, EVALUATE, CONTINUE, VARYING, END-PERFORM, leitura/regravação |
| CAIXAREG | 390 → 390 | 0 → 0 | Decimais implícitos V, COMPUTE com parênteses/subtração, MOVE para máscara editada ZZZ.ZZZ.ZZZ,ZZ, interação e validação |
| CALCMD01 | 285 → 285 | 0 → 0 | Soma/divisão, escala de quatro casas, comparações, PERFORM que volta à seção para repetir entrada |
| PROG024A | 1397 → 1397 | 0 → 0 | Dois FD, log com delimitadores, OPEN EXTEND, tabela, grupos/FILLER, COMP, CALL USING, RETURN-CODE, data via PROGDATA, DISPLAY WITH NO ADVANCING |

O CAD0005A original produz 518 tokens e três erros, antes `INVALID_INDICATOR`,
agora `MERGE_CONFLICT`. A cópia elimina somente o bloco duplicado autorizado.
Os quatro erros anteriores do CAD0002A eram `INVALID_CHARACTER` em 212:38,
316:57, 317:57 e 318:57: exatamente os dois-pontos de referências modificadas.

O corpus oficial usa nomes de programas e de parágrafos que continuam como
`IDENTIFIER`, incluindo nomes com prefixo numérico como `0001-LER-ARQUIVO`.
Literais com acentos permanecem `STRING`; o texto não é convertido para maiúsculas.
Máscaras como `9(05)V99`, `S9(4)` e `ZZZ.ZZZ.ZZZ,ZZ` continuam sendo um único
`PICTURE`, seguido de `PERIOD` quando a declaração termina. Não foi necessário
alterar o reconhecedor de máscaras para esse corpus.

As listas completas de identificadores e literais por programa estão nas entradas
`inventory.IDENTIFIER`, `inventory.STRING` e `inventory.NUMBER` do JSON atual;
`inventory.KEYWORD`, `PICTURE` e as demais categorias completam o inventário.

## Alterações e limites de responsabilidade

1. **Vocabulário fundamentado no corpus.** Foram acrescentadas palavras reais
   antes classificadas como identificadores: EXIT, GO, END-PERFORM, SPECIAL-NAMES,
   DECIMAL-POINT, COMMA, CONTINUE, NUMERIC, END-READ, VARYING, REDEFINES, LINKAGE,
   USING, CALL, GOBACK, INITIALIZE, ALPHANUMERIC, FILLER, GREATER, LESS, LENGTH,
   LINE, SEQUENTIAL, COMP, EXTEND, RETURN-CODE e fontes de data/hora. O corpus
   adicional também exigiu CORR/CORRESPONDING, ROUNDED, THEN, ALTER/PROCEED,
   ASCENDING, SD/SORT, UNSTRING/DELIMITED, SCREEN/BLANK/COLUMN/CRT/NORMAL,
   REFERENCE, DUPLICATES e delimitadores EXEC/END-EXEC. TRUE e FALSE são os
   valores de condição; TRUE ocorre nos exemplos. O conjunto exato está em
   `RESERVED_WORDS`, com testes de caixa e identificadores semelhantes.
2. **Palavras contextuais.** REVERSE, ORD, MOD, INTEGER, RANDOM e INTEGER-OF-DATE
   permanecem `IDENTIFIER`. Após FUNCTION, o parser futuro reconhecerá o nome da
   função. Não reservar globalmente esses nomes evita classificar variáveis comuns
   como comandos. LENGTH é palavra-chave pela expressão LENGTH OF já presente no
   oficial. SQL, CICS, SQLCA, nomes de mapas e palavras internas dessas extensões
   não recebem uma gramática por terem sido tokenizados. Nomes como CPF, NOME,
   INDICE, I e IDX continuam identificadores.
3. **Referência modificada.** `:` gera `COLON` com posição física. O lexer não
   verifica parênteses balanceados, existência de CAMPO, início ou comprimento.
4. **Comentários inline.** O leitor de linhas remove `*>` fora de strings, antes
   de unir continuações, respeitando aspas duplicadas e literais abertos. Texto
   comentado, inclusive TAB, não vira token nem altera o estado de aspas. `*>`
   dentro de literal é preservado. Comentários na coluna 7 e corte em 72 continuam.
5. **Convenção decimal.** A sequência de tokens `DECIMAL-POINT IS COMMA` configura
   o separador léxico para o restante do programa; a validade e localização da
   cláusula serão verificadas pelo parser. `100,00` no PROG025A agora é um NUMBER,
   com `lexeme="100,00"` e `value="100.00"`, sem float. Sem essa cláusula, ponto
   continua decimal e vírgula é COMMA. Espaço após vírgula mantém o separador.
   PROGRAM-ID e novas chamadas a tokenize reiniciam o modo; strings/comentários
   não o ativam. Copybooks isolados usam o padrão ponto; a futura expansão COPY
   deverá ocorrer no contexto do programa. Não há suporte prometido para decimais
   sem parte inteira ou expoentes, ausentes do corpus.
6. **Conflitos Git.** MERGE_CONFLICT identifica marcadores de abertura, separação,
   fechamento e ancestral diff3, inclusive na coluna 1 antes de descartar a área
   de sequência. Não confunde decoração em comentários, texto de strings ou área
   após 72 com conflito. O leitor não apaga os erros para aceitar os fontes.
7. **Recuperação numérica.** Decimais colados a letras, como `12.5BAD`, agora
   produzem INVALID_WORD inteiro, assim como já acontecia com sinal. Recuperação
   continua na próxima palavra; caracteres arbitrários seguem inválidos.

A API `CobolLexer(...).tokenize(source)`, Token, Diagnostic, LexerResult e CLI
foram preservadas. `COLON` é o novo kind e `MERGE_CONFLICT` o novo diagnóstico.
`fixed_format.py` continua responsável por colunas, comentários e mapa físico;
`scanner.py`, por tokens e configuração léxica local. As extensões vão além da
lista mínima da seção 2 do professor, sem implementar gramática no scanner.

Continuação de palavras, números, PIC e strings e seus spans já existiam: foram
mantidos e testados com comentários inline. O corpus oficial não exigiu reescrever
essa API. A regra existente de remover espaços finais e indentação em continuações
é mantida como decisão do projeto, sem alegar conformidade completa com todas as
regras de literais longos de todos os dialetos. As posições contam caracteres
Python/Unicode, não bytes de UTF-8. Validação de uso de área A/B pertence ao parser.

## Cobertura complementar e problemas reais dos fontes

Dos 86 arquivos analisados (85 originais + uma cópia), **77 não emitem erros
léxicos e nove são casos negativos**. Os 75 complementares incluem 67 sem erros
e oito negativos. Isso não equivale a 77 programas compiláveis: um fonte é vazio,
outros dependem de SQL/CICS ou bibliotecas e ainda não há parser/backend.

| Fonte | Classificação | Tratamento |
|---|---|---|
| CAD0005A original | Erro no fonte: conflito | Preservado; cópia corrigida é positiva |
| PROG002A, PROG010A, PROG023C, SORT001A, VALIDA1B | Erros no fonte: conflitos, respectivamente 3/30/3/3/27 marcadores | Negativos separados, sem correção silenciosa |
| CBREAKEX | Formato incompatível: muitas linhas iniciam código na coluna 7 | 38 INVALID_INDICATOR; formato livre/conversão exige opção futura, não deslocamento automático |
| PROG042A | Nomes de 31 caracteres (0007-INCLUIR-QUANTIDADE-PRODUTO), 219:20 e 280:8 | Dois IDENTIFIER_TOO_LONG; manter limite explícito de 30 da especificação |
| TELABMS.cbl | Macrofonte BMS DFHMSD/DFHMDF, não programa COBOL | Dois INVALID_CHARACTER para `&` e `$`; não ampliar lexer COBOL para aceitar macros BMS |
| CLIESQL01 | Arquivo vazio | Zero tokens; parser deverá diagnosticar ausência de programa |
| PROG006A e clientes-sql | EXEC CICS e EXEC SQL | Tokens delimitadores reconhecidos; tradução e infraestrutura fora do subconjunto planejado |
| NCURSESDEMO, PROGTEST2/3, main, ncurses_demo | ABI C/ncurses e wrappers ausentes | CALL é reconhecido, integração externa não implementada |
| GAMESNAK, PROGTEST, TESTE002 | Tela/terminal, posicionamento, teclas ou funções adicionais | Inventariados; suporte ao runtime futuro precisa ser explícito |

PROG003A traz CORRESPONDING e ROUNDED; PROG019A/020A trazem SEARCH, índices e
ordenação; PROG018A traz ALTER; PROGVSAM traz arquivo INDEXED, chave alternativa,
DUPLICATES, status e REDEFINES. Os exemplos PROG023*, PROG025A e PROG027A ampliam
arquivos, escalas e máscaras, UNSTRING, INTEGER-OF-DATE e logs. VALCNPJ/VALIDA1B
trazem MOD e ORD. Esses recursos entram no inventário e no planejamento, sem
promessa de toda a semântica COBOL nesta etapa.

Todos os dados `.dat` citados estão ausentes. O grafo COPY/CALL dos oficiais fecha
nos três arquivos de dependências importados. O corpus complementar fecha chamadas
COBOL com outros fontes importados, como PROGTIME e PROG042B; chamadas C e recursos
SQL/CICS permanecem externos. O inventário de ASSIGN inclui tanto entradas quanto
saídas; não infere que todo destino deva existir antes de executar.

Há divergências entre especificação e exemplos que exigem política explícita na
fase semântica: campos sem VALUE nos oficiais, nomes iguais em níveis diferentes
(TAB-ENT-LINHA no PROG024A) e níveis de linkage. Erros de lógica de negócio, como
validações duvidosas, não devem ser corrigidos no lexer nem nos originais.

## Validação

Após as alterações: **80 testes passaram**, incluindo os 58 anteriores. A suíte
verifica todos os originais pelo manifesto, a correção byte a byte, todos os
complementares, dependências, tokens/CLI dos sete oficiais, categorias novas,
lexemas e posições físicas de todos os tokens de uma linha do corpus. Casos
sintéticos verificam também spans de continuação, comentários, strings, máscaras,
sinais, decimais e erros. A suíte anterior continua conferindo cada erro inserido
nos sete exemplos de `examples/erros/`, com código, linha e coluna exatos.

O teste do inventário compara os dados gerados com uma nova auditoria offline.
Nenhum teste depende de rede, GCC, GnuCOBOL ou data atual. Ainda não há teste de
execução nativa, pois parser, semântica e gerador C são as próximas etapas.
