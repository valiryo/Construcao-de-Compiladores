"""Compila os sete, executa cenários explícitos e confere stdout/arquivos/retorno."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from cobol_compiler.driver import compile_file
from tools.backend_scenarios import ROOT,SCENARIOS,CLOCK,inputs_for,validate_scenario


class OfficialBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=tempfile.TemporaryDirectory()
        cls.binaries={}
        for program in sorted({s.program for s in SCENARIOS}):
            source,deps=inputs_for(program,cls.build.name)
            result=compile_file(source,Path(cls.build.name)/program,include_dirs=[ROOT/'examples/dependencias'],source_paths=deps)
            if not result.success:raise AssertionError('\n'.join(d.format() for d in result.diagnostics)+'\n'+result.gcc_stderr)
            if result.gcc_stderr:raise AssertionError(result.gcc_stderr)
            cls.binaries[program]=result.output

    @classmethod
    def tearDownClass(cls):cls.build.cleanup()

    def scenario(self,name):
        scenario=next(s for s in SCENARIOS if s.name==name)
        with tempfile.TemporaryDirectory() as td:
            for f,b in scenario.fixtures.items():(Path(td)/f).write_bytes(b)
            process=subprocess.run([self.binaries[scenario.program]],input=scenario.stdin.encode(),capture_output=True,cwd=td,
                env={**os.environ,'COBOL_DATETIME':CLOCK,'COBOL_TERMINAL_ENCODING':'utf8'},timeout=8)
            errors=validate_scenario(scenario,process,td)
            self.assertEqual(errors,[],process.stdout.decode(errors='replace')+'\n'+process.stderr.decode(errors='replace'))

    def test_calcmd_basic(self):self.scenario('calcmd-basic')
    def test_calcmd_retry_fraction(self):self.scenario('calcmd-retry-and-fraction')
    def test_calcmd_zero_divisor(self):self.scenario('calcmd-zero-divisor')
    def test_caixa_no_discount(self):self.scenario('caixa-no-discount')
    def test_caixa_retries_discount(self):self.scenario('caixa-retries-and-discount')
    def test_cad4_one(self):self.scenario('cad4-one')
    def test_cad4_multiple(self):self.scenario('cad4-two')
    def test_busca_first(self):self.scenario('busca-first')
    def test_busca_last(self):self.scenario('busca-last')
    def test_busca_absent(self):self.scenario('busca-absent')
    def test_busca_empty(self):self.scenario('busca-empty')
    def test_agenda_empty(self):self.scenario('agenda-empty')
    def test_agenda_add(self):self.scenario('agenda-add')
    def test_agenda_reopen_add(self):self.scenario('agenda-reopen-add')
    def test_agenda_list(self):self.scenario('agenda-list')
    def test_agenda_duplicate(self):self.scenario('agenda-duplicate')
    def test_agenda_fim(self):self.scenario('agenda-fim')
    def test_agenda_invalid(self):self.scenario('agenda-invalid-option')
    def test_library_empty(self):self.scenario('biblioteca-empty')
    def test_library_add_borrow_return_query(self):self.scenario('biblioteca-add-loan-return-query')
    def test_library_reopen_list(self):self.scenario('biblioteca-reopen-list')
    def test_library_absent(self):self.scenario('biblioteca-absent')
    def test_library_unavailable(self):self.scenario('biblioteca-loan-unavailable')
    def test_cad2_fim(self):self.scenario('cad2-fim')
    def test_cad2_validation_and_shared_storage(self):self.scenario('cad2-validation-and-shared-record')

    def test_progdata_clock_and_unassigned_fields(self):self.scenario('progdata-clock')
    def test_extra_reference_modification_count(self):self.scenario('extra-refmod-count')
    def test_extra_ordered_search_found(self):self.scenario('extra-search-found')
    def test_extra_ordered_search_absent(self):self.scenario('extra-search-absent')
    def test_extra_sequential_delete(self):self.scenario('extra-sequential-delete')
