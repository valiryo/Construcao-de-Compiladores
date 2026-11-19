"""Comparações de encerramento da Etapa 8 nas lacunas de execução do corpus."""

import base64
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from tools.backend_scenarios import ROOT, SCENARIOS
from tools.call_probes import MISSING_CASES, NATIVE_CASES, capture, check_deferred
from tools.compatibility_corpus import closure, discover, gnu_build
from tools.functional_execution import blob, clean_compile, copy_sources, digest, environment
from tools.terminal_probe import run_terminal


# Linhas do primeiro CALL incompatível no snapshot, conferidas antes de rodar.
CUTS = {'NCURSESDEMO': 25, 'PROGTEST2': 17, 'PROGTEST3': 22}
GUARD = b'           CALL "endwin"\n           MOVE 77 TO RETURN-CODE\n           STOP RUN.\n'
NCURSES_INPUT = b'1\n2\nx\n'
DIVISION_CASE = 'calcmd-zero-divisor'


def safe_source(source, out, target, line):
    original = source.read_bytes()
    lines = original.splitlines(keepends=True)
    if not lines[line-1].lstrip().startswith(f'CALL "{target}" '.encode('ascii')):
        raise ValueError(f'Limite do ensaio não corresponde a {source.name}:{line}.')
    # Só o prefixo documentado é compilado. O CALL incompatível fica fora do binário.
    prefix = b''.join(lines[:line-1])
    out.parent.mkdir()
    out.write_bytes(prefix+GUARD)
    return {'line':line, 'target':target, 'original_sha256':digest(original),
            'prefix':blob(prefix), 'guard':blob(GUARD), 'derived_sha256':digest(out.read_bytes())}


def compare(ours, reference):
    return {part:ours[part]==reference[part] for part in ('stdout','stderr','files','returncode')}


def terminal_run(executable, directory):
    directory.mkdir()
    result = run_terminal(executable, NCURSES_INPUT, directory)
    result.update(executable_sha256=digest(Path(executable).read_bytes()),
                  signal=-result['returncode'] if result['returncode']<0 else None,
                  files={str(p.relative_to(directory)):blob(p.read_bytes())
                         for p in sorted(directory.rglob('*')) if p.is_file()})
    return result


def compare_safe_prefix(stem, source, deps, include, work):
    target, _ = NATIVE_CASES[stem]
    derived = work/'guarded-source'/source.name
    cutoff = safe_source(source, derived, target, CUTS[stem])
    ours, proof = clean_compile(derived,deps,include,work/'guarded-ours',
                                compiler_options={'dialect':'gnucobol','libraries':['ncurses']})
    ref = gnu_build(derived,deps,include,work/'guarded-gnu',fmt='fixed',module=False,strict=True,
                    libraries=('-l:libncurses.so.6','-l:libtinfo.so.6'))
    original, original_proof = clean_compile(source,deps,include,work/'original-ours',
                            compiler_options={'dialect':'gnucobol','libraries':['ncurses']})
    result = {'scenario':stem, 'scope':'safe_prefix', 'cutoff':cutoff, 'stdin':blob(NCURSES_INPUT),
              'fixtures':{}, 'builds':{'ours':proof,'reference':ref,'original_ours':original_proof}, 'validated':False,
              'unverified':'CALL interrompido e tudo que o segue no original GnuCOBOL.'}
    if not ours.success or not original.success or not ref['compiled']:
        return result
    left = terminal_run(ours.output, work/'guarded-run-ours')
    right = terminal_run(ref['artifact'], work/'guarded-run-gnu')
    original_run = terminal_run(original.output, work/'original-run-ours')
    reason = f"{NATIVE_CASES[stem][1]}: CALL '{target}'".encode('ascii')
    original_valid = (original_run['returncode']==1 and original_run['terminal_restored']
                      and not original_run['timeout']
                      and reason in base64.b64decode(original_run['stderr']['base64']))
    result.update(ours=left,reference=right,comparison=compare(left,right),
                  original_ours=original_run,
                  original_ours_stdout_equal=original_run['stdout']==left['stdout'],
                  validated=original_valid and all(r['returncode']==77 and r['terminal_restored']
                                                  and not r['timeout'] for r in (left,right)))
    return result


def compare_original(stem, source, deps, include, work):
    ours, proof = clean_compile(source,deps,include,work/'ours',compiler_options={'dialect':'gnucobol'})
    ref = gnu_build(source,deps,include,work/'gnu',fmt='fixed',module=False)
    result = {'scenario':stem, 'scope':'missing_target' if stem in MISSING_CASES else 'zero_divisor',
              'builds':{'ours':proof,'reference':ref},'validated':False}
    if not ours.success or not ref['compiled']:
        return result
    if stem in MISSING_CASES:
        probe = check_deferred(stem,ours.output,ref['artifact'],work)
        result.update({key:probe[key] for key in ('ours','reference','validated','stdin','fixtures','target')})
        result['unverified'] = 'Execução com a implementação externa disponível.'
    else:
        fixture = next(s for s in SCENARIOS if s.name==DIVISION_CASE)
        stdin = fixture.stdin.encode('utf-8')
        left = capture(ours.output, work/'run-ours', stdin, fixture.fixtures)
        right = capture(ref['artifact'], work/'run-gnu', stdin, fixture.fixtures)
        left['executable_sha256'] = proof['artifact']['sha256']
        right['executable_sha256'] = ref['artifact_sha256']
        result.update(scenario=fixture.name, ours=left, reference=right, stdin=blob(stdin),
                      fixtures={n:blob(data) for n,data in fixture.fixtures.items()},
                      validated=left['returncode']==fixture.returncode and
                          fixture.stderr_contains.encode() in base64.b64decode(left['stderr']['base64'])
                          and right['returncode'] is not None and right['returncode']>=0,
                      stdout_prefix=base64.b64decode(right['stdout']['base64']).startswith(
                          base64.b64decode(left['stdout']['base64'])))
    result['comparison'] = compare(result['ours'],result['reference'])
    return result


def audit_execution_gaps():
    cobc = shutil.which('cobc')
    if not cobc:
        raise RuntimeError('Esta comparação requer GnuCOBOL instalado.')
    version = subprocess.run([cobc,'-V'],capture_output=True,text=True,timeout=10,check=True).stdout.splitlines()[0]
    entries, manifest, fronts, index = discover()
    selected = {Path(e['path']).stem:e for e in entries
                if Path(e['path']).stem in {*MISSING_CASES,*NATIVE_CASES,'CALCMD01'}}
    if set(selected)!={*MISSING_CASES,*NATIVE_CASES,'CALCMD01'}:
        raise ValueError('Inventário de lacunas incompatível com o snapshot.')
    results = {}
    with TemporaryDirectory(prefix='cobol-execution-gaps-') as directory:
        root = Path(directory)
        for stem, entry in sorted(selected.items()):
            path = entry['path']
            source = ROOT/path
            if digest(source.read_bytes())!=entry['sha256']:
                raise ValueError(f'Original diverge do manifesto: {path}.')
            work = root/stem
            work.mkdir()
            deps, _ = closure(path,fronts,index)
            copied, dep_paths, include, hashes, _ = copy_sources(
                source,[ROOT/p for p in deps],work/'sources',frontend_options={'dialect':'gnucobol'})
            runner = compare_safe_prefix if stem in NATIVE_CASES else compare_original
            results[stem] = runner(stem,copied,dep_paths,include,work)
            results[stem].update(source=path,source_sha256=entry['sha256'],sources=hashes)
            if digest(source.read_bytes())!=entry['sha256']:
                raise ValueError(f'Original modificado durante a comparação: {path}.')

        def portable(value):
            if isinstance(value,dict):
                return {k:portable(v) for k,v in value.items()}
            if isinstance(value,list):
                return [portable(v) for v in value]
            if isinstance(value,str):
                return value.replace(str(root),'$GAPS').replace(str(ROOT),'$REPO')
            return value

        env = environment()
        return {'snapshot':manifest['commit'], 'gnucobol':version, 'excluded':['GAMESNAK'],
                'execution_environment':{k:v for k,v in env.items() if k not in {'PATH','SYSTEMROOT','TMPDIR'}},
                'cases':portable(results),'success':all(r['validated'] for r in results.values())}
