"""CLI: python -m cobol_lexer arquivo.cob [--json | --stream] [--debug-lines]."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .model import LexerResult
from .scanner import CobolLexer, OPERATORS, PUNCTUATION

STREAM_WIDTH = 96
FIXED_LEXEME_KINDS = frozenset(PUNCTUATION.values()) | frozenset(OPERATORS.values())


def format_stream(result: LexerResult, width: int = STREAM_WIDTH) -> str:
    """Agrupa os tokens por linha física no formato <TIPO, lexema>, com os erros intercalados.

    Pontuação e operadores omitem o lexema, pois o tipo já o determina.
    """
    tokens_by_line: dict[int, list[str]] = {}
    for token in result.tokens:
        item = f"<{token.kind}>" if token.kind in FIXED_LEXEME_KINDS else f"<{token.kind}, {token.lexeme}>"
        tokens_by_line.setdefault(token.line, []).append(item)
    errors_by_line: dict[int, list[str]] = {}
    for error in result.diagnostics:
        errors_by_line.setdefault(error.line, []).append(
            f"ERRO {error.line}:{error.column} {error.code}: {error.message}"
        )

    output: list[str] = []
    gutter = "     | "
    for number in sorted(tokens_by_line.keys() | errors_by_line.keys()):
        rows: list[str] = []
        current = ""
        for item in tokens_by_line.get(number, []):
            if current and len(gutter) + len(current) + 1 + len(item) > width:
                rows.append(current)
                current = item
            else:
                current = f"{current} {item}" if current else item
        if current:
            rows.append(current)
        rows.extend(errors_by_line.get(number, []))
        output.append(f"{number:4} | {rows[0]}")
        output.extend(gutter + row for row in rows[1:])
    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisador léxico de COBOL em formato fixo")
    parser.add_argument("file", type=Path, help="Arquivo fonte COBOL (.cob, .cbl)")
    output_format = parser.add_mutually_exclusive_group()
    output_format.add_argument("--json", action="store_true", help="Imprime tokens e diagnósticos em JSON")
    output_format.add_argument("--stream", action="store_true", help="Imprime o fluxo de tokens agrupado por linha")
    parser.add_argument("--debug-lines", action="store_true", help="Inclui linhas marcadas com D na coluna 7")
    args = parser.parse_args()

    try:
        source = args.file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"Erro ao abrir {args.file}: {error}\n")

    result = CobolLexer(debug_lines=args.debug_lines).tokenize(source)
    if args.json:
        print(json.dumps({"tokens": [asdict(t) for t in result.tokens], "diagnostics": [asdict(e) for e in result.diagnostics]}, indent=2, ensure_ascii=False))
    elif args.stream:
        print(format_stream(result))
        print(f"\n{len(result.tokens)} tokens; {len(result.diagnostics)} erros léxicos.")
    else:
        for token in result.tokens:
            print(f"{token.line}:{token.column:<3} {token.kind:<12} {token.lexeme!r}")
        for error in result.diagnostics:
            print(f"ERRO {error.line}:{error.column} {error.code}: {error.message}")
        print(f"\n{len(result.tokens)} tokens; {len(result.diagnostics)} erros léxicos.")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
