"""Submete todo o snapshot local ao front-end e produz cobertura reproduzível.

python -m tools.auditar_parser [--write]
Sem rede, exclusões de arquivos difíceis, GCC ou dependências externas.
"""

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path

from cobol_compiler import parse_file
from cobol_compiler import ast as A
from cobol_compiler.validation import validate_ast
from tools.auditar_corpus import OFFICIAL_NAMES


ROOT = Path(__file__).resolve().parents[1]


def portable(value):
    if isinstance(value, dict):
        return {k: portable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [portable(v) for v in value]
    if isinstance(value, str) and value.startswith(str(ROOT) + "/"):
        return str(Path(value).relative_to(ROOT))
    return value


def audit_corpus():
    lexical = json.loads((ROOT / "docs/auditoria-lexer-depois.json").read_text(encoding="utf-8"))
    files = {}
    for path, old in lexical["files"].items():
        # Inclui inclusive os negativos da etapa léxica; nenhum caminho é pulado.
        result = parse_file(ROOT / path, include_dirs=[ROOT / "examples/dependencias"])
        pp_errors = [d for d in result.preprocessed.diagnostics if d.phase == "preprocessor"]
        lex_errors = [d for d in result.preprocessed.diagnostics if d.phase == "lexer"]
        validation = validate_ast(result.ast, result.preprocessed.tokens) if result.success else None
        if pp_errors:
            classification = "preprocessing_error"
        elif lex_errors:
            classification = "lexical_error"
        elif result.parsed and result.parsed.structural_errors:
            classification = "invalid_ast"
        elif any(d.code.startswith("UNSUPPORTED_") for d in result.diagnostics):
            classification = "unsupported_extension"
        elif not result.success:
            classification = "syntax_error"
        elif validation and validation.errors:
            classification = "invalid_ast"
        else:
            classification = "data_fragment" if isinstance(result.ast, A.DataFragment) else "program"
        files[path] = portable({
            "previously_accepted_by_lexer": not old["diagnostics"],
            "classification": classification,
            "success": result.success and validation is not None and validation.success,
            "preprocessing": "error" if pp_errors else "success",
            "lexing": "error" if lex_errors else "success",
            "parsing": "not_run" if result.parsed is None else "success" if result.parsed.success else "error",
            "original_token_count": old["token_count"],
            "expanded_token_count": len(result.preprocessed.tokens),
            "consumed_tokens": result.parsed.consumed_tokens if result.parsed else 0,
            "skipped_tokens": result.parsed.skipped_tokens if result.parsed else 0,
            "error_count": len(result.diagnostics),
            "diagnostics": [{k: v for k, v in asdict(d).items() if k != "related" or v} for d in result.diagnostics],
            "unsupported_constructions": sorted({d.code for d in result.diagnostics if d.code.startswith("UNSUPPORTED_")}),
            "dependencies": [asdict(d) for d in result.preprocessed.dependencies],
            "structural_validation": asdict(validation) if validation else None,
            "structural_errors": result.parsed.structural_errors if result.parsed else [],
            "program_id": result.ast.identification.program_id if isinstance(result.ast, A.Program) else None,
        })
    counts = Counter(v["classification"] for v in files.values())
    known = {
        "examples/complementares/CLIESQL01.cbl": ("syntax_error", {"SYNTAX_ERROR"}),
        "examples/complementares/PROG006A.cbl": ("unsupported_extension", {"UNSUPPORTED_EXEC"}),
        "examples/complementares/clientes-sql.cbl": ("unsupported_extension", {"UNSUPPORTED_EXEC"}),
    }
    unexpected = []
    for path, entry in files.items():
        if not entry["previously_accepted_by_lexer"] or entry["success"]:
            continue
        expected = known.get(path)
        if not expected or entry["classification"] != expected[0] or {d["code"] for d in entry["diagnostics"]} != expected[1]:
            unexpected.append(path)
    return {
        "repository": lexical["repository"], "commit": lexical["commit"],
        "summary": {
            "total_files": len(files),
            "previously_accepted_by_lexer": sum(v["previously_accepted_by_lexer"] for v in files.values()),
            "previously_accepted_submitted_to_parser": sum(v["previously_accepted_by_lexer"] and v["parsing"] != "not_run" for v in files.values()),
            "successful_files": sum(v["success"] for v in files.values()),
            "successful_programs": counts["program"], "successful_data_fragments": counts["data_fragment"],
            "classifications": dict(sorted(counts.items())),
            "unexpected_failures": unexpected,
        },
        "files": files,
    }


def markdown(report):
    s = report["summary"]
    rows = [
        "# Auditoria do pré-processador, parser e AST", "",
        "Relatório gerado por `python -m tools.auditar_parser --write`. O snapshot e os",
        "fontes originais permanecem intactos; os hashes são verificados pela suíte léxica.", "",
        f"Referência: [COBOL Dicas no commit {report['commit'][:12]}]({report['repository']}/tree/{report['commit']}).", "",
        "## Métricas", "",
        f"- **{s['total_files']} arquivos analisados:** 85 originais + CAD0005A corrigido.",
        f"- **{s['previously_accepted_by_lexer']} aceitos anteriormente pelo lexer; todos os {s['previously_accepted_submitted_to_parser']} foram efetivamente submetidos ao parser.**",
        f"- **{s['successful_files']} sucessos completos:** {s['successful_programs']} programas e {s['successful_data_fragments']} fragmentos .cpy, com consumo integral, zero recuperação e AST validada.",
        "- Três dos anteriormente aceitos ficam separados: arquivo vazio, EXEC CICS e EXEC SQL.",
        "- Nove negativos léxicos são novamente processados e bloqueiam o parser, sem virar falsos sucessos sintáticos.", "",
        "Sucesso sintático não inclui resolução de símbolos, validade de tipos, abertura de",
        "arquivos, disponibilidade de bibliotecas ou execução. CALL para ncurses/wrappers é",
        "uma construção sintaticamente reconhecida, mesmo que o runtime externo não exista.", "",
        "## Sete oficiais", "",
        "| Programa | Tokens expandidos/consumidos | Comandos representados | Nós AST | Itens de dados | Resultado |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name in OFFICIAL_NAMES:
        folder = "corrigidos" if name == "CAD0005A.cbl" else "oficiais"
        item = report["files"][f"examples/{folder}/{name}"]
        v = item["structural_validation"]
        nodes = v["node_counts"] if v else {}
        rows.append(f"| {name}{' (corrigido)' if folder == 'corrigidos' else ''} | {item['expanded_token_count']}/{item['consumed_tokens']} | "
                    f"{v['represented_statements'] if v else 0} | {sum(nodes.values())} | {nodes.get('DataItem', 0)} | {'OK' if item['success'] else 'ERRO'} |")
    rows += ["", "A diferença de tokens em CAD0002A e PROG024A é a expansão COPY, sem os tokens",
             "das diretivas. Testes conferem os campos incluídos, a hierarquia e a origem,",
             "além dos comandos esperados de cada programa. CAD0005A original continua negativo.", "",
             "## Resultado individual de todo o corpus", "",
             "PP = pré-processamento; AST inclui invariantes de intervalos, SourceSpan, filhos e",
             "correspondência independente de cada início de comando com um nó Statement.", "",
             "| Arquivo | Lexer anterior | PP | Parser | AST | Erros | Classificação |",
             "|---|---|---|---|---|---:|---|"]
    for path, item in report["files"].items():
        v = item["structural_validation"]
        ast_status = "OK" if v and not v["errors"] else "—"
        rows.append(f"| [{path}](../{path}) | {'OK' if item['previously_accepted_by_lexer'] else 'erro'} | "
                    f"{item['preprocessing']} | {item['parsing']} | {ast_status} | {item['error_count']} | {item['classification']} |")
    rows += ["", "## Construções efetivamente implementadas", "",
             "- Divisões, configuração/SPECIAL-NAMES, SELECT e cláusulas de arquivos, FD/SD, seções de dados e procedimentos, parágrafos e sentenças.",
             "- Hierarquia de dados, FILLER, níveis 77/88, PIC/VALUE/ranges, OCCURS/DEPENDING/índices/chaves, REDEFINES, USAGE/COMP-3 e itens SCREEN sem nome.",
             "- Referências qualificadas OF/IN, múltiplos subscritos, referência modificada e LENGTH OF; funções intrínsecas com argumentos estruturados.",
             "- Expressões aritméticas com precedência/potência associativa à direita, sinais, comparações/classe, NOT/AND/OR e relações abreviadas com sujeito rastreado.",
             "- IF aninhado e ELSE, EVALUATE/WHEN/ranges/ALSO/ANY/OTHER, PERFORM inline/alvo/THRU/TIMES/UNTIL/VARYING/TEST BEFORE/AFTER, GO TO, EXIT, CONTINUE, STOP RUN, GOBACK e NEXT SENTENCE.",
             "- MOVE/CORRESPONDING, INITIALIZE REPLACING, ACCEPT de fontes de data/hora, DISPLAY/posicionamento/NO ADVANCING.",
             "- ADD/SUBTRACT/MULTIPLY/DIVIDE/COMPUTE, GIVING/REMAINDER/ROUNDED e tratadores SIZE ERROR; READ/WRITE/OPEN/CLOSE/START e tratadores de fim/chave.",
             "- CALL USING por referência/valor/conteúdo, retorno e exceções; INSPECT TALLYING/REPLACING/CONVERTING, STRING/UNSTRING, SEARCH/SET, ALTER e forma SORT USING/GIVING.", "",
             "Os recursos fora dos exemplos reais também têm testes pequenos próprios; o reconhecimento",
             "de um nó não implica implementação semântica. A [gramática](gramatica-cobol.ebnf)",
             "e [contratos do front-end](frontend.md) descrevem as variantes e limites.", "",
             "## Falhas, dependências e limites", "",
             "| Arquivo/recurso | Evidência e tratamento |",
             "|---|---|",
             "| CLIESQL01.cbl | Zero bytes; diagnóstico em 1:1 por falta de IDENTIFICATION DIVISION. Erro real do fonte, não limitação de cobertura. |",
             "| PROG006A.cbl | UNSUPPORTED_EXEC em 9:8, 13:12, 16:12 e 21:12. Inclui EXEC CICS DFLD RECEIVE dentro de WORKING-STORAGE; essa extensão e sua posição não foram validadas. MAP/MAPSET EXEMPLO não fornecido; LOGINMAP.bms é outro mapa. Não contabilizado como sintaticamente válido. |",
             "| clientes-sql.cbl | EXEC SQL/SQLCA e banco externo; blocos embutidos não têm gramática implementada. UNSUPPORTED_EXEC, sem tratar SQL como texto bruto em um nó válido. |",
             "| CAD0005A original, PROG002A, PROG010A, PROG023C, SORT001A, VALIDA1B | Conflitos Git preservados, impedem parsing. Só CAD0005A tem cópia corrigida autorizada. |",
             "| CBREAKEX / PROG042A / TELABMS | Respectivamente formato incompatível, identificadores de 31 caracteres e macrofonte BMS. Negativos léxicos preservados; detalhes na auditoria anterior. |",
             "| COPY REPLACING | Nenhum caso no corpus. Gera UNSUPPORTED_COPY_REPLACING com origem; não há substituição silenciosa nem promessa de suporte a pseudotexto. |",
             "| Formato livre, programas aninhados, múltiplos programas por arquivo | Fora desta gramática; ordem inválida ou tokens após END PROGRAM são diagnosticados. |",
             "| RENAMES e verbos não implementados | Diagnóstico explícito; não existe nó genérico de comando nem passagem de tokens desconhecidos como sucesso. |",
             "| Arquivos .dat, SQLCA, bibliotecas C/ncurses e wrappers | Dependências de execução/semântica futuras, listadas no inventário léxico; não são necessárias para analisar sintaxe de CALL. |", "",
             "Não restam falhas de parsing em exemplos batch/tela do subconjunto entre os",
             "arquivos anteriormente aceitos. Isso não prova validade de todas as combinações",
             "de cláusulas COBOL: validações de categoria, símbolos, compatibilidade e layouts",
             "continuam para a análise semântica. O corpus é fixado por commit, não por HEAD remoto.", "",
             "## Testes e reprodução", "",
             "```bash", "python -m unittest discover -s tests -v", "python -m tools.auditar_parser --write", "```", "",
             "A suíte inicial desta etapa tinha 80 testes passando. Os testes novos cobrem COPY,",
             "gramática, metadados, ASTs oficiais, corpus inteiro, diagnósticos, recuperação,",
             "precedência, cláusulas adicionais e CLI. O resultado final e a organização dos",
             "testes estão em [frontend.md](frontend.md). Nenhum teste invoca GCC ou GnuCOBOL.", "",
             "O [JSON completo](auditoria-parser.json) registra por arquivo as fases, diagnósticos",
             "com origem/inclusões, tokens consumidos, dependências, validação estrutural e",
             "contagem de cada tipo de nó. Não editar as tabelas/JSON manualmente.", "",
             "## Próxima etapa", "",
             "Implementar tabela de símbolos, qualificações, interpretação de PIC/layout,",
             "tipagem e associação SELECT/FD; vincular referências de controle e CALL.",
             "Depois implementar runtime e geração C diretamente da AST. Os nós atuais",
             "preservam cláusulas, ordem, limites e SourceSpan para essas verificações.", ""]
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenera docs/auditoria-parser.md e .json")
    args = parser.parse_args()
    report = audit_corpus()
    if args.write:
        (ROOT / "docs/auditoria-parser.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "docs/auditoria-parser.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    # Os negativos documentados são parte da auditoria, não falha do comando.
    # Falha de invariantes ou ausência de submissão da coorte aceita é regressão.
    summary = report["summary"]
    return int(summary["previously_accepted_submitted_to_parser"] != summary["previously_accepted_by_lexer"]
               or bool(summary["unexpected_failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
