"""Casos mínimos para as falhas encontradas na validação do corpus real."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from cobol_compiler.driver import compile_file
from cobol_compiler.frontend import parse_source
from cobol_lexer import CobolLexer
from test_semantic import unit
from test_lexer import fixed


class FunctionalRegressionTests(unittest.TestCase):
    def run_cobol(self,text):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/'source.cbl';source.write_text(text,encoding='utf-8')
            built=compile_file(source,root/'program')
            self.assertTrue(built.success,repr(built.diagnostics)+built.gcc_stderr)
            result=subprocess.run([built.output],capture_output=True,cwd=root,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stderr,b'')
            return result.stdout

    def test_move_text_uses_receiver_decimal_convention(self):
        source=unit(environment=('CONFIGURATION SECTION.','SPECIAL-NAMES. DECIMAL-POINT IS COMMA.'),
            data=('01 RAW-TEXT PIC X(10) VALUE "-12,34".',
            '01 NUMBER-A PIC S9(3)V99.'),body=('MOVE RAW-TEXT TO NUMBER-A',
                'DISPLAY NUMBER-A STOP RUN.'))
        self.assertEqual(self.run_cobol(source),b'-012,34\n')

    def test_unstring_decimal_text_into_numeric_receivers(self):
        source=unit(environment=('CONFIGURATION SECTION.','SPECIAL-NAMES. DECIMAL-POINT IS COMMA.'),
            data=('01 INPUT-TEXT PIC X(20) VALUE "2,00|0,100".',
            '01 RATE-A PIC 9(3)V99.','01 RATE-B PIC 9(3)V999.'),body=(
                'UNSTRING INPUT-TEXT DELIMITED BY "|"',
                'INTO RATE-A RATE-B END-UNSTRING',
                'DISPLAY RATE-A ":" RATE-B STOP RUN.'))
        self.assertEqual(self.run_cobol(source),b'002,00:000,100\n')

    def test_frontend_preserves_literal_spaces_through_column72(self):
        prefix='           DISPLAY "A'
        first=prefix.ljust(72)
        text='\n'.join([fixed('IDENTIFICATION DIVISION.',area='A'),
            fixed('PROGRAM-ID. PADDING.',area='A'),fixed('PROCEDURE DIVISION.',area='A'),
            first,'      -    "B"',fixed('STOP RUN.')])
        expected='A'+' '*(72-len(prefix))+'B'
        parsed=parse_source(text)
        self.assertTrue(parsed.success,parsed.diagnostics)
        literal=next(t for t in parsed.preprocessed.tokens if t.kind=='STRING')
        self.assertEqual(literal.value,expected)
        self.assertEqual((literal.span.start.line,literal.span.end.line),(4,5))
        self.assertEqual(self.run_cobol(text),(expected+'\n').encode())

    def test_legacy_lexer_continuation_api_remains_compatible(self):
        text=fixed('DISPLAY "AB')+'\n'+fixed('"CD".',indicator='-')
        self.assertEqual(CobolLexer().tokenize(text).tokens[1].value,'ABCD')
        self.assertNotEqual(CobolLexer(preserve_literal_padding=True).tokenize(text).tokens[1].value,'ABCD')
