# Arquitetura do compilador COBOL

O compilador traduz um subconjunto COBOL para C11. O front-end calcula os vínculos semânticos e o layout de dados que o gerador consome. O executável roda o código C gerado com o runtime próprio.

```text
Fonte COBOL + copybooks
           │
           ▼
Pré-processamento COPY e lexer ──► tokens com origem física
           │
           ▼
Parser ─────────────────────────► AST tipada
           │
           ▼
Análise semântica ───────────────► símbolos, vínculos, tipos e layout
           │
           ▼
Geração C11 ────────────────────► código C
           │
           ▼
Driver GCC ─────────────────────► executável, objeto ou módulo .so
```

## Front-end

| Componente | Responsabilidade |
|---|---|
| `preprocessor.py`, `source.py` | Localizam e expandem COPY, detectam ciclos e mapeiam caminho, linha, coluna e pilha de inclusão. |
| `cobol_lexer/fixed_format.py`, `scanner.py` | Leem áreas físicas, indicadores e continuações. Produzem tokens e diagnósticos com coordenadas no fonte. |
| `parser.py`, `expressions.py`, `statements.py` | Analisam divisões, declarações, instruções e expressões com precedência. |
| `ast.py`, `validation.py` | Definem nós tipados, serialização, intervalos de fonte e invariantes estruturais da AST. |
| `semantic.py`, `symbols.py` | Coletam símbolos e rótulos, resolvem referências, qualificações e chamadas. Validam operações e elaboram verificações dinâmicas. |
| `types.py`, `layout.py` | Interpretam PIC e USAGE e calculam offsets, bytes, dimensões, passos de tabela e aliases. |
| `c_codegen.py`, `native.py`, `driver.py` | Geram C e adaptadores de FFI, invocam GCC e publicam o artefato concluído. |

O pré-processador procura COPY no diretório do fonte que faz a inclusão e nos diretórios `-I`. Uma varredura preliminar localiza as diretivas fora de strings e comentários. A tokenização sobre o texto expandido aplica as regras de decimal e PIC do programa. O mapa de origem conserva os dois extremos de tokens continuados e identifica a pilha COPY.

A análise semântica separa espaços de nomes de dados, arquivos, rótulos e programas. Referências qualificadas são vinculadas a símbolos. As tabelas laterais da AST registram tipo, armazenamento, conversões, verificações de limites e destinos de controle. A API Python oferece `parse_file`, `parse_source`, `check_file`, `check_source` e o driver `cobol_compiler.driver.compile_file`.

## Dados e precisão

O layout organiza campos em áreas contíguas. `cb_field` contém ponteiro, comprimento em bytes e descritor do campo. Grupos referenciam intervalos de armazenamento. `REDEFINES` cria uma vista sobre a mesma região. `OCCURS` registra dimensões e passo por ocorrência. Os subscritos são base 1. O runtime verifica subscritos, contagem ativa, referência modificada e tamanhos dinâmicos.

Campos de texto são de largura fixa, com padding de espaços e truncamento à direita. MOVE lê a origem antes de alterar regiões sobrepostas. Dados e registros usam ISO-8859-1. ACCEPT e DISPLAY convertem na fronteira do terminal para UTF-8 por padrão. A medida de um campo COBOL é em bytes.

| Representação | Contrato |
|---|---|
| Numérico DISPLAY | Dígitos de largura fixa, escala implícita e sinal overpunch no último byte. |
| COMP/BINARY | Little-endian, complemento de dois para campos assinados. Usa 2, 4 ou 8 bytes até 4, 9 ou 18 dígitos, com larguras maiores calculadas pelo layout. |
| COMP-3 | Decimal compactado, dois nibbles por byte, sinal C/D. A leitura aceita F. |
| Expressão numérica | Racional exato, com numerador e denominador em vetores de dígitos. |
| Armazenamento | Truncamento na escala do receptor. ROUNDED arredonda à metade para longe de zero. |

O backend aceita **128 dígitos por campo**, **512 por inteiro intermediário** e **64 MiB por área**. ON SIZE ERROR trata erros aritméticos suportados e preserva o receptor afetado. A divisão por zero sem tratador encerra o executável próprio com diagnóstico.

## C gerado e runtime

Cada programa usa um dispatcher C com posição de execução e pilhas explícitas de retorno e limites de PERFORM. Parágrafos conservam a ordem e podem seguir para o próximo parágrafo. O fim da faixa de PERFORM retorna ao ponto de chamada. GO TO altera a posição no dispatcher. GOBACK retorna ao chamador e STOP RUN encerra a unidade de execução. As pilhas de controle têm limite de 4096 entradas e CALL aceita até 16 ativações.

- `decimal.c` implementa a aritmética e a representação numérica.
- `fields.c` implementa campos, conversões, intrínsecas, terminal e relógio.
- `files.c` mantém os handles separados dos buffers de registro. LINE SEQUENTIAL usa LF e aceita CRLF na leitura. SEQUENTIAL fixo usa registros de comprimento definido, sem delimitador.
- `calls.c` resolve destinos, carrega módulos, verifica contratos e invoca funções.
- `cobol_runtime.h` descreve os tipos, a ABI e a interface C.

A geração associa a posição COBOL a cada comando com `cb_origin`. Os diagnósticos estáticos incluem códigos e spans. A falha de GCC preserva o C correspondente, com o diagnóstico do GCC em stderr. Erros fatais do runtime usam a posição COBOL ativa e código de saída diferente de zero.

## CALL, LINKAGE e ABI

WORKING-STORAGE persiste entre chamadas. LOCAL-STORAGE é inicializado por ativação. LINKAGE aponta para o espaço do chamador. BY REFERENCE compartilha bytes, BY CONTENT usa uma cópia e BY VALUE numérico converte para o descritor formal. A verificação de grupos compara as folhas, dimensões, offsets e representações.

O executável chama diretamente programas conhecidos no build. Para CALL dinâmico, o runtime considera as unidades internas e módulos já carregados, a assinatura C configurada e a busca em disco. Nomes COBOL usam PROGRAM-ID em caixa alta ASCII. A busca de símbolos C respeita a grafia exata. As dependências dinâmicas transitivas recebem os diretórios do executável.

| Artefato | Interface |
|---|---|
| Objeto | Exporta função de nome derivado de PROGRAM-ID com assinatura `int entrada(cb_runtime *, cb_field *, size_t)`. Um host C inicializa o runtime, fornece os argumentos e liga os arquivos C do runtime com `-ldl`. |
| Módulo próprio `.so` | Exporta `cobol_project_module_v1` com versão, tamanho de `cb_runtime`, entradas e metadados de USING. Requer um hospedeiro com a mesma ABI. |
| Biblioteca C de terceiros | Carregada por `dlopen` com `RTLD_NOW \| RTLD_LOCAL` e invocada por adaptador tipado. A assinatura precisa corresponder à ABI real. |

A ABI de módulos é própria e difere da do GnuCOBOL. Os módulos carregados são reutilizados até o término do runtime. Falha de resolução ou contrato aciona ON EXCEPTION, quando presente. NOT ON EXCEPTION corresponde a uma chamada concluída. Sem tratador, a falha é diagnosticada no ponto de CALL.

Buffers C temporários, literais copiados e temporários de saída duram durante a chamada. Bibliotecas que retêm memória, exigem liberações ou usam estruturas específicas precisam de um wrapper C com o contrato adequado. Ponteiros retornados são opacos e a propriedade segue a função externa. Use apenas módulos e bibliotecas de confiança, pois bibliotecas nativas podem executar inicializadores ao serem carregadas.

[Opções de compilação, busca de módulos e manifestos FFI](referencia-cli.md) · [Matriz de recursos](recursos-suportados.md)
