"""Oráculo opcional: comparação integral de saídas, retorno e arquivos."""
import shutil
import unittest
from tools.comparar_gnucobol import run_scenarios


@unittest.skipUnless(shutil.which('cobc'),'GnuCOBOL não disponível; testes próprios permanecem ativos')
class OracleTests(unittest.TestCase):
    def test_officials_dependencies_and_three_complementary_families(self):
        report=run_scenarios()
        self.assertEqual(report['summary']['compiled'],11)
        self.assertEqual(report['summary']['validated_scenarios'],30)
        self.assertEqual(report['summary']['oracle_compared'],29)
        self.assertEqual(report['summary']['oracle_matched'],29,
            {n:s['differences'] for n,s in report['scenarios'].items() if s['differences']})
        self.assertTrue(all(s['validated'] for s in report['scenarios'].values()))
