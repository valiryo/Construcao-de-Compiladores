"""Evidências da auditoria: recuperação não pode esconder o próximo bloqueio."""
from pathlib import Path
import unittest

from cobol_lexer import CobolLexer
from regression_pending import audit, conflict_variants, pending_inventory
from tools.corpus_contracts import corpus_contracts
from tools.backend_scenarios import ROOT
from tools.functional_execution import digest


class PendingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit()
        cls.by_name={Path(p).name:r for p,r in cls.report['files'].items()}

    def test_inventory_preserves_sources_and_distinguishes_contextual_fragments(self):
        pending,_=pending_inventory()
        self.assertEqual(set(self.report['files']),set(pending))
        self.assertEqual(len(pending),26)
        self.assertEqual(self.report['summary']['programs_executed'],0)
        for path,sha in self.report['original_hashes'].items():self.assertEqual(digest((ROOT/path).read_bytes()),sha)
        for path,sha in self.report['implementation_sha256'].items():self.assertEqual(digest((ROOT/path).read_bytes()),sha)
        for name,record,size in [('COD001A.cpy','COD001A-REGISTRO',81),('COPY002A.cpy','COPY002A-REGISTRO',10552)]:
            row=self.by_name[name]
            self.assertEqual(row['finding']['feasibility'],'E')
            self.assertEqual(row['original']['gcc']['status'],'not_run')
            self.assertTrue(row['contexts'])
            for context in row['contexts'].values():
                self.assertTrue(context['semantic_success'])
                self.assertEqual(context['root_layout_bytes'][record],size)

    def test_conflict_sides_preserve_equivalence_only_when_supported_by_tokens(self):
        for name in ('SORT001A.cbl','VALIDA1B.cbl','CAD0005A.cbl'):
            path=next(p for p in self.report['files'] if Path(p).name==name)
            variants,hunks=conflict_variants((ROOT/path).read_text())
            self.assertTrue(hunks)
            tokens=[]
            for side in ('ours','theirs'):
                lexical=CobolLexer().tokenize(variants[side])
                self.assertTrue(lexical.success,lexical.diagnostics)
                tokens.append([(t.kind,t.value) for t in lexical.tokens])
                trial=self.by_name[name]['experiments'][side]['pipeline']
                self.assertEqual(trial['gcc']['status'],'success')
            self.assertEqual(*tokens)
        other=self.by_name['PROG010A.cbl']['experiments']
        self.assertEqual(other['ours']['pipeline']['gcc']['status'],'success')
        self.assertIn('UNSUPPORTED_SORT',{d['code'] for d in other['theirs']['pipeline']['diagnostics']})

    def test_available_cobol_dependencies_recover_caller_without_sort_extension(self):
        row=self.by_name['CAD0001A.cbl']
        self.assertEqual(row['original']['first_blocker'],'link')
        trial=row['experiments']['with-recovered-sort']
        self.assertEqual(trial['pipeline']['gcc']['status'],'success')
        self.assertEqual(len(trial['pipeline']['dependencies']),7)
        self.assertEqual(trial['diff'],'')
        if trial.get('gnu',{}).get('available'):self.assertEqual(trial['gnu']['returncode'],0,trial['gnu']['stderr'])
        self.assertEqual(self.by_name['SORT001A.cbl']['experiments']['ours']['pipeline']['gcc']['module'],True)

    def test_indexed_intent_removes_sequential_errors_but_keeps_feature_block(self):
        row=self.by_name['PROGVSAM.cbl']
        codes={d['code'] for d in row['original']['diagnostics']}
        self.assertIn('KEY_ON_SEQUENTIAL_FILE',codes)
        trial=row['experiments']['indexed-intent']
        self.assertEqual({d['code'] for d in trial['pipeline']['diagnostics']},{'UNSUPPORTED_FILE_ORGANIZATION'})
        self.assertEqual(trial['pipeline']['backend']['status'],'not_run')
        if trial.get('gnu',{}).get('available'):self.assertEqual(trial['gnu']['returncode'],0,trial['gnu']['stderr'])
        valid=self.by_name['PROG018A.cbl']['experiments']['valid-alter-minimal']
        self.assertEqual({d['code'] for d in valid['pipeline']['diagnostics']},{'UNSUPPORTED_ALTER'})

    def test_format_and_dialect_changes_expose_remaining_blocks(self):
        row=self.by_name['CBREAKEX.cbl']
        self.assertEqual(row['original']['first_blocker'],'lexer')
        shifted=row['experiments']['shift-one']['pipeline']
        self.assertEqual(shifted['first_blocker'],'parser')
        semantic=row['experiments']['shift-without-data-record']['pipeline']
        self.assertEqual({d['code'] for d in semantic['diagnostics']},{'INVALID_PICTURE'})
        if row.get('gnu_free',{}).get('available'):self.assertEqual(row['gnu_free']['returncode'],0)
        names=self.by_name['PROG042A.cbl']
        if names.get('gnu_original',{}).get('available'):
            self.assertEqual(names['gnu_original']['returncode'],0)
            self.assertNotEqual(names['gnu_limit30']['returncode'],0)
        self.assertEqual(names['experiments']['rename-31']['pipeline']['gcc']['status'],'success')

    def test_variant_counts_and_native_calls_are_never_executed(self):
        expected=corpus_contracts()['pending_summary']
        self.assertEqual({key:self.report['summary'][key] for key in expected},expected)
        for row in self.report['files'].values():
            self.assertFalse(row['original']['executed'])
            for trial in row['experiments'].values():self.assertFalse(trial['pipeline']['executed'])
        self.assertEqual(self.report['snapshot_tree']['native_c_sources'],[])
        for name in ('NCURSESDEMO.cbl','PROGTEST2.cbl','PROGTEST3.cbl','main.cbl','ncurses_demo.cbl'):
            self.assertTrue(self.by_name[name]['original']['calls'])
            self.assertEqual(self.by_name[name]['finding']['feasibility'],'C')
