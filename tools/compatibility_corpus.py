"""Compilação comparável de cada original, sem derivados experimentais."""
from collections import Counter
import ctypes.util
import json
from pathlib import Path
import shutil
import tempfile

from cobol_compiler import ast as A
from cobol_compiler.frontend import parse_file
from tools.backend_scenarios import ROOT
from tools.functional_execution import digest,copy_sources,clean_compile
from tools.auditar_pendentes import command
from tools.terminal_probe import run_terminal

# Opção de entrada documentada, nunca uma transformação de bytes do fonte.
FORMATS={'CBREAKEX.cbl':'free'}
VOCABULARY=['-fnot-reserved=ID','-freserved=VALUES:VALUE']
NCURSES={'initscr','cbreak','noecho','clear','mvprintw','scanw','refresh','getch','endwin','keypad','mvscanw'}


def sources():
    manifest=json.loads((ROOT/'examples/manifesto-coboldicas.json').read_text())
    return [f for f in manifest['files'] if Path(f['path']).suffix.lower() in {'.cbl','.cob','.cpy'}],manifest


def discover():
    entries,manifest=sources();fronts={};index={}
    for item in entries:
        path=item['path'];fmt=FORMATS.get(Path(path).name,'fixed')
        front=parse_file(ROOT/path,include_dirs=[ROOT/'examples/dependencias'],source_format=fmt,dialect='gnucobol')
        fronts[path]=front
        if front.success and isinstance(front.ast,A.Program):index[front.ast.identification.program_id.upper()]=path
    return entries,manifest,fronts,index


def closure(path,fronts,index):
    seen={path};result=[];missing=set()
    def visit(unit):
        front=fronts[unit]
        if not front.ast:return
        for n in A.walk(front.ast):
            if not isinstance(n,A.Call):continue
            name=n.program.value.upper() if isinstance(n.program,A.Literal) else '(dynamic)'
            dep=index.get(name)
            if dep and dep not in seen:seen.add(dep);result.append(dep);visit(dep)
            elif not dep:missing.add(name)
    visit(path)
    return sorted(result),sorted(missing)


def gnu_build(source,deps,include,directory,*,fmt,module,strict=False,libraries=()):
    directory.mkdir();exe=shutil.which('cobc')
    if not exe:return {'available':False,'compiled':False,'linked':False}
    base=[exe,'-'+fmt,'-std=default',*VOCABULARY,'-I',str(include)]
    syntax=command([*base,'-fsyntax-only',str(source)],directory)
    artifact=directory/('module.o' if module else 'program')
    object_path=artifact if module else directory/'unit.o'
    object_build=command([*base,'-c',str(source),'-o',str(object_path)],directory) if syntax['returncode']==0 else None
    object_ok=bool(object_build and object_build['returncode']==0 and object_path.is_file())
    argv=[*base,'-c' if module else '-x']
    if strict:argv+=['-fstatic-call']
    argv+=[str(source)]
    if not module:argv += [str(p) for p in deps]
    argv += [*libraries,'-o',str(artifact)]
    build=object_build if module else command(argv,directory) if object_ok else None
    success=bool(build and build['returncode']==0 and artifact.is_file())
    return {'available':True,'temporary_directory':str(directory),'analysis':syntax,'object_build':object_build,'object_compiled':object_ok,'build':build,'compiled':success,
        'linked':success if not module else None,'mode':'module-object' if module else 'static-executable' if strict else 'dynamic-executable',
        'artifact_sha256':digest(artifact.read_bytes()) if success else None,
        'artifact':str(artifact) if success else None,'executed':False}


def audit_compilation(*,native_probes=True):
    entries,manifest,fronts,index=discover();rows={}
    before={e['path']:digest((ROOT/e['path']).read_bytes()) for e in entries}
    for e in entries:assert before[e['path']]==e['sha256']
    ncurses=ctypes.util.find_library('ncurses');tinfo=ctypes.util.find_library('tinfo')
    with tempfile.TemporaryDirectory(prefix='cobol-compatibility-') as td:
        root=Path(td)
        for e in entries:
            path=e['path'];front=fronts[path];fmt=FORMATS.get(Path(path).name,'fixed')
            record={'source_sha256':before[path],'format':fmt,'dialect':'gnucobol',
                'gnu_dialect':'default','gnu_vocabulary':VOCABULARY,
                'program_id':front.ast.identification.program_id if isinstance(front.ast,A.Program) else None,
                'kind':'module' if isinstance(front.ast,A.Program) and front.ast.procedure.parameters else 'main'}
            if path.endswith('.cpy'):
                record.update(kind='copybook',category='contextual_fragment',parser_success=front.success)
                rows[path]=record;continue
            if 'DFHMSD' in (ROOT/path).read_text() and not record['program_id']:
                record['language']='BMS'
            deps,missing=closure(path,fronts,index);record.update(dependencies=deps,unresolved_calls=missing)
            directory=root/Path(path).stem;directory.mkdir()
            source,dep_sources,include,hashes,_=copy_sources(ROOT/path,[ROOT/p for p in deps],directory/'sources',
                frontend_options={'source_format':fmt,'dialect':'gnucobol'})
            record['sources']=hashes;module=record['kind']=='module'
            ref=gnu_build(source,dep_sources,include,directory/'gnu',fmt=fmt,module=module)
            record['gnu']=ref
            if ref['compiled'] and not module:
                libs=[]
                if missing and all(n.lower() in NCURSES for n in missing) and ncurses:
                    libs=['-l:'+ncurses]+(['-l:'+tinfo] if tinfo else [])
                record['gnu_resolved_link']=gnu_build(source,dep_sources,include,directory/'gnu-resolved',fmt=fmt,module=False,strict=True,libraries=libs)
                if native_probes and libs and record['gnu_resolved_link']['compiled']:
                    run_dir=directory/'native-library-probe';run_dir.mkdir()
                    record['gnu_native_probe']=run_terminal(record['gnu_resolved_link']['artifact'],b'1\n2\nx\n',run_dir)
                    record['gnu_native_probe']['scope']='Tentativa isolada; não atesta correção do contrato FFI do fonte.'
            _,native=clean_compile(source,dep_sources,include,directory/'ours',module=module,
                compiler_options={'source_format':fmt,'dialect':'gnucobol'})
            record['ours']=native
            _,project=clean_compile(source,dep_sources,include,directory/'project',module=module,
                compiler_options={'source_format':fmt,'dialect':'project'})
            record['project_profile']=project
            codes={d['code'] for d in native['diagnostics']}
            if ref['compiled'] and native['success']:record['category']='both_compiled'
            elif ref['compiled']:
                resolved=record.get('gnu_resolved_link',{}).get('compiled',False)
                record['category']='gnu_only' if resolved else 'external_dependency_unavailable'
            elif 'UNSUPPORTED_EXEC' in codes or record.get('language')=='BMS':record['category']='external_extension_unavailable'
            else:record['category']='source_rejected'
            record['first_blocker']=next((d['phase'] for d in native['diagnostics'] if d['severity'] in {'E','S'}),None)
            rows[path]=record
        def portable(x):
            if isinstance(x,dict):return {k:portable(v) for k,v in x.items()}
            if isinstance(x,list):return [portable(v) for v in x]
            if isinstance(x,str):return x.replace(str(root),'$BUILD').replace(str(ROOT),'$REPO')
            return x
        rows=portable(rows)
    assert before=={p:digest((ROOT/p).read_bytes()) for p in before}
    compiled=[r for r in rows.values() if r.get('gnu',{}).get('compiled')]
    def metric(kind=None):
        units=[r for r in compiled if kind is None or r['kind']==kind]
        ours=sum(r['ours']['success'] for r in units)
        return {'ours':ours,'gnucobol':len(units),'percent':round(100*ours/len(units),4) if units else None}
    return {'snapshot':manifest['commit'],'original_files':len(entries),'derivative_excluded':'examples/corrigidos/CAD0005A.cbl',
        'summary':{'compilation':metric(),'mains':metric('main'),'modules':metric('module'),
            'project_profile_compiled':sum(r.get('project_profile',{}).get('success',False) for r in rows.values()),
            'newly_compiled_originals':sum(r.get('ours',{}).get('success',False) and not r.get('project_profile',{}).get('success',False) for r in rows.values()),
            'categories':dict(Counter(r['category'] for r in rows.values()))},'files':rows}
