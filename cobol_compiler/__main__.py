"""python -m cobol_compiler arquivo.cbl [-I diretório] [--dump-ast]."""

import argparse
import json
import sys

from .ast import to_dict, walk
from .frontend import parse_file
from .semantic import check_file


def main(*, compile_default=False):
    parser = argparse.ArgumentParser(description="Compilador COBOL fixo: análise estática e backend C11/GCC")
    parser.add_argument("file")
    parser.add_argument("-I", "--include-dir", action="append", default=[], dest="include_dirs")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--check-syntax", action="store_true")
    output.add_argument("--dump-ast", action="store_true", help="AST tipada em JSON, somente em caso de sucesso")
    output.add_argument("--check", action="store_true", help="verificar semântica e layout")
    output.add_argument("--dump-symbols", action="store_true", help="símbolos e vínculos semânticos em JSON")
    output.add_argument("--dump-layout", action="store_true", help="layout físico em JSON")
    output.add_argument("--check-backend", action="store_true", help="verificar geração C e ligação sem invocar GCC")
    parser.add_argument("-o", "--output", help="executável ou objeto de saída")
    parser.add_argument("--emit-c", help="preservar C gerado neste caminho")
    parser.add_argument("--keep-c", action="store_true", help="preservar C junto à saída")
    parser.add_argument("--module", action="store_true", help="produzir objeto chamável, sem main")
    parser.add_argument("--source", action="append", default=[], help="fonte de programa chamado; pode se repetir")
    parser.add_argument("--strict", action="store_true", help="exigir VALUE em itens elementares")
    parser.add_argument("--copybook", action="store_true", default=None, help="analisar fragmento de dados (automático em .cpy)")
    parser.add_argument("--debug-lines", action="store_true")
    parser.add_argument('--source-format',choices=('fixed','free'),default='fixed')
    parser.add_argument('--dialect',choices=('project','gnucobol'),default='project',help='perfil explícito de compatibilidade; padrão preserva a disciplina')
    args = parser.parse_args()
    static = args.check or args.dump_symbols or args.dump_layout or args.check_syntax or args.dump_ast
    if args.check_backend or args.output or args.emit_c or args.keep_c or args.module or compile_default and not static:
        from .driver import compile_file
        result = compile_file(args.file, args.output, include_dirs=args.include_dirs,
            source_paths=args.source, strict=args.strict, debug_lines=args.debug_lines,
            emit_c=args.emit_c, keep_c=args.keep_c, module=args.module, check_backend=args.check_backend,
            source_format=args.source_format,dialect=args.dialect)
        for diagnostic in result.diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        if result.gcc_stderr:
            print(result.gcc_stderr, file=sys.stderr, end="")
        if result.success:
            print("Backend válido." if args.check_backend else f"{'Objeto' if args.module else 'Executável'} gerado: {result.output}")
        return 0 if result.success else 1
    if args.check or args.dump_symbols or args.dump_layout:
        result = check_file(args.file, include_dirs=args.include_dirs, source_paths=args.source,
                            strict=args.strict, debug_lines=args.debug_lines,source_format=args.source_format,dialect=args.dialect)
        for diagnostic in result.diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        if args.dump_symbols or args.dump_layout:
            payload = result.dump_symbols() if args.dump_symbols else result.dump_layout()
            print(json.dumps({"success":result.success, "backend_ready":result.backend_ready, **payload}, ensure_ascii=False, indent=2))
        elif result.success:
            pending = f"; {len(result.pending_externals)} chamada(s) pendente(s) de ligação" if result.pending_externals else ""
            print(f"Semântica válida: {args.file} ({len(result.table.symbols)} símbolos{pending}).")
        return 0 if result.success else 2 if any(d.code == "SOURCE_READ_ERROR" for d in result.diagnostics) else 1
    result = parse_file(args.file, include_dirs=args.include_dirs, copybook=args.copybook, debug_lines=args.debug_lines,
                        source_format=args.source_format,dialect=args.dialect)
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
