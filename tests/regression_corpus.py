"""Verificações de regressão dos estados do lexer, parser, semântica e backend."""

from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
from pathlib import Path
import tempfile
import unittest

from cobol_compiler import analyze, parse_file
from cobol_compiler import ast as A
from cobol_compiler.driver import compile_result
from cobol_compiler.semantic import check_file
from cobol_compiler.validation import validate_ast
from cobol_lexer import CobolLexer
from tools.backend_scenarios import ROOT, EXTRA_PROGRAMS
from tools.comparar_gnucobol import run_scenarios
from tools.corpus_contracts import corpus_contracts

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


def portable(value):
    if isinstance(value, dict):
        return {k: portable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [portable(v) for v in value]
    if isinstance(value, str) and value.startswith(str(ROOT) + "/"):
        return str(Path(value).relative_to(ROOT))
    return value


def check_parser_corpus():
    contracts = corpus_contracts()
    files = {}
    for path, entry in contracts["files"].items():
        old = entry["lexer"]
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
            "previously_accepted_by_lexer": old["accepted"],
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
        "repository": contracts["repository"], "commit": contracts["commit"],
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


def check_semantic_corpus():
    contracts=corpus_contracts()
    parsed={path:parse_file(ROOT/path,include_dirs=[ROOT/'examples/dependencias']) for path in contracts['files']}
    programs={path:f for path,f in parsed.items() if f.success and isinstance(f.ast,A.Program)}
    by_name=defaultdict(list)
    for path,frontend in programs.items():
        by_name[frontend.ast.identification.program_id.upper()].append(path)

    def dependencies(path):
        seen={path}
        queue=[path]
        while queue:
            current=queue.pop(0)
            for node in A.walk(programs[current].ast.procedure):
                if isinstance(node,A.Call) and isinstance(node.program,A.Literal) and node.program.category=='string':
                    for target in by_name.get(node.program.value.upper(),[]):
                        if target not in seen:
                            seen.add(target);queue.append(target)
        return sorted(seen-{path})

    files={}
    for path,frontend in parsed.items():
        info={'lexing':'error' if any(d.phase=='lexer' for d in frontend.diagnostics) else 'success',
              'parsing':'success' if frontend.success else 'error' if frontend.parsed else 'not_run',
              'semantic':'not_run','success':False,'symbols':0,'resolved_references':0,'layouts':0,
              'areas':{},'errors':0,'warnings':0,'unsupported':[], 'external_calls':[],
              'source_dependencies':[], 'diagnostics':[asdict(d) for d in frontend.diagnostics]}
        if not frontend.success:
            info['classification']='unsupported_extension' if any(d.code.startswith('UNSUPPORTED_') for d in frontend.diagnostics) else 'invalid_source'
            info['errors']=sum(d.severity in {'E','S'} for d in frontend.diagnostics)
        elif isinstance(frontend.ast,A.DataFragment):
            info['classification']='copybook_context_only'
        else:
            deps=dependencies(path)
            result=analyze(frontend,sources=[programs[d] for d in deps])
            errors=[d for d in result.diagnostics if d.severity in {'E','S'}]
            unsupported=[d for d in errors if d.code.startswith(('UNSUPPORTED_','UNANALYZED_'))]
            real_errors=[d for d in errors if d not in unsupported]
            if real_errors: classification='invalid_source'
            elif unsupported: classification='partially_supported'
            elif result.pending_externals: classification='valid_pending_external'
            else: classification='semantic_valid'
            info.update(semantic='success' if result.success else 'error', success=result.success,
                classification=classification,symbols=len(result.table.symbols),
                resolved_references=sum(isinstance(n,A.Reference) and result.annotation(n).symbol_id is not None for n in A.walk(frontend.ast)),
                layouts=len(result.layout.items),areas=result.layout.areas,
                errors=len(errors),warnings=sum(d.severity=='W' for d in result.diagnostics),
                unsupported=sorted({d.code for d in unsupported}),external_calls=result.pending_externals,
                source_dependencies=deps,diagnostics=[asdict(d) for d in result.diagnostics],
                call_bindings=result.calls,parameters=result.parameters,
                data_layouts=[{'name':result.table.symbols[sid].name,'symbol_id':sid,
                    'type':asdict(result.table.symbols[sid].type),**asdict(layout)} for sid,layout in result.layout.items.items()],
                statement_count=sum(isinstance(n,A.Statement) for n in A.walk(frontend.ast)),
                dynamic_checks=sum(len(ann.checks) for ann in result.annotations.values()))
        files[path]=portable(info)
    counts=Counter(v['classification'] for v in files.values())
    analyzed=[v for v in files.values() if v['semantic']!='not_run']
    expected_programs={p for p,item in contracts['files'].items() if item['parser']['classification']=='program'}
    known_failures={'examples/complementares/ASCII001.cbl':('invalid_source','UNDEFINED_SYMBOL'),
        'examples/complementares/PROG018A.cbl':('invalid_source','INVALID_ALTER_TARGET'),
        'examples/complementares/PROGVSAM.cbl':('invalid_source','INVALID_FILE_ACCESS'),
        'examples/complementares/PROGTEST.cbl':('partially_supported','UNSUPPORTED_SCREEN')}
    unexpected=[]
    for path in sorted(expected_programs):
        item=files[path]
        if item['success']:
            continue
        expected=known_failures.get(path)
        if not expected or item['classification']!=expected[0] or expected[1] not in {d['code'] for d in item['diagnostics']}:
            unexpected.append(path)
    return {'repository':contracts['repository'],'commit':contracts['commit'],
        'policy':{'mode':'corpus','encoding':'ISO-8859-1','dependencies':'explicit inventory closure by PROGRAM-ID',
                  'copybooks':'analyzed only through COPY in including programs'},
        'summary':{'total_files':len(files),'parser_programs':len(programs),'semantic_programs':len(analyzed),
            'successful_programs':sum(v['success'] for v in analyzed),
            'symbols':sum(v['symbols'] for v in analyzed),'resolved_references':sum(v['resolved_references'] for v in analyzed),
            'layouts':sum(v['layouts'] for v in analyzed),'classifications':dict(sorted(counts.items())),
            'unexpected_failures':unexpected},'files':files}


def portable_report(value):
    if isinstance(value,dict):return {key:portable_report(item) for key,item in value.items()}
    if isinstance(value,list):return [portable_report(item) for item in value]
    if isinstance(value,str):return value.replace(str(ROOT)+'/', '')
    return value


def audit_backend(*,reference=True,execute=True,compile_code=True):
    contracts=corpus_contracts()
    rows={}
    with tempfile.TemporaryDirectory(prefix='cobol-backend-audit-') as td:
        for path,entry in contracts['files'].items():
            item=entry['semantic']
            row={'semantic_classification':item['classification'],'semantic_valid':item['success'],
                 'backend':'not_run','generated_c':False,'gcc':'not_run','compiled_as':None,
                 'diagnostics':[],'gcc_stderr':'','executed':False,'functionally_validated':False,'scenarios':[]}
            if item['success']:
                result=check_file(ROOT/path,include_dirs=[ROOT/'examples/dependencias'],
                    source_paths=[ROOT/p for p in item['source_dependencies']])
                try:
                    built=compile_result(result,Path(td)/(str(len(rows))+'.out'),module=bool(result.parameters),check_backend=not compile_code)
                    row['diagnostics']=[asdict(d) for d in built.diagnostics]
                    row['generated_c']=bool(built.generated and built.generated.success)
                    row['compiled_as']='module' if result.parameters else 'executable'
                    row['gcc']='success' if built.success and compile_code else 'error' if built.command else 'not_run'
                    row['gcc_stderr']=built.gcc_stderr
                    row['program_id']=result.frontend.ast.identification.program_id
                    if built.success:row['backend']='compiled' if compile_code else 'generated'
                    elif any(d.phase=='link' or d.code.startswith('LINK_') for d in built.diagnostics):row['backend']='external_dependency_missing'
                    elif any(d.code.startswith('UNSUPPORTED_') for d in built.diagnostics):row['backend']='unsupported_backend'
                    elif built.command:row['backend']='gcc_error'
                    else:row['backend']='generation_error'
                except Exception as error:
                    row['backend']='generation_error'
                    row['internal_error']=f'{type(error).__name__}: {error}'
            rows[path]=portable(row)
    functional=run_scenarios(reference=reference) if execute else None
    if functional:
        by_program={row.get('program_id'):row for row in rows.values() if row.get('program_id')}
        for name,scenario in functional['scenarios'].items():
            if scenario['program'] not in by_program:continue
            row=by_program[scenario['program']]
            row['scenarios'].append(name)
        for program,row in by_program.items():
            scenarios=[functional['scenarios'][name] for name in row['scenarios']]
            row['executed']=any(s['executed'] for s in scenarios)
            row['functionally_validated']=bool(scenarios) and all(s['validated'] for s in scenarios)
            compared=[s for s in scenarios if s['oracle_compared']]
            row['oracle_match']=all(s['oracle_match'] is True for s in compared) if compared else None
        # PROGDATA is exercised through CALL and deterministic clock in PROG024A.
        if 'PROGDATA' in by_program:
            by_program['PROGDATA']['executed_via']=['PROGDATA-DRIVER','PROG024A']
    counts=Counter(row['backend'] for row in rows.values())
    report={'snapshot':contracts['commit'],'files':rows,'functional':functional,
        'summary':{'files':len(rows),'suite_tests':unittest.TestLoader().discover(str(ROOT/'tests')).countTestCases(),
            'semantic_valid_programs':sum(r['semantic_valid'] for r in rows.values()),
            'generated_c':sum(r['generated_c'] for r in rows.values()),
            'gcc_compiled':sum(r['gcc']=='success' for r in rows.values()),
            'executables':sum(r['gcc']=='success' and r['compiled_as']=='executable' for r in rows.values()),
            'modules':sum(r['gcc']=='success' and r['compiled_as']=='module' for r in rows.values()),
            'executed_programs':sum(r['executed'] for r in rows.values()),
            'functionally_validated_programs':sum(r['functionally_validated'] for r in rows.values()),
            'additional_functionally_validated':sum(r['functionally_validated'] and r.get('program_id') in EXTRA_PROGRAMS for r in rows.values()),
            'classifications':dict(sorted(counts.items()))}}
    return portable_report(report)
