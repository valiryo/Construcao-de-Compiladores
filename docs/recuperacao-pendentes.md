# Causas, custos e ordem de recuperação — Etapa 6

Esta análise acompanha a [auditoria gerada](auditoria-pendentes.md) e seus
[diagnósticos e experimentos completos](auditoria-pendentes.json). O objetivo é
planejar recuperações mantendo o compilador atual. Nenhuma extensão foi
implementada, nenhum original foi alterado e nenhum binário experimental foi
executado. Passar pelo GCC prova compilabilidade, não comportamento funcional.

## Resultado e interpretação das contagens

A seleção real da auditoria anterior resulta em 26 arquivos: 24 programas/casos
com aparência de programa e dois copybooks. TELABMS, apesar de estar entre os
24 nomes `.cbl`, é macrofonte BMS; CLIESQL01 está vazio. Portanto não são 24
programas COBOL completos e válidos esperando apenas backend.

| Classe | Quantidade | Interpretação |
|---|---:|---|
| A | 9 | Correções localizadas de fonte/configuração ou dependências já acessíveis |
| B | 4 | CBREAKEX, GAMESNAK, TESTE002 e PROG018A: construção adicional ou intenção a revisar |
| C | 7 | Cinco interfaces nativas, SCREEN e armazenamento INDEXED |
| D | 4 | Vazio, SQL, CICS e macrofonte BMS |
| E | 2 | Copybooks contextuais válidos |

Os nove A são ASCII001, CAD0001A, PROG002A, PROG010A, PROG023C, PROG042A,
SORT001A, VALIDA1B e CAD0005A original. CAD0005A já tem derivada validada;
recuperá-lo de novo não amplia a coorte. Restam **oito candidatos novos de baixo
esforço**, contando SORT001A como módulo e CAD0001A como seu chamador.
PROG002A e PROG010A exigem escolha explícita de versão; a classificação A não
autoriza decidir silenciosamente qual comportamento o autor queria.

**Dez arquivos** chegaram a C/GCC em pelo menos uma experiência: os nove A e
PROG018A sem a instrução inválida/inalcançável. Esse décimo caso perde o objetivo
de demonstrar ALTER e não deve ser vendido como implementação do recurso.
Nenhum desses resultados aumenta o total de 60 programas funcionalmente validados.

As causas principais, sem dupla contagem, são seis conflitos, quatro defeitos
locais de fonte (ASCII001, vazio, ALTER inválido, organização de PROGVSAM), uma
dependência COBOL recuperável, duas incompatibilidades de formato/dialeto, três
limitações diretas de terminal/tela, cinco interfaces nativas e três linguagens/
extensões externas. Os dois fragmentos completam 26.

Há **13 arquivos com problemas concretos de código**, contando os dez de
fonte/conflito e os três chamadores diretos ncurses com assinaturas incorretas.
Também há **13 com limitações do compilador**, incluindo causas secundárias,
a restrição deliberada de 30 caracteres e a variante SORT de PROG010A.
Essas duas métricas se sobrepõem; não devem ser somadas. SQL/CICS/BMS foram
separados como trilhas fora do escopo, em vez de inflar a contagem de bugs COBOL.

## Conflitos: seis arquivos, 23 hunks

| Arquivo | O que difere | Resolução inequívoca? | Experimento e dependências |
|---|---|---|---|
| CAD0005A original | Um espaço final no mesmo DISPLAY | Sim, tokens e mensagem iguais | Dois lados compilam; HEAD coincide com a derivada já validada |
| SORT001A | Ortografia de comentário | Sim para comportamento; grafia correta é CLASSIFICACAO | Dois lados geram objeto; COPY002A; não usa verbo SORT |
| VALIDA1B | Nove comentários cobol-lint | Sim para comportamento | Os dois lados geram C/GCC e têm os mesmos tokens executáveis |
| PROG023C | AGENDA CHEIA versus TABELA CHEIA | Lógica igual, mensagem exige escolha | Ambos compilam com PROGDATA e PROGTIME; COD001A incluído |
| PROG002A | Dois programas completos diferentes | Não | Ambos compilam separadamente: data/controle versus aritmética/decimal/CORRESPONDING |
| PROG010A | Dez hunks mudam arquivos, SD, tabela e fluxo | Não | HEAD de leitura/gravação compila; outro lado exige SORT, embora GnuCOBOL o aceite |

As variantes preservam os bytes fora dos blocos. Não são uma remoção cega de
marcadores: cada lado foi reanalisado. Não foi tentado combinar arbitrariamente
os dez hunks de PROG010A. O JSON contém os conteúdos de ambos os lados e cada
patch experimental, inclusive as mudanças não equivalentes.

Na variante SORT de PROG010A, a chave nomeada é campo do FD de entrada, enquanto
o SD é um PIC X(100) sem essa chave subordinada. A aceitação do oráculo não
comprova que esse layout implemente a intenção de ordenação. Antes de implementar
SORT, definir registro/chave do SD e fixtures que comprovem a ordem física final.

## Formato, nomes e causas em cascata

**CBREAKEX:** o original usa coluna 7 como início do texto; GnuCOBOL `-free`
aceita. Deslocar uma coluna em cópia temporária faz `-fixed` aceitar, sem que o
nosso parser passe: ele não reconhece `DATA RECORD IS` no FD. Uma segunda cópia
omite só essas metacláusulas e expõe quatro `INVALID_PICTURE` para edição
flutuante (`----,--9.99` e `---,---,--9.99`). São três camadas diferentes, não 38
defeitos independentes sugeridos pelos indicadores inválidos. O registro de
entrada tem 60 bytes e o relatório 80; os ASSIGN INFILE/PRNTFILE são nomes externos.
Não se deve alterar as máscaras para Z apenas para obter sucesso: mudaria a saída.

**PROG042A:** o nome `0007-INCLUIR-QUANTIDADE-PRODUTO` tem 31 caracteres e aparece
em chamada e declaração. GnuCOBOL padrão aceita; `-fword-length=30` reproduz os
dois erros. O limite 30 é contrato do lexer/especificação local, não evidência de
invalidez em todos os dialetos. A cópia com nome abreviado e PROG042B compila. O
chamado recebe o ID PIC 9(5) por referência e consulta o último pedido. Qualquer
opção futura de dialeto deve manter o padrão da disciplina e testar colisões.

**ASCII001:** WS-CODIGO não está declarado. Acrescentar PIC 9(3) basta para C/GCC
e GnuCOBOL. O título ASCII não muda o contrato de ORD, cujo ordinal começa em 1;
um futuro teste funcional deve explicitar essa diferença, sem presumir código
ASCII baseado em zero.

**CLIESQL01:** zero bytes. Não há falha sintática inicial a consertar em um
programa oculto nem evidência de SQL; é preciso obter uma implementação.

**TELABMS:** DFHMSD/DFHMDI/DFHMDF, &SYSPARM e mapas são outra linguagem, não
identificadores COBOL que se resolvem liberando caracteres no lexer. Sua análise
pertence a ferramentas BMS, não à gramática do compilador batch.

## CAD0001A e os contratos COBOL recuperáveis

CAD0001A chama CAD0002A, LER0001A, GRAV001A, REL0001A e SORT001A com
COPY002A-REGISTRO, além de PROGDATA com COD001A-REGISTRO. REL0001A também chama
PROGDATA e PROGTIME. O fechamento tem **sete subprogramas**, não somente SORT001A.
Todos existem na árvore do snapshot; só SORT001A está impedido pelo conflito.

O experimento mantém CAD0001A intacto e fornece os seis módulos já declarados
mais a cópia resolvida de SORT001A. O nosso pipeline chega ao GCC; o oráculo
liga com `-fstatic-call`, demonstrando resolução real dos símbolos COBOL.
**Não é necessário implementar SORT para recuperar SORT001A:** o módulo já faz
bubble sort usando PERFORM, comparações e MOVE.

A ABI já suporta os argumentos: COPY002A-REGISTRO tem contador de dois bytes,
50 ocorrências de stride 211 e tamanho total 10552. COD001A-REGISTRO tem **81
bytes**; COPY002A-HEADER, que não é o registro de dados, tem 13 bytes. A auditoria
confere layouts em consumidores reais, sem criar main para copybooks.

Uma futura validação de CAD0001A precisa de SEQENT01.dat com registros de 211
bytes, opção de cadastro/FIM, resposta de classificação, SEQSAI02.dat e relatório
REL0001A.txt, conforme os SELECT dos módulos. Ao criar os cenários,
os experimentos desta etapa não abrem nem criam esses dados.

## Interfaces nativas: cinco casos complexos, não um --source faltante

A árvore completa do commit foi obtida por API imutável e conferida contra todos
os blobs do manifesto. Não há fontes `.c`, headers, bibliotecas ou implementação
de `exibir_tela`, `ncurses_wrapper.c`, `mostrar_mensagem`, `esperar_tecla` e
`finalizar_ncurses`. Há três programas que chamam a API ncurses diretamente.
As bibliotecas do sistema e os arquivos do snapshot são evidências distintas.

| Chamador | Contrato observado | Problema e trabalho real |
|---|---|---|
| NCURSESDEMO | Coordenadas BY VALUE, textos/literais BY REFERENCE; WS-NOME X(30), WS-IDADE 9(2), WS-KEY 9(2) | scanw sem formato/destinos, getch tratado como parâmetro de saída; strings sem NUL |
| PROGTEST2 | Mesmos campos; keypad(1,1); mvscanw(y,x,campo) | O primeiro argumento de keypad precisa de WINDOW*, não inteiro 1; mvscanw exige formato e destinos |
| PROGTEST3 | X(30), 9(2), X(3) para idade textual; scanw com um argumento | Converter DISPLAY em texto não acrescenta NUL nem fornece assinatura variádica; retorno de getch precisa ser recebido |
| main | exibir_tela usando X(30) e 9(2) por referência | Wrapper ausente; contrato desconhecido, não presumir int* sobre dois bytes DISPLAY |
| ncurses_demo | CALL a quatro nomes, MSG X(50) por referência | Nome `.c` não é compilação de C; pontos de entrada ausentes e contrato de string não definido |

A documentação oficial de [scanw/mvscanw](https://invisible-island.net/ncurses/man/curs_scanw.3x.html)
confirma o argumento de formato e destinos variádicos. A interface
[initscr](https://invisible-island.net/ncurses/man/curs_initscr.3x.html) devolve um
ponteiro WINDOW. Isso fundamenta a revisão dos chamadores; não autoriza executá-los
com assinaturas incompatíveis. Os modos, valores, nomes, tipos e tamanhos de **cada
CALL** foram extraídos da AST/anotações atuais para o JSON, sem regex de trechos.

O ambiente tem bibliotecas de runtime versionadas ncurses/ncursesw/tinfo, mas não
os headers e o nome de ligação de desenvolvimento `-lncurses`. A auditoria registra
ligações sem biblioteca, com `-lncurses` e, quando encontrada, com SONAME versionado.
Mesmo se esta última resolver os símbolos, não valida os argumentos: não executamos
esses programas. Instalar headers ou adicionar `-l` não implementa a ABI externa.

Hoje CALL gera funções internas com `(cb_runtime *, cb_field *, size_t)`, sem
interface FFI de C. BY VALUE ainda é valor COBOL passado por descritor conforme
assinatura resolvida. Seriam necessários wrappers reais ou registro explícito de
assinaturas, conversão para int/ponteiro, strings terminadas, cópia de volta,
tratamento de retorno/erro, flags de ligação e testes PTY com restauração do
terminal. Não usar stubs nem conversão implícita de todo CALL desconhecido em C.

## Custos dos recursos ausentes

| Recurso | Evidência e escopo mínimo | Esforço relativo e benefício |
|---|---|---|
| DISPLAY AT LINE/COLUMN | AST e semântica prontas; emissão bloqueia ScreenPosition em TESTE002 e GAMESNAK | Médio; contrato de coordenadas base 1, output sem newline indevido, terminal, CURSOR/CRT STATUS e PTY. Beneficia dois casos e telas batch simples |
| SCREEN SECTION | PROGTEST usa USING bidirecional, BLANK SCREEN e PIC de entrada | Alto; layout e bindings próprios, edição, foco, teclas, atributos, terminal. Reutiliza posicionamento, mas não se reduz a ele |
| Edição flutuante e DATA RECORD | CBREAKEX válido no GnuCOBOL após configuração adequada | Médio; metacláusula FD no parser e semântica/formatação de sinal flutuante no runtime. Formato livre é decisão adicional explícita |
| ALTER | Original tem alvo inválido; caso mínimo válido só emite UNSUPPORTED_ALTER | Médio; destino mutável no dispatcher, inicialização e interação com PERFORM/GO TO. Baixo benefício para requisitos batch; adiar |
| SORT de arquivo | Somente a variante alternativa de PROG010A precisa do verbo | Médio/alto; SD/keys, leitura/ordenação/saída, formatos, status, limites/memória ou disco. Não necessário para SORT001A/CAD0001A |
| INDEXED | PROGVSAM corrigido para intenção declarada passa no GnuCOBOL | Alto; persistência por chave, alternativos/duplicatas, cursor, I-O, status, INVALID KEY, consistência e recuperação |
| RELATIVE / START / VSAM mainframe | Sem programa pendente que comprove necessidade adicional específica | Projeto separado; não inferir suporte RELATIVE/serviços VSAM porque o parser reconhece palavras ou pelo nome PROGVSAM |
| SQL/CICS/BMS | Pré-compilação, APIs e infraestrutura fora do pipeline atual | Alto; separar do objetivo dos oficiais e dos três exemplos batch desconhecidos |

Em PROG018A, o alvo de ALTER deve ser parágrafo com apenas GO TO, conforme o
[contrato documentado pelo GnuCOBOL](https://gnucobol.sourceforge.io/HTML/gnucobpg.html#ALTER).
O original viola essa regra; um mínimo válido prova separadamente o bloqueio do
projeto. Remover a instrução não implementa ALTER.

Em PROGVSAM, a seleção ativa é LINE SEQUENTIAL; as regras sequenciais são aplicadas
corretamente. A variante que ativa INDEXED conserva chaves, DYNAMIC e I-O, passa
no oráculo e elimina KEY_ON_SEQUENTIAL_FILE, INVALID_FILE_ACCESS, os dois
INVALID_FILE_MODE e INVALID_FILE_HANDLER. Resta somente o recurso INDEXED não
implementado. Logo, não há evidência de bug de validação aplicando essas regras a
um arquivo declarado INDEXED. A ausência do backend indexado continua real.

## Ordem recomendada para a próxima implementação

1. **Recuperação de fontes e dependências já suportadas:** SORT001A e CAD0001A
   primeiro (um conflito só em comentário libera o módulo e o sistema de cadastro);
   depois VALIDA1B, ASCII001, PROG042A e PROG023C. Criar derivados documentados,
   hashes, cenários e comparação de bytes; preservar os negativos originais.
2. **Escolha editorial de PROG002A e PROG010A:** dois novos principais podem
   compilar sem extensão se forem escolhidas versões compatíveis com a intenção.
   Definir saídas esperadas antes de incorporar as cópias. CAD0005A já está atendido.
3. **Construções reutilizáveis selecionadas por requisito:** metacláusulas FD e
   edição flutuante para relatórios; posicionamento simples para batch com tela.
   Cada recurso exige mínimos de semântica/runtime e testes integrais dos 60.
   Não promover formato livre ou nomes longos a padrão sem decisão de dialeto.
4. **Adiar ALTER e SORT de arquivo até necessidade real.** Não recuperam mais
   programas do que as correções localizadas acima; o exemplo ALTER original
   continuaria errado mesmo com backend novo.
5. **Projetos separados para SCREEN completa, FFI/ncurses, INDEXED/RELATIVE e
   SQL/CICS/BMS.** São capacidades relevantes se exigidas, mas têm custo e risco
   muito maiores do que o ganho de contagem neste corpus.

Esta ordem libera até **oito identidades novas** pela trilha simples, sem alterar
o compilador. A inclusão definitiva requer validação funcional por fixtures;
nenhuma das experiências desta auditoria substitui essa etapa ou os três programas
que o professor ainda escolherá.

## Verificações da entrega

A preparação aprovou os **476 testes anteriores em 54,846 s**. As seis novas
verificações da auditoria passaram isoladamente; a execução integral final
aprovou **482 testes em 66,321 s**, incluindo os 140 cenários funcionais já
existentes. Os hashes de todos os fontes importados e da implementação do
compilador/runtime foram conferidos antes/depois dos experimentos. A auditoria
usa GCC 16.2.1 e GnuCOBOL 3.2.0 nesta máquina; os comandos/versões estão no JSON.

```bash
python -m tools.auditar_pendentes --write
PYTHONPATH=tests:. python -m unittest test_pending_audit -v
python -m unittest discover -s tests -v
```

A obtenção da árvore remota foi uma consulta somente de metadados do commit
fixado. Sua cópia fica versionada; a reprodução acima não precisa de rede,
download de dependências nem instalação de ncurses de desenvolvimento.
