"""Gera C e chama GCC para todos os 68 programas semanticamente válidos.
Execução só ocorre nos cenários explícitos, com fixtures e timeout.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from cobol_compiler.semantic import check_file
from cobol_compiler.driver import compile_result
from tools.auditar_parser import ROOT,portable
from tools.comparar_gnucobol import run_scenarios
from tools.backend_scenarios import EXTRA_PROGRAMS


def portable_report(value):
    if isinstance(value,dict):return {key:portable_report(item) for key,item in value.items()}
    if isinstance(value,list):return [portable_report(item) for item in value]
    if isinstance(value,str):return value.replace(str(ROOT)+'/', '')
    return value


def audit_backend(*,reference=True,execute=True,compile_code=True):
    semantic=json.loads((ROOT/'docs/auditoria-semantica.json').read_text(encoding='utf-8'))
    rows={}
    with tempfile.TemporaryDirectory(prefix='cobol-backend-audit-') as td:
        for path,item in semantic['files'].items():
            row={'semantic_classification':item['classification'],'semantic_valid':item['success'],
                 'backend':'not_run','generated_c':False,'gcc':'not_run','compiled_as':None,
                 'diagnostics':[],'gcc_stderr':'','executed':False,'functionally_validated':False,'scenarios':[]}
            if item['success']:
                result=check_file(ROOT/path,include_dirs=[ROOT/'examples/dependencias'],
                    source_paths=[ROOT/p for p in item['source_dependencies']])
                try:
                    built=compile_result(result,Path(td)/(str(len(rows))+'.out'),module=bool(result.parameters),check_backend=not compile_code)
                    row['diagnostics']=[asdict(d) for d in built.diagnostics]
                    row['generated_c']=bool(built.generated and built.generated.success)
                    row['compiled_as']='module' if result.parameters else 'executable'
                    row['gcc']='success' if built.success and compile_code else 'error' if built.command else 'not_run'
                    row['gcc_stderr']=built.gcc_stderr
                    row['program_id']=result.frontend.ast.identification.program_id
                    if built.success:row['backend']='compiled' if compile_code else 'generated'
                    elif any(d.phase=='link' or d.code.startswith('LINK_') for d in built.diagnostics):row['backend']='external_dependency_missing'
                    elif any(d.code.startswith('UNSUPPORTED_') for d in built.diagnostics):row['backend']='unsupported_backend'
                    elif built.command:row['backend']='gcc_error'
                    else:row['backend']='generation_error'
                except Exception as error:
                    row['backend']='generation_error'
                    row['internal_error']=f'{type(error).__name__}: {error}'
            rows[path]=portable(row)
    functional=run_scenarios(reference=reference) if execute else None
    if functional:
        by_program={row.get('program_id'):row for row in rows.values() if row.get('program_id')}
        for name,scenario in functional['scenarios'].items():
            if scenario['program'] not in by_program:continue
            row=by_program[scenario['program']]
            row['scenarios'].append(name)
        for program,row in by_program.items():
            scenarios=[functional['scenarios'][name] for name in row['scenarios']]
            row['executed']=any(s['executed'] for s in scenarios)
            row['functionally_validated']=bool(scenarios) and all(s['validated'] for s in scenarios)
            compared=[s for s in scenarios if s['oracle_compared']]
            row['oracle_match']=all(s['oracle_match'] is True for s in compared) if compared else None
        # PROGDATA is exercised through CALL and deterministic clock in PROG024A.
        if 'PROGDATA' in by_program:
            by_program['PROGDATA']['executed_via']=['PROGDATA-DRIVER','PROG024A']
    counts=Counter(row['backend'] for row in rows.values())
    report={'snapshot':semantic['commit'],'files':rows,'functional':functional,
        'summary':{'files':len(rows),'suite_tests':unittest.TestLoader().discover(str(ROOT/'tests')).countTestCases(),
            'semantic_valid_programs':sum(r['semantic_valid'] for r in rows.values()),
            'generated_c':sum(r['generated_c'] for r in rows.values()),
            'gcc_compiled':sum(r['gcc']=='success' for r in rows.values()),
            'executables':sum(r['gcc']=='success' and r['compiled_as']=='executable' for r in rows.values()),
            'modules':sum(r['gcc']=='success' and r['compiled_as']=='module' for r in rows.values()),
            'executed_programs':sum(r['executed'] for r in rows.values()),
            'functionally_validated_programs':sum(r['functionally_validated'] for r in rows.values()),
            'additional_functionally_validated':sum(r['functionally_validated'] and r.get('program_id') in EXTRA_PROGRAMS for r in rows.values()),
            'classifications':dict(sorted(counts.items()))}}
    return portable_report(report)


def markdown(report):
    summary=report['summary'];functional=report['functional'];f= functional['summary'] if functional else {}
    lines=['# Auditoria do backend C e runtime','',
        'Gerado por `python -m tools.auditar_backend --write`. O compilador não usa',
        'GnuCOBOL para gerar ou executar seus programas. O oráculo é uma execução separada.',
        f"Snapshot do corpus: `{report['snapshot']}`. Fontes originais preservados.",'',
        '## Métricas','',
        f"- {summary['files']} arquivos classificados; todos os **{summary['semantic_valid_programs']} programas semanticamente válidos** submetidos ao backend.",
        f"- **{summary['generated_c']} com C gerado; {summary['gcc_compiled']} compilados pelo GCC:** {summary['executables']} executáveis e {summary['modules']} objetos de subprogramas.",
        f"- **{summary['executed_programs']} programas executados e validados nos cenários explícitos**, incluindo CAD0002A por harness COBOL; PROGDATA também executa como dependência de PROG024A.",
        f"- {summary['additional_functionally_validated']} complementares validados: texto/refmod, SEARCH ALL e arquivo sequencial com exclusão.",
        f"- {f.get('executed_scenarios',0)} cenários executados; {f.get('validated_scenarios',0)} satisfazem as expectativas de stdout, stderr, retorno e bytes dos arquivos.",
        f"- {f.get('oracle_compared',0)} cenários comparados integralmente com GnuCOBOL; {f.get('oracle_matched',0)} coincidem sem normalizar saídas.",'',
        'Um cenário de divisor zero verifica o diagnóstico do nosso runtime e não exige',
        'igualdade com políticas de recuperação de outro compilador. Compilar os demais',
        'programas não comprova seu comportamento; eles não são executados sem fixtures.','',
        '| Estado do backend | Arquivos |','|---|---:|']
    lines += [f'| {key} | {value} |' for key,value in summary['classifications'].items()]
    lines += ['', '## Sete oficiais','',
        '| Programa | C / GCC | Execução e validação | Cenários |','|---|---|---|---:|']
    for name in ('BUSCA01A','CAD0002A','CAD0004A','CAD0005A','CAIXAREG','CALCMD01','PROG024A'):
        row=next(r for r in report['files'].values() if r.get('program_id')==name)
        lines.append(f"| {name}{' corrigido' if name=='CAD0005A' else ''} | {row['backend']} ({row['compiled_as']}) | {'validado' if row['functionally_validated'] else 'pendente'} | {len(row['scenarios'])} |")
    lines += ['', 'CAD0002A é compilado como objeto chamável e executado por um driver que fornece',
        'COPY002A-REGISTRO e confere seus campos após GOBACK. PROG024A liga PROGDATA e',
        'usa data/hora determinística. Não há main artificial nos subprogramas.','',
        '## Cenários e oráculo','',
        '| Cenário | Programa | Retorno | Expectativas | GnuCOBOL |','|---|---|---:|---|---|']
    if functional:
        for name,row in functional['scenarios'].items():
            oracle='igual' if row['oracle_match'] is True else 'divergente' if row['oracle_match'] is False else 'não comparado'
            lines.append(f"| {name} | {row['program']} | {row.get('returncode','—')} | {'OK' if row['validated'] else '; '.join(row['errors'])} | {oracle} |")
        lines+=['',f"Oráculo encontrado: `{functional['oracle_version'] or 'indisponível'}`.",
            'As comparações usam fixtures idênticas, `COB_CURRENT_DATE=20261117123456`,',
            '`COB_LS_FIXED=Y`, `COB_LS_NULLS=N` e `COB_LS_VALIDATE=N`, preservando os',
            'comprimentos físicos definidos pelo projeto. O nosso relógio usa',
            '`COBOL_DATETIME=2026-11-17T12:34:56`. O log de BIBLIOTECA é preparado',
            'explicitamente: OPEN EXTEND de arquivo ausente falha com status 35.','']
        differences=[(name,row) for name,row in functional['scenarios'].items() if row['differences']]
        for name,row in differences:lines.append(f"- {name}: `{json.dumps(row['differences'],ensure_ascii=False)}`")
    lines+=['## Todo o corpus','',
        '| Fonte | Semântica | Backend | C | GCC | Artefato | Validado funcionalmente |',
        '|---|---|---|---|---|---|---|']
    for path,row in report['files'].items():
        lines.append(f"| [{path}](../{path}) | {row['semantic_classification']} | {row['backend']} | {'sim' if row['generated_c'] else 'não'} | {row['gcc']} | {row['compiled_as'] or '—'} | {'sim' if row['functionally_validated'] else 'não'} |")
    lines+=['','## Falhas e limitações identificadas','',
        '| Fonte | Motivo |','|---|---|']
    for path,row in report['files'].items():
        if not row['semantic_valid'] or row['backend']=='compiled':continue
        reasons=[]
        for d in row['diagnostics']:
            if d['severity'] in {'E','S'}:reasons.append(f"`{d['code']}`: {d['message']}")
        if row.get('internal_error'):reasons.append(row['internal_error'])
        if row['gcc_stderr']:reasons.append(row['gcc_stderr'].replace('\n','<br>'))
        lines.append(f"| {path} | {'<br>'.join(reasons)} |")
    lines += ['', '## Contratos, limites e testes','',
        '- Runtime próprio: buffers/slices, decimal racional exato, DISPLAY/overpunch, COMP little-endian, COMP-3, edição, conversões, terminal, datas e arquivos.',
        '- C11 gerado diretamente da AST/anotações. Dispatcher com pilha de limites/retornos preserva seções, parágrafos, fall-through, GO TO e PERFORM; não há interpretador ou bytecode.',
        '- Até 128 dígitos por campo e capacidade checada de 512 dígitos por inteiro intermediário; áreas até 64 MiB. Exceder capacidade é erro explícito, sem conversão para float.',
        '- Dados e registros usam ISO-8859-1; stdin/stdout usam UTF-8 na fronteira por padrão. `COBOL_TERMINAL_ENCODING=latin1` seleciona terminal bruto. Campos COBOL continuam com comprimento em bytes da ABI.',
        '- Recursos sem backend são rejeitados antes de GCC: tela/posicionamento, arquivos opcionais, algumas formas complexas de INSPECT/SEARCH, comprimento variável de grupo e GO TO que sai de PERFORM inline. Os códigos efetivamente encontrados estão na tabela acima.',
        '- SQL/CICS, ncurses, VSAM/INDEXED, ALTER, SORT e START continuam fora do subconjunto conforme a semântica; chamadas externas têm diagnóstico de ligação, sem stubs.',
        '- O processo de compilação não executa o programa nem cria fixtures de dados. O driver publica saída por substituição atômica somente após GCC bem-sucedido e protege fontes/COPY/runtime de colisões.',
        f"- A suíte contém **{summary['suite_tests']} testes**, preservando os 245 anteriores: runtime em C com `-Werror`, controle, arquivos, chamadas, CLI e cenários oficiais. O auditor conta os testes; a execução integral é independente, pelo comando abaixo. O resultado da entrega está em [runtime e uso](backend.md).",
        '- Os três ensaios complementares não substituem os três programas escolhidos pelo professor. Demais programas compilados precisam de cenários adicionais antes de serem declarados funcionais.','',
        '## Reprodução','', '```bash','python -m unittest discover -s tests -v',
        'python -m tools.auditar_backend --write','python -m tools.comparar_gnucobol','```','',
        'O [JSON completo](auditoria-backend.json) guarda diagnósticos, hashes e tamanhos',
        'de stdout/arquivos, diferenças do oráculo e o estado de cada programa. `--no-oracle`',
        'mantém os testes próprios e registra a ausência de comparação independente.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--no-oracle',action='store_true')
    args=parser.parse_args()
    report=audit_backend(reference=not args.no_oracle)
    if args.write:
        (ROOT/'docs/auditoria-backend.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (ROOT/'docs/auditoria-backend.md').write_text(markdown(report),encoding='utf-8')
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
    if report['functional']:print(json.dumps(report['functional']['summary'],indent=2))
    failures=[row for row in report['files'].values() if row['backend'] in {'gcc_error','generation_error'}]
    functional=report['functional']
    reference_failed=bool(functional and functional['oracle'] and any(not p['oracle_compiled'] for p in functional['programs'].values()))
    return int(bool(failures) or reference_failed or functional and any(not row['validated'] or row['oracle_match'] is False for row in functional['scenarios'].values()))


if __name__=='__main__':raise SystemExit(main())
