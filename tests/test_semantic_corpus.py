"""Todos os 72 programas e os negativos permanecem no relatório reproduzível."""

from dataclasses import asdict
import json
from pathlib import Path
import unittest

from cobol_compiler import check_file
from cobol_compiler import ast as A
from regression_corpus import ROOT, OFFICIAL_NAMES, check_semantic_corpus
from tools.corpus_contracts import corpus_contracts, fingerprint


class SemanticCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=check_semantic_corpus()
        cls.official={name:check_file(ROOT/'examples'/('corrigidos' if name=='CAD0005A.cbl' else 'oficiais')/name,
            include_dirs=[ROOT/'examples/dependencias'],source_paths=[ROOT/'examples/dependencias/PROGDATA.cbl'])
            for name in OFFICIAL_NAMES}

    def test_every_previous_parser_program_was_analyzed(self):
        previous=corpus_contracts()['files']
        expected={p for p,item in previous.items() if item['parser']['classification']=='program'}
        actual={p for p,item in self.report['files'].items() if item['semantic']!='not_run'}
        self.assertEqual(actual,expected)
        self.assertEqual(len(actual),72)
        self.assertEqual(self.report['summary']['unexpected_failures'],[])
        self.assertEqual(set(self.report['files']),set(previous))

    def test_seven_officials_are_valid_and_every_expression_is_typed(self):
        for name,r in self.official.items():
            with self.subTest(name=name):
                self.assertTrue(r.success,[d.format() for d in r.diagnostics])
                self.assertTrue(r.backend_ready)
                for node in A.walk(r.ast):
                    if isinstance(node,A.Expr):self.assertIsNotNone(r.annotation(node).type)
                    if isinstance(node,A.Statement):self.assertEqual(r.annotation(node).role,'statement')

    def test_copy002a_all_fifty_records_and_exact_offsets(self):
        r=self.official['CAD0002A.cbl']
        def layout(name):return r.layout.for_symbol(r.table.candidates(name,['data'])[0])
        record,table=layout('COPY002A-REGISTRO'),layout('COPY002A-CADUSUAR')
        self.assertEqual((record.offset,record.size),(0,10552))
        self.assertEqual((table.offset,table.size,table.total_size),(2,211,10550))
        self.assertEqual(table.dimensions[0].maximum,50)
        self.assertEqual(layout('COPY002A-NOME').offset,4)
        self.assertEqual(layout('COPY002A-CEP').offset,205)
        self.assertEqual(layout('COPY002A-CEP').offset+49*211+8,10552)
        self.assertFalse(record.local)
        self.assertEqual(r.parameters[0]['symbol_id'],record.symbol_id)

    def test_official_areas_and_file_record_lengths(self):
        expected={'BUSCA01A.cbl':(26,[43]),'CAD0004A.cbl':(48,[47]),
            'CAD0005A.cbl':(504,[45]),'CAIXAREG.cbl':(61,[]),
            'CALCMD01.cbl':(41,[]),'PROG024A.cbl':(3980,[76,113])}
        for name,(working,records) in expected.items():
            r=self.official[name]
            self.assertEqual(r.layout.areas['WORKING-STORAGE'],working)
            self.assertEqual(sorted(n for f in r.files.values() for n in f['record_lengths']),records)

    def test_prog024a_homonyms_and_progdata_layout(self):
        r=self.official['PROG024A.cbl']
        homonyms=r.table.candidates('TAB-ENT-LINHA',['data'])
        self.assertEqual(len(homonyms),2)
        self.assertEqual(homonyms[1].parent,homonyms[0].id)
        self.assertEqual(r.layout.for_symbol(homonyms[0]).size,3800)
        call=next(iter(r.calls.values()))
        self.assertEqual(call['status'],'resolved')
        self.assertEqual(call['arguments'][0]['length'],r.source_results[0].parameters[0]['type']['length'])
        self.assertTrue(call['parameter_bindings'])

    def test_corpus_totals_distinguish_local_validity_and_link_pending(self):
        self.assertEqual(self.report['summary']['successful_programs'],68)
        counts=self.report['summary']['classifications']
        self.assertEqual(counts['semantic_valid'],62)
        self.assertEqual(counts['valid_pending_external'],6)
        self.assertEqual(counts['partially_supported'],1)
        self.assertEqual(counts['invalid_source'],13)

    def test_real_errors_and_unsupported_are_not_counted_as_valid(self):
        expected={'ASCII001.cbl':'UNDEFINED_SYMBOL','PROG018A.cbl':'INVALID_ALTER_TARGET',
            'PROGVSAM.cbl':'INVALID_FILE_ACCESS','PROGTEST.cbl':'UNSUPPORTED_SCREEN'}
        for name,code in expected.items():
            row=self.report['files']['examples/complementares/'+name]
            self.assertFalse(row['success'])
            self.assertIn(code,[d['code'] for d in row['diagnostics']])
        self.assertEqual(self.report['files']['examples/complementares/PROGTEST.cbl']['classification'],'partially_supported')

    def test_external_c_calls_and_missing_conflicted_program_remain_pending(self):
        main=self.report['files']['examples/complementares/CAD0001A.cbl']
        self.assertEqual([c['name'] for c in main['external_calls']],['SORT001A'])
        self.assertIn('examples/oficiais/CAD0002A.cbl',main['source_dependencies'])
        curses=self.report['files']['examples/complementares/NCURSESDEMO.cbl']
        self.assertTrue(curses['success'])
        self.assertIn('MVPRINTW',[c['name'] for c in curses['external_calls']])
        self.assertEqual(curses['external_calls'][0]['original_name'],'initscr')

    def test_copybooks_only_have_contextual_semantics_and_original_negative_remains(self):
        for name in ('COD001A','COPY002A'):
            item=self.report['files'][f'examples/dependencias/{name}.cpy']
            self.assertEqual(item['classification'],'copybook_context_only')
            self.assertEqual(item['semantic'],'not_run')
        original=self.report['files']['examples/oficiais/CAD0005A.cbl']
        self.assertEqual(original['lexing'],'error')
        self.assertEqual(original['semantic'],'not_run')

    def test_report_artifacts_are_fresh_and_portable(self):
        self.assertEqual(fingerprint(self.report),corpus_contracts()['semantic_sha256'])
        self.assertNotIn(str(ROOT),json.dumps(self.report))
