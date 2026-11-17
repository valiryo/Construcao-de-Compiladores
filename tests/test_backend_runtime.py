"""Runtime C independente, compilado com warnings como erros."""
import subprocess
import tempfile
from pathlib import Path
import unittest
from cobol_compiler.driver import ROOT,RUNTIME,RUNTIME_SOURCES


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=tempfile.TemporaryDirectory()
        cls.binary=Path(cls.directory.name)/'probe'
        result=subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I',str(RUNTIME),
            str(ROOT/'tests/fixtures/runtime_probe.c'),*(str(p) for p in RUNTIME_SOURCES),'-o',str(cls.binary)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):cls.directory.cleanup()

    def run_probe(self,name,code=None):
        r=subprocess.run([str(self.binary),name],capture_output=True,text=True,timeout=5)
        if code:
            self.assertEqual(r.returncode,1,r.stderr)
            self.assertIn(code,r.stderr)
            self.assertIn('runtime-probe.cob:12:8:',r.stderr)
        else:
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(r.stdout,'')
            self.assertEqual(r.stderr,'')

    def test_exact_large_decimal_and_rational_intermediates(self):self.run_probe('big')
    def test_rounding_truncation_and_overpunch(self):self.run_probe('round')
    def test_binary_little_endian_above_int64(self):self.run_probe('binary')
    def test_packed_decimal_bytes_and_round_trip(self):self.run_probe('packed')
    def test_edited_mask_exact_spaces_and_separators(self):self.run_probe('edited')
    def test_checked_overflow_leaves_receiver_unchanged(self):self.run_probe('overflow')
    def test_buffers_padding_truncation_overlap_and_comparison(self):self.run_probe('strings')
    def test_numeric_and_alphabetic_classes(self):self.run_probe('class')
    def test_reference_modification_runtime_bounds(self):self.run_probe('refmod-error','REFMOD_BOUNDS')
    def test_subscript_runtime_bounds(self):self.run_probe('index-error','SUBSCRIPT_BOUNDS')
    def test_zero_divisor_is_explicit_error(self):self.run_probe('zero-error','DIVISION_BY_ZERO')
    def test_dates_mod_and_reverse_padding(self):self.run_probe('intrinsics')
