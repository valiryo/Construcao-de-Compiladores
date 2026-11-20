"""Contratos executáveis pequenos, independentes dos programas oficiais."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from cobol_compiler.driver import compile_file,RUNTIME,RUNTIME_SOURCES,ROOT
from cobol_compiler.c_codegen import function_name
from test_semantic import unit
from test_lexer import fixed


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.directory=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def build(self,text,*,sources=(),**options):
        path=self.directory/'main.cbl';path.write_text(text)
        deps=[]
        for i,source in enumerate(sources):
            dep=self.directory/f'sub{i}.cbl';dep.write_text(source);deps.append(dep)
        result=compile_file(path,self.directory/'program',source_paths=deps,**options)
        self.assertTrue(result.success,'\n'.join(d.format() for d in result.diagnostics)+'\n'+result.gcc_stderr)
        self.assertEqual(result.gcc_stderr,'')
        return result

    def run_program(self,text,stdin='',*,sources=(),fixtures=None,**options):
        result=self.build(text,sources=sources,**options)
        for name,data in (fixtures or {}).items():(self.directory/name).write_bytes(data)
        process=subprocess.run([result.output],input=stdin.encode(),capture_output=True,cwd=self.directory,
            env={**os.environ,'COBOL_DATETIME':'2024-02-29T12:34:56'},timeout=4)
        return process

    def good(self,text,expected,stdin='',**kwargs):
        result=self.run_program(text,stdin,**kwargs)
        self.assertEqual(result.returncode,0,result.stderr.decode())
        self.assertEqual(result.stderr,b'')
        self.assertEqual(result.stdout,expected.encode())
        return result

    def test_fallthrough_between_paragraphs(self):
        self.good(unit(body=('A-PARA.','DISPLAY "A".','B-PARA.','DISPLAY "B".','STOP RUN.')),'A\nB\n')

    def test_perform_paragraph_returns_before_next_paragraph(self):
        self.good(unit(body=('PERFORM A-PARA','DISPLAY "DONE" STOP RUN.',
            'A-PARA.','DISPLAY "A".','B-PARA.','DISPLAY "BAD".')),'A\nDONE\n')

    def test_perform_section_includes_its_paragraphs(self):
        self.good(unit(body=('PERFORM A-SECTION','DISPLAY "DONE" STOP RUN.',
            'A-SECTION SECTION.','A-PARA.','DISPLAY "A".',
            'B-PARA.','DISPLAY "B".','B-SECTION SECTION.','DISPLAY "BAD".')),'A\nB\nDONE\n')

    def test_nested_perform_and_goto_to_end_of_section(self):
        self.good(unit(body=('PERFORM A-SECTION','DISPLAY "DONE" STOP RUN.',
            'A-SECTION SECTION.','DISPLAY "A" PERFORM B-SECTION',
            'GO TO A-END DISPLAY "BAD".','A-END.','EXIT.',
            'B-SECTION SECTION.','DISPLAY "B".','B-END.','EXIT.')),'A\nB\nDONE\n')

    def test_recursive_section_returns_use_explicit_stack(self):
        self.good(unit(data=('01 N PIC 99 VALUE 0.',),body=('PERFORM A-SECTION STOP RUN.',
            'A-SECTION SECTION.','ADD 1 TO N DISPLAY N',
            'IF N < 3 PERFORM A-SECTION END-IF.','A-END.','EXIT.')),'01\n02\n03\n')

    def test_inline_varying_and_receiving_value(self):
        self.good(unit(data=('01 I PIC 99.','01 TOTAL-A PIC 999.'),body=(
            'PERFORM VARYING I FROM 1 BY 1 UNTIL I > 3',
            'ADD I TO TOTAL-A END-PERFORM','DISPLAY TOTAL-A I STOP RUN.')),'00604\n')

    def test_nested_varying_after_dimensions(self):
        self.good(unit(data=('01 I PIC 9.','01 J PIC 9.','01 N PIC 99.'),body=(
            'PERFORM VARYING I FROM 1 BY 1 UNTIL I > 2',
            'AFTER J FROM 1 BY 1 UNTIL J > 3',
            'ADD 1 TO N END-PERFORM DISPLAY N STOP RUN.')),'06\n')

    def test_nested_times_and_exit_perform(self):
        self.good(unit(data=('01 N PIC 99.',),body=('PERFORM 2 TIMES',
            'PERFORM 3 TIMES ADD 1 TO N END-PERFORM END-PERFORM',
            'PERFORM 10 TIMES ADD 1 TO N IF N = 8',
            'EXIT PERFORM END-IF END-PERFORM DISPLAY N STOP RUN.')),'08\n')

    def test_test_after_executes_once_when_initial_condition_is_true(self):
        self.good(unit(data=('01 N PIC 9.',),body=(
            'PERFORM WITH TEST AFTER UNTIL N >= 0',
            'ADD 1 TO N END-PERFORM DISPLAY N STOP RUN.')),'1\n')
        self.good(unit(data=('01 I PIC 9.',),body=(
            'PERFORM WITH TEST AFTER VARYING I FROM 1 BY 1',
            'UNTIL I > 0 DISPLAY I END-PERFORM DISPLAY I STOP RUN.')),'1\n1\n')

    def test_next_sentence_skips_remainder_of_sentence(self):
        self.good(unit(body=('IF 1 = 1 NEXT SENTENCE END-IF DISPLAY "BAD".',
            'DISPLAY "GOOD" STOP RUN.')),'GOOD\n')

    def test_goto_depending_and_forward_targets(self):
        self.good(unit(data=('01 N PIC 9 VALUE 2.',),body=(
            'GO TO A-PARA B-PARA DEPENDING ON N','DISPLAY "BAD" STOP RUN.',
            'A-PARA.','DISPLAY "A" STOP RUN.','B-PARA.','DISPLAY "B" STOP RUN.')),'B\n')

    def test_condition_names_and_evaluate_true(self):
        self.good(unit(data=('01 FLAG-A PIC X.','88 YES-A VALUE "Y".',),body=(
            'SET YES-A TO TRUE','EVALUATE YES-A WHEN TRUE DISPLAY "YES"',
            'WHEN OTHER DISPLAY "BAD" END-EVALUATE STOP RUN.')),'YES\n')

    def test_evaluate_also_ranges_any_and_abbreviated_conditions(self):
        self.good(unit(data=('01 N PIC 9 VALUE 2.',),body=(
            'EVALUATE N ALSO TRUE WHEN 1 THRU 3 ALSO ANY DISPLAY "RANGE"',
            'WHEN OTHER DISPLAY "BAD" END-EVALUATE',
            'IF N = 1 OR 2 DISPLAY "OR" END-IF STOP RUN.')),'RANGE\nOR\n')

    def test_redefines_and_dynamic_reference_modification(self):
        self.good(unit(data=('01 BASE-A PIC X(4) VALUE "1234".',
            '01 VIEW-A REDEFINES BASE-A PIC 9(4).','01 N PIC 9 VALUE 2.'),body=(
            'DISPLAY VIEW-A BASE-A(N:2) LENGTH OF BASE-A(N:)',
            'MOVE "XY" TO BASE-A(N:2) DISPLAY BASE-A STOP RUN.')),'1234233\n1XY4\n')

    def test_dynamic_subscript_and_refmod_fail_with_origin(self):
        for body,data,code in [
            (('DISPLAY FIELD-A(I).',),('01 I PIC 9.','01 TAB-A OCCURS 2.','05 FIELD-A PIC X.'),'SUBSCRIPT_BOUNDS'),
            (('DISPLAY FIELD-A(I).',),('01 I PIC 99 VALUE 51.','01 TAB-A OCCURS 50.','05 FIELD-A PIC X.'),'SUBSCRIPT_BOUNDS'),
            (('DISPLAY FIELD-A(I:2).',),('01 I PIC 9 VALUE 4.','01 FIELD-A PIC X(4).'),'REFMOD_BOUNDS')]:
            with self.subTest(code=code):
                result=self.run_program(unit(data=data,body=body))
                self.assertEqual(result.returncode,1)
                self.assertIn(code.encode(),result.stderr)
                self.assertIn(b'main.cbl:',result.stderr)

    def test_exact_rational_and_twenty_eight_digit_results(self):
        self.good(unit(data=('01 N PIC 9(28).','01 R PIC 9V99.'),body=(
            'COMPUTE N = 9999999999999999999999999998 + 1',
            'COMPUTE R = (1 / 3) * 3 DISPLAY N "|" R STOP RUN.')),
            '9999999999999999999999999999|1.00\n')

    def test_size_error_and_division_zero_handlers_preserve_receiver(self):
        self.good(unit(data=('01 N PIC 999 VALUE 777.',),body=(
            'COMPUTE N = 1000 ON SIZE ERROR DISPLAY "SIZE"',
            'NOT ON SIZE ERROR DISPLAY "BAD" END-COMPUTE',
            'COMPUTE N = 1 / 0 ON SIZE ERROR DISPLAY "ZERO" END-COMPUTE',
            'DISPLAY N STOP RUN.')),'SIZE\nZERO\n777\n')

    def test_multiply_divide_giving_remainder_and_rounded(self):
        self.good(unit(data=('01 N PIC 99.','01 R PIC 9.','01 D PIC 9V99.'),body=(
            'MULTIPLY 3 BY 4 GIVING N DISPLAY N',
            'DIVIDE 10 BY 3 GIVING N REMAINDER R DISPLAY N R',
            'COMPUTE D ROUNDED = 1.235 DISPLAY D STOP RUN.')),'12\n031\n1.24\n')

    def test_string_unstring_pointers_counts_and_padding(self):
        self.good(unit(data=('01 TEXT-A PIC X(8).','01 P PIC 9 VALUE 1.',
            '01 A-TEXT PIC X(3).','01 B-TEXT PIC X(5).','01 N PIC 9.'),body=(
            'STRING "AB" DELIMITED BY SIZE "-CD" DELIMITED BY SIZE',
            'INTO TEXT-A WITH POINTER P END-STRING DISPLAY TEXT-A P',
            'UNSTRING TEXT-A DELIMITED BY "-" INTO A-TEXT B-TEXT',
            'TALLYING N END-UNSTRING DISPLAY A-TEXT B-TEXT N STOP RUN.')),
            'AB-CD   6\nAB CD   2\n')
        self.good(unit(data=('01 TEXT-A PIC X(4) VALUE "Ab c".',),body=(
            'INSPECT TEXT-A CONVERTING "abc" TO "ABC"',
            'INSPECT TEXT-A REPLACING ALL "C" BY "D" DISPLAY TEXT-A',
            'INSPECT TEXT-A REPLACING CHARACTERS BY "X"',
            'DISPLAY TEXT-A STOP RUN.')),'AB D\nXXXX\n')

    def test_initialize_corresponding_and_occurs(self):
        self.good(unit(data=('01 A-GROUP.','05 FIELD-A PIC 99 VALUE 12.',
            '01 B-GROUP.','05 FIELD-A PIC 99.',
            '01 TABLE-A OCCURS 2.','05 VALUE-A PIC 9 VALUE 7.'),body=(
            'MOVE CORRESPONDING A-GROUP TO B-GROUP',
            'INITIALIZE TABLE-A REPLACING NUMERIC BY 3',
            'DISPLAY FIELD-A OF B-GROUP VALUE-A(1) VALUE-A(2)',
            'STOP RUN.')),'1233\n')

    def test_file_status_missing_input_and_eof_handlers(self):
        env=('INPUT-OUTPUT SECTION.','FILE-CONTROL.',
            'SELECT F-A ASSIGN "in.dat" ORGANIZATION LINE SEQUENTIAL',
            'FILE STATUS FS.')
        self.good(unit(environment=env,files=('FD F-A.','01 REC-A PIC X(3).'),data=('01 FS PIC XX.',),body=('OPEN INPUT F-A DISPLAY FS STOP RUN.',)),'35\n')
        self.good(unit(environment=env,files=('FD F-A.','01 REC-A PIC X(3).'),data=('01 FS PIC XX.',),body=(
            'OPEN INPUT F-A READ F-A AT END DISPLAY "END"',
            'NOT AT END DISPLAY "BAD" END-READ DISPLAY FS',
            'CLOSE F-A STOP RUN.')),'END\n10\n',fixtures={'in.dat':b''})
        self.good(unit(environment=env,files=('FD F-A.','01 REC-A PIC X(3).'),data=('01 FS PIC XX.',),body=(
            'OPEN INPUT F-A READ F-A DISPLAY REC-A FS',
            'CLOSE F-A STOP RUN.')),'ABC00\n',fixtures={'in.dat':b'ABC\r\n'})

    def test_extend_preserves_exact_record_width(self):
        self.good(unit(environment=('INPUT-OUTPUT SECTION.','FILE-CONTROL.',
            'SELECT F-A ASSIGN "out.dat" ORGANIZATION LINE SEQUENTIAL.'),
            files=('FD F-A.','01 REC-A PIC X(3) VALUE "AB".'),body=('OPEN EXTEND F-A WRITE REC-A CLOSE F-A STOP RUN.',)),'',fixtures={'out.dat':b'OLD\n'})
        self.assertEqual((self.directory/'out.dat').read_bytes(),b'OLD\nAB \n')

    def test_terminal_utf8_and_iso88591_records_have_different_byte_widths(self):
        self.good(unit(environment=('INPUT-OUTPUT SECTION.','FILE-CONTROL.',
            'SELECT F-A ASSIGN "out.dat" ORGANIZATION LINE SEQUENTIAL.'),
            files=('FD F-A.','01 REC-A PIC X(5).'),body=(
            'OPEN OUTPUT F-A ACCEPT REC-A DISPLAY REC-A',
            'WRITE REC-A CLOSE F-A STOP RUN.')),'José \n','José\n')
        self.assertEqual((self.directory/'out.dat').read_bytes(),b'Jos\xe9 \n')

    def test_call_reference_value_content_return_code_and_persistence(self):
        callee=unit(name='SUB-A',linkage=('01 ARG-A PIC 99.',),using=' USING ARG-A',
            data=('01 CALLS-A PIC 9.',),body=('ADD 1 TO ARG-A CALLS-A','DISPLAY ARG-A CALLS-A','MOVE 7 TO RETURN-CODE GOBACK.'))
        main=unit(data=('01 ARG-A PIC 99 VALUE 10.',),body=(
            'CALL "SUB-A" USING ARG-A DISPLAY ARG-A RETURN-CODE',
            'CALL "SUB-A" USING ARG-A DISPLAY ARG-A RETURN-CODE',
            'MOVE ZERO TO RETURN-CODE STOP RUN.'))
        self.good(main,'111\n11+000000007\n122\n12+000000007\n',sources=[callee])
        callee=unit(name='SUB-A',linkage=('01 ARG-A PIC S9(4) COMP.',),using=' USING BY VALUE ARG-A',body=('ADD 1 TO ARG-A DISPLAY ARG-A GOBACK.',))
        self.good(unit(data=('01 ARG-A PIC 99 VALUE 10.',),body=('CALL "SUB-A" USING BY VALUE ARG-A DISPLAY ARG-A STOP RUN.',)),
            '+0011\n10\n',sources=[callee])

    def test_local_storage_is_reinitialized_on_each_call(self):
        callee=unit(name='SUB-A',data=('01 N PIC 9 VALUE 4.',),body=('ADD 1 TO N DISPLAY N GOBACK.',)).replace('WORKING-STORAGE SECTION.','LOCAL-STORAGE SECTION.  ')
        self.good(unit(body=('CALL "SUB-A" CALL "SUB-A" STOP RUN.',)),'5\n5\n',sources=[callee])

    def test_module_object_can_be_called_from_c_harness(self):
        text=unit(name='SUB-A',linkage=('01 ARG-A PIC 99.',),using=' USING ARG-A',body=('ADD 1 TO ARG-A GOBACK.',))
        result=self.build(text,module=True,keep_c=True)
        self.assertNotIn('int main(',result.generated.c_source)
        harness=self.directory/'harness.c'
        harness.write_text('#include "cobol_runtime.h"\n#include <assert.h>\n'+
            f'extern int {function_name("SUB-A")}(cb_runtime*,cb_field*,size_t);\n'+
            'int main(void) { cb_runtime rt; cb_runtime_init(&rt); unsigned char data[2]={\'0\',\'1\'}; '+
            'cb_desc d={1,2,0,0,0,\'.\',"99"}; cb_field f={data,2,&d}; '+
            f'{function_name("SUB-A")}(&rt,&f,1); '+
            'assert(data[0]==\'0\' && data[1]==\'2\'); cb_runtime_destroy(&rt); return 0; }\n')
        process=subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I',str(RUNTIME),str(harness),
            result.output,*(str(p) for p in RUNTIME_SOURCES),'-o',str(self.directory/'harness')],capture_output=True,text=True)
        self.assertEqual(process.returncode,0,process.stderr)
        self.assertEqual(subprocess.run([str(self.directory/'harness')],timeout=4).returncode,0)

    def test_unresolved_call_blocks_gcc_without_stubs(self):
        path=self.directory/'main.cbl';path.write_text(unit(body=('CALL "missing" STOP RUN.',)))
        with patch('cobol_compiler.driver.subprocess.run') as run:
            result=compile_file(path,self.directory/'program')
            self.assertFalse(result.success);run.assert_not_called()
        self.assertIn('LINK_UNRESOLVED_CALL',[d.code for d in result.diagnostics])
        self.assertFalse((self.directory/'program').exists())

    def test_unsupported_backend_before_gcc_and_syntax_api_preserved(self):
        path=self.directory/'main.cbl';path.write_text(unit(body=('DISPLAY "x" AT LINE 2 COLUMN 3 STOP RUN.',)))
        with patch('cobol_compiler.driver.subprocess.run') as run:
            result=compile_file(path,self.directory/'program')
            self.assertFalse(result.success);run.assert_not_called()
        self.assertIn('UNSUPPORTED_BACKEND_SCREEN_POSITION',[d.code for d in result.diagnostics])

    def test_driver_preserves_executable_after_gcc_failure(self):
        path=self.directory/'main.cbl';path.write_text(unit(body=('STOP RUN.',)))
        target=self.directory/'program';target.write_bytes(b'previous executable')
        failed=subprocess.CompletedProcess([],1,'','synthetic GCC error')
        with patch('cobol_compiler.driver.subprocess.run',return_value=failed):
            result=compile_file(path,target)
        self.assertFalse(result.success)
        self.assertEqual(target.read_bytes(),b'previous executable')
        self.assertTrue(Path(result.c_path).exists())
        self.assertIn('GCC_FAILED',[d.code for d in result.diagnostics])

    def test_driver_preserves_source_and_reports_missing_gcc(self):
        path=self.directory/'main.cbl';text=unit();path.write_text(text)
        result=compile_file(path,path)
        self.assertFalse(result.success)
        self.assertIn('OUTPUT_SOURCE_COLLISION',[d.code for d in result.diagnostics])
        self.assertEqual(path.read_text(),text)
        result=compile_file(path,self.directory/'program',gcc='missing-gcc-etapa4')
        self.assertIn('GCC_NOT_FOUND',[d.code for d in result.diagnostics])

    def test_cli_compile_emit_c_and_backend_check(self):
        path=self.directory/'main.cbl';path.write_text(unit(body=('DISPLAY "HELLO" STOP RUN.',)))
        target=self.directory/'program';c_path=self.directory/'program.c'
        result=subprocess.run([os.sys.executable,str(ROOT/'compiler.py'),str(path),'-o',str(target),
            '--emit-c',str(c_path)],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(target.exists());self.assertTrue(c_path.exists())
        target.unlink()
        result=subprocess.run([os.sys.executable,'-m','cobol_compiler',str(path),'--check-backend'],
            capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(target.exists())

    def test_accept_clock_and_progdata_fields(self):
        body=('CALL "PROGDATA" USING COD001A-REGISTRO',
            'ACCEPT TIME-A FROM TIME',
            'DISPLAY COD001A-DATA "|" COD001A-DIA-SEMANA "|"',
            'COD001A-DIAS-ANO "|" TIME-A STOP RUN.')
        self.good(unit(data=('COPY COD001A.','01 TIME-A PIC 9(8).'),body=body),
            '20240229|04|060|12345600\n',sources=[(ROOT/'examples/dependencias/PROGDATA.cbl').read_text()],
            include_dirs=[ROOT/'examples/dependencias'])

    def test_goto_escape_inline_is_diagnosed_before_gcc(self):
        path=self.directory/'main.cbl'
        path.write_text(unit(body=('PERFORM 3 TIMES GO TO END-A END-PERFORM.',
            'END-A.','STOP RUN.')))
        with patch('cobol_compiler.driver.subprocess.run') as run:
            result=compile_file(path,self.directory/'program')
            self.assertFalse(result.success);run.assert_not_called()
        self.assertIn('UNSUPPORTED_BACKEND_GO_ESCAPE_INLINE',[d.code for d in result.diagnostics])

    def test_exit_program_distinguishes_main_and_called_program(self):
        callee=unit(name='SUB-A',body=('DISPLAY "SUB" EXIT PROGRAM',
            'DISPLAY "BAD" GOBACK.'))
        self.good(unit(body=('EXIT PROGRAM DISPLAY "MAIN"',
            'CALL "SUB-A" DISPLAY "DONE" STOP RUN.')),
            'MAIN\nSUB\nDONE\n',sources=[callee])
