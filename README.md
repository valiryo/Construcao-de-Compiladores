# Compilador COBOL acadêmico

O repositório oficial no GitHub é [valiryo/Construcao-de-Compiladores](https://github.com/valiryo/Construcao-de-Compiladores).

Compilador para o subconjunto COBOL da disciplina de Construção de Compiladores, com extensões para os programas do corpus COBOL Dicas. O front-end expande `COPY`, tokeniza o fonte, constrói a AST, valida símbolos e tipos e calcula o layout dos dados. O backend gera C11 e usa GCC para produzir executáveis, objetos e módulos compartilhados. Os binários usam o runtime deste projeto. GnuCOBOL é um oráculo opcional de testes.

O runtime implementa campos de largura fixa, aritmética decimal exata, arquivos sequenciais, entrada e saída, controle de fluxo, `CALL` e `LINKAGE`. O perfil `gnucobol` amplia o subconjunto com recursos de terminal e resolução dinâmica. Chamadas a bibliotecas C usam adaptadores de FFI com assinaturas explícitas.

## Instalação no Linux

Use **Python 3.11 ou posterior** e **GCC com suporte a C11**, com os headers de desenvolvimento da libc e o carregador POSIX (`libdl`). Use Git para obter o repositório e binutils para a suíte completa, que usa `nm`. O comando de clonagem abaixo seleciona a [branch `main`](https://github.com/valiryo/Construcao-de-Compiladores/tree/main).

Em Debian ou Ubuntu com Python 3.11 ou posterior disponível, execute os comandos abaixo.

```bash
sudo apt install git python3 gcc libc6-dev binutils
git clone --branch main https://github.com/valiryo/Construcao-de-Compiladores.git
cd Construcao-de-Compiladores
python3 --version
gcc --version
```

O projeto usa apenas a biblioteca padrão do Python. Para comparar resultados com o oráculo, instale GnuCOBOL 3.2 e confira `cobc -V`. Os cenários de FFI com ncurses precisam do runtime `libncurses.so.6`. A auditoria de compatibilidade usa também `libtinfo.so.6` e um terminal POSIX com a definição `ansi`.

## Como executar os programas oficiais

Compile e execute a partir da raiz do repositório. Os binários ficam em `build/`. Prepare os arquivos de dados indicados na raiz e digite cada entrada no terminal, seguida de Enter.

| Programa | Compilação |
|---|---|
| [CAD0004A](#cad0004a) | Direta |
| [CALCMD01](#calcmd01) | Direta |
| [CAIXAREG](#caixareg) | Direta |
| [BUSCA01A](#busca01a) | Direta |
| [CAD0005A](#cad0005a) | Direta com o fonte corrigido |
| [PROG024A](#prog024a) | Executável com `COD001A.cpy` e `PROGDATA.cbl` |
| [CAD0002A](#cad0002a) | Subprograma com `COPY002A.cpy` e um chamador |

### CAD0004A

```bash
python3 compiler.py examples/oficiais/CAD0004A.cbl -o build/cad0004a
./build/cad0004a
```

Para cadastrar uma pessoa, digite `Ana`, `25`, `111.222.333-44` e `N`. O programa grava `CADASTRO.dat` e recria o arquivo se ele já existir.

### CALCMD01

```bash
python3 compiler.py examples/oficiais/CALCMD01.cbl -o build/calcmd01
./build/calcmd01
```

Digite `1`, `2` e `3` como os três valores e `3` como divisor. O programa mostra o total `00000006,0000` e a média `00000002,0000`. Para guardar o C gerado na compilação, acrescente `--emit-c build/calcmd01.c` ao comando do compilador.

### CAIXAREG

```bash
python3 compiler.py examples/oficiais/CAIXAREG.cbl -o build/caixareg
./build/caixareg
```

Digite `10,50`, `20,25` e `30,75` para os três itens. Responda `N` à pergunta sobre desconto para obter o total de `61,50`.

### BUSCA01A

Se ainda não tiver `CADASTRO2.dat`, crie-o no editor com a linha abaixo. Cada registro tem 30 posições para o nome, duas para a idade e 11 para o CPF. Preserve os espaços após `Ana` e termine a linha com Enter.

```text
Ana                           2511111111111
```

```bash
python3 compiler.py examples/oficiais/BUSCA01A.cbl -o build/busca01a
./build/busca01a
```

Digite `11111111111` para encontrar o CPF do registro de exemplo.

### CAD0005A

Use o fonte corrigido. Para começar uma agenda, crie no editor um arquivo vazio chamado `CADAGENDA.dat`. Para usar uma agenda existente, mantenha o arquivo com seus dados.

```bash
python3 compiler.py examples/corrigidos/CAD0005A.cbl -o build/cad0005a
./build/cad0005a
```

Digite `1`, `Ana` e `12345` para cadastrar um contato. Para listá-lo, execute `./build/cad0005a` novamente e digite `2`.

### PROG024A

Para começar um acervo novo, crie no editor os arquivos vazios `BIBLIOTECA.dat` e `BIBLIOTECA.txt`. O compilador busca `COD001A.cpy` no diretório informado com `-I` e inclui `PROGDATA.cbl` no executável por meio de `--source`.

```bash
python3 compiler.py examples/oficiais/PROG024A.cbl -I examples/dependencias \
  --source examples/dependencias/PROGDATA.cbl -o build/prog024a
./build/prog024a
```

Para cadastrar um livro, digite `1` no menu, `1` como código, `Livro` como nome e `Autor` como autor. Digite `4` no menu para listar o acervo e `9` para sair.

### CAD0002A

O subprograma recebe `COPY002A-REGISTRO` de um chamador. No editor, salve o exemplo abaixo como `cad0002-driver.cbl` na raiz. Preserve a indentação do formato fixo.

```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CAD0002-DRIVER.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           COPY COPY002A.
       PROCEDURE DIVISION.
           INITIALIZE COPY002A-REGISTRO
           CALL 'CAD0002A' USING COPY002A-REGISTRO
           DISPLAY 'CADASTROS: ' COPY002A-QUANT-REG
           STOP RUN.
```

```bash
python3 compiler.py cad0002-driver.cbl -I examples/dependencias \
  --source examples/oficiais/CAD0002A.cbl -o build/cad0002a
./build/cad0002a
```

Digite `FIM` no campo de nome para sair. Para testar um cadastro antes de sair, informe `Ana`, `25`, `15/05/2000`, `Dev`, `ana@example.com`, `123456789`, `Rua Um`, `Cidade`, `SP` e `12345678`. Quando o programa pedir outro nome, digite `FIM`. O chamador mostra `CADASTROS: 01`.

## COPY, arquivos e módulos

Para compilar somente o objeto do subprograma `CAD0002A`, use `--module`.

```bash
python3 compiler.py examples/oficiais/CAD0002A.cbl -I examples/dependencias \
  --module -o build/CAD0002A.o
```

Para carregar `PROGDATA` como módulo compartilhado, compile-o separadamente. Use os mesmos arquivos de dados do [PROG024A](#prog024a) e digite `9` no menu para sair.

```bash
python3 compiler.py examples/oficiais/PROG024A.cbl -I examples/dependencias \
  --dialect gnucobol --module-dir build/modulos -o build/biblioteca
python3 compiler.py examples/dependencias/PROGDATA.cbl -I examples/dependencias \
  --module -o build/modulos/PROGDATA.so
./build/biblioteca
```

## Observações sobre os programas oficiais

- **CAD0005A.** O [arquivo original fornecido](examples/oficiais/CAD0005A.cbl) contém marcadores de conflito Git não resolvidos que impedem sua compilação. O original foi preservado. Os testes e a validação funcional usam a [versão corrigida](examples/corrigidos/CAD0005A.cbl).
- **Cláusula `VALUE`.** O [enunciado](docs/enunciado/EspecificacaoCOBOL.md#33-data-division-opcional--estrutural) exige `VALUE` nas declarações elementares, mas alguns programas oficiais omitem a cláusula. Para manter a compatibilidade com os fontes fornecidos, o compilador aceita essa omissão por padrão. A opção `--strict` habilita a exigência.

## Testes e alcance

```bash
python3 -m unittest discover -s tests -v
```

A suíte reúne testes unitários de análise e runtime, testes de integração que compilam C com GCC e cenários funcionais que verificam entrada, saída, código de retorno e arquivos. A comparação com GnuCOBOL ocorre quando o oráculo está disponível. Com o ambiente de comparação instalado, a suíte final passou com **536 testes**.

- **70/70 unidades compiladas** no corpus comparável com GnuCOBOL 3.2. São 63 programas principais e 7 módulos.
- **Sete programas oficiais compilados e validados**, usando a cópia corrigida de `CAD0005A` para os cenários positivos.
- **152 cenários funcionais validados** segundo suas expectativas. Em 60 dos 70 originais, os resultados coincidiram nos cenários comparados por inteiro. Os casos restantes incluem diferenças de ABI, comparação parcial do jogo e chamadas externas ausentes ou incompatíveis.

O resultado de compilação vale para o corpus fixado no manifesto. Entre as limitações estão `COPY REPLACING`, arquivos indexados ou relativos, `ALTER`, `SORT`, SQL/CICS embutido e formatos de tela fora do subconjunto. Módulos compartilhados usam a ABI própria do projeto em Linux. A matriz de recursos descreve as diferenças de dialeto e de execução.

Para validar apenas os casos oficiais sem o oráculo ou gerar um relatório comparativo do corpus:

```bash
python3 -m tools.auditar_funcional --officials --no-oracle
python3 -m tools.auditar_compatibilidade --write
```

## Organização

```text
compiler.py        entrada de compilação
cobol_lexer/       leitor e analisador léxico
cobol_compiler/    COPY, AST, semântica, geração C e driver
runtime/           implementação do runtime e cabeçalho da ABI
examples/          oficiais, complementares, copybooks e exemplos de diagnóstico
tests/             suíte, dados de regressão e programas chamadores
tools/             validadores funcionais e comparador com GnuCOBOL
docs/              guias técnicos e enunciado da disciplina
```

## Referências do projeto

- [Referência da CLI](docs/referencia-cli.md)
- [Arquitetura e ABI](docs/arquitetura.md)
- [Recursos suportados e limites](docs/recursos-suportados.md)
- [Especificação da disciplina](docs/enunciado/EspecificacaoCOBOL.md) e [instruções adicionais](docs/enunciado/InstrucoesAdicionaisCOBOL.md)
- [Origem, créditos e licenças dos exemplos](examples/README.md) e [manifesto do corpus COBOL Dicas](examples/manifesto-coboldicas.json)
