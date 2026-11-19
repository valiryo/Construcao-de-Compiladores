"""Proveniência e denominadores do relatório integral de compatibilidade."""
import base64
import json
import unittest

from tools.backend_scenarios import ROOT
from tools.functional_execution import digest
from tools.auditar_compatibilidade import markdown
from tools.terminal_probe import cells


class CompatibilityEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=json.loads((ROOT/'docs/compatibilidade-gnucobol.json').read_text())

    def test_coverage_uses_unique_original_programs_and_equivalent_artifacts(self):
        rows=self.report['files']
        self.assertEqual(len(rows),85)
        self.assertNotIn('examples/corrigidos/CAD0005A.cbl',rows)
        for kind,key in [(None,'compilation'),('main','mains'),('module','modules')]:
            valid=[r for r in rows.values() if r.get('gnu',{}).get('compiled') and (kind is None or r['kind']==kind)]
            metric=self.report['summary'][key]
            self.assertEqual(metric['gnucobol'],len(valid))
            self.assertEqual(metric['ours'],sum(r['ours']['success'] for r in valid))
            self.assertEqual(metric['percent'],round(100*metric['ours']/metric['gnucobol'],4))
            for row in valid:
                self.assertEqual(row['gnu']['mode'],'module-object' if row['kind']=='module' else 'dynamic-executable')
        self.assertEqual(self.report['summary']['compilation']['ours'],70)

    def test_six_deferred_calls_have_fresh_build_and_explicit_execution_outcomes(self):
        probes={p:r for p,r in self.report['files'].items() if 'call_probe' in r}
        self.assertEqual(len(probes),6)
        for path,row in probes.items():
            probe=row['call_probe']
            self.assertTrue(probe['validated'],path)
            self.assertTrue(row['ours']['success'],path)
            self.assertEqual(probe['ours']['returncode'],1)
            self.assertEqual(probe['ours']['executable_sha256'],row['ours']['artifact']['sha256'])
            self.assertTrue(row['unresolved_calls'])
            if probe['status']=='native_contract_rejected':
                self.assertTrue(row['gnu_resolved_link']['compiled'],path)
                self.assertTrue(probe['ours']['terminal_restored'],path)
            else:
                self.assertEqual(probe['reference']['executable_sha256'],row['gnu']['artifact_sha256'])
                self.assertEqual(probe['reference']['returncode'],1)

    def test_hashes_and_fresh_build_proofs_are_real(self):
        for path,row in self.report['files'].items():
            self.assertEqual(row['source_sha256'],digest((ROOT/path).read_bytes()))
            if row.get('gnu',{}).get('compiled'):self.assertTrue(row['gnu']['object_compiled'])
            proof=row.get('ours',{})
            if proof.get('success'):
                for key in ['generated_c','absent_before','c_regenerated','gcc_executed','artifact_fresh']:self.assertTrue(proof[key],(path,key))
                self.assertTrue(proof['command'])
                self.assertTrue(proof['artifact']['sha256'])

    def test_baseline_and_officials_preserved_with_honest_game_scope(self):
        f=self.report['functional_execution'];baseline=f['baseline']['summary']
        self.assertEqual((baseline['validated_programs'],baseline['validated_scenarios'],baseline['official_programs_validated']),(60,140,7))
        self.assertEqual((baseline['identical_comparisons'],baseline['expected_abi_differences']),(136,3))
        game=f['terminal']['scenarios']['game-quit']
        self.assertTrue(game['validated']);self.assertFalse(game['fully_compared'])
        self.assertEqual(game['comparison'],'partial-random')
        for row in f['terminal']['scenarios'].values():
            for run in row['runs'].values():
                raw=base64.b64decode(run['stdout']['base64'])
                self.assertEqual(digest(raw),run['stdout']['sha256'])
                self.assertEqual(cells(raw,run['rows'],run['columns']),run['cells'])

    def test_markdown_matches_structured_evidence(self):
        self.assertEqual((ROOT/'docs/compatibilidade-gnucobol.md').read_text(),markdown(self.report))

    def test_final_comparison_preserves_raw_outputs_and_stops_ncurses_before_invalid_calls(self):
        gaps=self.report['execution_gaps']
        self.assertTrue(gaps['success'])
        self.assertEqual(gaps['excluded'],['GAMESNAK'])
        self.assertEqual(set(gaps['cases']),{
            'CAD0001A','CALCMD01','NCURSESDEMO','PROGTEST2','PROGTEST3','main','ncurses_demo'})
        for name,row in gaps['cases'].items():
            original=(ROOT/row['source']).read_bytes()
            self.assertEqual(digest(original),row['source_sha256'])
            for channel,equal in row['comparison'].items():
                self.assertEqual(equal,row['ours'][channel]==row['reference'][channel],(name,channel))
            if row['scope']=='safe_prefix':
                cutoff=row['cutoff']
                prefix=base64.b64decode(cutoff['prefix']['base64'])
                guard=base64.b64decode(cutoff['guard']['base64'])
                self.assertEqual(prefix,b''.join(original.splitlines(keepends=True)[:cutoff['line']-1]))
                self.assertEqual(digest(prefix+guard),cutoff['derived_sha256'])
                self.assertTrue(all(row['comparison'].values()),name)
                self.assertTrue(row['original_ours_stdout_equal'],name)
                self.assertEqual(row['ours']['returncode'],77,name)
                self.assertEqual(row['original_ours']['returncode'],1,name)
            elif row['scope']=='missing_target':
                self.assertEqual(row['comparison'],{
                    'stdout':True,'stderr':False,'files':True,'returncode':True},name)
        zero=gaps['cases']['CALCMD01']
        self.assertTrue(zero['stdout_prefix'])
        self.assertEqual((zero['ours']['returncode'],zero['reference']['returncode']),(1,0))
        self.assertEqual(zero['comparison'],{'stdout':False,'stderr':False,'files':True,'returncode':False})
