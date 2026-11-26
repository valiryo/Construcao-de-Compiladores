"""Contratos compactos para selecionar e verificar a coorte de regressão."""

import hashlib
import json

from tools.backend_scenarios import ROOT


def corpus_contracts():
    return json.loads((ROOT/'tests/fixtures/corpus-contracts.json').read_text(encoding='utf-8'))


def fingerprint(value):
    encoded=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def backend_contract(contracts):
    return {
        'snapshot':contracts['commit'],
        'files':{path:entry['backend'] for path,entry in contracts['files'].items()},
        'summary':contracts['backend_summary'],
        'functional':contracts['backend_execution'],
    }
