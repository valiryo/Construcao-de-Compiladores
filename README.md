# Compilador COBOL acadêmico

Compilador para o subconjunto COBOL da disciplina de Construção de Compiladores, com extensões para os programas do corpus COBOL Dicas. O front-end expande `COPY`, tokeniza o fonte, constrói a AST, valida símbolos e tipos e calcula o layout dos dados. O backend gera C11 e usa GCC para produzir executáveis, objetos e módulos compartilhados. Os binários usam o runtime deste projeto. GnuCOBOL é um oráculo opcional de testes.

O runtime implementa campos de largura fixa, aritmética decimal exata, arquivos sequenciais, entrada e saída, controle de fluxo, `CALL` e `LINKAGE`. O perfil `gnucobol` amplia o subconjunto com recursos de terminal e resolução dinâmica. Chamadas a bibliotecas C usam adaptadores de FFI com assinaturas explícitas.

## Instalação no Linux

Use **Python 3.11 ou posterior** e **GCC com suporte a C11**, com os headers de desenvolvimento da libc e o carregador POSIX (`libdl`). Use Git para obter o repositório e binutils para a suíte completa, que usa `nm`. Em Debian ou Ubuntu com Python 3.11 ou posterior disponível:

```bash
sudo apt install git python3 gcc libc6-dev binutils
git clone --branch feat/compilador-cobol-final CAMINHO_OU_URL_DA_ENTREGA Construcao-de-Compiladores
cd Construcao-de-Compiladores
python3 --version
gcc --version
```

Substitua `CAMINHO_OU_URL_DA_ENTREGA` pelo endereço ou caminho da cópia entregue. O projeto usa apenas a biblioteca padrão do Python. Execute os exemplos da raiz do repositório. Em distribuições que oferecem apenas `python3`, use `python3` no lugar de `python`. Para comparar resultados com o oráculo, instale GnuCOBOL 3.2 e confira `cobc -V`. Os cenários de FFI com ncurses precisam do runtime `libncurses.so.6`. A auditoria de compatibilidade usa também `libtinfo.so.6` e um terminal POSIX com a definição `ansi`.

## Uso rápido

Compile o exemplo oficial `CALCMD01` e forneça três valores seguidos do divisor:

```bash
python compiler.py examples/oficiais/CALCMD01.cbl -o build/calcmd01
printf '1\n2\n3\n3\n' | ./build/calcmd01
```

O programa exibe total `00000006,0000` e média `00000002,0000`. Para guardar o C que o GCC recebe:

```bash
python compiler.py examples/oficiais/CALCMD01.cbl -o build/calcmd01 --emit-c build/calcmd01.c
```

## COPY, arquivos e módulos

`-I` acrescenta um diretório para localizar copybooks. `CAD0002A` é um subprograma com `USING`. Compile-o como objeto:

```bash
python compiler.py examples/oficiais/CAD0002A.cbl -I examples/dependencias --module -o build/CAD0002A.o
```

`CAD0004A` cria `CADASTRO.dat` no diretório de execução. O exemplo abaixo registra Ana e encerra:

```bash
python compiler.py examples/oficiais/CAD0004A.cbl -o build/cadastro
mkdir -p build/cadastro-dados
(cd build/cadastro-dados && printf 'Ana\n25\n111.222.333-44\nN\n' | ../cadastro)
```

`PROG024A` usa o copybook `COD001A` e chama `PROGDATA`. Para integrar o subprograma ao executável, passe seu fonte com `--source`:

```bash
python compiler.py examples/oficiais/PROG024A.cbl -I examples/dependencias \
  --source examples/dependencias/PROGDATA.cbl -o build/biblioteca-estatica
```

Para carregar o subprograma em execução, gere o executável e o módulo separadamente. Prepare os arquivos que o programa espera encontrar e use a opção `9` para sair:

```bash
python compiler.py examples/oficiais/PROG024A.cbl -I examples/dependencias \
  --dialect gnucobol --module-dir build/modulos -o build/biblioteca
python compiler.py examples/dependencias/PROGDATA.cbl -I examples/dependencias \
  --module -o build/modulos/PROGDATA.so
mkdir -p build/biblioteca-dados
touch build/biblioteca-dados/BIBLIOTECA.dat build/biblioteca-dados/BIBLIOTECA.txt
(cd build/biblioteca-dados && printf '9\n' | ../biblioteca)
```

## Observações sobre os programas oficiais

- **CAD0005A.** O [arquivo original fornecido](examples/oficiais/CAD0005A.cbl) contém marcadores de conflito Git não resolvidos que impedem sua compilação. O original foi preservado. Os testes e a validação funcional usam a [versão corrigida](examples/corrigidos/CAD0005A.cbl).
- **Cláusula `VALUE`.** O [enunciado](docs/enunciado/EspecificacaoCOBOL.md#33-data-division-opcional--estrutural) exige `VALUE` nas declarações elementares, mas alguns programas oficiais omitem a cláusula. Para manter a compatibilidade com os fontes fornecidos, o compilador aceita essa omissão por padrão. A opção `--strict` habilita a exigência.

## Testes e alcance

```bash
python -m unittest discover -s tests -v
```

A suíte reúne testes unitários de análise e runtime, testes de integração que compilam C com GCC e cenários funcionais que verificam entrada, saída, código de retorno e arquivos. A comparação com GnuCOBOL ocorre quando o oráculo está disponível. Com o ambiente de comparação instalado, a suíte final passou com **536 testes**.

- **70/70 unidades compiladas** no corpus comparável com GnuCOBOL 3.2. São 63 programas principais e 7 módulos.
- **Sete programas oficiais compilados e validados**, usando a cópia corrigida de `CAD0005A` para os cenários positivos.
- **152 cenários funcionais validados** segundo suas expectativas. Em 60 dos 70 originais, os resultados coincidiram nos cenários comparados por inteiro. Os casos restantes incluem diferenças de ABI, comparação parcial do jogo e chamadas externas ausentes ou incompatíveis.

O resultado de compilação vale para o corpus fixado no manifesto. Entre as limitações estão `COPY REPLACING`, arquivos indexados ou relativos, `ALTER`, `SORT`, SQL/CICS embutido e formatos de tela fora do subconjunto. Módulos compartilhados usam a ABI própria do projeto em Linux. A matriz de recursos descreve as diferenças de dialeto e de execução.

Para validar apenas os casos oficiais sem o oráculo ou gerar um relatório comparativo do corpus:

```bash
python -m tools.auditar_funcional --officials --no-oracle
python -m tools.auditar_compatibilidade --write
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

- [Referência da CLI](docs/referencia-cli.md)
- [Arquitetura e ABI](docs/arquitetura.md)
- [Recursos suportados e limites](docs/recursos-suportados.md)
- [Especificação da disciplina](docs/enunciado/EspecificacaoCOBOL.md) e [instruções adicionais](docs/enunciado/InstrucoesAdicionaisCOBOL.md)
- [Origem, créditos e licenças dos exemplos](examples/README.md)
