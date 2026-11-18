"""O auditor visita toda a coorte e separa compilação de comportamento validado."""
import json
import unittest
from unittest.mock import patch
from tools.auditar_backend import audit_backend,markdown,ROOT


class BackendAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('cobol_compiler.driver.subprocess.run') as run:
            cls.fresh=audit_backend(reference=False,execute=False,compile_code=False)
            run.assert_not_called()
        cls.saved=json.loads((ROOT/'docs/auditoria-backend.json').read_text(encoding='utf-8'))

    def test_every_semantically_valid_program_is_checked_and_covers_saved_generation(self):
        previous=json.loads((ROOT/'docs/auditoria-semantica.json').read_text())
        self.assertEqual(set(self.fresh['files']),set(previous['files']))
        valid={p for p,v in previous['files'].items() if v['success']}
        self.assertEqual(len(valid),68)
        for path in valid:
            self.assertNotEqual(self.fresh['files'][path]['backend'],'not_run')
            self.assertEqual(self.fresh['files'][path]['generated_c'],self.saved['files'][path]['generated_c'],path)
        self.assertEqual(self.fresh['summary']['generated_c'],60)
        self.assertEqual(self.fresh['summary']['gcc_compiled'],0)

    def test_saved_execution_and_oracle_evidence_distinguish_untested_programs(self):
        summary=self.saved['summary']
        self.assertEqual(summary['gcc_compiled'],60)
        self.assertEqual(summary['executables'],53)
        self.assertEqual(summary['modules'],7)
        self.assertEqual(summary['functionally_validated_programs'],11)
        functional=self.saved['functional']['summary']
        self.assertEqual(functional['validated_scenarios'],30)
        expected_comparisons=29 if self.saved['functional']['oracle'] else 0
        self.assertEqual(functional['oracle_compared'],expected_comparisons)
        self.assertEqual(functional['oracle_matched'],expected_comparisons)
        self.assertTrue(any(row['gcc']=='success' and not row['functionally_validated'] for row in self.saved['files'].values()))
        self.assertFalse(any(row['functionally_validated'] and row['gcc']!='success' for row in self.saved['files'].values()))

    def test_generated_markdown_is_fresh_and_artifact_paths_are_portable(self):
        self.assertEqual((ROOT/'docs/auditoria-backend.md').read_text(encoding='utf-8'),markdown(self.saved))
        self.assertNotIn(str(ROOT),json.dumps(self.saved))
        for row in self.saved['files'].values():
            if row['gcc']=='success':self.assertEqual(row['gcc_stderr'],'')
