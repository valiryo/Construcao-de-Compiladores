# Exemplos COBOL importados

Os sete arquivos `.cob` são cópias sem alterações do repositório
[ebasso/cobol-exemplos](https://github.com/ebasso/cobol-exemplos/tree/dbe15b74769c994ceda82b48b2640fb208907d3c),
branch `master`, commit `dbe15b74769c994ceda82b48b2640fb208907d3c`.
Copyright (c) 2018 Enio Basso. A [licença MIT original](LICENSE) está incluída.
Os comentários e o conteúdo dos programas originais foram preservados integralmente.

## Validação do lexer

Data da validação: 20/10/2026. Execute a partir da raiz do projeto:

```bash
python -m cobol_lexer examples/ebasso/prog001_divisoes.cob --json
```

Para analisar todos os programas importados e retornar um código de erro caso
algum falhe, após processar todos os arquivos, execute este subshell Bash:

```bash
(
    status=0
    for source in examples/ebasso/*.cob; do
        python -m cobol_lexer "$source" || status=$?
    done
    exit "$status"
)
```

O lexer foi ampliado para reconhecer os recursos utilizados pelos programas
importados: palavras-chave adicionais, identificadores com underscore,
operadores aritméticos e relacionais, máscaras `PIC` e continuações de tokens.
Os arquivos `.cob` permanecem idênticos aos originais.

| Arquivo | Tokens | Diagnósticos | Código de saída da CLI |
| --- | ---: | ---: | ---: |
| `prog001_divisoes.cob` | 76 | 0 | 0 |
| `prog002_operacoes.cob` | 320 | 0 | 0 |
| `prog003_calculadora.cob` | 229 | 0 | 0 |
| `prog004_folha_pgto.cob` | 221 | 0 | 0 |
| `prog005_strings.cob` | 236 | 0 | 0 |
| `prog006_files.cob` | 225 | 0 | 0 |
| `prog007_loja.cob` | 566 | 0 | 0 |

Total: **zero diagnósticos nos sete arquivos**. Na implementação anterior,
seis programas produziam 33 diagnósticos. As contagens de tokens também mudaram:
máscaras como `S9(05)V99` agora formam um único token `PICTURE`, operadores
compostos como `**` formam um único token `POWER` e nomes como `PROG007_LOJA`
são identificadores únicos.

Nos programas de folha de pagamento e arquivos, o identificador
`TAB-TRABALHADOR` está dividido entre duas linhas físicas. O lexer agora
reconstrói esse identificador e registra o início na coluna 72 da primeira
linha e o fim na coluna 21 da continuação. A linha com `WRK-VALOR2` após um
literal fechado em `prog002_operacoes.cob` também é analisada integralmente.

O exemplo existente `examples/hello.cob` passou com 16 tokens e nenhum diagnóstico.
Os **58 testes automatizados** passaram com:

```bash
python -m unittest discover -s tests -v
```

A suíte inclui a execução dos sete arquivos pela CLI JSON e testes de regressão
para os tokens e as posições físicas. As correções de comentários com TAB e
linhas restritas à área de sequência foram verificadas comparando as saídas
JSON completas dos oito exemplos antes e depois da alteração, com e sem
`--debug-lines`: tokens, valores, posições e diagnósticos permaneceram idênticos.
Esta validação verifica o comportamento léxico; nenhum compilador COBOL ou
parser foi executado.
