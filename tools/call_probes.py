"""Isolated execution of the six original CALL cases, with explicit fixtures."""

import base64
import subprocess
from pathlib import Path

from tools.functional_execution import blob, digest, environment, execution_limits
from tools.terminal_probe import run_terminal


MISSING_CASES = {
    'CAD0001A': ('SORT001A', b'FIM\n', {'SEQENT01.dat': b''}),
    'main': ('exibir_tela', b'', {}),
    'ncurses_demo': ('ncurses_wrapper.c', b'', {}),
}
NATIVE_CASES = {
    'NCURSESDEMO': ('scanw', 'CALL_NATIVE_FORMAT'),
    'PROGTEST2': ('keypad', 'CALL_NATIVE_ARGUMENT'),
    'PROGTEST3': ('scanw', 'CALL_NATIVE_FORMAT'),
}


def capture(executable, root, stdin, fixtures):
    root.mkdir()
    for name, data in fixtures.items():
        (root/name).write_bytes(data)
    env = environment({'COB_LIBRARY_PATH':str(root), 'COBOL_MODULE_PATH':str(root)})
    try:
        proc = subprocess.run([executable], input=stdin, cwd=root, env=env, capture_output=True,
                              timeout=8, preexec_fn=execution_limits)
        result = {'returncode':proc.returncode, 'timeout':False, 'stdout':blob(proc.stdout),
                  'stderr':blob(proc.stderr), 'signal':-proc.returncode if proc.returncode<0 else None}
    except subprocess.TimeoutExpired as exc:
        result = {'returncode':None,'timeout':True,'stdout':blob(exc.stdout or b''),'stderr':blob(exc.stderr or b'')}
    result['files'] = {f.name:blob(f.read_bytes()) for f in root.iterdir() if f.is_file()}
    return result


def check_deferred(stem, native, reference, root):
    if stem in MISSING_CASES:
        target, stdin, fixtures = MISSING_CASES[stem]
        ours = capture(native, root/'call-ours', stdin, fixtures)
        ref = capture(reference, root/'call-gnu', stdin, fixtures)
        ours['executable_sha256'] = digest(Path(native).read_bytes())
        ref['executable_sha256'] = digest(Path(reference).read_bytes())
        expected = f"CALL_NOT_FOUND: CALL '{target}'".encode()
        original = base64.b64decode(ref['stderr']['base64'])
        previous_output = base64.b64decode(ours['stdout']['base64'])
        return {'status':'missing_at_runtime','target':target,'expected':'CALL_NOT_FOUND',
                'validated':ours['returncode']==ref['returncode']==1 and expected in base64.b64decode(ours['stderr']['base64'])
                    and target.lower().encode() in original.lower() and ours['files']==ref['files']
                    and (stem!='CAD0001A' or b'NOME' in previous_output.upper()),
                'stdout_equal':ours['stdout']==ref['stdout'],'fixtures':{n:blob(data) for n,data in fixtures.items()},
                'stdin':blob(stdin),'ours':ours,'reference':ref,
                'comparison':'same missing target and exit status, independent diagnostics'}
    target, code = NATIVE_CASES[stem]
    run_dir = root/'call-ours'
    run_dir.mkdir()
    ours = run_terminal(native,b'1\n2\nx\n',run_dir)
    ours['executable_sha256'] = digest(Path(native).read_bytes())
    ours['signal'] = -ours['returncode'] if ours['returncode']<0 else None
    expected = f"{code}: CALL '{target}'".encode()
    return {'status':'native_contract_rejected','target':target,'expected':code,
            'validated':ours['returncode']==1 and ours['terminal_restored'] and not ours['timeout']
                and expected in base64.b64decode(ours['stderr']['base64']),
            'ours':ours,'reference':None,
            'comparison':'compiled and linked with GnuCOBOL. Execution with invalid C arguments omitted.'}
