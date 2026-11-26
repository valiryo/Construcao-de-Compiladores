"""Auditar todo original contra GnuCOBOL, sem reparos ou derivados de fontes."""
import argparse
import base64
from collections import Counter
import json
from pathlib import Path
import platform
import shutil
import subprocess
import unittest

from tools.backend_scenarios import ROOT
from tools.compatibility_corpus import audit_compilation
from tools.compatibility_scenarios import run_batch,run_screens
from tools.auditar_funcional import audit_functional
from tools.execution_gaps import audit_execution_gaps
from tools.functional_execution import digest


FIXES={
    'CBREAKEX':'Formato livre explícito; FD DATA RECORD; edição numérica com sinal flutuante.',
    'PROG042A':'Perfil de identificadores até 63 posições, mantendo o nome original de 31; CALL PROG042B existente.',
    'PROGTEST':'SCREEN SECTION com LINE/COLUMN, BLANK SCREEN, PIC e USING; edição em terminal real.',
    'TESTE002':'DISPLAY posicionado e CRT STATUS.',
    'GAMESNAK':'DISPLAY/ACCEPT posicionados e CURSOR; execução de saída, com RANDOM comparado parcialmente.',
}
DEFERRED={
    'NCURSESDEMO':'Liga ncurses no GnuCOBOL. O runtime próprio executa a inicialização e a escrita, depois rejeita scanw sem destinos de conversão.',
    'PROGTEST2':'Liga ncurses no GnuCOBOL. O runtime próprio recusa o inteiro usado no lugar de WINDOW* em keypad.',
    'PROGTEST3':'Liga ncurses no GnuCOBOL. O runtime próprio rejeita scanw sem destinos de conversão.',
    'CAD0001A':'Carrega as dependências COBOL disponíveis. CALL SORT001A falha quando alcançado. O único SORT001A do snapshot contém conflitos.',
    'main':'CALL exibir_tela permanece no executável e falha por implementação ausente na execução.',
    'ncurses_demo':'O CALL ncurses_wrapper.c e os demais CALLs permanecem no binário. O primeiro falha por implementação ausente.',
}


def version(executable,*args):
    path=shutil.which(executable)
    return subprocess.run([path,*args],capture_output=True,text=True,timeout=10).stdout.splitlines()[0] if path else None


def audit(*,compile_only=False):
    if not shutil.which('cobc'):raise RuntimeError('Esta auditoria comparativa requer GnuCOBOL instalado.')
    report=audit_compilation(call_probes=not compile_only)
    report['mode']='compilation-only' if compile_only else 'compilation-and-functional'
    report['toolchain']={'python':platform.python_version(),'platform':platform.platform(),'gnucobol':version('cobc','-V'),'gcc':version('gcc','--version')}
    report['test_execution']='A contagem não executa a suíte; executar python -m unittest discover -s tests -v separadamente.'
    report['changes']=FIXES
    report['method']={'immutable_originals':True,'dependencies':'Apenas fontes/COPY declarados presentes no snapshot; fechamento de CALL por PROGRAM-ID.',
        'gnu':'-std=default; -fixed ou -free explícito; -fnot-reserved=ID -freserved=VALUES:VALUE para vocabulário do corpus.',
        'analysis':'-fsyntax-only, objeto -c e executável -x separados; -fstatic-call adicional para testar dependências de executáveis.',
        'ours':'compile_file(..., source_format=formato, dialect=gnucobol, source_paths=dependências); comando GCC integral em cada build.',
        'execution':'Diretórios vazios, entradas finitas, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s, arquivos até 16 MiB.',
        'compiler_temporary_files':'Cada compilação GnuCOBOL recebe TMPDIR no diretório exclusivo de build; evita colisões de nomes baseados em PID entre namespaces.',
        'terminal':'PTY 40x100, TERM=ansi, UTF-8, COB_EXIT_WAIT=off; bytes brutos e matriz completa de células conservados.',
        'signed_file':'CBREAKEX: GnuCOBOL -fsign=EBCDIC seleciona overpunch }JKLMNOPQR equivalente à ABI própria; não altera encoding ISO-8859-1 dos registros.'}
    for path,row in report['files'].items():
        row['compilation_category']=row['category']
        stem=Path(path).stem
        row['action']=FIXES.get(stem,DEFERRED.get(stem,'Fonte preservado; manter os testes existentes.' if row['category']=='both_compiled' else 'Registrar diagnóstico; não alterar fonte original.'))
        row['functional']={'executed':False,'compared':False,'status':'not_run'}
    probes={p:r['call_probe'] for p,r in report['files'].items() if 'call_probe' in r}
    report['summary']['deferred_call_probes']={
        'executed':len(probes),'validated':sum(p['validated'] for p in probes.values()),
        'compared_missing_targets':sum(p['reference'] is not None for p in probes.values()),
    }
    for path,probe in probes.items():
        report['files'][path]['functional']['status']=probe['status']
    complete_build=report['summary']['compilation']['ours']==report['summary']['compilation']['gnucobol']==70
    if not compile_only:
        baseline=audit_functional();batch=run_batch();screens=run_screens()
        report['functional_execution']={'baseline':baseline,'batch':batch,'terminal':screens}
        rows=report['files']
        for name,item in baseline['inventory'].items():
            if item['path'] not in rows:continue # Derivada CAD0005A preservada, fora do denominador original.
            cases=[baseline['execution']['scenarios'][s] for s in item['scenarios']]
            abi=any(c['abi_expected'] for c in cases)
            row=rows[item['path']]
            row['functional']={'executed':item['executed'],'compared':any(c['oracle_compared'] for c in cases),
                'status':'known_abi_difference' if abi else 'raw_equal' if item['validated'] else 'failed',
                'contract_validated':item['validated'],'cases':item['scenarios']}
            if abi:row['category']='both_compiled_functional_difference'
        for program in batch['programs']:
            cases={n:r for n,r in batch['scenarios'].items() if r['program']==program}
            valid=bool(cases) and all(c['validated'] and c['oracle_match'] for c in cases.values())
            rows[f'examples/complementares/{program}.cbl']['functional']={'executed':all(c['executed'] for c in cases.values()),
                'compared':all(c['oracle_compared'] for c in cases.values()),'status':'raw_equal' if valid else 'failed','contract_validated':valid,'cases':list(cases)}
        for program in screens['programs']:
            cases={n:r for n,r in screens['scenarios'].items() if r['program']==program}
            valid=all(c['validated'] for c in cases.values());partial=program=='GAMESNAK'
            row=rows[f'examples/complementares/{program}.cbl']
            row['functional']={'executed':True,'compared':True,'status':'partial_random_difference' if partial else 'text_cells_equal' if valid else 'failed',
                'contract_validated':valid and not partial,'partial_probe_validated':valid,'cases':list(cases)}
            if partial:row['category']='both_compiled_functional_difference'
        functions=[r['functional'] for r in rows.values() if r.get('gnu',{}).get('compiled')]
        counts=Counter(r['status'] for r in functions)
        denominator=report['summary']['compilation']['gnucobol']
        equivalent=counts['raw_equal']+counts['text_cells_equal']
        report['summary']['functional']={'original_programs_executed':sum(r['executed'] for r in functions),
            'original_programs_compared':sum(r['compared'] for r in functions),
            'original_programs_equivalent_in_scenarios':equivalent,'gnucobol_programs':denominator,
            'coverage_percent':round(100*equivalent/denominator,4),
            'contracts_validated_including_known_abi':sum(r.get('contract_validated',False) for r in functions),
            'statuses':dict(counts),'baseline_scenarios':baseline['summary']['executed_scenarios'],
            'baseline_validated':baseline['summary']['validated_scenarios'],'officials_validated':baseline['summary']['official_programs_validated'],
            'new_batch_scenarios':len(batch['scenarios']),'new_terminal_scenarios':len(screens['scenarios']),
            'new_scenarios_validated':sum(c['validated'] for c in batch['scenarios'].values())+sum(c['validated'] for c in screens['scenarios'].values()),
            'game_scope':'Uma saída por Q; posição de comida/RANDOM difere; não atesta jogabilidade ou equivalência integral.'}
        report['success']=complete_build and len(probes)==len(DEFERRED) and all(p['validated'] for p in probes.values()) and baseline['summary']['validated_programs']==60 and all(r['validated'] and r['oracle_match'] for r in batch['scenarios'].values()) and all(r['validated'] for r in screens['scenarios'].values())
        report['execution_gaps']=audit_execution_gaps()
        report['success']=report['success'] and report['execution_gaps']['success']
    else:report['success']=complete_build
    report['suite_tests_discovered']=unittest.TestLoader().discover(str(ROOT/'tests')).countTestCases()
    report['implementation_hashes']={str(p.relative_to(ROOT)):digest(p.read_bytes()) for folder in ['cobol_lexer','cobol_compiler','runtime','tools'] for p in sorted((ROOT/folder).rglob('*')) if p.suffix in {'.py','.c','.h'}}
    report['summary']['categories']=dict(Counter(r['category'] for r in report['files'].values()))
    return report


def markdown(report):
    s=report['summary']
    lines=['# Validação de compatibilidade com GnuCOBOL','',
           f"Snapshot `{report['snapshot']}`. Modo `{report['mode']}`. Oráculo `{report['toolchain']['gnucobol']}`.",'',
           '| Unidades comparáveis | Próprio C + GCC | GnuCOBOL | Cobertura |','|---|---:|---:|---:|']
    for label,key in [('Todas','compilation'),('Programas principais','mains'),('Módulos objeto','modules')]:
        counts=s[key]
        lines.append(f"| {label} | {counts['ours']} | {counts['gnucobol']} | {counts['percent']:.2f}% |")
    if s.get('functional'):
        f=s['functional']
        total=f['baseline_validated']+f['new_scenarios_validated']
        lines += ['', f"**{total} cenários** satisfizeram as expectativas, incluindo os {f['officials_validated']} oficiais.",
                  f"{f['original_programs_equivalent_in_scenarios']} originais coincidiram nos cenários comparados por inteiro.",
                  'O JSON contém os casos parciais, as diferenças de ABI, os comandos e as saídas brutas.']
    lines += ['', '| Fonte | Build próprio | Build GnuCOBOL | Resultado funcional |',
              '|---|---|---|---|']
    for path,row in report['files'].items():
        if row['kind']=='copybook':
            ours=reference='fragmento COPY'
        else:
            ours='OK' if row['ours']['success'] else 'bloqueado'
            reference='OK' if row['gnu']['compiled'] else 'bloqueado'
        lines.append(f"| {path} | {ours} | {reference} | {row['functional']['status']} |")
    if 'execution_gaps' in report:
        lines += ['',*gap_markdown(report['execution_gaps'])]
    return '\n'.join(lines)+'\n'


def gap_markdown(gaps):
    lines=['## Revisão final das lacunas de execução','',
        f"Oráculo `{gaps['gnucobol']}`. A revisão inclui o divisor zero e reexecuta os seis CALLs adiados. GAMESNAK ficou fora desta rodada.",
        '', '| Programa | Ponto observado | stdout | stderr | Arquivos | Retorno próprio / GnuCOBOL |',
        '|---|---|---|---|---|---:|']
    for name,row in gaps['cases'].items():
        comparison=row.get('comparison')
        if comparison is None:
            lines.append(f'| {name} | Build interrompido | — | — | — | — |')
            continue
        if row['scope']=='safe_prefix':
            cutoff=row['cutoff']
            point=f"Antes de `{cutoff['target']}`, linha {cutoff['line']}"
        elif row['scope']=='missing_target':
            point=f"Até `{row['target']}` ausente"
        else:
            point='Divisor zero'
        columns=['igual' if comparison[part] else 'diferente' for part in ('stdout','stderr','files')]
        returns=f"{row['ours']['returncode']} / {row['reference']['returncode']}"
        lines.append(f'| {name} | {point} | {" | ".join(columns)} | {returns} |')
    lines.append('')
    zero=gaps['cases']['CALCMD01']
    if zero.get('stdout_prefix') and not zero['comparison']['stdout']:
        ref_stdout=base64.b64decode(zero['reference']['stdout']['base64']).decode(errors='replace')
        average=next((line.partition(':')[2].strip() for line in ref_stdout.splitlines()
                      if line.startswith('VALOR MEDIO:')),None)
        if average is not None:
            lines.append(f'Em CALCMD01, as saídas coincidem até o total. O próprio aborta na divisão por zero. O GnuCOBOL prossegue até exibir a média `{average}`.')
    original_match=sum(r.get('original_ours_stdout_equal',False) for r in gaps['cases'].values())
    lines += [
        'Os três destinos ausentes produziram diagnósticos com redações próprias de cada runtime. A execução com as implementações disponíveis permanece sem verificação.',
        'O ensaio ncurses compila, nos dois compiladores, cópias temporárias do prefixo original até a linha indicada. Depois do prefixo, a cópia chama `endwin` e sai com o marcador 77. Esse retorno é do ensaio. A chamada incompatível e a execução subsequente ficam fora da comparação. Os fontes originais do corpus permanecem intactos.',
        f'A saída do executável próprio original, encerrado pelo diagnóstico e com o terminal restaurado, coincidiu com a saída do prefixo em {original_match}/3 casos.',
        'Os três casos com diferenças conhecidas de ABI já têm comparação de saída na auditoria funcional e ficaram fora desta rodada.',
        'O JSON guarda os comandos de compilação, hashes, entradas, saídas brutas do PTY, arquivos e os bytes usados na derivação do prefixo. A revisão complementa os 152 cenários registrados acima.', '']
    return lines


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--compile-only',action='store_true')
    mode.add_argument('--execution-gaps',action='store_true',help='comparar somente as lacunas da revisão final, sem executar GAMESNAK')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    if args.execution_gaps:
        report=audit_execution_gaps()
        rendered='\n'.join(gap_markdown(report))
        stem='compatibilidade-execucao'
    else:
        report=audit(compile_only=args.compile_only)
        rendered=markdown(report)
        stem='compatibilidade-compilacao' if args.compile_only else 'compatibilidade'
    encoded=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(encoded,encoding='utf-8')
    if args.write:
        output=ROOT/'build'
        output.mkdir(exist_ok=True)
        (output/(stem+'.json')).write_text(encoded,encoding='utf-8')
        (output/(stem+'.md')).write_text(rendered,encoding='utf-8')
    print(rendered if args.execution_gaps else json.dumps(report['summary'],ensure_ascii=False,indent=2))
    return 0 if report['success'] else 1


if __name__=='__main__':raise SystemExit(main())
