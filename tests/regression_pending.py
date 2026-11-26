"""Casos negativos e variantes temporárias usadas pelos testes de regressão."""

from collections import Counter
import ctypes.util
from dataclasses import asdict
import difflib
import json
from pathlib import Path
import shutil
import tempfile

from cobol_compiler import ast as A
from cobol_compiler.driver import compile_result
from cobol_compiler.frontend import parse_file
from cobol_compiler.semantic import check_file
from cobol_lexer import CobolLexer
from cobol_lexer.fixed_format import read_fixed_lines
from tools.backend_scenarios import ROOT
from tools.corpus_contracts import backend_contract, corpus_contracts
from tools.functional_execution import command, digest

INCLUDES=[ROOT/'examples/dependencias']
TREE=ROOT/'tests/fixtures/upstream-tree.json'


def pending_inventory():
    previous=backend_contract(corpus_contracts())
    return {p:r for p,r in previous['files'].items() if r['gcc']!='success'},previous


def conflict_variants(text):
    """Escolhe cada lado inteiro; mantém todos os bytes fora dos hunks."""
    ours=[];theirs=[];hunks=[];state=0;left=[];right=[]
    for number,line in enumerate(text.splitlines(keepends=True),1):
        if line.startswith('<<<<<<<'):
            if state:raise ValueError('Conflito aninhado')
            start=number;state=1;left=[];right=[]
        elif state and line.startswith('======='):state=2
        elif state and line.startswith('>>>>>>>'):
            if state!=2:raise ValueError('Conflito sem separador')
            ours.extend(left);theirs.extend(right)
            hunks.append({'start_line':start,'end_line':number,'ours':''.join(left),'theirs':''.join(right)})
            state=0
        elif state==1:left.append(line)
        elif state==2:right.append(line)
        else:ours.append(line);theirs.append(line)
    if state:raise ValueError('Conflito sem fim')
    return {"ours":''.join(ours),"theirs":''.join(theirs)},hunks





def gnu(source,directory,*,fmt='fixed',flags=(),deps=(),link=False,module=False):
    executable=shutil.which('cobc')
    if not executable:return {'available':False}
    options=['-c' if module else '-x'] if link else ['-fsyntax-only']
    argv=[executable,*options,'-'+fmt,'-std=default','-fnot-reserved=ID','-freserved=VALUES:VALUE',
        '-I',str(INCLUDES[0]),*flags,str(source),*(str(p) for p in deps)]
    artifact=directory/('reference.o' if module else 'reference')
    if link:argv+=['-o',str(artifact)]
    result=command(argv,directory)
    result.update(available=True,format=fmt,flags=list(flags),dependencies=[str(p) for p in deps],
        artifact_created=artifact.is_file(),executed=False)
    return result


def call_contracts(semantic):
    if not semantic.ast:return []
    nodes={semantic.node_ids[id(n)]:n for n in A.walk(semantic.ast)}
    calls=[]
    for nid,info in semantic.calls.items():
        entry=dict(info,line=nodes[nid].span.start.line)
        entry['arguments']=[]
        for argument in info['arguments']:
            a=dict(argument);node=nodes[a['node_id']]
            a['expression']=getattr(node,'name',getattr(node,'value',type(node).__name__))
            if a['symbol_id']:a['symbol']=semantic.table.symbols[a['symbol_id']].name
            entry['arguments'].append(a)
        calls.append(entry)
    return calls


def pipeline(source,directory,*,deps=(),copybook=False):
    text=source.read_text(encoding='utf-8')
    lexical=CobolLexer(preserve_literal_padding=True).tokenize(text)
    physical=list(read_fixed_lines(text))
    front=parse_file(source,include_dirs=INCLUDES,copybook=copybook)
    row={'sha256':digest(source.read_bytes()),'bytes':source.stat().st_size,
        'fixed_format':{'physical_code_lines':len(physical),
            'invalid_indicators':[p.line_number for p in physical if p.indicator.upper() not in {' ','-','D','*','/'}],
            'conflict_lines':[p.line_number for p in physical if p.conflict_column]},
        'lexer':{'success':lexical.success,'diagnostics':[asdict(d) for d in lexical.diagnostics]},
        'preprocessor':{'success':front.preprocessed.success,'diagnostics':[asdict(d) for d in front.preprocessed.diagnostics],
            'dependencies':[asdict(d) for d in front.preprocessed.dependencies]},
        'parser':{'status':'success' if front.success else 'error' if front.parsed else 'not_run',
            'diagnostics':[asdict(d) for d in front.parsed.diagnostics] if front.parsed else []},
        'semantic':{'status':'not_run'},'backend':{'status':'not_run'},'gcc':{'status':'not_run'},
        'executed':False,'dependencies':[str(p) for p in deps]}
    if copybook:
        row['first_blocker']=None if front.success else 'lexer' if not lexical.success else 'parser'
        return row
    sem=check_file(source,include_dirs=INCLUDES,source_paths=deps)
    row['semantic']={'status':'success' if sem.success else 'error' if front.success else 'not_run',
        'diagnostics':[asdict(d) for d in sem.diagnostics if d.phase=='semantic']}
    row['calls']=call_contracts(sem)
    row['files']=list(sem.files.values())
    row['parameters']=sem.parameters
    absent=not (directory/'native').exists() and not (directory/'native.c').exists()
    if not absent:raise ValueError('Artefato de experimento já existe')
    built=compile_result(sem,directory/'native',emit_c=directory/'native.c',module=bool(sem.parameters))
    row['diagnostics']=[asdict(d) for d in built.diagnostics]
    row['backend']={'status':'success' if built.generated and built.generated.success else 'error' if built.generated else 'not_run',
        'diagnostics':[asdict(d) for d in built.diagnostics if d.phase in {'backend','link'}],
        'c_sha256':digest(built.generated.c_source.encode()) if built.generated and built.generated.success else None}
    row['gcc']={'status':'success' if built.success else 'error' if built.command else 'not_run',
        'command':built.command,'stdout':built.gcc_stdout,'stderr':built.gcc_stderr,
        'artifact_sha256':digest(Path(built.output).read_bytes()) if built.success else None,
        'module':bool(sem.parameters),'artifact_absent_before':absent}
    errors=[d for d in built.diagnostics if d.severity in {'E','S'}]
    row['first_blocker']=errors[0].phase if errors else None
    return row


def experiments(name,text):
    result={}
    if '<<<<<<<' in text:result.update((key,(value,'Selecionar integralmente o lado '+key)) for key,value in conflict_variants(text)[0].items())
    if name=='ASCII001.cbl':result['declare-code']=(text.replace('       PROCEDURE DIVISION.','       01 WS-CODIGO PIC 9(3).\n       PROCEDURE DIVISION.'),'Declarar WS-CODIGO PIC 9(3).')
    if name=='CBREAKEX.cbl':
        shifted='\n'.join(' '+line if line.strip() else line for line in text.splitlines())+'\n'
        result['shift-one']=(shifted,'Deslocar uma coluna à direita; manter as cláusulas originais.')
        result['shift-without-data-record']=(shifted.replace('       DATA RECORD IS NEXT-RECORD.','       .').replace('       DATA RECORD IS REPORT-RECORD.','       .'),
            'Após deslocamento, substituir as duas metacláusulas DATA RECORD IS por ponto; não alterar PIC.')
    if name=='PROG042A.cbl':result['rename-31']=(text.replace('0007-INCLUIR-QUANTIDADE-PRODUTO','0007-INCLUIR-QTDE-PRODUTO'),'Renomear chamada e seção para nome de 25 caracteres, sem colisão.')
    if name=='PROGVSAM.cbl':result['indexed-intent']=(text.replace('      *       ORGANIZATION IS INDEXED','              ORGANIZATION IS INDEXED').replace('              ORGANIZATION IS LINE SEQUENTIAL\n',''),'Ativar INDEXED e remover somente LINE SEQUENTIAL; preservar DYNAMIC, chaves e I-O.')
    if name=='PROG018A.cbl':
        result['remove-unreachable-alter']=(''.join(line for line in text.splitlines(keepends=True) if 'ALTER 100-INICIO' not in line),
            'Remover instrução inválida/inalcançável; abandona a demonstração de ALTER, não é recuperação desse recurso.')
        result['valid-alter-minimal']=('       IDENTIFICATION DIVISION.\n       PROGRAM-ID. VALIDALTER.\n       PROCEDURE DIVISION.\n'
            '           ALTER TARGET-PARA TO PROCEED TO END-PARA.\n       TARGET-PARA.\n           GO TO END-PARA.\n       END-PARA.\n           STOP RUN.\n',
            'Caso mínimo separado: alvo contém somente GO TO; distingue validade do fonte e suporte ao verbo.')
    return result


def audit(*,reference=True):
    pending,previous=pending_inventory()
    manifest=json.loads((ROOT/'examples/manifesto-coboldicas.json').read_text())
    contracts=corpus_contracts()
    findings=contracts['pending_findings']
    originals={p:digest((ROOT/p).read_bytes()) for p in set(previous['files'])|{f['path'] for f in manifest['files']}}
    upstream=json.loads(TREE.read_text())
    assert upstream['sha']==manifest['commit'] and not upstream['truncated']
    tree={item['path']:item for item in upstream['tree']}
    for item in manifest['files']:
        assert originals[item['path']]==item['sha256']
        assert tree[item['upstream_path']]['sha']==item['git_blob']
    assert {Path(p).name for p in pending}==set(findings)
    implementation={str(p.relative_to(ROOT)):digest(p.read_bytes()) for folder in ('cobol_compiler','cobol_lexer','runtime')
        for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.c','.h'}}
    result={'snapshot':manifest['commit'],'implementation_sha256':implementation,
        'snapshot_tree':{'file':str(TREE.relative_to(ROOT)),'sha256':digest(TREE.read_bytes()),
        'url':f"https://api.github.com/repos/Coboldicas/codigo_fonte_cobol/git/trees/{manifest['commit']}?recursive=1",
        'checked_on':'2026-11-18','tracked_paths':sorted(tree),'native_c_sources':[p for p in tree if Path(p).suffix.lower() in {'.c','.h','.so'}]},
        'toolchain':{},'native_libraries':{name:ctypes.util.find_library(name) for name in ('ncurses','ncursesw','tinfo')},
        'native_headers':{str(p):p.exists() for p in (Path('/usr/include/curses.h'),Path('/usr/include/ncurses.h'))},
        'previous_counts':dict(Counter(r['semantic_classification'] if r['backend']=='not_run' else r['backend'] for r in pending.values())),
        'files':{},'original_hashes':originals}
    with tempfile.TemporaryDirectory(prefix='cobol-pending-audit-') as td:
        root=Path(td)
        for tool,flag in [('cobc','-V'),('gcc','--version')]:
            result['toolchain'][tool]=command([shutil.which(tool),flag],root)['stdout'].splitlines()[0] if shutil.which(tool) else None
        resolved={}
        for path in pending:
            text=(ROOT/path).read_text()
            if '<<<<<<<' in text:
                f=root/'resolved'/Path(path).name;f.parent.mkdir(exist_ok=True);f.write_text(conflict_variants(text)[0]['ours']);resolved[Path(path).name]=f
        for path,old in pending.items():
            name=Path(path).name;original=ROOT/path;text=original.read_text();base=root/Path(path).stem;base.mkdir()
            src=base/name;src.write_bytes(original.read_bytes())
            deps=[ROOT/p for p in contracts['files'][path]['semantic']['source_dependencies']]
            row={'finding':findings[name],'original_diagnostics':old['diagnostics'],
                'previous_classification':old['semantic_classification'],'previous_backend':old['backend'],
                'original':pipeline(src,base,deps=deps,copybook=src.suffix=='.cpy'),
                'experiments':{},'conflicts':conflict_variants(text)[1] if '<<<<<<<' in text else []}
            if reference and src.suffix!='.cpy':
                row['gnu_original']=gnu(src,base)
                if name=='CBREAKEX.cbl':row['gnu_free']=gnu(src,base,fmt='free')
                if name=='PROG042A.cbl':row['gnu_limit30']=gnu(src,base,flags=['-fword-length=30'])
                if name in {'NCURSESDEMO.cbl','PROGTEST2.cbl','PROGTEST3.cbl','main.cbl','ncurses_demo.cbl'}:
                    row['gnu_static_link']=gnu(src,base,link=True,flags=['-fstatic-call'])
                if name in {'NCURSESDEMO.cbl','PROGTEST2.cbl','PROGTEST3.cbl'}:
                    row['gnu_ncurses_devel']=gnu(src,base,link=True,flags=['-fstatic-call','-lncurses'])
                    soname=result['native_libraries']['ncurses']
                    flags=['-fstatic-call','-l:'+soname] if soname else []
                    if result['native_libraries']['tinfo']:flags+=['-l:'+result['native_libraries']['tinfo']]
                    if soname:row['gnu_ncurses_runtime']=gnu(src,base,link=True,flags=flags)
            for label,(content,description) in experiments(name,text).items():
                directory=base/label;directory.mkdir();target=directory/name;target.write_text(content)
                experiment_deps=list(deps)
                if name=='PROG023C.cbl':experiment_deps=[ROOT/'examples/dependencias/PROGDATA.cbl',ROOT/'examples/complementares/PROGTIME.cbl']
                if name=='PROG042A.cbl':experiment_deps=[ROOT/'examples/complementares/PROG042B.cbl']
                trial={'description':description,'diff':''.join(difflib.unified_diff(text.splitlines(True),content.splitlines(True),fromfile=path,tofile=label+'/'+name)),
                    'pipeline':pipeline(target,directory,deps=experiment_deps)}
                if reference:trial['gnu']=gnu(target,directory,deps=experiment_deps,link=True,module=trial['pipeline']['gcc']['module'])
                row['experiments'][label]=trial
            if name=='CAD0001A.cbl':
                directory=base/'with-recovered-sort';directory.mkdir()
                expdeps=[*deps,resolved['SORT001A.cbl']]
                row['experiments']['with-recovered-sort']={'description':'Fonte CAD0001A intacto; acrescentar SORT001A resolvido aos seis módulos já declarados, incluindo PROGTIME transitivo.',
                    'diff':'','pipeline':pipeline(src,directory,deps=expdeps)}
                if reference:row['experiments']['with-recovered-sort']['gnu']=gnu(src,directory,deps=expdeps,link=True,flags=['-fstatic-call'])
            if src.suffix=='.cpy':
                contexts={}
                # Only real consumers, with their declared source closure. No main
                # manufactured for the fragment and no independent module compilation.
                for consumer,oldrow in previous['files'].items():
                    if oldrow['gcc']!='success':continue
                    front=parse_file(ROOT/consumer,include_dirs=INCLUDES)
                    if not any(d.resolved_file and Path(d.resolved_file).resolve()==original.resolve() for d in front.preprocessed.dependencies):continue
                    ctx=check_file(ROOT/consumer,include_dirs=INCLUDES,source_paths=[ROOT/p for p in contracts['files'][consumer]['semantic']['source_dependencies']])
                    lengths={s.name:ctx.layout.items[s.id].total_size for s in ctx.table.symbols.values() if s.name in {'COD001A-REGISTRO','COPY002A-REGISTRO','COPY002A-HEADER'} and s.id in ctx.layout.items}
                    contexts[consumer]={'semantic_success':ctx.success,'root_layout_bytes':lengths}
                row['contexts']=contexts
            result['files'][path]=row
        assert originals=={p:digest((ROOT/p).read_bytes()) for p in originals}
        assert implementation=={p:digest((ROOT/p).read_bytes()) for p in implementation}
        def portable(value):
            if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
            if isinstance(value,list):return [portable(v) for v in value]
            if isinstance(value,str):return value.replace(str(root),'$AUDIT').replace(str(ROOT),'$REPO')
            return value
        result=portable(result)
    rows=result['files'].values()
    advanced={p for p,r in result['files'].items() if any(e['pipeline']['gcc']['status']=='success' for e in r['experiments'].values())}
    result['summary']={'audited_files':len(pending),'programs':sum(not p.endswith('.cpy') for p in pending),'fragments':sum(p.endswith('.cpy') for p in pending),
        'classes':dict(sorted(Counter(r['finding']['feasibility'] for r in rows).items())),
        'primary_causes':dict(Counter(r['finding']['primary_cause'] for r in rows)),
        'source_or_merge_primary':sum(r['finding']['primary_cause'] in {'source','merge'} for r in rows),
        'source_or_native_contract_issues':sum(bool({'source_error','native_contract_error'} & set(r['finding']['tags'])) for r in rows),
        'compiler_limitations_including_secondary':sum('compiler_limitation' in r['finding']['tags'] for r in rows),
        'truly_external_native_dependencies':sum(r['finding']['primary_cause']=='native_dependency' for r in rows),
        'simple_recovery_files':sum(r['finding']['feasibility']=='A' for r in rows),
        'moderate_or_complex':sum(r['finding']['feasibility'] in {'B','C'} for r in rows),
        'experimental_c_generated_files':sum(any(e['pipeline']['backend']['status']=='success' for e in r['experiments'].values()) for r in rows),
        'experimental_gcc_files':len(advanced),'experimental_gcc_paths':sorted(advanced),
        'simple_recovery_new_programs':sum(r['finding']['feasibility']=='A' and Path(p).name!='CAD0005A.cbl' for p,r in result['files'].items()),
        'programs_executed':0,'compiler_or_runtime_modified':False,'originals_unchanged':True}
    return result
