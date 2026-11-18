# Auditoria dos arquivos pendentes — Etapa 6

Gerado por `python -m tools.auditar_pendentes --write`. A coorte vem das linhas
sem GCC bem-sucedido da auditoria anterior, não de uma lista de métricas.
Snapshot `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`. Nenhum fonte original, compilador ou runtime alterado.

## Resumo consolidado

A auditoria investiga compilabilidade e custo de recuperação. **Nenhum programa
experimental foi executado ou declarado funcional.** Os 60 programas validados
na Etapa 5 permanecem como a coorte funcional; os experimentos não alteram esse total.

```json
{
  "audited_files": 26,
  "programs": 24,
  "fragments": 2,
  "classes": {
    "A": 9,
    "B": 4,
    "C": 7,
    "D": 4,
    "E": 2
  },
  "primary_causes": {
    "source": 4,
    "recoverable_cobol_dependency": 1,
    "format_dialect": 2,
    "compiler": 3,
    "native_dependency": 5,
    "merge": 6,
    "outside_scope": 3,
    "fragment": 2
  },
  "source_or_merge_primary": 10,
  "source_or_native_contract_issues": 13,
  "compiler_limitations_including_secondary": 13,
  "truly_external_native_dependencies": 5,
  "simple_recovery_files": 9,
  "moderate_or_complex": 11,
  "experimental_c_generated_files": 10,
  "experimental_gcc_files": 10,
  "experimental_gcc_paths": [
    "examples/complementares/ASCII001.cbl",
    "examples/complementares/CAD0001A.cbl",
    "examples/complementares/PROG002A.cbl",
    "examples/complementares/PROG010A.cbl",
    "examples/complementares/PROG018A.cbl",
    "examples/complementares/PROG023C.cbl",
    "examples/complementares/PROG042A.cbl",
    "examples/complementares/SORT001A.cbl",
    "examples/complementares/VALIDA1B.cbl",
    "examples/oficiais/CAD0005A.cbl"
  ],
  "simple_recovery_new_programs": 8,
  "programs_executed": 0,
  "compiler_or_runtime_modified": false,
  "originals_unchanged": true
}
```

A = simples; B = moderada; C = complexa; D = fora do escopo; E = fragmento.
Os nove A incluem CAD0005A, cuja derivada já está entre os 60: são oito
candidatos novos. Escolher um lado de conflito pode exigir decisão de intenção.
Os dez casos com fonte/merge como causa principal e os três contratos ncurses
defeituosos totalizam 13 arquivos com problemas de código; os 13 com limitações
do compilador incluem causas secundárias, uma restrição de dialeto deliberada
e o SORT da variante alternativa de PROG010A. Essas contagens se sobrepõem.

## Reconciliação da classificação anterior

```json
{
  "invalid_source": 13,
  "external_dependency_missing": 6,
  "unsupported_backend": 2,
  "unsupported_extension": 2,
  "partially_supported": 1,
  "copybook_context_only": 2
}
```

As quantidades anteriores se confirmam (6 ligação, 2 backend, 13 inválidos,
2 extensões, 1 parcial, 2 copybooks), mas os rótulos precisam de nuance:
CBREAKEX é válido em formato livre, PROG042A é válido no dialeto padrão do
GnuCOBOL, TELABMS é macrofonte BMS e CAD0001A tem dependência COBOL recuperável.
Os cinco restantes de ligação exigem interfaces nativas ou wrappers não fornecidos.

## Tabela individual

| Arquivo | Falha anterior | Causa-raiz confirmada | Fonte válido? | Primeira fase bloqueada | Recuperável? | Correção necessária | Esforço | Prioridade | Classe |
|---|---|---|---|---|---|---|---|---|---|
| [examples/complementares/ASCII001.cbl](../examples/complementares/ASCII001.cbl) | invalid_source | Só WS-CHAR está declarado. COMPUTE e DISPLAY usam WS-CODIGO nas linhas 10 e 12; ambos os compiladores rejeitam. A declaração experimental alcança GCC. | não | semantic | sim | Declarar WS-CODIGO (por exemplo PIC 9(3)) em cópia separada; esclarecer que ORD é ordinal baseado em 1. | baixo | alta | A |
| [examples/complementares/CAD0001A.cbl](../examples/complementares/CAD0001A.cbl) | LINK_UNRESOLVED_CALL | SORT001A existe no snapshot e ordena uma tabela por bubble sort; não contém verbo SORT. Os demais módulos já estão validados. O conflito desse módulo, não uma biblioteca externa ausente, bloqueia a unidade completa. | sim, dependências necessárias | link | sim | Resolver o conflito de comentário de SORT001A e fornecer os sete subprogramas transitivos por --source. | baixo | alta | A |
| [examples/complementares/CBREAKEX.cbl](../examples/complementares/CBREAKEX.cbl) | invalid_source | Cabeçalhos começam na coluna 7 e passam no GnuCOBOL -free. Deslocar uma coluna faz GnuCOBOL -fixed aceitar, mas expõe DATA RECORD IS não reconhecido pelo parser. Omitir somente essa metainformação em outra cópia expõe quatro PIC com sinais flutuantes repetidos. Não basta reindentar. | sim em formato livre; não no fixo original | lexer | sim, com extensão moderada | Oferecer formato configurável ou cópia deslocada uma coluna; reconhecer DATA RECORD IS; implementar edição flutuante de sinal. | médio | média | B |
| [examples/complementares/CLIESQL01.cbl](../examples/complementares/CLIESQL01.cbl) | invalid_source | Arquivo vazio confirmado por tamanho e hash. Falta PROGRAM-ID em ambos. O nome do arquivo não demonstra que exista SQL nele. | não: zero bytes | parser | não com o conteúdo disponível | Obter a implementação original; não há código a corrigir. | alto | baixa | D |
| [examples/complementares/GAMESNAK.cbl](../examples/complementares/GAMESNAK.cbl) | UNSUPPORTED_BACKEND_SCREEN_POSITION | AST, tipos, tabelas e operações já passam. A primeira emissão C bloqueia ScreenPosition, não CALL ncurses. Coordenadas dinâmicas e ciclo do jogo exigem validação do terminal; não precisa de SCREEN SECTION completa. | sim no dialeto GnuCOBOL | backend | sim, após suporte de terminal | Implementar DISPLAY AT LINE/COLUMN e contrato CURSOR/terminal; validar em pseudo-terminal com entrada Q e relógio/RANDOM controlados. | médio | média | B |
| [examples/complementares/NCURSESDEMO.cbl](../examples/complementares/NCURSESDEMO.cbl) | LINK_UNRESOLVED_CALL | scanw recebe WS-NOME/WS-IDADE como único argumento, onde C exige formato e destinos. getch retorna int, não preenche PIC 9(2) passado por referência. PIC X não garante NUL. -lncurses não corrige esses contratos. | sintaxe sim; contrato nativo incorreto | link | incerto sem corrigir interfaces | Projetar ABI externa e wrappers reais para strings, números, retorno e ncurses; corrigir contratos de scanw/getch e testar em PTY. | alto | baixa | C |
| [examples/complementares/PROG002A.cbl](../examples/complementares/PROG002A.cbl) | invalid_source | O único conflito ocupa o programa inteiro: HEAD demonstra data/controle; o outro lado demonstra aritmética/decimal e CORRESPONDING. Ambos chegam ao GCC, mas não existe resolução funcional inequívoca. | não enquanto conflitado; ambos os lados válidos | lexer | sim | Escolher e documentar uma versão completa em cópia separada; não concatenar os dois programas. | baixo | alta | A |
| [examples/complementares/PROG006A.cbl](../examples/complementares/PROG006A.cbl) | unsupported_extension | A falha EXEC é de extensão deliberadamente ausente, não token perdido pelo parser. Há comando aparente em seção de dados e mapa EXEMPLO não fornecido; LOGINMAP é outro mapa. GnuCOBOL puro não valida CICS, portanto sua rejeição não basta para julgar o dialeto. | dependente de tradutor CICS; trecho suspeito | parser | incerto; fora dos requisitos batch | Separar trilha CICS, obter tradutor e mapas EXEMPLO e revisar EXEC CICS DFLD RECEIVE em WORKING-STORAGE. | alto | baixa | D |
| [examples/complementares/PROG010A.cbl](../examples/complementares/PROG010A.cbl) | invalid_source | Dez conflitos alteram SELECT/SD, tabela e fluxo. HEAD chega a GCC; o outro lado é aceito por GnuCOBOL e bloqueia UNSUPPORTED_SORT no projeto. A chave do SORT menciona o FD de entrada, não um campo do SD; revisar o layout da chave antes de prometer ordenação correta. | não enquanto conflitado; variantes dependem da intenção | lexer | sim | Escolher a versão HEAD de leitura/gravação ou tratar a versão com SORT como projeto adicional. | baixo | alta | A |
| [examples/complementares/PROG018A.cbl](../examples/complementares/PROG018A.cbl) | invalid_source | 100-INICIO contém PERFORM, GO TO e ALTER, violando a exigência de um único GO TO. Ambos rejeitam o original. PERFORM 300-ETAPA2 executa STOP RUN antes de ALTER. Remover a linha alcança GCC, mas deixa de demonstrar ALTER; um caso mínimo válido continua bloqueado apenas por UNSUPPORTED_ALTER. | não: alvo de ALTER inválido | semantic | sim | Definir a intenção: reconstruir exemplo com parágrafo contendo só GO TO e implementar ALTER; ou remover explicitamente a instrução inválida e inalcançável em derivado. | médio | baixa | B |
| [examples/complementares/PROG023C.cbl](../examples/complementares/PROG023C.cbl) | invalid_source | Única diferença é a mensagem de tabela cheia, não a lógica. Não há escolha textual inequívoca. Resolver marcadores expõe dois CALL acessíveis; com as fontes de data/hora, ambos os lados chegam a GCC. | não enquanto conflitado; ambos os lados válidos | lexer | sim | Escolher mensagem AGENDA/TABELA em cópia separada e fornecer PROGDATA e PROGTIME. | baixo | alta | A |
| [examples/complementares/PROG042A.cbl](../examples/complementares/PROG042A.cbl) | invalid_source | Um identificador de 31 caracteres ocorre em chamada e declaração. GnuCOBOL default (limite 63) aceita; configuração -fword-length=30 reproduz a restrição. Não é erro universal COBOL. A cópia renomeada com PROG042B chega a GCC. | sim no GnuCOBOL padrão; incompatível com limite 30 | lexer | sim | Renomear consistentemente 0007-INCLUIR-QUANTIDADE-PRODUTO em derivado e fornecer PROG042B, ou projetar opção de dialeto sem relaxar o modo da disciplina. | baixo | alta | A |
| [examples/complementares/PROGTEST.cbl](../examples/complementares/PROGTEST.cbl) | partially_supported | SCREEN SECTION tem campos de entrada USING WS-NOME/WS-IDADE e apresentação. Reconhecer AST não fornece edição nem transferência de dados de tela. Requer projeto maior que emitir sequências ANSI para DISPLAY. | sim no dialeto GnuCOBOL | semantic | sim | Implementar semântica/layout de SCREEN, USING bidirecional, BLANK SCREEN, edição, foco/teclas e terminal; reutilizar depois o posicionamento. | alto | baixa | C |
| [examples/complementares/PROGTEST2.cbl](../examples/complementares/PROGTEST2.cbl) | LINK_UNRESOLVED_CALL | keypad recebe inteiro 1 no lugar de WINDOW*; mvscanw recebe campo como formato sem destinos variádicos. Aceitação sintática/ligação C não torna seguro executar essas chamadas. | sintaxe sim; contrato nativo incorreto | link | incerto sem corrigir interfaces | Corrigir ponteiro WINDOW, formatos/destinos mvscanw e retorno getch; adicionar ABI externa/wrappers e ligação ncurses. | alto | baixa | C |
| [examples/complementares/PROGTEST3.cbl](../examples/complementares/PROGTEST3.cbl) | LINK_UNRESOLVED_CALL | Campos inicializados não corrigem a assinatura scanw(fmt,...). Idade DISPLAY e WS-IDADE-STR não são int C nem strings terminadas por NUL. A biblioteca fornece símbolos, mas o chamador precisa cumprir contratos. | sintaxe sim; contrato nativo incorreto | link | incerto sem corrigir interfaces | Adicionar wrappers reais e corrigir scanw, terminação de strings, conversões DISPLAY/int e retorno de getch. | alto | baixa | C |
| [examples/complementares/PROGVSAM.cbl](../examples/complementares/PROGVSAM.cbl) | invalid_source | INDEXED está comentado e LINE SEQUENTIAL está ativo. Chaves, DYNAMIC, I-O e INVALID KEY contradizem a organização efetiva; GnuCOBOL confirma. Ao ativar INDEXED, todos os erros sequenciais desaparecem e resta apenas UNSUPPORTED_FILE_ORGANIZATION. Não há EXEC VSAM/serviço mainframe neste fonte: é COBOL INDEXED. | não no original; variante INDEXED válida | semantic | sim | Restaurar intenção INDEXED em derivado e implementar armazenamento indexado com chave primária/alternativa, duplicatas, I-O, status e INVALID KEY. | alto | baixa | C |
| [examples/complementares/SORT001A.cbl](../examples/complementares/SORT001A.cbl) | invalid_source | O único conflito modifica comentário. Tokens executáveis dos lados são iguais; ambos geram objeto GCC. Usa bubble sort com PERFORM, não o verbo SORT. LINKAGE de 10552 bytes deve vir do chamador. | não enquanto conflitado; ambos os lados válidos | lexer | sim | Resolver o comentário CÇASSIFICACAO/CLASSIFICACAO em derivado e compilar como módulo USING COPY002A-REGISTRO. | baixo | alta | A |
| [examples/complementares/TELABMS.cbl](../examples/complementares/TELABMS.cbl) | invalid_source | DFHMSD/DFHMDI/DFHMDF e &SYSPARM são macros de mapa. Não há IDENTIFICATION/PROGRAM-ID/PROCEDURE; o erro léxico é apenas o primeiro sintoma de alimentar a linguagem errada ao compilador. | não é programa COBOL: macrofonte BMS | lexer | não como programa COBOL independente | Encaminhar a uma cadeia de montagem BMS/CICS, com revisão própria; não liberar & e $ no lexer COBOL para aceitá-lo. | alto | baixa | D |
| [examples/complementares/TESTE002.cbl](../examples/complementares/TESTE002.cbl) | UNSUPPORTED_BACKEND_SCREEN_POSITION | Único bloqueio atual de emissão C é DISPLAY AT LINE 5 COLUMN 10. Requer subconjunto de terminal menor que SCREEN completo; imprimir 50 linhas não substitui cursor/endereço. | sim no dialeto GnuCOBOL | backend | sim | Implementar posicionamento DISPLAY e definir efeito de CRT STATUS no ACCEPT; verificar coordenadas e escape bytes em PTY. | médio | média | B |
| [examples/complementares/VALIDA1B.cbl](../examples/complementares/VALIDA1B.cbl) | invalid_source | Os nove hunks só acrescentam comentários *> cobol-lint. Os fluxos executáveis dos dois lados são iguais e ambos chegam ao GCC; nenhuma nova extensão é necessária. | não enquanto conflitado; ambos os lados válidos | lexer | sim | Resolver nove conflitos de comentários cobol-lint em cópia separada e preservar lógica de validação. | baixo | alta | A |
| [examples/complementares/clientes-sql.cbl](../examples/complementares/clientes-sql.cbl) | unsupported_extension | EXEC SQL não é COBOL base para cobc puro. SQLCA e SQLCODE dependem de expansão externa, e banco meubanco/tabela clientes não são fixtures fornecidas. Não retirar EXEC para fabricar um programa positivo. | dependente de pré-compilador SQL | parser | incerto; infraestrutura ausente | Trilha separada para SQLCA, pré-compilador SQL, driver/banco, credenciais e esquema clientes. | alto | baixa | D |
| [examples/complementares/main.cbl](../examples/complementares/main.cbl) | LINK_UNRESOLVED_CALL | CALL exibir_tela recebe nome de 30 bytes e idade de dois dígitos por referência. A árvore completa do snapshot não contém sua implementação. Sem assinatura C não se pode presumir que idade seja int* ou que nome termine em NUL. | sintaxe sim; contrato externo não fornecido | link | incerto sem implementação | Obter/implementar exibir_tela com contrato explícito de buffer X(30) e idade DISPLAY 9(2); projetar ABI externa e ligação. | alto | baixa | C |
| [examples/complementares/ncurses_demo.cbl](../examples/complementares/ncurses_demo.cbl) | LINK_UNRESOLVED_CALL | Quatro CALL não têm implementação no snapshot. CALL ncurses_wrapper.c não compila/carrega um fonte C automaticamente. MSG é slice de 50 bytes e não C string. Não há assinatura para as outras três rotinas. | sintaxe sim; dependências não fornecidas | link | incerto sem implementação | Fornecer wrapper real e seu ponto de entrada; corrigir a tentativa de chamar nome de arquivo .c e definir conversão de MSG X(50). | alto | baixa | C |
| [examples/dependencias/COD001A.cpy](../examples/dependencias/COD001A.cpy) | copybook_context_only | Estrutura de data/hora com 81 bytes. Não possui PROGRAM-ID e não deve receber main artificial. | sim como copybook | nenhuma; fragmento contextual | não se aplica | Nenhuma correção; manter COPY e validação no contexto de PROGDATA/PROGTIME e chamadores. | baixo | média | E |
| [examples/dependencias/COPY002A.cpy](../examples/dependencias/COPY002A.cpy) | copybook_context_only | Contador de dois bytes e 50 registros de stride 211: 10552 bytes. O comentário TAMANHO 02125 não define armazenamento. Contextos compilados e LINKAGE confirmam o layout. | sim como copybook | nenhuma; fragmento contextual | não se aplica | Nenhuma correção; manter COPY, layout e ABI compartilhada nos módulos de cadastro. | baixo | média | E |
| [examples/oficiais/CAD0005A.cbl](../examples/oficiais/CAD0005A.cbl) | invalid_source | Os dois lados diferem só por espaço final no DISPLAY. A seleção HEAD coincide byte a byte com a derivada validada na Etapa 5. Recuperar o original em experimento não adiciona um novo programa à coorte de 60. | não no original; cópia corrigida já validada | lexer | sim | Nenhuma nova recuperação: manter a derivada já existente em examples/corrigidos; não alterar o original negativo. | baixo | baixa | A |

## Evidências por arquivo

### ASCII001.cbl

Só WS-CHAR está declarado. COMPUTE e DISPLAY usam WS-CODIGO nas linhas 10 e 12; ambos os compiladores rejeitam. A declaração experimental alcança GCC.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=error, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **declare-code**: Declarar WS-CODIGO PIC 9(3). C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.

### CAD0001A.cbl

SORT001A existe no snapshot e ordena uma tabela por bubble sort; não contém verbo SORT. Os demais módulos já estão validados. O conflito desse módulo, não uma biblioteca externa ausente, bloqueia a unidade completa.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.
- Experimento **with-recovered-sort**: Fonte CAD0001A intacto; acrescentar SORT001A resolvido aos seis módulos já declarados, incluindo PROGTIME transitivo. C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.

### CBREAKEX.cbl

Cabeçalhos começam na coluna 7 e passam no GnuCOBOL -free. Deslocar uma coluna faz GnuCOBOL -fixed aceitar, mas expõe DATA RECORD IS não reconhecido pelo parser. Omitir somente essa metainformação em outra cópia expõe quatro PIC com sinais flutuantes repetidos. Não basta reindentar.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `97`; formato `fixed`.
- gnu_free: retorno `0`; formato `free`.
- Experimento **shift-one**: Deslocar uma coluna à direita; manter as cláusulas originais. C `not_run`, GCC `not_run`; bloqueios: SYNTAX_ERROR. GnuCOBOL: `0`.
- Experimento **shift-without-data-record**: Após deslocamento, substituir as duas metacláusulas DATA RECORD IS por ponto; não alterar PIC. C `not_run`, GCC `not_run`; bloqueios: INVALID_PICTURE. GnuCOBOL: `0`.

### CLIESQL01.cbl

Arquivo vazio confirmado por tamanho e hash. Falta PROGRAM-ID em ambos. O nome do arquivo não demonstra que exista SQL nele.

Fases do original: lexer=True, preprocessor=True, parser=error, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.

### GAMESNAK.cbl

AST, tipos, tabelas e operações já passam. A primeira emissão C bloqueia ScreenPosition, não CALL ncurses. Coordenadas dinâmicas e ciclo do jogo exigem validação do terminal; não precisa de SCREEN SECTION completa.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.

### NCURSESDEMO.cbl

scanw recebe WS-NOME/WS-IDADE como único argumento, onde C exige formato e destinos. getch retorna int, não preenche PIC 9(2) passado por referência. PIC X não garante NUL. -lncurses não corrige esses contratos.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.
- gnu_static_link: retorno `1`; formato `fixed`.
- gnu_ncurses_devel: retorno `1`; formato `fixed`.
- gnu_ncurses_runtime: retorno `0`; formato `fixed`.

### PROG002A.cbl

O único conflito ocupa o programa inteiro: HEAD demonstra data/controle; o outro lado demonstra aritmética/decimal e CORRESPONDING. Ambos chegam ao GCC, mas não existe resolução funcional inequívoca.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **ours**: Selecionar integralmente o lado ours C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Experimento **theirs**: Selecionar integralmente o lado theirs C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Conflito 1–313: 169 linhas HEAD / 141 linhas do outro lado. Os conteúdos e patches completos estão no JSON.

### PROG006A.cbl

A falha EXEC é de extensão deliberadamente ausente, não token perdido pelo parser. Há comando aparente em seção de dados e mapa EXEMPLO não fornecido; LOGINMAP é outro mapa. GnuCOBOL puro não valida CICS, portanto sua rejeição não basta para julgar o dialeto.

Fases do original: lexer=True, preprocessor=True, parser=error, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.

### PROG010A.cbl

Dez conflitos alteram SELECT/SD, tabela e fluxo. HEAD chega a GCC; o outro lado é aceito por GnuCOBOL e bloqueia UNSUPPORTED_SORT no projeto. A chave do SORT menciona o FD de entrada, não um campo do SD; revisar o layout da chave antes de prometer ordenação correta.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **ours**: Selecionar integralmente o lado ours C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Experimento **theirs**: Selecionar integralmente o lado theirs C `not_run`, GCC `not_run`; bloqueios: UNSUPPORTED_SORT. GnuCOBOL: `0`.
- Conflito 18–23: 0 linhas HEAD / 3 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 44–49: 0 linhas HEAD / 3 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 54–73: 0 linhas HEAD / 17 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 85–96: 3 linhas HEAD / 6 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 110–113: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 128–131: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 155–158: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 172–179: 1 linhas HEAD / 4 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 188–216: 0 linhas HEAD / 26 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 224–233: 2 linhas HEAD / 5 linhas do outro lado. Os conteúdos e patches completos estão no JSON.

### PROG018A.cbl

100-INICIO contém PERFORM, GO TO e ALTER, violando a exigência de um único GO TO. Ambos rejeitam o original. PERFORM 300-ETAPA2 executa STOP RUN antes de ALTER. Remover a linha alcança GCC, mas deixa de demonstrar ALTER; um caso mínimo válido continua bloqueado apenas por UNSUPPORTED_ALTER.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=error, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **remove-unreachable-alter**: Remover instrução inválida/inalcançável; abandona a demonstração de ALTER, não é recuperação desse recurso. C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Experimento **valid-alter-minimal**: Caso mínimo separado: alvo contém somente GO TO; distingue validade do fonte e suporte ao verbo. C `not_run`, GCC `not_run`; bloqueios: UNSUPPORTED_ALTER. GnuCOBOL: `0`.

### PROG023C.cbl

Única diferença é a mensagem de tabela cheia, não a lógica. Não há escolha textual inequívoca. Resolver marcadores expõe dois CALL acessíveis; com as fontes de data/hora, ambos os lados chegam a GCC.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **ours**: Selecionar integralmente o lado ours C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Experimento **theirs**: Selecionar integralmente o lado theirs C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Conflito 163–167: 1 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.

### PROG042A.cbl

Um identificador de 31 caracteres ocorre em chamada e declaração. GnuCOBOL default (limite 63) aceita; configuração -fword-length=30 reproduz a restrição. Não é erro universal COBOL. A cópia renomeada com PROG042B chega a GCC.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.
- gnu_limit30: retorno `1`; formato `fixed`.
- Experimento **rename-31**: Renomear chamada e seção para nome de 25 caracteres, sem colisão. C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.

### PROGTEST.cbl

SCREEN SECTION tem campos de entrada USING WS-NOME/WS-IDADE e apresentação. Reconhecer AST não fornece edição nem transferência de dados de tela. Requer projeto maior que emitir sequências ANSI para DISPLAY.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=error, backend=not_run, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.

### PROGTEST2.cbl

keypad recebe inteiro 1 no lugar de WINDOW*; mvscanw recebe campo como formato sem destinos variádicos. Aceitação sintática/ligação C não torna seguro executar essas chamadas.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.
- gnu_static_link: retorno `1`; formato `fixed`.
- gnu_ncurses_devel: retorno `1`; formato `fixed`.
- gnu_ncurses_runtime: retorno `0`; formato `fixed`.

### PROGTEST3.cbl

Campos inicializados não corrigem a assinatura scanw(fmt,...). Idade DISPLAY e WS-IDADE-STR não são int C nem strings terminadas por NUL. A biblioteca fornece símbolos, mas o chamador precisa cumprir contratos.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.
- gnu_static_link: retorno `1`; formato `fixed`.
- gnu_ncurses_devel: retorno `1`; formato `fixed`.
- gnu_ncurses_runtime: retorno `0`; formato `fixed`.

### PROGVSAM.cbl

INDEXED está comentado e LINE SEQUENTIAL está ativo. Chaves, DYNAMIC, I-O e INVALID KEY contradizem a organização efetiva; GnuCOBOL confirma. Ao ativar INDEXED, todos os erros sequenciais desaparecem e resta apenas UNSUPPORTED_FILE_ORGANIZATION. Não há EXEC VSAM/serviço mainframe neste fonte: é COBOL INDEXED.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=error, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **indexed-intent**: Ativar INDEXED e remover somente LINE SEQUENTIAL; preservar DYNAMIC, chaves e I-O. C `not_run`, GCC `not_run`; bloqueios: UNSUPPORTED_FILE_ORGANIZATION. GnuCOBOL: `0`.

### SORT001A.cbl

O único conflito modifica comentário. Tokens executáveis dos lados são iguais; ambos geram objeto GCC. Usa bubble sort com PERFORM, não o verbo SORT. LINKAGE de 10552 bytes deve vir do chamador.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **ours**: Selecionar integralmente o lado ours C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Experimento **theirs**: Selecionar integralmente o lado theirs C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Conflito 4–8: 1 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.

### TELABMS.cbl

DFHMSD/DFHMDI/DFHMDF e &SYSPARM são macros de mapa. Não há IDENTIFICATION/PROGRAM-ID/PROCEDURE; o erro léxico é apenas o primeiro sintoma de alimentar a linguagem errada ao compilador.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.

### TESTE002.cbl

Único bloqueio atual de emissão C é DISPLAY AT LINE 5 COLUMN 10. Requer subconjunto de terminal menor que SCREEN completo; imprimir 50 linhas não substitui cursor/endereço.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.

### VALIDA1B.cbl

Os nove hunks só acrescentam comentários *> cobol-lint. Os fluxos executáveis dos dois lados são iguais e ambos chegam ao GCC; nenhuma nova extensão é necessária.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **ours**: Selecionar integralmente o lado ours C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Experimento **theirs**: Selecionar integralmente o lado theirs C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Conflito 111–114: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 133–136: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 174–177: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 201–204: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 211–214: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 231–234: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 296–299: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 363–366: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.
- Conflito 386–389: 0 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.

### clientes-sql.cbl

EXEC SQL não é COBOL base para cobc puro. SQLCA e SQLCODE dependem de expansão externa, e banco meubanco/tabela clientes não são fixtures fornecidas. Não retirar EXEC para fabricar um programa positivo.

Fases do original: lexer=True, preprocessor=True, parser=error, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.

### main.cbl

CALL exibir_tela recebe nome de 30 bytes e idade de dois dígitos por referência. A árvore completa do snapshot não contém sua implementação. Sem assinatura C não se pode presumir que idade seja int* ou que nome termine em NUL.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.
- gnu_static_link: retorno `1`; formato `fixed`.

### ncurses_demo.cbl

Quatro CALL não têm implementação no snapshot. CALL ncurses_wrapper.c não compila/carrega um fonte C automaticamente. MSG é slice de 50 bytes e não C string. Não há assinatura para as outras três rotinas.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=success, backend=error, gcc=not_run.

- gnu_original: retorno `0`; formato `fixed`.
- gnu_static_link: retorno `1`; formato `fixed`.

### COD001A.cpy

Estrutura de data/hora com 81 bytes. Não possui PROGRAM-ID e não deve receber main artificial.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=not_run, backend=not_run, gcc=not_run.

- COPY em examples/complementares/PROG016A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/complementares/PROG023D.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/complementares/PROG023E.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/complementares/PROG025A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/complementares/PROG027A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/complementares/PROG028A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/complementares/PROGTIME.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/complementares/REL0001A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81, 'COPY002A-HEADER': 13, 'COPY002A-REGISTRO': 10552}`.
- COPY em examples/complementares/REL0002A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/dependencias/PROGDATA.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.
- COPY em examples/oficiais/PROG024A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81}`.

### COPY002A.cpy

Contador de dois bytes e 50 registros de stride 211: 10552 bytes. O comentário TAMANHO 02125 não define armazenamento. Contextos compilados e LINKAGE confirmam o layout.

Fases do original: lexer=True, preprocessor=True, parser=success, semantic=not_run, backend=not_run, gcc=not_run.

- COPY em examples/complementares/GRAV001A.cbl: semântica `True`, layouts `{'COPY002A-HEADER': 13, 'COPY002A-REGISTRO': 10552}`.
- COPY em examples/complementares/LER0001A.cbl: semântica `True`, layouts `{'COPY002A-HEADER': 13, 'COPY002A-REGISTRO': 10552}`.
- COPY em examples/complementares/REL0001A.cbl: semântica `True`, layouts `{'COD001A-REGISTRO': 81, 'COPY002A-HEADER': 13, 'COPY002A-REGISTRO': 10552}`.
- COPY em examples/oficiais/CAD0002A.cbl: semântica `True`, layouts `{'COPY002A-HEADER': 13, 'COPY002A-REGISTRO': 10552}`.

### CAD0005A.cbl

Os dois lados diferem só por espaço final no DISPLAY. A seleção HEAD coincide byte a byte com a derivada validada na Etapa 5. Recuperar o original em experimento não adiciona um novo programa à coorte de 60.

Fases do original: lexer=False, preprocessor=False, parser=not_run, semantic=not_run, backend=not_run, gcc=not_run.

- gnu_original: retorno `1`; formato `fixed`.
- Experimento **ours**: Selecionar integralmente o lado ours C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Experimento **theirs**: Selecionar integralmente o lado theirs C `success`, GCC `success`; bloqueios: nenhum. GnuCOBOL: `0`.
- Conflito 97–101: 1 linhas HEAD / 1 linhas do outro lado. Os conteúdos e patches completos estão no JSON.

## Diagnóstico, contratos e plano de recuperação

A interpretação detalhada, custo dos recursos, contratos nativos e prioridades
estão em [plano de recuperação](recuperacao-pendentes.md). O [JSON completo](auditoria-pendentes.json)
guarda todos os diagnósticos atuais e anteriores, comandos GnuCOBOL/GCC, formatos,
dependências, contratos de CALL, SHA-256, patches experimentais e lados de cada conflito.

## Método e reprodução

Preparação: 476 testes aprovados em 54.846 s.
Cada original é copiado byte a byte para temporário. O lexer roda novamente;
o pré-processador/parser e a semântica usam as APIs reais. compile_result emite
C e chama GCC somente quando as fases anteriores aprovam. Fases posteriores
a um bloqueio são not_run, não sucessos presumidos. Dependências são explícitas.
As cópias experimentais têm diff completo; originais e os 60 validados têm hashes
verificados antes/depois. Não se executa nenhum binário, não se usam stubs,
não se acessa rede durante a auditoria. As consultas/compilações do oráculo têm
timeout de 30 s, CPU de 20 s, arquivos de até 32 MiB e core dumps desabilitados.
A compilação GCC própria conserva o timeout de 120 s do driver existente.
GnuCOBOL é oráculo de sintaxe/compilação, nunca backend. -fsyntax-only não prova
a presença de CALL dinâmico; por isso há ligação -fstatic-call nos experimentos
nativos e em CAD0001A. Uma ligação bem-sucedida tampouco valida a assinatura C.
As opções de vocabulário são as mesmas da Etapa 5; formato/dialeto e dependências
ficam registrados em cada comando. Paths temporários aparecem como $AUDIT.

```bash
python -m tools.auditar_pendentes --write
python -m tools.auditar_pendentes --write --no-gnu
python -m unittest discover -s tests -v
```

A árvore completa e imutável do snapshot foi consultada pela API do GitHub e
preservada em [evidência da árvore](evidencias-pendentes/arvore-upstream.json).
Seus blobs COBOL coincidem com o manifesto; não há .c/.h/.so nem implementações
de exibir_tela ou ncurses_wrapper nessa árvore. A ferramenta usa essa evidência offline.
