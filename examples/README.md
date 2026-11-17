# Corpus COBOL para a entrega final

Origem: [COBOL Dicas / codigo_fonte_cobol](https://github.com/Coboldicas/codigo_fonte_cobol),
commit [`1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`](https://github.com/Coboldicas/codigo_fonte_cobol/tree/1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295),
obtido em 17/11/2026 por clone raso. A primeira tentativa no sandbox falhou por
DNS; o clone com acesso de rede autorizado funcionou. Não foi necessário fallback
local. Nenhum arquivo externo foi executado.

| Diretório | Conteúdo |
|---|---|
| `oficiais/` | Sete fontes originais, byte a byte; CAD0005A contém conflito |
| `dependencias/` | COPY002A.cpy, COD001A.cpy e PROGDATA.cbl, originais |
| `corrigidos/` | Somente CAD0005A com a correção descrita abaixo |
| `complementares/` | Todos os outros 75 arquivos .cbl/.cob/.cpy do commit |
| `referencia/` | README original, quatro JCL e LOGINMAP.bms para contexto externo |
| `ebasso/`, `erros/`, `hello.cob` | Corpus anterior, preservado |

O [manifesto](manifesto-coboldicas.json) registra caminho upstream, caminho local,
SHA-256 e Git blob de cada original importado, além do hash da cópia corrigida.
Foram importados todos os 85 fontes COBOL/copybooks rastreados pelo Git, sem
normalizar encoding, espaços, colunas ou finais de linha. São UTF-8 legíveis pela
CLI existente. O `.gitignore` upstream ignora quase todos os nomes e `*.dat`;
por isso a enumeração usou `git ls-files`, não uma busca que respeitasse esse ignore.

## Atribuição e licença

Os comentários com autores e datas permanecem nos fontes. O projeto externo se
atribui ao COBOL Dicas; muitos fontes identificam José Roberto. O
[README upstream preservado](referencia/README.md) declara MIT, mas não existe
arquivo LICENSE/COPYING no commit consultado. Essa ausência está registrada;
não foi criado um texto de licença atribuído aos autores. Os fontes mantêm sua
atribuição original e não têm autoria transferida para este projeto.

## Correção única autorizada

Em `oficiais/CAD0005A.cbl`, linhas 97–101, os dois lados do conflito contêm o mesmo
DISPLAY; o segundo possui um espaço final adicional. Em `corrigidos/CAD0005A.cbl`
foram removidos os três marcadores e o segundo DISPLAY, mantendo literalmente o
primeiro e todos os bytes fora do bloco. O DISPLAY continua na coluna 21.

```cobol
               WHEN OTHER
                    DISPLAY 'OPÇÃO INVÁLIDA!'
           END-EVALUATE
```

SHA-256 corrigido: `19b1d31741229462db14bae6b83c4e014bb20a8902d8b023b7dcdecb3ddf009e`.
Os testes positivos e o inventário oficial selecionam explicitamente a cópia
corrigida; o original é teste negativo, com `MERGE_CONFLICT` em 97:1, 99:1 e 101:1.
Nenhum outro fonte importado foi corrigido.

## Dependências oficiais e execução futura

| Fonte | Dependências | Situação |
|---|---|---|
| BUSCA01A | CADASTRO2.dat | Entrada ausente; layout NOME X(30), IDADE 9(02), CPF 9(11) |
| CAD0002A | COPY002A.cpy | Presente; subprograma `PROCEDURE DIVISION USING COPY002A-REGISTRO`, termina com GOBACK |
| CAD0004A | CADASTRO.dat | Saída gerada por OPEN OUTPUT, registro de 47 posições |
| CAD0005A | CADAGENDA.dat | Persistência, leitura e regravação; entrada inicial não fornecida |
| CAIXAREG | stdin/stdout | Sem COPY/CALL/arquivo externo |
| CALCMD01 | stdin/stdout | Sem COPY/CALL/arquivo externo |
| PROG024A | COD001A.cpy, PROGDATA.cbl; BIBLIOTECA.dat e BIBLIOTECA.txt | Fontes presentes; dados iniciais ausentes, .txt usado como log |
| PROGDATA | COD001A.cpy, data do sistema | Dependência transitiva presente |

Nenhum arquivo de dados é rastreado no commit. Não se deve substituir dado ausente
por sucesso silencioso de OPEN INPUT. Na validação executável futura serão criados
fixtures com layouts conhecidos em diretórios temporários. CAD0002A exige um
chamador com área de linkage: `complementares/CAD0001A.cbl` é um exemplo real e
também depende de LER0001A, GRAV001A, REL0001A e SORT001A (todos importados).
O teste isolado deverá usar um driver mínimo próprio, sem alterar CAD0002A.

O [inventário completo](../docs/inventario-corpus.md) lista COPY, CALL e ASSIGN
por fonte e linha. Todos os COPY e CALL de nomes COBOL do corpus têm fontes
correspondentes neste snapshot. Chamadas ncurses e wrappers C são dependências
externas, algumas sem implementação fornecida, como `ncurses_wrapper.c`,
`mostrar_mensagem`, `esperar_tecla`, `finalizar_ncurses` e `obter_dados`.
SQLCA/DB2 e recursos CICS/BMS também exigem infraestrutura externa.

## Verificação offline

```bash
python -m tools.auditar_corpus
python -m tools.auditar_parser --write
python -m unittest discover -s tests -v
python -m cobol_lexer examples/corrigidos/CAD0005A.cbl --json
python -m cobol_compiler examples/oficiais/CAD0002A.cbl -I examples/dependencias --check-syntax
```

Os comandos de auditoria regeneram os relatórios atuais, preservando a auditoria
anterior às alterações. Os testes conferem hashes, diferença exata do patch,
corpus inteiro, fluxos oficiais, AST/CLI, posições físicas e casos negativos sem
acessar a rede. Na Etapa 2, todos os 77 aceitos pelo lexer foram submetidos ao
parser: 72 programas e dois copybooks passam; fonte vazio e SQL/CICS ficam
separados. O [relatório sintático](../docs/auditoria-parser.md) detalha cada arquivo.
