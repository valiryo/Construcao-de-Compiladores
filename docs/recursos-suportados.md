# Recursos COBOL suportados

**Suportado** indica geração e execução dentro do subconjunto descrito. **Parcial** indica restrições de forma, perfil ou ABI. Sintaxe reconhecida pelo parser também pode ser rejeitada antes de gerar um binário.

| Área | Situação | Escopo |
|---|---|---|
| Estrutura | Suportado | IDENTIFICATION, ENVIRONMENT, DATA e PROCEDURE DIVISION. PROGRAM-ID, seções, parágrafos e fontes separados. Cabeçalhos e rótulos respeitam a área A em formato fixo. |
| Formatos | Parcial | Fixo por padrão, com área de sequência 1–6, indicador 7, áreas A/B e código até 72. Formato livre explícito, com comentários inline e sem corte de coluna. O livre não cobre todas as continuações de literais. |
| COPY | Parcial | Inclusão recursiva com busca no fonte que inclui e em `-I`, com origem, ciclos e limite de profundidade. Nomes sem extensão tentam `.cpy`, `.cbl` e `.cob`. COPY REPLACING é rejeitado. |
| Data Division | Suportado | Grupos, elementos, FILLER, níveis 77 e 88, VALUE, WORKING-STORAGE, LOCAL-STORAGE e LINKAGE. |
| PIC e tipos | Parcial | Texto A/X, numérico 9/S/V, DISPLAY, COMP/BINARY, COMP-3 e edição com Z, separadores e sinais no subconjunto. COMP-1/2, moeda e inserções de edição não suportadas recebem diagnóstico. |
| Tabelas e aliases | Parcial | OCCURS fixo e DEPENDING ON, subscritos, índices, REDEFINES, qualificação e referência modificada. SEARCH e SEARCH ALL têm limites de forma e chave. |
| Movimentação | Parcial | MOVE de campos e grupos, incluindo CORRESPONDING, INITIALIZE e REPLACING nas formas suportadas. STRING, UNSTRING e INSPECT com limites de cláusulas. |
| Aritmética e condições | Suportado | ADD, SUBTRACT, MULTIPLY, DIVIDE, COMPUTE, relações, classes e condições 88. ROUNDED, REMAINDER e ON SIZE ERROR nas combinações admitidas. ROUNDED combinado com REMAINDER é rejeitado. |
| Controle de fluxo | Parcial | IF, EVALUATE, PERFORM de rótulo ou inline, THRU, TIMES, UNTIL, VARYING, GO TO, NEXT SENTENCE, EXIT, GOBACK e STOP RUN. GO TO saindo de PERFORM inline é rejeitado. |
| Arquivos | Parcial | SELECT/FD para LINE SEQUENTIAL e SEQUENTIAL fixo. OPEN INPUT/OUTPUT/EXTEND nas formas suportadas, READ com INTO e AT END, WRITE, CLOSE e FILE STATUS. |
| Entrada e saída | Suportado | ACCEPT/DISPLAY de console, NO ADVANCING, DATE, DAY, DAY-OF-WEEK e TIME. Entrada e saída textual com conversão Latin-1/UTF-8. |
| Terminal e SCREEN | Parcial | No perfil `gnucobol`, posicionamento ANSI/POSIX, SCREEN SECTION, LINE/COLUMN, BLANK SCREEN, VALUE, PIC e USING para texto ou inteiro DISPLAY sem sinal ou escala. Requer TTY. |
| Intrínsecas | Parcial | LENGTH, REVERSE, UPPER-CASE, LOWER-CASE, ORD, INTEGER, MOD, INTEGER-OF-DATE, DATE-OF-INTEGER e RANDOM. LENGTH de grupos variáveis tem restrições. |
| CALL e módulos | Suportado | Destino literal ou variável nas formas dinâmicas suportadas. BY REFERENCE, BY CONTENT, BY VALUE, LINKAGE, RETURN-CODE, RETURNING e tratadores de exceção. Integração de fontes, objetos e módulos próprios `.so`. |
| FFI | Parcial | Símbolos e bibliotecas C com assinaturas explícitas, incluindo ponteiros, buffers, strings, inteiros e varargs tipados. Sem structs por valor, floats, callbacks ou convenções alternativas. |
| Extensões externas | Inexistente | EXEC SQL/CICS, integração JCL/BMS, programas aninhados e diretivas gerais de compilação. |
| Arquivos e verbos fora do subconjunto | Inexistente | INDEXED, RELATIVE, acesso DYNAMIC/RANDOM a arquivos, START, SORT, ALTER, SELECT OPTIONAL e WRITE ADVANCING. |

## Perfis

| Regra | `project` | `gnucobol` |
|---|---|---|
| Identificadores | Até 30 caracteres | Até 63 caracteres |
| CALL pendente em executável ou objeto | Resolução no build. `--dynamic-call` habilita o carregador. | Resolução em execução. `--static-call` exige destinos resolvidos. |
| FD DATA RECORD(S) | Fora do subconjunto | Aceito no FD |
| PIC de sinal flutuante | Fora do subconjunto | Disponível nas máscaras suportadas |
| Terminal posicionado e SCREEN | Fora do backend | Subconjunto ANSI/POSIX |
| USAGE POINTER | Fora do subconjunto | Ponteiro opaco para FFI |
| CALL inteiro com RETURNING | Atualiza também RETURN-CODE | Preserva RETURN-CODE quando o resultado vai ao receptor explícito |

O perfil e o formato físico são opções independentes. CBREAKEX usa `--dialect gnucobol --source-format free`. Módulos compartilhados permitem resolução dinâmica por padrão. Os dois perfis usam a mesma ABI própria de armazenamento.

## Limites de execução

- O runtime de tela aceita até 1024 campos editáveis de até 4096 bytes. Coordenadas são base 1 e limitadas à janela. DISPLAY posicionado aplica AT ao operando imediatamente anterior.
- ON SIZE ERROR preserva o receptor em erro aritmético tratado. A divisão por zero sem tratador é fatal. Potência aceita expoente inteiro de magnitude até 4096.
- Entradas longas, valores fora da faixa e subscritos inválidos podem falhar em runtime. Campos e arquivos seguem o layout de largura fixa e a codificação da ABI. Literais precisam ser representáveis em ISO-8859-1.
- OPEN INPUT e EXTEND exigem arquivo existente. OUTPUT cria ou trunca. LINE SEQUENTIAL grava todos os bytes do registro seguidos de LF. FILE STATUS distingue sucesso, comprimento divergente, EOF, falha de I/O, arquivo ausente e modo incompatível.
- RANDOM usa uma sequência própria. As conversões de datas usam o calendário gregoriano no intervalo de 1601 a 9999.
- Módulos `.so` do GnuCOBOL têm ABI diferente. Chamadas C exigem um protótipo conhecido. O runtime diagnostica destinos ausentes e contratos incompatíveis.

## Evidência de compatibilidade

O corpus COBOL Dicas está fixado por commit e hashes no [manifesto](../examples/manifesto-coboldicas.json). GnuCOBOL 3.2.0 compilou 70 unidades comparáveis, com 63 programas principais e sete módulos objeto. Todas foram compiladas pelo backend C11 próprio. Copybooks são analisados no contexto de inclusão. Fontes rejeitados pelas duas implementações e fontes que exigem pré-processadores externos ficam em categorias distintas.

Os **152 cenários** satisfizeram suas expectativas. As sete unidades oficiais foram validadas, incluindo CAD0002A em um chamador e CAD0005A na cópia corrigida. Entre os 70 originais, **60 coincidiram nos cenários completos**. A comparação foi byte a byte em 58 e por células do terminal em dois. Três diferenças conhecidas envolvem inicialização de registro e padding de caracteres acentuados. GAMESNAK tem ensaio parcial de encerramento e sequência de aleatoriedade diferente.

A comparação adicional de CALCMD01 com divisor zero confirmou a mesma saída até o total. O executável próprio termina com erro e o GnuCOBOL 3.2.0 prossegue até exibir média `00000006,0000`. Em CAD0001A, `main` e `ncurses_demo`, os dois binários coincidiram em stdout, arquivos e código de retorno até o destino ausente. O texto de stderr é distinto. Em NCURSESDEMO, PROGTEST2 e PROGTEST3 os prefixos seguros coincidiram, com interrupção antes das chamadas ncurses incompatíveis.

Os validadores geram relatórios em `build/` com comandos, entradas, hashes, saídas brutas e arquivos. [Reprodução](referencia-cli.md#validação-reproduzível) · [ABI e layout](arquitetura.md#dados-e-precisão)
