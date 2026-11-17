"""Inventário offline reproduzível: python -m tools.auditar_corpus.

Não expande COPY, não valida gramática e não executa fontes externos.
"""

from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from cobol_lexer import CobolLexer


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_NAMES = (
    "BUSCA01A.cbl", "CAD0002A.cbl", "CAD0004A.cbl", "CAD0005A.cbl",
    "CAIXAREG.cbl", "CALCMD01.cbl", "PROG024A.cbl",
)
SPECIAL_WORDS = frozenset("""
    COPY CALL LINKAGE USING REDEFINES OCCURS INDEXED SEARCH INITIALIZE
    INSPECT STRING UNSTRING FUNCTION LENGTH NUMERIC VARYING END-PERFORM
    END-READ GO EXIT GOBACK CONTINUE SPECIAL-NAMES DECIMAL-POINT COMP
    SORT SD ALTER SCREEN CRT RETURN-CODE ROUNDED CORR CORRESPONDING
    NO ADVANCING EXTEND DUPLICATES EXEC
""".split())


def inventory(tokens):
    """Cada lexema original e valor normalizado, frequência e primeira posição."""
    counts = Counter((t.kind, t.lexeme, t.value) for t in tokens)
    first = {}
    for t in tokens:
        first.setdefault((t.kind, t.lexeme, t.value), [t.line, t.column])
    categories = {}
    for (kind, lexeme, value), count in sorted(counts.items()):
        categories.setdefault(kind, []).append({
            "lexeme": lexeme, "value": value, "count": count,
            "first_position": first[kind, lexeme, value],
        })
    return categories


def dependencies(tokens, sources):
    found = []
    for i, token in enumerate(tokens[:-1]):
        if token.kind != "KEYWORD" or token.value not in ("COPY", "CALL", "ASSIGN"):
            continue
        j = i + 1
        if token.value == "ASSIGN" and tokens[j].value == "TO":
            j += 1
        if j >= len(tokens):
            continue
        target = tokens[j]
        dynamic = token.value == "CALL" and target.kind != "STRING"
        suffix = ".cpy" if token.value == "COPY" else ".cbl"
        key = target.value.upper()
        resolved = sources.get(key) or sources.get(key + suffix.upper())
        found.append({
            "kind": token.value, "target": target.value,
            "line": token.line, "column": token.column,
            "dynamic": dynamic,
            "resolved_path": None if dynamic or token.value == "ASSIGN" else resolved,
        })
    return found


def audit_file(path, sources, baseline):
    source = path.read_text(encoding="utf-8-sig")
    result = CobolLexer().tokenize(source)
    categories = inventory(result.tokens)
    words = {t.value for t in result.tokens if t.kind == "KEYWORD"}
    deps = dependencies(result.tokens, sources)
    values = [t.value for t in result.tokens]
    pairs = set(zip(values, values[1:]))
    families = []
    if ("EXEC", "SQL") in pairs:
        families.append("SQL embutido (fora do subconjunto)")
    if ("EXEC", "CICS") in pairs:
        families.append("CICS (fora do subconjunto)")
    if "DFHMSD" in values:
        families.append("BMS, não é fonte COBOL apesar da extensão")
    if any(d["kind"] == "CALL" and d["target"] in (
        "initscr", "endwin", "mvprintw", "printw", "getch", "clear", "refresh",
    ) for d in deps):
        families.append("biblioteca externa ncurses/ABI C")
    if "SCREEN" in words or "COLUMN" in words or "CRT" in words:
        families.append("terminal/tela (runtime futuro)")
    if not source.strip():
        families.append("arquivo vazio; sucesso léxico não representa programa")
    previous = baseline.get("identifiers", [])
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "token_count": len(result.tokens),
        "kind_counts": dict(sorted(Counter(t.kind for t in result.tokens).items())),
        "diagnostics": [asdict(d) for d in result.diagnostics],
        # Diagnostic atual contém apenas erros. Não inventar severidades.
        "warnings": [],
        "inventory": categories,
        "special_constructions": sorted(words & SPECIAL_WORDS)
        + (["reference_modification_colon"] if "COLON" in categories else []),
        "functions": sorted({values[i + 1] for i, value in enumerate(values[:-1]) if value == "FUNCTION"}),
        "dependencies": deps,
        "families": families,
        "reclassified_as_keyword": sorted(set(previous) & words),
        "before_token_count": baseline.get("tokens"),
        "before_diagnostics": baseline.get("diagnostics", []),
    }


def main():
    manifest = json.loads((ROOT / "examples/manifesto-coboldicas.json").read_text())
    before = json.loads((ROOT / "docs/auditoria-lexer-antes.json").read_text())["files"]
    entries = [e for e in manifest["files"] if e["category"] != "referencia"]
    sources = {e["upstream_path"].upper(): e["path"] for e in entries}
    paths = [e["path"] for e in entries] + ["examples/corrigidos/CAD0005A.cbl"]
    files = {p: audit_file(ROOT / p, sources, before.get(p, {})) for p in sorted(paths)}
    report = {"repository": manifest["repository"], "commit": manifest["commit"], "files": files}
    (ROOT / "docs/auditoria-lexer-depois.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    rows = [
        "# Inventário gerado do corpus COBOL Dicas", "",
        "Gerado por `python -m tools.auditar_corpus`; não editar manualmente.", "",
        f"Commit de referência: `{manifest['commit']}`.", "",
        "O [JSON completo](auditoria-lexer-depois.json) registra por arquivo todos os lexemas,",
        "valores, frequências, primeiras posições, categorias, dependências, máscaras,",
        "palavras reclassificadas e diagnósticos antes/depois. Não expande COPY.", "",
        "## Programas oficiais (CAD0005A corrigido)", "",
        "| Programa | Tokens antes → depois | Erros antes → depois | PIC |",
        "|---|---:|---:|---|",
    ]
    for name in OFFICIAL_NAMES:
        folder = "corrigidos" if name == "CAD0005A.cbl" else "oficiais"
        p = f"examples/{folder}/{name}"
        item = files[p]
        pics = ", ".join(f"`{v}`" for v in sorted({x["value"] for x in item["inventory"].get("PICTURE", [])}))
        rows.append(f"| [{name}](../{p}) | {item['before_token_count']} → {item['token_count']} | "
                    f"{len(item['before_diagnostics'])} → {len(item['diagnostics'])} | {pics} |")
    rows += ["", "## Todos os fontes importados e a cópia corrigida", "",
             "Zero erros significa apenas tokenização bem formada; não atesta suporte sintático/semântico.", "",
             "| Arquivo | Tokens | Diagnósticos por código | Observações |", "|---|---:|---|---|"]
    for p, item in files.items():
        codes = Counter(d["code"] for d in item["diagnostics"])
        errors = ", ".join(f"{k}: {v}" for k, v in sorted(codes.items())) or "0"
        rows.append(f"| [{Path(p).name}](../{p}) | {item['token_count']} | {errors} | {'; '.join(item['families'])} |")
    rows += ["", "## Dependências por fonte", "",
             "ASSIGN lista destinos físicos; não implica arquivo de entrada existente. CALL dinâmico",
             "e dependências de EXEC SQL/CICS exigem análise específica. A tabela é inventário léxico.", "",
             "| Fonte | Tipo | Alvo | Linha | Resolução |", "|---|---|---|---:|---|"]
    for p, item in files.items():
        for dep in item["dependencies"]:
            target = dep["target"].replace("|", "\\|")
            resolved = dep["resolved_path"] or ("dinâmico" if dep["dynamic"] else "não fornecido / externo")
            rows.append(f"| {Path(p).name} | {dep['kind']} | `{target}` | {dep['line']} | {resolved} |")
    (ROOT / "docs/inventario-corpus.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    errors = {p: len(v["diagnostics"]) for p, v in files.items() if v["diagnostics"]}
    print(f"{len(files)} fontes auditados; {len(files) - len(errors)} sem erros léxicos; {len(errors)} casos negativos.")
    for path, count in errors.items():
        print(f"  {path}: {count} diagnósticos")


if __name__ == "__main__":
    main()
