# Exemplos e procedência

O corpus COBOL Dicas vem de [Coboldicas/codigo_fonte_cobol](https://github.com/Coboldicas/codigo_fonte_cobol/tree/1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295) no commit `1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295`. O [manifesto](manifesto-coboldicas.json) registra caminhos, hashes SHA-256 e blobs Git de cada original. Os 85 fontes COBOL e copybooks foram preservados byte a byte.

| Local | Conteúdo |
|---|---|
| `oficiais/` | Sete fontes da disciplina. CAD0005A original contém um conflito de merge. |
| `corrigidos/` | CAD0005A usado nas regressões positivas. |
| `dependencias/` | COPY002A, COD001A e PROGDATA. |
| `complementares/` | Outros originais do snapshot. |
| `referencia/` | README original, exemplos de JCL e mapa BMS. |
| `ebasso/` | [Programas de Enio Basso](ebasso/README.md) com [licença MIT](ebasso/LICENSE). |
| `erros/` | [Exemplos para testar diagnósticos do lexer](erros/README.md). |
| `hello.cob` | Exemplo introdutório em formato fixo. |

Os autores e datas do COBOL Dicas permanecem nos fontes. Muitos exemplos identificam José Roberto nos comentários. O [README upstream em texto](referencia/README.upstream.txt) declara MIT. O texto foi conservado byte a byte, incluindo a referência ao banner do repositório de origem. O snapshot consultado não contém um arquivo LICENSE ou COPYING dessa origem.

## Programas oficiais

| Fonte | Entrada, saída ou dependência |
|---|---|
| BUSCA01A | Lê `CADASTRO2.dat`, com registro NOME X(30), IDADE 9(02), CPF 9(11). |
| CAD0002A | Subprograma com `COPY002A` e área LINKAGE fornecida pelo chamador. |
| CAD0004A | Gera `CADASTRO.dat`, com registros de 47 posições. |
| CAD0005A corrigido | Lê e regrava `CADAGENDA.dat`. |
| CAIXAREG e CALCMD01 | Entrada e saída de console. |
| PROG024A | Usa `COD001A`, chama `PROGDATA` e usa `BIBLIOTECA.dat` e `BIBLIOTECA.txt`. |

Na cópia de CAD0005A foram removidos os marcadores de conflito e o DISPLAY repetido, mantendo os bytes fora do bloco. O original continua como caso negativo do lexer. Os testes preparam dados e chamadores em diretórios temporários. Veja [os comandos de uso](../README.md#copy-arquivos-e-módulos) e [o escopo de validação](../docs/recursos-suportados.md#evidência-de-compatibilidade).
