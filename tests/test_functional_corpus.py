"""Cada programa recompila do zero; cada cenário confere resultados e proveniência.

Um teste individual prepara somente o programa correspondente. A ordem dos testes
não fornece estado: todos os processos e fixtures são independentes.
"""
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from tools.auditar_funcional import discover_programs,input_resolver,markdown,OFFICIALS
from tools.functional_execution import run_cases,digest
from tools.functional_scenarios import SCENARIOS
from tools.backend_scenarios import ROOT
from tools.backend_scenarios import Scenario

_inventory=None


def inventory():
    global _inventory
    if _inventory is None:_inventory=discover_programs()[0]
    return _inventory


class _CorpusCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        info=inventory()
        modules={cls.program:ROOT/info[cls.program]['path']} if info[cls.program]['kind']=='module' else {}
        cls.report=run_cases(cls.cases,input_resolver(info),module_sources=modules)

    def check_case(self,name):
        row=self.report['scenarios'][name]
        proof=self.report['programs'][self.program]
        self.assertTrue(proof['compiled'],str(proof['diagnostics'])+proof['gcc_stderr'])
        for build in [proof['build'],*([proof['module_build']] if 'module_build' in proof else [])]:
            for key in ('absent_before','c_regenerated','gcc_executed','artifact_fresh'):
                self.assertTrue(build[key],(name,key))
        self.assertTrue(row['executed'],row['errors'])
        self.assertTrue(row['validated'],row['errors'])
        self.assertEqual(row['runs']['ours']['executable_sha256'],proof['build']['artifact']['sha256'])
        self.assertEqual(row['runs']['ours']['initial_files'],{n:b['sha256'] for n,b in row['fixtures'].items()})
        scenario=next(s for s in self.cases if s.name==name)
        if self.report['oracle'] and scenario.oracle:
            self.assertTrue(proof['oracle_compiled'],proof['oracle_compile_stderr'])
            self.assertTrue(row['oracle_compared'])
            self.assertTrue(row['oracle_match'] or row['abi_expected'],str(row['differences'])[:2000])
        for run in row['runs'].values():
            self.assertNotIn('timeout',run)
            for data in [run['stdout'],run['stderr'],*run['files'].values()]:
                decoded=base64.b64decode(data['base64'])
                self.assertEqual(digest(decoded),data['sha256'])
                self.assertEqual(len(decoded),data['bytes'])


def install_cases():
    for program in sorted({s.program for s in SCENARIOS}):
        cases=[s for s in SCENARIOS if s.program==program]
        members={'program':program,'cases':cases,'__module__':__name__}
        for scenario in cases:
            def test(self,name=scenario.name):self.check_case(name)
            members['test_'+re.sub('[^a-zA-Z0-9_]','_',scenario.name)]=test
        name='Functional_'+program.replace('-','_')+'_Tests'
        globals()[name]=type(name,(_CorpusCase,),members)


install_cases()


class FunctionalAuditContracts(unittest.TestCase):
    def test_missing_source_records_failure_and_keeps_visiting(self):
        info=inventory()
        cases=[s for s in SCENARIOS if s.program=='MEU-PROGRAMA']+[Scenario('missing-source','MISSING','')]
        with tempfile.TemporaryDirectory() as td:
            def resolve(program,directory):
                return (Path(td)/'absent.cbl',[]) if program=='MISSING' else input_resolver(info)(program,directory)
            report=run_cases(cases,resolve,reference=False)
        self.assertFalse(report['programs']['MISSING']['compiled'])
        self.assertTrue(report['scenarios']['missing-source']['errors'])
        self.assertTrue(report['scenarios']['meu-programa-message']['validated'])

    def test_real_inventory_is_covered_including_all_five_pending_modules(self):
        data=inventory()
        self.assertEqual(set(data),{s.program for s in SCENARIOS})
        self.assertEqual(len([p for p in data.values() if not p['previously_validated']]),49)
        modules=[p for p in data.values() if p['kind']=='module' and not p['previously_validated']]
        self.assertEqual(len(modules),5)
        for item in modules:self.assertTrue((ROOT/'tests/fixtures/functional'/(item['program_id'].lower()+'.cbl')).is_file())

    def test_official_count_is_25_and_24_are_comparable(self):
        cases=[s for s in SCENARIOS if s.program in OFFICIALS]
        self.assertEqual(len(cases),25)
        self.assertEqual(sum(s.oracle for s in cases),24)

    def test_repeated_and_shuffled_builds_have_new_provenance(self):
        info=inventory();cases=[s for s in SCENARIOS if s.program=='GRAV001A']
        modules={'GRAV001A':ROOT/info['GRAV001A']['path']}
        first=run_cases(cases,input_resolver(info),reference=False,module_sources=modules,seed=1)
        second=run_cases(cases,input_resolver(info),reference=False,module_sources=modules,seed=2)
        self.assertNotEqual(first['run_id'],second['run_id'])
        for name in first['scenarios']:
            a,b=first['scenarios'][name],second['scenarios'][name]
            self.assertTrue(a['validated'] and b['validated'])
            self.assertEqual(a['stdout_sha256'],b['stdout_sha256'])
            self.assertEqual(a['files'],b['files'])

    def test_saved_report_is_generated_and_source_fingerprints_match(self):
        report=json.loads((ROOT/'docs/auditoria-funcional.json').read_text())
        self.assertEqual((ROOT/'docs/auditoria-funcional.md').read_text(),markdown(report))
        for row in report['inventory'].values():
            self.assertEqual(row['source_sha256'],digest((ROOT/row['path']).read_bytes()))
        self.assertEqual(set(report['execution']['scenarios']),{s.name for s in SCENARIOS})

    def test_cli_selects_real_program_from_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as td:
            report=Path(td)/'selection.json'
            run=subprocess.run([sys.executable,'-m','tools.auditar_funcional','--program','PROG001A.cbl',
                '--no-oracle','--report',str(report)],cwd=td,env={**os.environ,'PYTHONPATH':str(ROOT)},capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            data=json.loads(report.read_text())
            self.assertEqual(set(data['inventory']),{'PROG001A'})
            self.assertEqual(data['summary']['validated_programs'],1)
            # A successful report has no failed cases; rerun must not compile others.
            rerun=subprocess.run([sys.executable,'-m','tools.auditar_funcional','--failed-from',str(report)],
                cwd=td,env={**os.environ,'PYTHONPATH':str(ROOT)},capture_output=True,text=True,timeout=10)
            self.assertEqual(rerun.returncode,0,rerun.stderr)
            self.assertIn('Nenhum cenário falho',rerun.stdout)
            # Force just the selection state to failed; the real scenario remains
            # unchanged and must be rebuilt/executed, not copied from this log.
            data['inventory']['PROG001A']['validated']=False
            failed_case='prog001a-leap-clock'
            data['execution']['scenarios'][failed_case]['validated']=False
            report.write_text(json.dumps(data))
            retry=Path(td)/'retry.json'
            rerun=subprocess.run([sys.executable,'-m','tools.auditar_funcional','--failed-from',str(report),
                '--no-oracle','--report',str(retry)],cwd=td,env={**os.environ,'PYTHONPATH':str(ROOT)},
                capture_output=True,text=True,timeout=30)
            self.assertEqual(rerun.returncode,0,rerun.stdout+rerun.stderr)
            fresh=json.loads(retry.read_text())
            self.assertEqual(fresh['summary']['selected_programs'],1)
            self.assertEqual(set(fresh['execution']['scenarios']),{failed_case})
            self.assertNotEqual(data['execution']['run_id'],fresh['execution']['run_id'])
