"""python -m cobol_compiler arquivo.cbl [-I diretório] [--dump-ast]."""

import argparse
import json
import sys

from .ast import to_dict, walk
from .frontend import parse_file


def main():
    parser = argparse.ArgumentParser(description="Pré-processador e parser COBOL em formato fixo")
    parser.add_argument("file")
    parser.add_argument("-I", "--include-dir", action="append", default=[], dest="include_dirs")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--check-syntax", action="store_true")
    output.add_argument("--dump-ast", action="store_true", help="AST tipada em JSON, somente em caso de sucesso")
    parser.add_argument("--copybook", action="store_true", default=None, help="analisar fragmento de dados (automático em .cpy)")
    parser.add_argument("--debug-lines", action="store_true")
    args = parser.parse_args()
    result = parse_file(args.file, include_dirs=args.include_dirs, copybook=args.copybook, debug_lines=args.debug_lines)
    for diagnostic in result.diagnostics:
        print(diagnostic.format(), file=sys.stderr)
    if result.parsed:
        for error in result.parsed.structural_errors:
            print("AST_STRUCTURE: " + error, file=sys.stderr)
    if not result.success:
        return 2 if any(d.code == "SOURCE_READ_ERROR" for d in result.diagnostics) else 1
    if args.dump_ast:
        print(json.dumps(to_dict(result.ast), ensure_ascii=False, indent=2))
    else:
        print(f"Sintaxe válida: {args.file} ({len(result.preprocessed.tokens)} tokens; {sum(1 for _ in walk(result.ast))} nós AST).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
