"""Perfis explícitos, contratos numéricos e execução dos cinco originais ampliados."""
import base64
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import termios
import time
import unittest

from cobol_lexer.scanner import CobolLexer
from cobol_compiler import ast as A
from cobol_compiler.frontend import parse_source
from cobol_compiler.semantic import check_source
from cobol_compiler.types import parse_picture,PictureError
from cobol_compiler.driver import compile_file
from tools.backend_scenarios import ROOT
from tools.compatibility_corpus import sources
from tools.compatibility_scenarios import run_batch,run_screens
from tools.functional_execution import environment,digest
from tools.terminal_probe import cells,run_terminal


def source(data='',body='STOP RUN.',environment=''):
    return f'IDENTIFICATION DIVISION.\nPROGRAM-ID. PROBE.\n{environment}\nDATA DIVISION.\n{data}\nPROCEDURE DIVISION.\n{body}\n'


def check(text):return check_source(text,source_format='free',dialect='gnucobol')
def codes(result):return {d.code for d in result.diagnostics}


class CompatibilityFrontendTests(unittest.TestCase):
    def test_project_identifier_limit_is_preserved(self):
        text=source('WORKING-STORAGE SECTION.\n01 '+('L'*31)+' PIC X.')
        self.assertIn('IDENTIFIER_TOO_LONG',codes(parse_source(text,source_format='free')))
        self.assertTrue(check(text).success)

    def test_gnu_identifier_limit_63_rejects_64(self):
        for n,valid in [(63,True),(64,False)]:
            with self.subTest(n=n):self.assertEqual(check(source('WORKING-STORAGE SECTION.\n01 '+('L'*n)+' PIC X.')).success,valid)

    def test_free_columns_beyond_72_are_not_truncated(self):
        result=parse_source(source(body=' '*80+'DISPLAY "OK". STOP RUN.'),source_format='free',dialect='gnucobol')
        self.assertTrue(result.success,result.diagnostics)
        node=next(n for n in A.walk(result.ast) if isinstance(n,A.Display))
        self.assertEqual(node.span.start.column,81)

    def test_free_inline_comment_and_literal_comment_marker(self):
        result=parse_source(source(body='DISPLAY "*> keep" *> comment\nSTOP RUN.'),source_format='free')
        self.assertTrue(result.success,result.diagnostics)
        self.assertTrue(any(isinstance(n,A.Literal) and n.value=='*> keep' for n in A.walk(result.ast)))

    def test_free_copy_preserves_column_and_physical_origin(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);(path/'part.cpy').write_text('01 COPIED PIC X.\n')
            result=parse_source(source('WORKING-STORAGE SECTION.\nCOPY part.'),filename=str(path/'root.cbl'),include_dirs=[path],source_format='free')
            self.assertTrue(result.success,result.diagnostics)
            node=next(n for n in A.walk(result.ast) if isinstance(n,A.DataItem))
            self.assertEqual((Path(node.span.start.file).name,node.span.start.column),('part.cpy',1))

    def test_free_copy_cycle_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);(path/'loop.cpy').write_text('COPY loop.\n')
            result=parse_source(source('WORKING-STORAGE SECTION.\nCOPY loop.'),filename=str(path/'root.cbl'),include_dirs=[path],source_format='free')
            self.assertFalse(result.success)
            self.assertTrue(any('CYCLE' in c for c in codes(result)))

    def test_conflict_markers_are_never_repaired(self):
        result=parse_source(source(body='<<<<<<< HEAD\nSTOP RUN.'),source_format='free',dialect='gnucobol')
        self.assertFalse(result.success)

    def test_data_records_are_typed_and_bound_to_own_fd(self):
        env="ENVIRONMENT DIVISION. INPUT-OUTPUT SECTION. FILE-CONTROL. SELECT INPUT-FILE ASSIGN TO 'in'."
        text=source('FILE SECTION. FD INPUT-FILE RECORD CONTAINS 2 CHARACTERS DATA RECORDS ARE REC.\n01 REC PIC XX.',environment=env)
        result=check(text);self.assertTrue(result.success,result.diagnostics)
        clause=next(n for n in A.walk(result.ast) if isinstance(n,A.DataRecordsClause))
        self.assertEqual(clause.records[0].name,'REC')
        self.assertIsNotNone(result.annotation(clause.records[0]).symbol_id)

    def test_data_record_outside_fd_is_error(self):
        env="ENVIRONMENT DIVISION. INPUT-OUTPUT SECTION. FILE-CONTROL. SELECT INPUT-FILE ASSIGN TO 'in'."
        result=check(source('FILE SECTION. FD INPUT-FILE DATA RECORD IS WRONG-REC.\n01 REC PIC XX.\nWORKING-STORAGE SECTION.\n01 WRONG-REC PIC XX.',environment=env))
        self.assertIn('INVALID_DATA_RECORD',codes(result))

    def test_screen_using_requires_writable_declared_target(self):
        self.assertFalse(check(source('SCREEN SECTION.\n01 PANEL.\n05 PIC XX USING MISSING.',body='ACCEPT PANEL. STOP RUN.')).success)

    def test_screen_using_requires_picture(self):
        result=check(source('WORKING-STORAGE SECTION.\n01 RECEIVER PIC XX.\nSCREEN SECTION.\n01 PANEL.\n05 USING RECEIVER.',body='ACCEPT PANEL. STOP RUN.'))
        self.assertIn('SCREEN_PICTURE_REQUIRED',codes(result))

    def test_screen_signed_or_scaled_picture_is_explicitly_unsupported(self):
        for pic in ['S99','9V9','ZZ9']:
            result=check(source(f'WORKING-STORAGE SECTION.\n01 RECEIVER PIC {pic}.\nSCREEN SECTION.\n01 PANEL.\n05 PIC {pic} USING RECEIVER.',body='ACCEPT PANEL. STOP RUN.'))
            self.assertFalse(result.success)
            self.assertTrue(any('SCREEN_PICTURE' in c for c in codes(result)))

    def test_cursor_and_status_contracts(self):
        for setting,pic,code in [('CURSOR','99','INVALID_CURSOR_FIELD'),('CRT STATUS','X(4)','INVALID_CRT_STATUS')]:
            result=check(source(f'WORKING-STORAGE SECTION.\n01 KEY-FIELD PIC {pic}.',environment=f'ENVIRONMENT DIVISION. CONFIGURATION SECTION. SPECIAL-NAMES. {setting} IS KEY-FIELD.'))
            self.assertIn(code,codes(result))

    def test_floating_picture_layout(self):
        t=parse_picture('----,--9.99',allow_floating=True)
        self.assertEqual((t.length,t.precision,t.scale),(11,8,2))

    def test_floating_unsupported_combinations(self):
        for pic,usage in [('---ZZ9','DISPLAY'),('---+9','DISPLAY'),('---$9','DISPLAY'),('---9','COMP'),('---9','COMP-3'),('9--9','DISPLAY')]:
            with self.subTest(pic=pic,usage=usage),self.assertRaises(PictureError):parse_picture(pic,usage,allow_floating=True)

    def test_default_profile_still_rejects_floating(self):
        with self.assertRaises(PictureError):parse_picture('----,--9.99')


class CompatibilityExecutableTests(unittest.TestCase):
    def compile(self,text,directory):
        path=directory/'probe.cbl';path.write_text(text)
        result=compile_file(path,directory/'probe',source_format='free',dialect='gnucobol')
        self.assertTrue(result.success,result.diagnostics)
        return Path(result.output),path

    def test_floating_plus_minus_zero_max_and_deediting(self):
        body=[];expected=b''
        for mask in ['----,--9.99','++++,++9.99']:
            for value in [0,123456,-123456,99999999,-99999999]:
                text=f'{value//100}.{abs(value)%100:02}' if value>=0 else f'-{abs(value)//100}.{abs(value)%100:02}'
                body += [f'MOVE {text} TO EDITED. DISPLAY "[" EDITED "]".', 'MOVE EDITED TO BACK-NUM. DISPLAY BACK-NUM.']
                amount=f'{abs(value)//100:,}.{abs(value)%100:02}'
                amount=('-' if value<0 else '+' if mask[0]=='+' else '')+amount
                expected+=('['+amount.rjust(11)+']\n'+('+' if value>=0 else '-')+f'{abs(value)//100:06}.{abs(value)%100:02}\n').encode()
            # Separate masks, same exact expected and reference comparisons.
            with tempfile.TemporaryDirectory() as td:
                directory=Path(td)
                exe,path=self.compile(source(f'WORKING-STORAGE SECTION.\n01 EDITED PIC {mask}.\n01 BACK-NUM PIC S9(6)V99.',body='\n'.join(body)+'\nSTOP RUN.'),directory)
                ours=subprocess.run([exe],capture_output=True,env=environment(),timeout=5)
                self.assertEqual(ours.returncode,0,ours.stderr);self.assertEqual(ours.stdout,expected)
                if shutil.which('cobc'):
                    build=subprocess.run(['cobc','-free','-x',str(path),'-o',str(directory/'reference')],capture_output=True)
                    self.assertEqual(build.returncode,0,build.stderr)
                    ref=subprocess.run([directory/'reference'],capture_output=True,env=environment(),timeout=5)
                    self.assertEqual(ref.stdout,expected)
            body=[];expected=b''

    def test_terminal_operation_requires_tty(self):
        with tempfile.TemporaryDirectory() as td:
            exe,_=self.compile(source(body='DISPLAY "X" AT LINE 2 COLUMN 3. STOP RUN.'),Path(td))
            run=subprocess.run([exe],capture_output=True,timeout=5)
            self.assertEqual(run.returncode,1);self.assertIn(b'TERMINAL_REQUIRED',run.stderr)

    def test_terminal_bounds_checked_at_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            exe,_=self.compile(source(body='DISPLAY "X" AT LINE 99 COLUMN 3. STOP RUN.'),Path(td))
            run=run_terminal(exe,b'',td)
            self.assertEqual(run['returncode'],1)
            self.assertIn(b'SCREEN_BOUNDS',base64.b64decode(run['stderr']['base64']))

    def test_positioned_accept_unsupported_numeric_forms_block_before_gcc(self):
        for pic in ['S99','9V9','ZZ9','9(5) COMP']:
            with self.subTest(pic=pic),tempfile.TemporaryDirectory() as td:
                directory=Path(td);path=directory/'probe.cbl'
                path.write_text(source(f'WORKING-STORAGE SECTION.\n01 ANSWER PIC {pic}.',body='ACCEPT ANSWER AT LINE 2 COLUMN 3. STOP RUN.'))
                result=compile_file(path,directory/'probe',source_format='free',dialect='gnucobol')
                self.assertFalse(result.success)
                self.assertIn('UNSUPPORTED_BACKEND_SCREEN_PICTURE',codes(result))
                self.assertFalse(result.command)

    def test_signal_restores_terminal(self):
        with tempfile.TemporaryDirectory() as td:
            exe,_=self.compile(source('WORKING-STORAGE SECTION.\n01 ANSWER PIC XX.',body='ACCEPT ANSWER AT LINE 2 COLUMN 3. STOP RUN.'),Path(td))
            master,slave=pty.openpty()
            try:
                before=termios.tcgetattr(slave)
                process=subprocess.Popen([exe],stdin=slave,stdout=slave,stderr=subprocess.PIPE,env=environment())
                deadline=time.monotonic()+3
                while time.monotonic()<deadline and termios.tcgetattr(slave)[3]&termios.ICANON:
                    select.select([master],[],[],.02)
                    if select.select([master],[],[],0)[0]:os.read(master,65536)
                self.assertFalse(termios.tcgetattr(slave)[3]&termios.ICANON)
                process.send_signal(signal.SIGTERM);process.wait(timeout=3)
                self.assertEqual(process.returncode,-signal.SIGTERM)
                self.assertEqual(termios.tcgetattr(slave)[3],before[3])
                process.stderr.close()
            finally:
                if process.poll() is None:process.kill();process.wait()
                os.close(master);os.close(slave)


class CompatibilityOriginalBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=run_batch()

    def test_cbreak_full_original_empty(self):self.verify('compat-cbreak-empty')
    def test_cbreak_full_original_control_breaks_signed_and_zero(self):self.verify('compat-cbreak-breaks-signed-zero')
    def test_order_full_original_create_and_call(self):self.verify('compat-order-create')
    def test_order_full_original_append_and_call(self):self.verify('compat-order-append')
    def test_order_full_original_unknown_client(self):self.verify('compat-order-missing-client')
    def test_order_full_original_unknown_product(self):self.verify('compat-order-missing-product')
    def test_order_full_original_invalid_quantity(self):self.verify('compat-order-zero-quantity')

    def verify(self,name):
        row=self.report['scenarios'][name]
        self.assertTrue(row['validated'],row['errors'])
        if self.report['oracle']:self.assertTrue(row['oracle_match'],row['differences'])


class CompatibilityOriginalScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=run_screens()

    def test_screen_full_original_backspace_tab_partial_numeric(self):self.verify('screen-edit')
    def test_screen_full_original_maximum_name(self):self.verify('screen-full')
    def test_screen_full_original_zero(self):self.verify('screen-zero')
    def test_status_position_full_original(self):self.verify('position-status')
    def test_game_full_original_quits_with_partial_comparison(self):
        self.verify('game-quit');self.assertFalse(self.report['scenarios']['game-quit']['fully_compared'])

    def verify(self,name):
        if not shutil.which('cobc'):self.skipTest('GnuCOBOL absent')
        row=self.report['scenarios'][name];self.assertTrue(row['validated'],row['errors'])


class CompatibilityAuditTests(unittest.TestCase):
    def test_compiler_temporary_files_are_isolated_across_concurrent_builds(self):
        from tools.functional_execution import command
        script='import os,sys,time; from pathlib import Path; p=Path(os.environ["TMPDIR"])/"cob-fixed.o"; p.write_text(sys.argv[1]); time.sleep(.1); print(p.read_text())'
        with tempfile.TemporaryDirectory() as td:
            directories=[Path(td)/name for name in ['first','second']]
            for d in directories:d.mkdir()
            with ThreadPoolExecutor(2) as pool:
                futures=[pool.submit(command,[sys.executable,'-c',script,d.name],d) for d in directories]
                results=[f.result() for f in futures]
            self.assertEqual([r['returncode'] for r in results],[0,0])
            self.assertEqual([r['stdout'] for r in results],['first\n','second\n'])
            self.assertFalse((Path(td)/'cob-fixed.o').exists())

    def test_all_original_hashes_and_derivative_exclusion(self):
        entries,_=sources();self.assertEqual(len(entries),85)
        self.assertNotIn('examples/corrigidos/CAD0005A.cbl',{e['path'] for e in entries})
        for e in entries:self.assertEqual(digest((ROOT/e['path']).read_bytes()),e['sha256'])

    def test_terminal_renderer_preserves_padding_and_rejects_unknown_control(self):
        self.assertEqual(cells(b'\x1b[2;3HX',3,5),['     ','  X  ','     '])
        with self.assertRaises(ValueError):cells(b'\x1b[999z')
