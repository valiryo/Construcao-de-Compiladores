# Relatório da Entrega 1 — Análise Léxica COBOL (rascunho)

**Situação:** implementação inicial concluída; testes oficiais do professor ainda não recebidos.

## 1. Objetivo

Converter arquivos COBOL em formato fixo em tokens, tratando previamente as colunas físicas e registrando a posição original dos lexemas. Escopo fundamentado na seção 2 da especificação entregue na disciplina.

## 2. Tecnologias

Python 3.11+ e biblioteca padrão. Reconhecimento léxico implementado com expressões regulares e máquina de estados para literais que cruzam linhas.

## 3. Arquitetura

1. `fixed_format.py`: lê uma linha física e separa indicadores (coluna 7) da região de código (colunas 8-72). Descarta sequência (1-6) e identificação (73+).
2. `scanner.py`: reconhece palavras reservadas, identificadores, literais e pontuação, com controle de estado para strings e continuação marcada por hífen na coluna 7.
3. `model.py`: formaliza tokens e diagnósticos para consumo futuro pelo parser.
4. `__main__.py`: recebe arquivo-fonte e exibe resultados legíveis ou em JSON.

## 4. Regras e ambiguidades

Os critérios foram extraídos de §2.1-§2.2. Itens não definidos explicitamente pelo professor, como a política padrão para a linha `D`, foram tratados como decisões documentadas no `README.md`, para revisão quando chegarem os casos de teste oficiais.

## 5. Casos de teste

Os testes automatizados abrangem: palavras-chave; reconhecimento independente de caixa; nomes com hífen; números inteiros, sinalizados e decimais; strings; aspas duplicadas; pontuação; descarte das colunas fora da região de código; comentários; debugging; continuação; limite de 30 caracteres; pontuação inválida; indicador inválido; continuação indevida; strings não terminadas; TAB em código; e linhas curtas fora do formato.

## 6. Resultados

A suíte local incluiu **25 casos de teste**, executados com sucesso em 15/10/2026 usando Python 3.13.5 (compatível com o projeto, que requer Python 3.11+). Todos passaram, sem falhas.

Comando de reprodução: `python -m unittest discover -s tests -v`. O relatório deverá ser complementado com os casos oficiais do professor assim que forem divulgados; eles **ainda não foram executados**.

## 7. Limitações

Validação gramatical da ordem das divisões, análise semântica, resolução de `COPY` e geração de código pertencem a entregas posteriores. Esta entrega reconhece apenas o subconjunto léxico especificado.
