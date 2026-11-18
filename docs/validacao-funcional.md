# Validação funcional e reprodução — Etapa 5

A Etapa 5 recompila e executa a coorte real de 60 programas da auditoria do
backend. Os 49 antes pendentes foram investigados e receberam cenários: 44
principais e cinco módulos. Os sete oficiais conservam seus **25 cenários**;
os cinco demais cenários da Etapa 4 pertenciam a PROGDATA e três complementares.

O resultado atual é **60 programas validados, 140 cenários**, 136 comparações
idênticas e três diferenças previstas da ABI. O cenário restante verifica o
diagnóstico próprio de divisor zero. Não há divergência inesperada nem programa
sem fixture nessa coorte. Os seis bloqueios de chamadas externas e os dois de
terminal posicionado continuam fora dela, sem alegação de validação.

As evidências por programa/cenário estão na
[auditoria funcional](auditoria-funcional.md) e no
[JSON completo](auditoria-funcional.json). A auditoria do backend permanece como
registro da Etapa 4; suas 11 validações não representam o limite atual de cobertura.
Validado significa aprovado nos cenários documentados, sem promessa de cobertura
de todas as entradas ou de todos os ramos de cada programa.

## Requisitos e execução integral

Na raiz do repositório, em Linux, são necessários Python 3.11+ e GCC/C11. Não há
pacotes Python externos. GnuCOBOL é opcional, utilizado exclusivamente como oráculo
independente. O JSON registra as versões usadas e hashes dos arquivos do runtime.

```bash
python -m tools.auditar_funcional --write
python -m unittest discover -s tests -v
```

O primeiro comando regenera `docs/auditoria-funcional.json` e `.md`. O segundo
executa a suíte completa, incluindo os 326 testes anteriores, quatro regressões
mínimas, 140 casos funcionais e seis verificações do auditor: **476 testes**.
A contagem é descoberta automaticamente; contar testes não substitui executá-los.

Na preparação desta entrega, os **326 testes anteriores passaram**. Após as
correções e a integração, a rodada final aprovou **476 testes em 54,824 s**.
A auditoria integral foi repetida com `--seed 2026`: os mesmos 60 programas e
140 cenários passaram. O cenário individual de estoque abaixo também passou;
os contratos automatizados verificam outro diretório de trabalho, duas construções
sucessivas de módulo e repetição somente do cenário selecionado como falho.

Para verificar somente os oficiais, um programa ou um cenário:

```bash
python -m tools.auditar_funcional --officials
python -m tools.auditar_funcional --program PROG036A
python -m tools.auditar_funcional --program PROG008A.cbl
python -m tools.auditar_funcional --scenario prog023e-minimum-stock
python -m tools.auditar_funcional --failed-from docs/auditoria-funcional.json
```

A seleção aceita PROGRAM-ID, nome/caminho do fonte ou stem. Isso inclui casos em
que arquivo e PROGRAM-ID diferem, como PROG008A/LEARQDAT. `--failed-from` recompila
somente os cenários falhos; um relatório sem falhas retorna uma mensagem explícita,
sem compilar outro conjunto. Seleções desconhecidas falham, sem sucesso vazio.

Para variar a ordem e guardar os resultados sem substituir a auditoria integral:

```bash
python -m tools.auditar_funcional --seed 2026 --report build/ordem-alternada
python -m tools.auditar_funcional --program GRAV001A --no-oracle
PYTHONPATH=tests:. python -m unittest \
  test_functional_corpus.Functional_PROG023E_Tests.test_prog023e_minimum_stock -v
```

`--report caminho` grava JSON/Markdown nesse local. `--write` com seleção grava
em `build/auditoria-funcional-selecao.*`; não sobrescreve o relatório integral.
Sem GnuCOBOL, `--no-oracle` preserva expectativas próprias e registra zero
comparações independentes. O processo de teste pode partir de outro diretório
com `PYTHONPATH` apontando para a raiz; uma regressão verifica esse uso.

## Construção limpa e proveniência

`tools/functional_execution.py` é compartilhado com
`tools/comparar_gnucobol.py`. O auditor funcional acrescenta descoberta/inventário,
seleção, resultados por programa e relatórios. As fixtures são reutilizadas por
`tests/test_functional_corpus.py`; não há uma segunda implementação dos cenários.

Para cada programa:

1. Cria um diretório temporário independente, copia os fontes declarados e o
   fechamento de COPY sem mudar seus bytes, e registra seus hashes.
2. Executa `compile_file` desde pré-processamento e semântica. C e artefato devem
   estar ausentes antes da construção. O C preservado precisa ser idêntico ao
   resultado recém-gerado; timestamps e hashes comprovam a criação atual.
3. Invoca GCC pelo driver, registra o comando/diagnósticos e o SHA-256 do binário.
   Um módulo também é compilado como objeto sem main e chamado por harness COBOL.
4. Compila os mesmos fontes copiados com GnuCOBOL, em construção independente.
5. Para cada cenário e cada compilador, cria outro diretório vazio e instala
   somente as fixtures declaradas. O hash do executável efetivamente usado deve
   coincidir com o da construção atual.
6. Confere retorno, stdout, stderr, conteúdo binário dos arquivos e ausência de
   arquivos inesperados. Fixtures de entrada devem permanecer intactas quando
   o cenário não prevê alteração. Os registros esperados incluem padding e LF.

Persistência é declarada nas fixtures de cada caso, inclusive reabertura e ponto
anterior; não há dependência da execução de outro teste. Cada programa tem uma
construção por rodada, reutilizada apenas pelos seus cenários na mesma rodada.
Nenhum executável, objeto ou C de `build/` entra na validação. Não se remove o
diretório de build do usuário para simular limpeza.

Os temporários são descartados ao terminar. O JSON retém entradas/saídas e todos
os arquivos em base64, tamanho e SHA-256, além de versões, comandos, hashes dos
fontes e evidências de construção. Caminhos legíveis usam `$RUN` e `$REPO`; os
bytes capturados em base64 permanecem integrais. Hashes de executáveis podem
variar entre builds porque o C inclui caminhos de origem temporários; o contrato
de reprodução funcional compara resultados, não identidade binária entre máquinas.

## Isolamento, relógio e oráculo

Processos recebem stdin finito, timeout de oito segundos, limite de CPU de cinco
segundos, limite de arquivos de 16 MiB e core dumps desabilitados. Timeout e sinais
de limite são falhas. O runtime disponível não oferece chamadas de rede; chamadas
externas sem implementação já bloqueiam a compilação. Caminhos externos não
preparáveis são classificados antes da execução.

O ambiente de execução remove configurações COBOL herdadas, define `C.UTF-8` e
UTC e fixa `COBOL_DATETIME=2026-11-17T12:34:56`. No GnuCOBOL, usa
`COB_CURRENT_DATE=2026111712345600`, `COB_LS_FIXED=Y`, `COB_LS_NULLS=N` e
`COB_LS_VALIDATE=N`. **Os dois últimos dígitos da data de referência fixam os
centésimos**: a configuração anterior de 14 dígitos ainda deixava essa fração
dependente do relógio real. Cenários de ano bissexto e período da tarde/noite têm
substituições explícitas nos dois ambientes.

GnuCOBOL recebe `-fnot-reserved=ID -freserved=VALUES:VALUE`, conforme seu suporte
a vocabulário configurável. Nosso dialeto já aceita ID como nome e VALUES como
sinônimo de VALUE; assim, os originais PROG008A e PROG017A podem ser comparados
sem edição ou reescrita do fonte. Não há normalização de stdout ou arquivos.

As três diferenças preservadas têm expectativas completas para os dois lados:

| Caso | Justificativa |
|---|---|
| PROG021A, login inválido | VALUE acentuado em PIC X(50): ISO-8859-1 interno no projeto versus bytes UTF-8 armazenados pelo GnuCOBOL, alterando padding |
| PROGTEST4, busca | O mesmo efeito em JOÃO SILVA dentro de PIC X(20) |
| PROG005A, arquivo vazio | O fonte usa o FD após EOF sem leitura válida: nosso armazenamento textual é inicializado com espaços; GnuCOBOL 3.2 deixa NUL nesse buffer |

Esses casos são validados pela expectativa da ABI do projeto e pela expectativa
binária específica do oráculo, sem contá-los como resultados idênticos. Divergência
diferente dessas expectativas falha. Os logs conservam os bytes e o primeiro
ponto de diferença. O divisor zero de CALCMD01 verifica nosso diagnóstico e não
impõe a política de recuperação de outro compilador.

## Correções e comportamentos dos fontes

Duas falhas foram reproduzidas e corrigidas com testes mínimos:

- **Conversão textual decimal:** MOVE e UNSTRING não aplicavam o separador do
  receptor, falhando em MINICALC e PROG025A. O runtime agora usa esse descritor.
- **Literais continuados:** o frontend descartava espaços de literais abertos
  até a coluna 72, alterando cabeçalhos de PROG044A. Ele agora habilita
  `preserve_literal_padding=True`; a API histórica do lexer isolado mantém seu
  padrão e os 326 testes existentes foram preservados.

Os testes não corrigem os exemplos silenciosamente. Documentam, entre outros:
VALCNPJ sempre conta 40 posições antes de checar 14; PROGTIME chama 20h de
MADRUGADA pela condição impossível; REL0001A escreve o telefone antes de
atualizá-lo; PROG034A escreve um registro mesmo com entrada vazia; PROG035A não
exibe os registros percorridos; PROG023E não grava o log quando o estoque fica
exatamente no mínimo devido ao escopo do ELSE. GnuCOBOL confirma esses caminhos.

Todos os 60 elegíveis têm cenários. Os seis programas com chamadas externas e
os dois com tela posicionada continuam com os impedimentos da Etapa 4. Os três
exemplos que o professor escolher ainda precisam ser executados quando conhecidos;
novas entradas e ramos podem ampliar a cobertura sem alterar os fontes originais.

Os bloqueios externos são CAD0001A (implementação de SORT001A ausente),
NCURSESDEMO, PROGTEST2 e PROGTEST3 (chamadas ncurses), main (exibir_tela) e
ncurses_demo (wrapper C e funções auxiliares). GAMESNAK e TESTE002 dependem
de posicionamento de tela ainda sem backend. Nenhum desses oito entra nos
60 programas validados.
