"""CLI: python -m cobol_lexer arquivo.cob [--json] [--debug-lines]."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .scanner import CobolLexer


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisador léxico de COBOL em formato fixo")
    parser.add_argument("file", type=Path, help="Arquivo fonte COBOL (.cob, .cbl)")
    parser.add_argument("--json", action="store_true", help="Imprime tokens e diagnósticos em JSON")
    parser.add_argument("--debug-lines", action="store_true", help="Inclui linhas marcadas com D na coluna 7")
    args = parser.parse_args()

    try:
        source = args.file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"Erro ao abrir {args.file}: {error}\n")

    result = CobolLexer(debug_lines=args.debug_lines).tokenize(source)
    if args.json:
        print(json.dumps({"tokens": [asdict(t) for t in result.tokens], "diagnostics": [asdict(e) for e in result.diagnostics]}, indent=2, ensure_ascii=False))
    else:
        for token in result.tokens:
            print(f"{token.line}:{token.column:<3} {token.kind:<12} {token.lexeme!r}")
        for error in result.diagnostics:
            print(f"ERRO {error.line}:{error.column} {error.code}: {error.message}")
        print(f"\n{len(result.tokens)} tokens; {len(result.diagnostics)} erros léxicos.")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
