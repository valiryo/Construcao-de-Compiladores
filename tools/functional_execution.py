"""Construção limpa e execução compartilhadas pelos auditores e pelo oráculo.

Cada programa recebe fontes copiados e build novos; cada cenário recebe outro
diretório vazio. Evidências nunca dependem de artefatos de build/ do repositório.
"""
from dataclasses import asdict
import base64
import hashlib
import os
import platform
from pathlib import Path
import random
import resource
import shutil
import subprocess
import tempfile
import time

from cobol_compiler.driver import compile_file, RUNTIME_SOURCES
from cobol_compiler.frontend import parse_file
from tools.backend_scenarios import ROOT, CLOCK, validate_scenario


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return {'bytes':len(data),'sha256':digest(data),'base64':base64.b64encode(data).decode('ascii')}


def environment(extra=()):
    # Do not inherit COB_* settings, locale, preload hooks or runtime flags.
    env={k:os.environ[k] for k in ('PATH','SYSTEMROOT','TMPDIR') if k in os.environ}
    env.update(LANG='C.UTF-8',LC_ALL='C.UTF-8',TZ='UTC',
        COBOL_DATETIME=CLOCK,COBOL_TERMINAL_ENCODING='utf8',
        COB_CURRENT_DATE='2026111712345600',COB_LS_FIXED='Y',COB_LS_NULLS='N',COB_LS_VALIDATE='N')
    env.update(extra)
    # A 14-digit override leaves the reference runtime's current centiseconds.
    # Explicitly pin them too; never mask them in captured output.
    if len(env['COB_CURRENT_DATE'])==14:env['COB_CURRENT_DATE']+='00'
    return env


def execution_limits():
    resource.setrlimit(resource.RLIMIT_CPU,(5,5))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def relative_name(path):
    path=Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else 'harnesses/'+path.name


def copy_sources(source,deps,directory,*,frontend_options=None):
    """Copiar apenas unidades declaradas e seu fechamento COPY, sem alterações."""
    paths={Path(source).resolve(),*(Path(p).resolve() for p in deps)}
    for path in list(paths):
        parsed=parse_file(path,include_dirs=[ROOT/'examples/dependencias'],**(frontend_options or {}))
        paths.update(Path(d.resolved_file).resolve() for d in parsed.preprocessed.dependencies if d.resolved_file)
    copied={}
    evidence={}
    for path in sorted(paths):
        target=directory/relative_name(path)
        target.parent.mkdir(parents=True,exist_ok=True)
        data=path.read_bytes()
        target.write_bytes(data)
        if target.read_bytes()!=data:raise AssertionError('Source copy mismatch')
        copied[path]=target
        evidence[relative_name(path)]={'bytes':len(data),'sha256':digest(data)}
    include=directory/'examples/dependencias'
    include.mkdir(parents=True,exist_ok=True)
    return copied[Path(source).resolve()],[copied[Path(p).resolve()] for p in deps],include,evidence,copied


def clean_compile(source,deps,include,directory,*,module=False,compiler_options=None):
    directory.mkdir()
    c_path=directory/'program.c'
    output=directory/('program.o' if module else 'program')
    absent=not c_path.exists() and not output.exists()
    start=time.time_ns()
    result=compile_file(source,output,include_dirs=[include],source_paths=deps,emit_c=c_path,module=module,**(compiler_options or {}))
    c_bytes=c_path.read_bytes() if c_path.exists() else b''
    generated=bool(result.generated and result.generated.success)
    regenerated=bool(absent and generated and c_bytes==result.generated.c_source.encode('utf-8') and c_path.stat().st_mtime_ns>=start)
    fresh=bool(absent and result.success and output.is_file() and output.stat().st_mtime_ns>=start)
    proof={'success':result.success,'generated_c':generated,'absent_before':absent,
        'started_ns':start,'c_regenerated':regenerated,
        'gcc_executed':bool(result.command),'artifact_fresh':fresh,
        'command':result.command,'gcc_stdout':result.gcc_stdout,'gcc_stderr':result.gcc_stderr,
        'diagnostics':[asdict(d) for d in result.diagnostics],
        'c':blob(c_bytes) if c_bytes else None,
        'artifact':{'bytes':output.stat().st_size,'sha256':digest(output.read_bytes())} if fresh else None}
    # The C text is a build artifact, not a log; retain its fingerprint, not base64.
    if proof['c']:proof['c'].pop('base64')
    if result.success and not (regenerated and fresh and proof['gcc_executed']):
        raise AssertionError('Clean-build proof failed')
    return result,proof


def differences(a,b,left_files,right_files):
    result=[]
    for key in ('stdout','stderr','returncode'):
        x,y=getattr(a,key),getattr(b,key)
        if x==y:continue
        if isinstance(x,bytes):
            first=next((i for i,(u,v) in enumerate(zip(x,y)) if u!=v),min(len(x),len(y)))
            result.append({'part':key,'first_byte':first,'ours':repr(x[max(0,first-30):first+100]),'reference':repr(y[max(0,first-30):first+100])})
        else:result.append({'part':key,'ours':x,'reference':y})
    for name in sorted(set(left_files)|set(right_files)):
        x,y=left_files.get(name),right_files.get(name)
        if x!=y:result.append({'part':'file','name':name,'ours':blob(x) if x is not None else None,'reference':blob(y) if y is not None else None})
    return result


def run_cases(scenarios,input_resolver,*,reference=True,module_sources=None,seed=None,compiler_options=None,reference_options=None):
    scenarios=list(scenarios)
    if len({s.name for s in scenarios})!=len(scenarios):raise ValueError('Duplicate scenario name')
    module_sources=module_sources or {}
    oracle=shutil.which('cobc') if reference else None
    report={'oracle':oracle is not None,'oracle_version':None,'programs':{},'scenarios':{},
        'seed':seed,'environment':environment(),'runtime_sources':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in [*RUNTIME_SOURCES,ROOT/'runtime/cobol_runtime.h']}}
    gcc=shutil.which('gcc')
    report['toolchain']={'python':platform.python_version(),
        'gcc':subprocess.run([gcc,'--version'],capture_output=True,text=True,timeout=10).stdout.splitlines()[0] if gcc else None}
    if oracle:report['oracle_version']=subprocess.run([oracle,'-V'],capture_output=True,text=True,timeout=10).stdout.splitlines()[0]
    names=sorted({s.program for s in scenarios})
    if seed is not None:random.Random(seed).shuffle(names)
    with tempfile.TemporaryDirectory(prefix='cobol-functional-') as temporary:
        root=Path(temporary)
        report['run_id']=root.name
        for program in names:
            options=(compiler_options or {}).get(program,{})
            build=root/program
            build.mkdir()
            try:
                source,deps=input_resolver(program,build)
                source,deps,include,sources,copied=copy_sources(source,deps,build/'sources',frontend_options=options)
                ours,proof=clean_compile(source,deps,include,build/'native',compiler_options=options)
                info={'generated_c':proof['generated_c'],'compiled':ours.success,
                    'diagnostics':proof['diagnostics'],'gcc_stderr':ours.gcc_stderr,'build':proof,
                    'sources':sources,'oracle_compiled':False,'oracle_compile_stderr':''}
                if program in module_sources:
                    original=Path(module_sources[program]).resolve()
                    _,info['module_build']=clean_compile(copied[original],[p for p in deps if p!=copied[original]],include,build/'module',module=True,compiler_options=options)
                    info['compiled']=info['compiled'] and info['module_build']['success']
            except Exception as error:
                info={'generated_c':False,'compiled':False,'diagnostics':[],
                    'gcc_stderr':'','oracle_compiled':False,'oracle_compile_stderr':'',
                    'setup_error':f'{type(error).__name__}: {error}'}
            binary=build/'reference'
            if oracle and not info.get('setup_error'):
                command=[oracle,'-x','-'+options.get('source_format','fixed'),'-fnot-reserved=ID','-freserved=VALUES:VALUE',*(reference_options or {}).get(program,[]),
                    '-I',str(include),str(source),*(str(p) for p in deps),'-o',str(binary)]
                try:
                    reference_build=subprocess.run(command,capture_output=True,text=True,env=environment(),cwd=build,timeout=60)
                    info['oracle_compiled']=reference_build.returncode==0
                    info['oracle_compile_stderr']=reference_build.stderr
                except subprocess.TimeoutExpired:info['oracle_compile_stderr']='GnuCOBOL compilation timeout'
                info['oracle_command']=command
            report['programs'][program]=info
            program_cases=[s for s in scenarios if s.program==program]
            if seed is not None:random.Random(seed).shuffle(program_cases)
            for scenario in program_cases:
                row={'program':program,'executed':False,'validated':False,'errors':[],
                    'oracle_compared':False,'oracle_match':None,'differences':[],
                    'stdin':blob(scenario.stdin.encode('utf-8')),'rationale':scenario.rationale,
                    'environment':{k:v for k,v in environment(scenario.environment).items() if k not in {'PATH','SYSTEMROOT','TMPDIR'}},
                    'fixtures':{n:blob(b) for n,b in scenario.fixtures.items()},
                    'oracle_note':scenario.oracle_note,'abi_expected':False,'runs':{}}
                if not info['compiled']:
                    row['errors']=[info.get('setup_error','compilation failed')];report['scenarios'][scenario.name]=row;continue
                processes={};snapshots={}
                for tag,executable in [('ours',Path(ours.output)),('reference',binary)]:
                    if tag=='reference' and not (oracle and info['oracle_compiled'] and scenario.oracle):continue
                    directory=build/'runs'/scenario.name/tag
                    directory.mkdir(parents=True)
                    assert not any(directory.iterdir())
                    for name,data in scenario.fixtures.items():
                        target=directory/name
                        if not target.resolve().is_relative_to(directory):raise ValueError('Fixture outside run directory')
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(data)
                    run={'directory':str(directory),'initial_files':{n:digest(b) for n,b in scenario.fixtures.items()},
                        'executable_sha256':digest(executable.read_bytes())}
                    row['runs'][tag]=run
                    try:
                        p=subprocess.run([str(executable)],input=scenario.stdin.encode('utf-8'),capture_output=True,
                            cwd=directory,env=environment(scenario.environment),timeout=8,preexec_fn=execution_limits)
                    except subprocess.TimeoutExpired as error:
                        row['errors'].append(tag+' timeout')
                        run.update(timeout=True,stdout=blob(error.stdout or b''),stderr=blob(error.stderr or b''));continue
                    snapshot={str(path.relative_to(directory)):path.read_bytes() for path in sorted(directory.rglob('*')) if path.is_file()}
                    processes[tag]=p;snapshots[tag]=snapshot
                    run.update(returncode=p.returncode,stdout=blob(p.stdout),stderr=blob(p.stderr),files={n:blob(b) for n,b in snapshot.items()})
                    if tag=='ours':
                        assert run['executable_sha256']==proof['artifact']['sha256']
                        row['executed']=True
                        row['errors']+=validate_scenario(scenario,p,directory)
                        row.update(returncode=p.returncode,stdout_sha256=digest(p.stdout),stdout_bytes=len(p.stdout),
                            stderr=p.stderr.decode(errors='replace'),files={n:{'bytes':len(b),'sha256':digest(b)} for n,b in snapshot.items()})
                if 'reference' in processes and 'ours' in processes:
                    row['oracle_compared']=True
                    row['differences']=differences(processes['ours'],processes['reference'],snapshots['ours'],snapshots['reference'])
                    row['oracle_match']=not row['differences']
                    row['abi_expected']=bool(row['differences'] and scenario.oracle_note
                        and scenario.stdout_exact is not None and scenario.reference_stdout_exact is not None
                        and processes['ours'].stdout==scenario.stdout_exact
                        and processes['reference'].stdout==scenario.reference_stdout_exact
                        and all(d['part']=='stdout' for d in row['differences']))
                row['validated']=row['executed'] and not row['errors']
                report['scenarios'][scenario.name]=row
        # Full bytes stay encoded. Human-readable paths are stable and still identify
        # separate programs/scenarios. No machine-specific temp path in checked-in logs.
        def portable(value):
            if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
            if isinstance(value,list):return [portable(v) for v in value]
            if isinstance(value,str):return value.replace(str(root),'$RUN').replace(str(ROOT),'$REPO')
            return value
        report=portable(report)
    report['summary']={'programs':len(report['programs']),
        'compiled':sum(p['compiled'] for p in report['programs'].values()),
        'executed_scenarios':sum(p['executed'] for p in report['scenarios'].values()),
        'validated_scenarios':sum(p['validated'] for p in report['scenarios'].values()),
        'oracle_compared':sum(p['oracle_compared'] for p in report['scenarios'].values()),
        'oracle_matched':sum(p['oracle_match'] is True for p in report['scenarios'].values())}
    return report
