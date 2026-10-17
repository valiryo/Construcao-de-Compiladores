# Relatório da Entrega 1 — Análise Léxica COBOL

**Situação:** implementação e validação local concluídas para o lexer ampliado, incluindo os exemplos ebasso fornecidos pelo professor.

## 1. Objetivo

Converter arquivos COBOL em formato fixo em tokens, tratando previamente as colunas físicas e registrando a posição original dos lexemas. Escopo fundamentado na seção 2 da [especificação entregue na disciplina](EspecificacaoCOBOL.pdf), com extensões para os sete programas de `examples/ebasso/`.

## 2. Tecnologias

Python 3.11+ e biblioteca padrão. Reconhecimento léxico implementado com expressões regulares e máquina de estados para literais que cruzam linhas.

## 3. Arquitetura

1. `fixed_format.py`: separa indicadores (coluna 7) da região de código (colunas 8-72), valida as linhas e une continuações. Cada caractere da linha lógica possui um mapeamento para sua linha e coluna físicas. Descarta sequência (1-6) e identificação (73+).
2. `scanner.py`: reconhece palavras reservadas, identificadores, literais, pontuação, operadores e máscaras `PIC`. O contexto de `PIC`/`PICTURE` permite emitir uma máscara completa como `PICTURE`, preservando o ponto final da declaração. O mapa de posições mantém as coordenadas de tokens que cruzam linhas.
3. `model.py`: formaliza tokens e diagnósticos para consumo futuro pelo parser.
4. `__main__.py`: recebe arquivo-fonte e exibe resultados legíveis ou em JSON.

## 4. Regras e ambiguidades

Os critérios foram extraídos de §2.1-§2.2. Itens não definidos explicitamente pelo professor, como a política padrão para a linha `D`, foram tratados como decisões documentadas no `README.md`, para revisão quando chegarem os casos de teste oficiais.

As extensões incluem vocabulário reservado adicional, underscores internos em identificadores, operadores aritméticos e relacionais, máscaras `PIC` e continuação de palavras e números. Elas foram adicionadas para suportar os exemplos importados e não são apresentadas como exigências da especificação original. O `README.md` detalha a distinção entre sinais numéricos, operadores e hífens internos.

## 5. Casos de teste

Os testes automatizados abrangem: palavras-chave; reconhecimento independente de caixa; nomes com hífen; números inteiros, sinalizados e decimais; strings; aspas duplicadas; pontuação; descarte das colunas fora da região de código; comentários; debugging; continuação; limite de 30 caracteres; pontuação inválida; indicador inválido; continuação indevida; strings não terminadas; TAB em código; e descarte de linhas restritas às colunas 1-6.

As regressões de formato fixo verificam comentários com TAB, validação de TAB em linhas `D` somente quando habilitadas e preservação das posições de tokens e diagnósticos após linhas ignoradas. Comentários e linhas de sequência entre partes de uma string ou identificador não interrompem a continuação. A coluna 7 continua sendo validada, inclusive em linhas sem código.

Os testes das extensões verificam operadores compostos, underscores, máscaras válidas e inválidas, recuperação de erros, isolamento do estado entre chamadas, continuações de palavras/números/máscaras e posições físicas. A integração executa os sete programas importados pela CLI JSON. Há verificações específicas de que `T` seguido de `AB-TRABALHADOR` na continuação resulta em um único identificador `TAB-TRABALHADOR`.

## 6. Resultados

A suíte local inclui **52 casos de teste**, executados com sucesso em 17/10/2026 usando Python 3.14.8 (o projeto requer Python 3.11+). Os sete programas importados e `examples/hello.cob` foram analisados pela CLI com código de saída 0 e nenhum diagnóstico. As contagens de tokens estão em [examples/ebasso/README.md](../examples/ebasso/README.md).

Após as correções de comentários e linhas de sequência, foram comparadas as saídas JSON completas dos oito exemplos com os resultados anteriores às correções, com e sem `--debug-lines`. As 16 execuções preservaram exatamente os tokens, seus valores e posições, além dos diagnósticos vazios.

Comando de reprodução: `python -m unittest discover -s tests -v`. Os resultados apresentados correspondem à suíte local e aos exemplos incluídos na entrega. Uma eventual suíte externa de avaliação do professor não faz parte desta validação.

## 7. Limitações

Validação gramatical da ordem das divisões, análise semântica, resolução de `COPY` e geração de código pertencem a entregas posteriores. Esta entrega reconhece o subconjunto léxico especificado com as extensões documentadas para os exemplos; não implementa todos os recursos do COBOL nem verifica a execução dos programas.
