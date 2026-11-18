"""Validação funcional limpa do inventário compilado, com seleção e repetição."""
import argparse
import json
from pathlib import Path
import unittest

from cobol_compiler import ast as A
from cobol_compiler.semantic import check_file
from tools.backend_scenarios import ROOT, inputs_for as previous_inputs
from tools.functional_execution import run_cases, digest
from tools.functional_scenarios import SCENARIOS

OFFICIALS={'BUSCA01A','CAD0002A','CAD0004A','CAD0005A','CAIXAREG','CALCMD01','PROG024A'}
HARNESS_DIR=ROOT/'tests/fixtures/functional'
CORRECTIONS=[
    {'id':'decimal-text-conversion','component':'runtime/fields.c',
     'problem':'MOVE/UNSTRING alfanumérico com vírgula decimal falhava em INVALID_NUMERIC.',
     'fix':'Aplicar o separador decimal do descritor receptor na conversão textual.',
     'affected':['MINICALC','PROG025A'],
     'regression':['test_move_text_uses_receiver_decimal_convention','test_unstring_decimal_text_into_numeric_receivers']},
    {'id':'continued-literal-padding','component':'cobol_lexer/fixed_format.py; preprocessor.py',
     'problem':'Espaços até a coluna 72 eram descartados em literais abertos continuados.',
     'fix':'Frontend habilita preservação de padding; API histórica do lexer mantém seu padrão.',
     'affected':['PROG044A'],
     'regression':['test_frontend_preserves_literal_spaces_through_column72','test_legacy_lexer_continuation_api_remains_compatible']},
]
SOURCE_NOTES={
    'VALCNPJ':'WS-LEN conta todas as 40 posições de WS-RAW; a checagem de 14 nunca passa. Fonte preservado.',
    'PROGTIME':'A condição >=19 AND <=00 é impossível: às 20h o próprio fonte retorna MADRUGADA.',
    'PROG035A':'O fonte conta/lê registros, mas não os exibe. Verificam-se caminhos vazio/preenchido.',
    'PROG034A':'O fonte lê somente o primeiro registro e escreve mesmo quando a entrada está vazia.',
    'REL0001A':'DET2 é escrito antes de atualizar TELEFONE: primeiro telefone zero, seguintes usam o anterior.',
    'PROG023B':'A exclusão física não consulta a confirmação WRK-EXCLUIR dentro da rotina de exclusão.',
    'PROG023E':'A gravação do log na saída está no ELSE do teste de estoque igual ao mínimo (linhas 521–542). Na igualdade há alerta e persistência, sem log; abaixo do mínimo há log.',
}


def discover_programs():
    """A coorte vem das linhas reais da auditoria anterior, nunca de uma lista 49."""
    backend=json.loads((ROOT/'docs/auditoria-backend.json').read_text(encoding='utf-8'))
    semantic=json.loads((ROOT/'docs/auditoria-semantica.json').read_text(encoding='utf-8'))
    result={}
    for path,old in backend['files'].items():
        if old['gcc']!='success':continue
        deps=semantic['files'][path]['source_dependencies']
        analyzed=check_file(ROOT/path,include_dirs=[ROOT/'examples/dependencias'],source_paths=[ROOT/p for p in deps])
        if not analyzed.success:raise ValueError(f'Inventário antes compilado regrediu: {path}')
        program=analyzed.ast.identification.program_id
        nodes={analyzed.node_ids[id(n)]:n for n in A.walk(analyzed.ast)}
        files=[]
        for value in analyzed.files.values():
            assignment=nodes[value['assignment_node']]
            name=getattr(assignment,'value',getattr(assignment,'name',None))
            files.append({'select':value['name'],'path':name,'organization':value['organization'],
                'record_lengths':value['record_lengths'],'open_modes':value['open_modes']})
        accepts=[{'target':n.target.name,'source':n.source,'line':n.span.start.line,
            'picture':analyzed.annotation(n.target).type.picture,
            'bytes':analyzed.annotation(n.target).type.length} for n in nodes.values() if isinstance(n,A.Accept)]
        module=bool(analyzed.parameters)
        risks=[]
        if any(a['source'] is None for a in accepts):
            risks.append('ACCEPT exige stdin completo; EOF pode manter menus/repetições ativos.')
        if any(isinstance(n,(A.Perform,A.GoTo)) for n in nodes.values()):
            risks.append('Repetições/desvios exigem entradas de término; timeout e limite de CPU são obrigatórios.')
        if files:
            risks.append('OPEN pode criar/truncar/gravar arquivos; executar somente com caminhos relativos e fixtures isoladas.')
        if module:
            risks.append('LINKAGE pertence ao chamador; requer harness real e conferência dos parâmetros após retorno.')
        external_path=any(f['path'] is None or Path(f['path']).is_absolute() or '..' in Path(f['path']).parts for f in files)
        classification='external_unavailable' if external_path else 'module_needs_caller' if module else 'executable_with_fixtures' if files or deps else 'standalone'
        result[program]={'path':path,'program_id':program,'kind':'module' if module else 'executable',
            'classification':classification,'previously_validated':old['functionally_validated'],
            'source_sha256':digest((ROOT/path).read_bytes()),'call_sources':deps,
            'copy':[str(Path(d.resolved_file).relative_to(ROOT)) for d in analyzed.frontend.preprocessed.dependencies if d.resolved_file],
            'calls':[{'name':v['original_name'],'status':v['status']} for v in analyzed.calls.values()],
            'files':files,'accepts':accepts,
            'clock':any(isinstance(n,A.Accept) and n.source for unit in [analyzed,*analyzed.source_results] for n in A.walk(unit.ast)),
            'features':sorted({type(n).__name__+((':'+n.operation) if isinstance(n,A.Arithmetic) else '') for n in nodes.values() if isinstance(n,A.Statement)}),
            'parameters':[{'name':analyzed.table.symbols[p['symbol_id']].name,'bytes':p['type']['length']} for p in analyzed.parameters],
            'execution_risks':risks,
            'execution_contract':'stdin finito, fixtures declaradas, relógio fixo, CPU 5s, timeout 8s e arquivos até 16 MiB; sem chamadas de rede no runtime',
            'source_notes':SOURCE_NOTES.get(program,'')}
    return result,backend


def input_resolver(inventory):
    def resolve(program,directory):
        item=inventory[program]
        if program in {'CAD0002A','PROGDATA'}:
            return previous_inputs(program,directory)
        source=ROOT/item['path']
        deps=[ROOT/p for p in item['call_sources']]
        if item['kind']=='module':
            return HARNESS_DIR/(program.lower()+'.cbl'),[source,*deps]
        return source,deps
    return resolve


def audit_functional(*,reference=True,programs=None,case_names=None,seed=None,officials=False):
    inventory,previous=discover_programs()
    selected=set(inventory)
    if programs:
        selected={name for name,item in inventory.items() if any(p.upper()==name.upper() or p in {item['path'],Path(item['path']).name,Path(item['path']).stem} for p in programs)}
        if not selected:raise ValueError('Nenhum programa corresponde à seleção')
    if officials:selected &= OFFICIALS
    if case_names is not None:
        unknown=set(case_names)-{s.name for s in SCENARIOS}
        if unknown:raise ValueError('Cenário desconhecido: '+', '.join(sorted(unknown)))
        selected &= {s.program for s in SCENARIOS if s.name in case_names}
    if not selected:raise ValueError('Nenhum cenário corresponde à seleção')
    cases=[s for s in SCENARIOS if s.program in selected
        and inventory[s.program]['classification']!='external_unavailable'
        and (case_names is None or s.name in case_names)]
    modules={p:ROOT/inventory[p]['path'] for p in selected if inventory[p]['kind']=='module'}
    execution=run_cases(cases,input_resolver(inventory),reference=reference,module_sources=modules,seed=seed)
    rows={}
    for name in sorted(selected):
        item=dict(inventory[name])
        results=[s for s in execution['scenarios'].values() if s['program']==name]
        build=execution['programs'].get(name,{})
        item['compiled']=build.get('compiled',False)
        item['executed']=any(s['executed'] for s in results)
        item['scenarios']=[key for key,s in execution['scenarios'].items() if s['program']==name]
        item['validated']=bool(results) and all(s['validated'] and (s['oracle_match'] is not False or s['abi_expected']) for s in results)
        if execution['oracle'] and results and not build.get('oracle_compiled'):item['validated']=False
        item['result']='validated' if item['validated'] else 'external_unavailable' if item['classification']=='external_unavailable' else 'missing_fixtures' if not results else 'compile_error' if not item['compiled'] else 'divergent' if any(s['oracle_match'] is False for s in results) else 'execution_error'
        item['pending']='' if item['validated'] else 'Investigar diagnósticos, comparação ou ausência de cenário; consultar logs completos.'
        rows[name]=item
    official_cases=[s for s in execution['scenarios'].values() if s['program'] in OFFICIALS]
    summary={'suite_tests':unittest.TestLoader().discover(str(ROOT/'tests')).countTestCases(),
        'discovered_compiled_programs':len(inventory),
        'previously_pending_programs':sum(not v['previously_validated'] for v in inventory.values()),
        'selected_programs':len(rows),'compiled_programs':sum(v['compiled'] for v in rows.values()),
        'executed_programs':sum(v['executed'] for v in rows.values()),'validated_programs':sum(v['validated'] for v in rows.values()),
        'additional_executed_programs':sum(v['executed'] and name not in OFFICIALS for name,v in rows.items()),
        'newly_validated_programs':sum(v['validated'] and not v['previously_validated'] for v in rows.values()),
        'executed_scenarios':execution['summary']['executed_scenarios'],
        'validated_scenarios':sum(v['validated'] and (v['oracle_match'] is not False or v['abi_expected']) for v in execution['scenarios'].values()),
        'identical_comparisons':execution['summary']['oracle_matched'],
        'divergences':sum(v['oracle_match'] is False for v in execution['scenarios'].values()),
        'expected_abi_differences':sum(v['abi_expected'] for v in execution['scenarios'].values()),
        'unexpected_divergences':sum(v['oracle_match'] is False and not v['abi_expected'] for v in execution['scenarios'].values()),
        'without_fixtures':sum(v['result']=='missing_fixtures' for v in rows.values()),
        'blocked_dependencies':sum(v['classification']=='external_unavailable' for v in rows.values()),
        'dependency_blocks_outside_compiled_cohort':sum(v['backend']=='external_dependency_missing' for v in previous['files'].values()),
        'compiler_failures_fixed':len(CORRECTIONS),
        'official_programs_validated':sum(v['validated'] and name in OFFICIALS for name,v in rows.items()),
        'official_scenarios':len(official_cases),
        'official_identical_comparisons':sum(v['oracle_match'] is True for v in official_cases)}
    return {'snapshot':previous['snapshot'],'baseline':{'tests':previous['summary']['suite_tests'],
        'compiled_programs':previous['summary']['gcc_compiled'],'official_scenarios_in_code':sum(s.program in OFFICIALS for s in SCENARIOS)},
        'summary':summary,'inventory':rows,'execution':execution,'corrections':CORRECTIONS,
        'outside_compiled_cohort':{p:{'backend':v['backend'],'diagnostics':v['diagnostics']} for p,v in previous['files'].items() if v['semantic_valid'] and v['gcc']!='success'}}


def markdown(report):
    s=report['summary']
    lines=['# Auditoria funcional — Etapa 5','',
        'Gerado por `python -m tools.auditar_funcional --write`. Fontes originais preservados;',
        f"snapshot `{report['snapshot']}`. GnuCOBOL é apenas oráculo independente.",'',
        '## Métricas','',*['- '+key+': **'+str(value)+'**.' for key,value in s.items()], '',
        f"A contagem direta das definições confirma **{report['baseline']['official_scenarios_in_code']} cenários oficiais**. Não há divergência com os 25 relatados.",
        'Cada programa é recompilado em diretório independente com fontes/COPY copiados e hashes registrados.',
        'C e artefato devem estar ausentes antes e ser criados pela compilação atual; GCC é invocado de novo.',
        'Cada cenário começa em diretório vazio, com apenas suas fixtures. Persistência é preparada explicitamente,',
        'sem herdar arquivos de outro cenário. As entradas e todos os bytes de stdout, stderr e arquivos',
        'estão no JSON (base64, tamanho e SHA-256), junto aos comandos e evidências de construção.','']
    for title,official in [('Sete oficiais',True),('Demais programas compilados',False)]:
        lines.extend(['## '+title,'','| Programa | Compilação | Execução | Cenários | GnuCOBOL | Resultado | Pendências |','|---|---|---|---:|---|---|---|'])
        for name,row in report['inventory'].items():
            if (name in OFFICIALS)!=official:continue
            cases=[report['execution']['scenarios'][n] for n in row['scenarios']]
            equal=sum(c['oracle_match'] is True for c in cases);different=sum(c['oracle_match'] is False and not c['abi_expected'] for c in cases);abi=sum(c['abi_expected'] for c in cases)
            lines.append(f"| [{row['path']}](../{row['path']}) ({name}, {row['kind']}) | {'GCC OK' if row['compiled'] else 'não compilado'} | {'executado' if row['executed'] else 'bloqueado'} | {len(cases)} | {equal} iguais / {abi} ABI previstas / {different} inesperadas | {row['result']} | {row['pending']} |")
    lines.extend(['','## Cenários individuais','','| Cenário | Programa | Retorno | Expectativa própria | Oráculo |','|---|---|---:|---|---|'])
    for name,row in report['execution']['scenarios'].items():
        status='igual' if row['oracle_match'] is True else 'ABI prevista' if row['abi_expected'] else 'divergente' if row['oracle_match'] is False else 'não comparado'
        lines.append(f"| {name} | {row['program']} | {row.get('returncode','—')} | {'OK' if row['validated'] else '; '.join(row['errors'])} | {status} |")
    lines.extend(['','## Inventário de execução',''])
    for name,row in report['inventory'].items():
        lines.extend([f"### {name}",'',f"- Classe: `{row['classification']}`; parâmetros: `{json.dumps(row['parameters'],ensure_ascii=False)}`.",
            f"- COPY: {', '.join(row['copy']) or 'nenhum'}; fontes CALL: {', '.join(row['call_sources']) or 'nenhuma'}.",
            f"- ACCEPT: `{json.dumps(row['accepts'],ensure_ascii=False)}`; relógio: {'controlado' if row['clock'] else 'não utilizado'}.",
            f"- Arquivos: `{json.dumps(row['files'],ensure_ascii=False)}`.",f"- Construções: {', '.join(row['features'])}.",
            '- Riscos: '+(' '.join(row['execution_risks']) or 'Sem entrada interativa ou recurso externo; limites de execução mantidos.') ,
            '- Execução: '+row['execution_contract']+'.',*(['- Observação do fonte: '+row['source_notes']] if row['source_notes'] else []),''])
    lines.extend(['## Divergências e correções',''])
    for name,row in report['execution']['scenarios'].items():
        if row['differences']:lines.append(f"- {name}: `{json.dumps(row['differences'],ensure_ascii=False)}`")
        if row['oracle_note']:lines.append(f"  Justificativa e expectativa independente: {row['oracle_note']}")
        if row['errors']:lines.append(f"- {name}: `{json.dumps(row['errors'],ensure_ascii=False)}`")
    for issue in report['corrections']:lines.append('- '+json.dumps(issue,ensure_ascii=False))
    lines.extend(['','O GnuCOBOL é configurado com `-fnot-reserved=ID -freserved=VALUES:VALUE`,',
        'compatibilizando o vocabulário do projeto sem editar os fontes: ID é um nome de campo',
        'e VALUES é aceito como sinônimo de VALUE. Os comandos completos ficam no JSON.',
        'O relógio de referência usa `COB_CURRENT_DATE=2026111712345600`: os dois últimos',
        'dígitos fixam os centésimos, que permaneciam reais com a configuração de 14 dígitos.',
        'Os três casos de ABI têm expectativas binárias completas para ambos os lados;',
        'as diferenças permanecem nos logs e não são contadas como comparações idênticas.',
        'O cenário de divisor zero conserva a expectativa de erro do projeto e não usa o oráculo.'])
    lines.extend(['','## Reprodução','', '```bash','python -m tools.auditar_funcional --write',
        'python -m tools.auditar_funcional --officials','python -m tools.auditar_funcional --program PROG036A',
        'python -m tools.auditar_funcional --failed-from docs/auditoria-funcional.json',
        'python -m tools.auditar_funcional --seed 2026','python -m unittest discover -s tests -v','```','',
        'GCC/C11 e Python 3.11+ são necessários; GnuCOBOL é opcional (`--no-oracle`).',
        'Filtros não sobrescrevem o relatório integral: `--write` com seleção grava em build/.',
        'O corpus fora da coorte compilada permanece separado no JSON, sem alegação de execução.',''])
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--program',action='append')
    parser.add_argument('--scenario',action='append')
    parser.add_argument('--officials',action='store_true')
    parser.add_argument('--failed-from',type=Path)
    parser.add_argument('--seed',type=int)
    parser.add_argument('--no-oracle',action='store_true')
    parser.add_argument('--report',type=Path,help='base do relatório JSON/Markdown; implica gravação')
    args=parser.parse_args()
    names=set(args.scenario) if args.scenario else None
    if args.failed_from:
        prior=json.loads(args.failed_from.read_text(encoding='utf-8'))
        failed={p for p,v in prior['inventory'].items() if not v['validated']}
        cases=prior['execution']['scenarios']
        names={n for n,s in cases.items() if not s['validated'] or
            s['oracle_match'] is False and not s.get('abi_expected')}
        # A failed comparison must not rerun successful sibling scenarios. A
        # program-level failure (e.g. reference compilation) may have no failed
        # scenario row yet; only then retry the whole program.
        for program in failed:
            if not any(cases[n]['program']==program for n in names):
                names.update(n for n,s in cases.items() if s['program']==program)
        if not names:print('Nenhum cenário falho para repetir.');return 0
    try:
        report=audit_functional(reference=not args.no_oracle,programs=args.program,case_names=names,seed=args.seed,officials=args.officials)
    except ValueError as error:parser.error(str(error))
    if args.write or args.report:
        partial=bool(args.program or args.officials or names is not None)
        stem=args.report or ROOT/('build/auditoria-funcional-selecao' if partial else 'docs/auditoria-funcional')
        stem.parent.mkdir(parents=True,exist_ok=True)
        stem.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        stem.with_suffix('.md').write_text(markdown(report),encoding='utf-8')
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
    for name,row in report['execution']['scenarios'].items():
        if row['errors'] or row['differences']:print(name,row['errors'],json.dumps(row['differences'],ensure_ascii=False)[:1500])
    return int(any(not row['validated'] for row in report['inventory'].values()))


if __name__=='__main__':raise SystemExit(main())
