"""Arquivos, chamadas disponíveis/externas e integração da CLI."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cobol_compiler import parse_source, analyze, check_source, check_file
from cobol_compiler import ast as A
from test_semantic import unit
from test_parser import program

ROOT=Path(__file__).resolve().parents[1]


def file_program(body, *, select=None, files=None, data=()):
    return unit(environment=('INPUT-OUTPUT SECTION.','FILE-CONTROL.',*(select or (
        'SELECT FILE-A ASSIGN TO "input.dat"', 'ORGANIZATION IS LINE SEQUENTIAL FILE STATUS FS.'))),
        files=files or ('FD FILE-A.','01 RECORD-A.','05 TEXT-A PIC X(4).'),
        data=('01 FS PIC XX.',*data),body=body)


class BindingTests(unittest.TestCase):
    def test_select_fd_status_and_io_operations(self):
        r=check_source(file_program(('OPEN INPUT FILE-A','READ FILE-A INTO DEST-A AT END CONTINUE',
            'NOT AT END DISPLAY DEST-A END-READ','CLOSE FILE-A.'),data=('01 DEST-A PIC X(4).',)))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        info=next(iter(r.files.values()))
        self.assertEqual(info['organization'],'LINE SEQUENTIAL')
        self.assertEqual(info['record_lengths'],[4])
        self.assertEqual(info['open_modes'],['INPUT'])
        status=r.table.symbols[info['status_symbol']]
        self.assertEqual(status.name,'FS')
        read=next(n for n in A.walk(r.ast) if isinstance(n,A.Read))
        self.assertEqual(r.annotation(read).details['file_id'],next(iter(r.files)))
        self.assertEqual(r.annotation(read).conversions[0]['target_type']['length'],4)

    def test_missing_select_fd_and_undefined_file(self):
        cases=[('MISSING_SELECT',unit(files=('FD FILE-A.','01 RECORD-A PIC X.',))),
            ('MISSING_FD',unit(environment=('INPUT-OUTPUT SECTION.','FILE-CONTROL.','SELECT FILE-A ASSIGN "x".'))),
            ('UNDEFINED_SYMBOL',program('OPEN INPUT FILE-A.'))]
        for code,text in cases:
            with self.subTest(code=code):
                r=check_source(text)
                self.assertFalse(r.success)
                self.assertIn(code,[d.code for d in r.diagnostics])

    def test_invalid_status_and_mode(self):
        text=file_program(('OPEN OUTPUT FILE-A','READ FILE-A END-READ.'),select=('SELECT FILE-A ASSIGN "x" FILE STATUS FS.',))
        r=check_source(text.replace('PIC XX.','PIC X(3).'))
        self.assertIn('INVALID_FILE_STATUS',[d.code for d in r.diagnostics])
        self.assertIn('INVALID_FILE_MODE',[d.code for d in r.diagnostics])

    def test_write_requires_fd_root_and_output_mode(self):
        r=check_source(file_program(('OPEN INPUT FILE-A','WRITE RECORD-A.')))
        self.assertIn('INVALID_FILE_MODE',[d.code for d in r.diagnostics])
        r=check_source(file_program(('WRITE TEXT-A.',)))
        self.assertIn('WRITE_NOT_RECORD',[d.code for d in r.diagnostics])

    def test_write_from_and_handler_incompatibility(self):
        r=check_source(file_program(('OPEN OUTPUT FILE-A','WRITE RECORD-A FROM "ABCD"',
            'CLOSE FILE-A.')))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        r=check_source(file_program(('READ FILE-A INVALID KEY CONTINUE END-READ.',)))
        self.assertIn('INVALID_FILE_HANDLER',[d.code for d in r.diagnostics])

    def test_record_contains_size_checked(self):
        r=check_source(file_program(('STOP RUN.',),files=('FD FILE-A RECORD CONTAINS 8 CHARACTERS.','01 RECORD-A PIC X(4).')))
        self.assertIn('RECORD_SIZE_MISMATCH',[d.code for d in r.diagnostics])

    def test_multiple_fd_records_share_storage(self):
        r=check_source(file_program(('STOP RUN.',),files=('FD FILE-A.','01 SHORT-A PIC X(4).','01 LONG-A PIC X(7).')))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        info=next(iter(r.files.values()))
        layouts=[r.layout.items[sid] for sid in info['records']]
        self.assertEqual([s.offset for s in layouts],[0,0])
        self.assertEqual(r.layout.areas[layouts[0].area],7)

    def test_external_assign_identifier_is_not_undefined_data(self):
        r=check_source(file_program(('STOP RUN.',),select=('SELECT FILE-A ASSIGN DISK-FILE.',)))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        target=next(n.target for n in A.walk(r.ast) if isinstance(n,A.AssignClause))
        self.assertEqual(r.annotation(target).role,'external-assignment-name')

    def test_indexed_file_reports_limit_and_checks_key(self):
        r=check_source(file_program(('STOP RUN.',),select=(
            'SELECT FILE-A ASSIGN "x" ORGANIZATION INDEXED','RECORD KEY TEXT-A FILE STATUS FS.')))
        self.assertFalse(r.success)
        self.assertIn('UNSUPPORTED_FILE_ORGANIZATION',[d.code for d in r.diagnostics])
        self.assertEqual(len(next(iter(r.files.values()))['keys']),1)

    def callee(self, *, data=('01 ARG-A PIC X(4).',), using=' USING ARG-A', body=('GOBACK.',)):
        r=parse_source(unit(name='SUB-A',linkage=data,using=using,body=body),filename='sub.cbl')
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        return r

    def caller(self, *, body=('CALL "SUB-A" USING ARG-A.',), data=('01 ARG-A PIC X(4).',), callee=None):
        return check_source(unit(name='MAIN-A',data=data,body=body),sources=[callee or self.callee()])

    def test_call_resolves_formal_and_actual_layouts(self):
        r=self.caller()
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        self.assertTrue(r.backend_ready)
        info=next(iter(r.calls.values()))
        self.assertEqual(info['status'],'resolved')
        self.assertEqual(info['parameter_bindings'][0]['formal_type']['length'],4)
        self.assertEqual(len(r.source_results),1)
        self.assertEqual(r.source_results[0].parameters[0]['layout']['initial']['policy'],'external')

    def test_call_layout_and_arity_mismatch(self):
        r=self.caller(data=('01 ARG-A PIC X(3).',))
        self.assertIn('CALL_LAYOUT_MISMATCH',[d.code for d in r.diagnostics])
        r=self.caller(body=('CALL "SUB-A".',))
        self.assertIn('CALL_ARITY',[d.code for d in r.diagnostics])

    def test_call_same_size_numeric_scale_mismatch(self):
        r=self.caller(data=('01 ARG-A PIC 9(4).',),callee=self.callee(data=('01 ARG-A PIC 99V99.',)))
        self.assertIn('CALL_LAYOUT_MISMATCH',[d.code for d in r.diagnostics])

    def test_unresolved_external_and_dynamic_call_preserve_metadata(self):
        r=check_source(program('CALL "external" USING FIELD-A.',data=('01 FIELD-A PIC X(4).',)))
        self.assertTrue(r.success)
        self.assertFalse(r.backend_ready)
        self.assertEqual(r.pending_externals[0]['name'],'EXTERNAL')
        self.assertEqual(r.diagnostics[0].severity,'I')
        r=check_source(program('CALL FIELD-A USING FIELD-A.',data=('01 FIELD-A PIC X(4).',)))
        self.assertTrue(r.success)
        self.assertEqual(r.pending_externals[0]['status'],'dynamic')

    def test_external_literal_by_reference_uses_temporary(self):
        r=check_source(program('CALL "printw" USING "hello".'))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        self.assertTrue(r.pending_externals[0]['arguments'][0]['temporary'])

    def test_invalid_callee_blocks_caller_and_preserves_dependency_results(self):
        r=self.caller(callee=self.callee(body=('DISPLAY MISSING.',)))
        self.assertFalse(r.success)
        self.assertIn('INVALID_CALLEE',[d.code for d in r.diagnostics])
        self.assertIn('UNDEFINED_SYMBOL',[d.code for d in r.source_results[0].diagnostics])

    def test_external_dependency_propagates_transitively(self):
        r=self.caller(callee=self.callee(body=('CALL "external".','GOBACK.')))
        self.assertTrue(r.success)
        self.assertFalse(r.backend_ready)
        self.assertEqual(next(iter(r.calls.values()))['pending_dependencies'],['EXTERNAL'])

    def test_duplicate_program_definitions_are_ambiguous_at_call(self):
        r=check_source(program('CALL "SUB-A".'),sources=[self.callee(),self.callee()])
        self.assertIn('AMBIGUOUS_PROGRAM',[d.code for d in r.diagnostics])

    def test_copy_origin_on_semantic_error(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            (path/'FIELDS.cpy').write_text('       01 NUM-A PIC 9 VALUE 100.\n')
            (path/'main.cbl').write_text(unit(data=('COPY FIELDS.',)))
            r=check_file(path/'main.cbl')
            diagnostic=next(d for d in r.diagnostics if d.code=='VALUE_OUT_OF_RANGE')
            self.assertEqual(Path(diagnostic.span.start.file).name,'FIELDS.cpy')
            self.assertEqual(len(diagnostic.span.start.inclusion_stack),1)
            self.assertIn('incluído de',diagnostic.format())

    def test_cli_check_and_json_layout(self):
        command=[sys.executable,'-m','cobol_compiler','examples/oficiais/CALCMD01.cbl']
        result=subprocess.run([*command,'--check'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Semântica válida',result.stdout)
        result=subprocess.run([*command,'--dump-layout'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        payload=json.loads(result.stdout)
        self.assertEqual(payload['areas']['WORKING-STORAGE'],41)
        self.assertTrue(payload['success'])

    def test_cli_syntax_remains_independent_and_partial_dump_is_marked_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'main.cbl'
            path.write_text(program('DISPLAY MISSING.'))
            command=[sys.executable,'-m','cobol_compiler',str(path)]
            syntax=subprocess.run([*command,'--check-syntax'],cwd=ROOT,text=True,capture_output=True)
            semantic=subprocess.run([*command,'--dump-symbols'],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(syntax.returncode,0,syntax.stderr)
            self.assertEqual(semantic.returncode,1)
            self.assertFalse(json.loads(semantic.stdout)['success'])
            self.assertIn('UNDEFINED_SYMBOL',semantic.stderr)

    def test_cli_explicit_source_resolves_progdata(self):
        result=subprocess.run([sys.executable,'-m','cobol_compiler','examples/oficiais/PROG024A.cbl',
            '-I','examples/dependencias','--source','examples/dependencias/PROGDATA.cbl','--dump-symbols'],
            cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        payload=json.loads(result.stdout)
        self.assertTrue(payload['backend_ready'])
        self.assertEqual(next(iter(payload['calls'].values()))['status'],'resolved')

    def test_same_size_groups_with_different_abi_are_rejected(self):
        r=self.caller(data=('01 ARG-A.','05 TEXT-A PIC X(4).'),
            callee=self.callee(data=('01 ARG-A.','05 NUM-A PIC 9(4).')))
        self.assertFalse(r.success)
        self.assertIn('CALL_LAYOUT_MISMATCH',[d.code for d in r.diagnostics])

    def test_differently_named_groups_with_same_abi_match(self):
        r=self.caller(data=('01 ARG-A.','05 TEXT-A PIC X(4).'),
            callee=self.callee(data=('01 ARG-A.','05 OTHER-NAME PIC X(4).')))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        r=self.caller(body=('CALL "SUB-A" USING VIEW-A.',),
            data=('01 ARG-A PIC X(4).','01 VIEW-A REDEFINES ARG-A.','05 TEXT-A PIC X(4).'),
            callee=self.callee(data=('01 ARG-A.','05 OTHER-NAME PIC X(4).')))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])

    def test_table_occurrence_argument_matches_scalar_formal(self):
        r=self.caller(body=('CALL "SUB-A" USING ARG-A(2).',),
            data=('01 ARG-A OCCURS 3.','05 TEXT-A PIC X(4).'),
            callee=self.callee(data=('01 ARG-A.','05 TEXT-A PIC X(4).')))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])

    def test_invalid_additional_source_is_reported(self):
        invalid=parse_source('')
        r=analyze(parse_source(program('STOP RUN.')),sources=[invalid])
        self.assertFalse(r.success)
        self.assertIn('SYNTAX_ERROR',[d.code for d in r.diagnostics])
