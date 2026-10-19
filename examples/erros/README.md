# Programas com erros léxicos inseridos

Cópias dos sete programas de [`examples/ebasso/`](../ebasso/README.md) com
**15 erros léxicos** inseridos para demonstrar o tratamento de erros do lexer.
Cada alteração substitui uma única linha, então a numeração das linhas é a
mesma dos originais. Os programas originais são de Enio Basso, sob a
[licença MIT](../ebasso/LICENSE).

| Arquivo | Linhas alteradas | Diagnósticos esperados |
| --- | --- | --- |
| `prog001_divisoes_erros.cob` | 55, 56 | `TAB_IN_SOURCE`, `UNTERMINATED_STRING` |
| `prog002_operacoes_erros.cob` | 25, 28 | `INVALID_INDICATOR`, `INVALID_WORD` |
| `prog003_calculadora_erros.cob` | 36, 70 | `INVALID_CHARACTER`, `INVALID_IDENTIFIER` |
| `prog004_folha_pgto_erros.cob` | 19, 20, 53 | `INVALID_PICTURE`, `INVALID_CHARACTER` (×3) |
| `prog005_strings_erros.cob` | 11, 25 | `UNEXPECTED_CONTINUATION`, `UNTERMINATED_STRING` |
| `prog006_files_erros.cob` | 17, 39 | `INVALID_CHARACTER` (×2), `IDENTIFIER_TOO_LONG` |
| `prog007_loja_erros.cob` | 49, 117, 118 | `INVALID_PICTURE`, `UNTERMINATED_STRING` (×2) |

A linha 55 de `prog001_divisoes_erros.cob` contém caracteres TAB de propósito;
não converta a indentação para espaços ao editar o arquivo.

Para ver os erros intercalados no fluxo de tokens:

```bash
python -m cobol_lexer examples/erros/prog004_folha_pgto_erros.cob --stream
```

O teste `test_error_examples_report_every_inserted_error`, em
`tests/test_extended_lexer.py`, confere o código, a linha e a coluna de cada
diagnóstico. A explicação de cada erro e da recuperação correspondente está na
seção 4 do [relatório](../../docs/relatorio-lexer.md).
