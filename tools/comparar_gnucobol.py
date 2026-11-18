"""Oráculo independente opcional. Nenhum resultado deste módulo compõe o backend."""
from tools.backend_scenarios import SCENARIOS, inputs_for
from tools.functional_execution import digest, run_cases


def run_scenarios(*, reference=True):
    return run_cases(SCENARIOS, inputs_for, reference=reference)


if __name__=='__main__':
    import json
    result=run_scenarios()
    print(json.dumps(result['summary'],indent=2))
    for name,item in result['scenarios'].items():
        if item['errors'] or item['differences']:print(name,item['errors'],item['differences'])
    reference_failed=result['oracle'] and any(not p['oracle_compiled'] for p in result['programs'].values())
    raise SystemExit(int(reference_failed or any(not s['validated'] or s['oracle_match'] is False for s in result['scenarios'].values())))
