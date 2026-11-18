"""Oráculo independente opcional. Nenhum resultado deste módulo compõe o backend."""
from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from cobol_compiler.driver import compile_file
from tools.backend_scenarios import ROOT,SCENARIOS,CLOCK,inputs_for,validate_scenario


def digest(data):return hashlib.sha256(data).hexdigest()


def run_scenarios(*,reference=True):
    oracle=shutil.which('cobc') if reference else None
    report={'oracle':oracle is not None,'oracle_version':None,'programs':{},'scenarios':{}}
    if oracle:
        report['oracle_version']=subprocess.run([oracle,'-V'],capture_output=True,text=True).stdout.splitlines()[0]
    with tempfile.TemporaryDirectory(prefix='cobol-scenarios-') as build:
        build=Path(build)
        for program in sorted({s.program for s in SCENARIOS}):
            source,deps=inputs_for(program,build)
            ours=compile_file(source,build/(program+'-ours'),include_dirs=[ROOT/'examples/dependencias'],source_paths=deps)
            info={'generated_c':bool(ours.generated and ours.generated.success),'compiled':ours.success,
                  'diagnostics':[asdict(d) for d in ours.diagnostics], 'gcc_stderr':ours.gcc_stderr,
                  'oracle_compiled':False,'oracle_compile_stderr':''}
            binary=build/(program+'-reference')
            if oracle:
                command=[oracle,'-x','-fixed','-I',str(ROOT/'examples/dependencias'),str(source),*(str(p) for p in deps),'-o',str(binary)]
                reference_build=subprocess.run(command,capture_output=True,text=True,timeout=60)
                info['oracle_compiled']=reference_build.returncode==0
                info['oracle_compile_stderr']=reference_build.stderr
            report['programs'][program]=info
            for scenario in [s for s in SCENARIOS if s.program==program]:
                row={'program':program,'executed':False,'validated':False,'errors':[],
                     'oracle_compared':False,'oracle_match':None,'differences':[]}
                if not ours.success:
                    row['errors']=['compilation failed'];report['scenarios'][scenario.name]=row;continue
                processes=[];files=[]
                with tempfile.TemporaryDirectory() as run_root:
                    for tag,executable in [('ours',Path(ours.output)),('reference',binary)]:
                        if tag=='reference' and not (oracle and info['oracle_compiled'] and scenario.oracle):continue
                        directory=Path(run_root)/tag;directory.mkdir()
                        for name,data in scenario.fixtures.items():(directory/name).write_bytes(data)
                        environment={**os.environ,'COBOL_DATETIME':CLOCK,'COBOL_TERMINAL_ENCODING':'utf8','COB_CURRENT_DATE':'20261117123456',
                                     'COB_LS_FIXED':'Y','COB_LS_NULLS':'N','COB_LS_VALIDATE':'N'}
                        try:
                            p=subprocess.run([str(executable)],input=scenario.stdin.encode('utf-8'),capture_output=True,cwd=directory,env=environment,timeout=8)
                        except subprocess.TimeoutExpired:
                            row['errors'].append(tag+' timeout');continue
                        processes.append((tag,p))
                        snapshot={path.name:path.read_bytes() for path in sorted(directory.iterdir()) if path.is_file()}
                        files.append((tag,snapshot))
                        if tag=='ours':
                            row['executed']=True
                            row['errors']+=validate_scenario(scenario,p,directory)
                            row.update(returncode=p.returncode,stdout_sha256=digest(p.stdout),stdout_bytes=len(p.stdout),
                                stderr=p.stderr.decode(errors='replace'),files={n:{'bytes':len(b),'sha256':digest(b)} for n,b in snapshot.items()})
                            row['validated']=not row['errors']
                    results=dict(processes);snapshots=dict(files)
                    if 'reference' in results and 'ours' in results:
                        a,b=results['ours'],results['reference'];row['oracle_compared']=True
                        for key in ('stdout','stderr','returncode'):
                            x,y=getattr(a,key),getattr(b,key)
                            if x!=y:
                                if isinstance(x,bytes):
                                    first=next((i for i,(left,right) in enumerate(zip(x,y)) if left!=right),min(len(x),len(y)))
                                    row['differences'].append({'part':key,'first_byte':first,'ours':repr(x[max(0,first-30):first+100]),'reference':repr(y[max(0,first-30):first+100])})
                                else:row['differences'].append({'part':key,'ours':x,'reference':y})
                        for name in sorted(set(snapshots['ours'])|set(snapshots['reference'])):
                            if snapshots['ours'].get(name)!=snapshots['reference'].get(name):
                                row['differences'].append({'part':'file','name':name,'ours':repr(snapshots['ours'].get(name))[:250],'reference':repr(snapshots['reference'].get(name))[:250]})
                        row['oracle_match']=not row['differences']
                report['scenarios'][scenario.name]=row
    report['summary']={'programs':len(report['programs']),
        'compiled':sum(p['compiled'] for p in report['programs'].values()),
        'executed_scenarios':sum(p['executed'] for p in report['scenarios'].values()),
        'validated_scenarios':sum(p['validated'] for p in report['scenarios'].values()),
        'oracle_compared':sum(p['oracle_compared'] for p in report['scenarios'].values()),
        'oracle_matched':sum(p['oracle_match'] is True for p in report['scenarios'].values())}
    return report


if __name__=='__main__':
    import json
    result=run_scenarios()
    print(json.dumps(result['summary'],indent=2))
    for name,item in result['scenarios'].items():
        if item['errors'] or item['differences']:print(name,item['errors'],item['differences'])
    reference_failed=result['oracle'] and any(not p['oracle_compiled'] for p in result['programs'].values())
    raise SystemExit(int(reference_failed or any(not s['validated'] or s['oracle_match'] is False for s in result['scenarios'].values())))
