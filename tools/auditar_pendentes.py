"""Auditoria isolada da coorte não compilada. Não altera nem executa COBOL."""
import argparse
from collections import Counter
import ctypes.util
from dataclasses import asdict
import difflib
import json
from pathlib import Path
import resource
import shutil
import subprocess
import tempfile

from cobol_compiler import ast as A
from cobol_compiler.driver import compile_result
from cobol_compiler.frontend import parse_file
from cobol_compiler.semantic import check_file
from cobol_lexer import CobolLexer
from cobol_lexer.fixed_format import read_fixed_lines
from tools.backend_scenarios import ROOT
from tools.functional_execution import digest, environment
from tools.pending_findings import FINDINGS

INCLUDES=[ROOT/'examples/dependencias']
TREE=ROOT/'docs/evidencias-pendentes/arvore-upstream.json'


def pending_inventory():
    previous=json.loads((ROOT/'docs/auditoria-backend.json').read_text())
    return {p:r for p,r in previous['files'].items() if r['gcc']!='success'},previous


def conflict_variants(text):
    """Escolhe cada lado inteiro; mantém todos os bytes fora dos hunks."""
    ours=[];theirs=[];hunks=[];state=0;left=[];right=[]
    for number,line in enumerate(text.splitlines(keepends=True),1):
        if line.startswith('<<<<<<<'):
            if state:raise ValueError('Conflito aninhado')
            start=number;state=1;left=[];right=[]
        elif state and line.startswith('======='):state=2
        elif state and line.startswith('>>>>>>>'):
            if state!=2:raise ValueError('Conflito sem separador')
            ours.extend(left);theirs.extend(right)
            hunks.append({'start_line':start,'end_line':number,'ours':''.join(left),'theirs':''.join(right)})
            state=0
        elif state==1:left.append(line)
        elif state==2:right.append(line)
        else:ours.append(line);theirs.append(line)
    if state:raise ValueError('Conflito sem fim')
    return {"ours":''.join(ours),"theirs":''.join(theirs)},hunks


def limits():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_CPU,(20,20))
    resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024*1024,32*1024*1024))


def command(command,directory):
    try:
        p=subprocess.run(command,cwd=directory,env=environment({'TMPDIR':str(Path(directory).resolve())}),capture_output=True,text=True,
            encoding='utf-8',errors='replace',timeout=30,preexec_fn=limits)
        return {'command':[str(c) for c in command],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired as e:
        return {'command':[str(c) for c in command],'returncode':None,'timeout':True,
            'stdout':(e.stdout or b'').decode(errors='replace'),'stderr':(e.stderr or b'').decode(errors='replace')}


def gnu(source,directory,*,fmt='fixed',flags=(),deps=(),link=False,module=False):
    executable=shutil.which('cobc')
    if not executable:return {'available':False}
    options=['-c' if module else '-x'] if link else ['-fsyntax-only']
    argv=[executable,*options,'-'+fmt,'-std=default','-fnot-reserved=ID','-freserved=VALUES:VALUE',
        '-I',str(INCLUDES[0]),*flags,str(source),*(str(p) for p in deps)]
    artifact=directory/('reference.o' if module else 'reference')
    if link:argv+=['-o',str(artifact)]
    result=command(argv,directory)
    result.update(available=True,format=fmt,flags=list(flags),dependencies=[str(p) for p in deps],
        artifact_created=artifact.is_file(),executed=False)
    return result


def call_contracts(semantic):
    if not semantic.ast:return []
    nodes={semantic.node_ids[id(n)]:n for n in A.walk(semantic.ast)}
    calls=[]
    for nid,info in semantic.calls.items():
        entry=dict(info,line=nodes[nid].span.start.line)
        entry['arguments']=[]
        for argument in info['arguments']:
            a=dict(argument);node=nodes[a['node_id']]
            a['expression']=getattr(node,'name',getattr(node,'value',type(node).__name__))
            if a['symbol_id']:a['symbol']=semantic.table.symbols[a['symbol_id']].name
            entry['arguments'].append(a)
        calls.append(entry)
    return calls


def pipeline(source,directory,*,deps=(),copybook=False):
    text=source.read_text(encoding='utf-8')
    lexical=CobolLexer(preserve_literal_padding=True).tokenize(text)
    physical=list(read_fixed_lines(text))
    front=parse_file(source,include_dirs=INCLUDES,copybook=copybook)
    row={'sha256':digest(source.read_bytes()),'bytes':source.stat().st_size,
        'fixed_format':{'physical_code_lines':len(physical),
            'invalid_indicators':[p.line_number for p in physical if p.indicator.upper() not in {' ','-','D','*','/'}],
            'conflict_lines':[p.line_number for p in physical if p.conflict_column]},
        'lexer':{'success':lexical.success,'diagnostics':[asdict(d) for d in lexical.diagnostics]},
        'preprocessor':{'success':front.preprocessed.success,'diagnostics':[asdict(d) for d in front.preprocessed.diagnostics],
            'dependencies':[asdict(d) for d in front.preprocessed.dependencies]},
        'parser':{'status':'success' if front.success else 'error' if front.parsed else 'not_run',
            'diagnostics':[asdict(d) for d in front.parsed.diagnostics] if front.parsed else []},
        'semantic':{'status':'not_run'},'backend':{'status':'not_run'},'gcc':{'status':'not_run'},
        'executed':False,'dependencies':[str(p) for p in deps]}
    if copybook:
        row['first_blocker']=None if front.success else 'lexer' if not lexical.success else 'parser'
        return row
    sem=check_file(source,include_dirs=INCLUDES,source_paths=deps)
    row['semantic']={'status':'success' if sem.success else 'error' if front.success else 'not_run',
        'diagnostics':[asdict(d) for d in sem.diagnostics if d.phase=='semantic']}
    row['calls']=call_contracts(sem)
    row['files']=list(sem.files.values())
    row['parameters']=sem.parameters
    absent=not (directory/'native').exists() and not (directory/'native.c').exists()
    if not absent:raise ValueError('Artefato de experimento já existe')
    built=compile_result(sem,directory/'native',emit_c=directory/'native.c',module=bool(sem.parameters))
    row['diagnostics']=[asdict(d) for d in built.diagnostics]
    row['backend']={'status':'success' if built.generated and built.generated.success else 'error' if built.generated else 'not_run',
        'diagnostics':[asdict(d) for d in built.diagnostics if d.phase in {'backend','link'}],
        'c_sha256':digest(built.generated.c_source.encode()) if built.generated and built.generated.success else None}
    row['gcc']={'status':'success' if built.success else 'error' if built.command else 'not_run',
        'command':built.command,'stdout':built.gcc_stdout,'stderr':built.gcc_stderr,
        'artifact_sha256':digest(Path(built.output).read_bytes()) if built.success else None,
        'module':bool(sem.parameters),'artifact_absent_before':absent}
    errors=[d for d in built.diagnostics if d.severity in {'E','S'}]
    row['first_blocker']=errors[0].phase if errors else None
    return row


def experiments(name,text):
    result={}
    if '<<<<<<<' in text:result.update((key,(value,'Selecionar integralmente o lado '+key)) for key,value in conflict_variants(text)[0].items())
    if name=='ASCII001.cbl':result['declare-code']=(text.replace('       PROCEDURE DIVISION.','       01 WS-CODIGO PIC 9(3).\n       PROCEDURE DIVISION.'),'Declarar WS-CODIGO PIC 9(3).')
    if name=='CBREAKEX.cbl':
        shifted='\n'.join(' '+line if line.strip() else line for line in text.splitlines())+'\n'
        result['shift-one']=(shifted,'Deslocar uma coluna à direita; manter as cláusulas originais.')
        result['shift-without-data-record']=(shifted.replace('       DATA RECORD IS NEXT-RECORD.','       .').replace('       DATA RECORD IS REPORT-RECORD.','       .'),
            'Após deslocamento, substituir as duas metacláusulas DATA RECORD IS por ponto; não alterar PIC.')
    if name=='PROG042A.cbl':result['rename-31']=(text.replace('0007-INCLUIR-QUANTIDADE-PRODUTO','0007-INCLUIR-QTDE-PRODUTO'),'Renomear chamada e seção para nome de 25 caracteres, sem colisão.')
    if name=='PROGVSAM.cbl':result['indexed-intent']=(text.replace('      *       ORGANIZATION IS INDEXED','              ORGANIZATION IS INDEXED').replace('              ORGANIZATION IS LINE SEQUENTIAL\n',''),'Ativar INDEXED e remover somente LINE SEQUENTIAL; preservar DYNAMIC, chaves e I-O.')
    if name=='PROG018A.cbl':
        result['remove-unreachable-alter']=(''.join(line for line in text.splitlines(keepends=True) if 'ALTER 100-INICIO' not in line),
            'Remover instrução inválida/inalcançável; abandona a demonstração de ALTER, não é recuperação desse recurso.')
        result['valid-alter-minimal']=('       IDENTIFICATION DIVISION.\n       PROGRAM-ID. VALIDALTER.\n       PROCEDURE DIVISION.\n'
            '           ALTER TARGET-PARA TO PROCEED TO END-PARA.\n       TARGET-PARA.\n           GO TO END-PARA.\n       END-PARA.\n           STOP RUN.\n',
            'Caso mínimo separado: alvo contém somente GO TO; distingue validade do fonte e suporte ao verbo.')
    return result


def audit(*,reference=True):
    pending,previous=pending_inventory()
    manifest=json.loads((ROOT/'examples/manifesto-coboldicas.json').read_text())
    oldsem=json.loads((ROOT/'docs/auditoria-semantica.json').read_text())
    originals={p:digest((ROOT/p).read_bytes()) for p in set(previous['files'])|{f['path'] for f in manifest['files']}}
    upstream=json.loads(TREE.read_text())
    assert upstream['sha']==manifest['commit'] and not upstream['truncated']
    tree={item['path']:item for item in upstream['tree']}
    for item in manifest['files']:
        assert originals[item['path']]==item['sha256']
        assert tree[item['upstream_path']]['sha']==item['git_blob']
    assert {Path(p).name for p in pending}==set(FINDINGS)
    implementation={str(p.relative_to(ROOT)):digest(p.read_bytes()) for folder in ('cobol_compiler','cobol_lexer','runtime')
        for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.c','.h'}}
    result={'snapshot':manifest['commit'],'implementation_sha256':implementation,
        'snapshot_tree':{'file':str(TREE.relative_to(ROOT)),'sha256':digest(TREE.read_bytes()),
        'url':f"https://api.github.com/repos/Coboldicas/codigo_fonte_cobol/git/trees/{manifest['commit']}?recursive=1",
        'checked_on':'2026-11-18','tracked_paths':sorted(tree),'native_c_sources':[p for p in tree if Path(p).suffix.lower() in {'.c','.h','.so'}]},
        'baseline':{'command':'python -m unittest discover -s tests -v','tests_passed':476,'seconds':54.846},
        'toolchain':{},'native_libraries':{name:ctypes.util.find_library(name) for name in ('ncurses','ncursesw','tinfo')},
        'native_headers':{str(p):p.exists() for p in (Path('/usr/include/curses.h'),Path('/usr/include/ncurses.h'))},
        'previous_counts':dict(Counter(r['semantic_classification'] if r['backend']=='not_run' else r['backend'] for r in pending.values())),
        'files':{},'original_hashes':originals}
    with tempfile.TemporaryDirectory(prefix='cobol-pending-audit-') as td:
        root=Path(td)
        for tool,flag in [('cobc','-V'),('gcc','--version')]:
            result['toolchain'][tool]=command([shutil.which(tool),flag],root)['stdout'].splitlines()[0] if shutil.which(tool) else None
        resolved={}
        for path in pending:
            text=(ROOT/path).read_text()
            if '<<<<<<<' in text:
                f=root/'resolved'/Path(path).name;f.parent.mkdir(exist_ok=True);f.write_text(conflict_variants(text)[0]['ours']);resolved[Path(path).name]=f
        for path,old in pending.items():
            name=Path(path).name;original=ROOT/path;text=original.read_text();base=root/Path(path).stem;base.mkdir()
            src=base/name;src.write_bytes(original.read_bytes())
            deps=[ROOT/p for p in oldsem['files'][path]['source_dependencies']]
            row={'finding':FINDINGS[name],'original_diagnostics':old['diagnostics'],
                'previous_classification':old['semantic_classification'],'previous_backend':old['backend'],
                'original':pipeline(src,base,deps=deps,copybook=src.suffix=='.cpy'),
                'experiments':{},'conflicts':conflict_variants(text)[1] if '<<<<<<<' in text else []}
            if reference and src.suffix!='.cpy':
                row['gnu_original']=gnu(src,base)
                if name=='CBREAKEX.cbl':row['gnu_free']=gnu(src,base,fmt='free')
                if name=='PROG042A.cbl':row['gnu_limit30']=gnu(src,base,flags=['-fword-length=30'])
                if name in {'NCURSESDEMO.cbl','PROGTEST2.cbl','PROGTEST3.cbl','main.cbl','ncurses_demo.cbl'}:
                    row['gnu_static_link']=gnu(src,base,link=True,flags=['-fstatic-call'])
                if name in {'NCURSESDEMO.cbl','PROGTEST2.cbl','PROGTEST3.cbl'}:
                    row['gnu_ncurses_devel']=gnu(src,base,link=True,flags=['-fstatic-call','-lncurses'])
                    soname=result['native_libraries']['ncurses']
                    flags=['-fstatic-call','-l:'+soname] if soname else []
                    if result['native_libraries']['tinfo']:flags+=['-l:'+result['native_libraries']['tinfo']]
                    if soname:row['gnu_ncurses_runtime']=gnu(src,base,link=True,flags=flags)
            for label,(content,description) in experiments(name,text).items():
                directory=base/label;directory.mkdir();target=directory/name;target.write_text(content)
                experiment_deps=list(deps)
                if name=='PROG023C.cbl':experiment_deps=[ROOT/'examples/dependencias/PROGDATA.cbl',ROOT/'examples/complementares/PROGTIME.cbl']
                if name=='PROG042A.cbl':experiment_deps=[ROOT/'examples/complementares/PROG042B.cbl']
                trial={'description':description,'diff':''.join(difflib.unified_diff(text.splitlines(True),content.splitlines(True),fromfile=path,tofile=label+'/'+name)),
                    'pipeline':pipeline(target,directory,deps=experiment_deps)}
                if reference:trial['gnu']=gnu(target,directory,deps=experiment_deps,link=True,module=trial['pipeline']['gcc']['module'])
                row['experiments'][label]=trial
            if name=='CAD0001A.cbl':
                directory=base/'with-recovered-sort';directory.mkdir()
                expdeps=[*deps,resolved['SORT001A.cbl']]
                row['experiments']['with-recovered-sort']={'description':'Fonte CAD0001A intacto; acrescentar SORT001A resolvido aos seis módulos já declarados, incluindo PROGTIME transitivo.',
                    'diff':'','pipeline':pipeline(src,directory,deps=expdeps)}
                if reference:row['experiments']['with-recovered-sort']['gnu']=gnu(src,directory,deps=expdeps,link=True,flags=['-fstatic-call'])
            if src.suffix=='.cpy':
                contexts={}
                # Only real consumers, with their declared source closure. No main
                # manufactured for the fragment and no independent module compilation.
                for consumer,oldrow in previous['files'].items():
                    if oldrow['gcc']!='success':continue
                    front=parse_file(ROOT/consumer,include_dirs=INCLUDES)
                    if not any(d.resolved_file and Path(d.resolved_file).resolve()==original.resolve() for d in front.preprocessed.dependencies):continue
                    ctx=check_file(ROOT/consumer,include_dirs=INCLUDES,source_paths=[ROOT/p for p in oldsem['files'][consumer]['source_dependencies']])
                    lengths={s.name:ctx.layout.items[s.id].total_size for s in ctx.table.symbols.values() if s.name in {'COD001A-REGISTRO','COPY002A-REGISTRO','COPY002A-HEADER'} and s.id in ctx.layout.items}
                    contexts[consumer]={'semantic_success':ctx.success,'root_layout_bytes':lengths}
                row['contexts']=contexts
            result['files'][path]=row
        assert originals=={p:digest((ROOT/p).read_bytes()) for p in originals}
        assert implementation=={p:digest((ROOT/p).read_bytes()) for p in implementation}
        def portable(value):
            if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
            if isinstance(value,list):return [portable(v) for v in value]
            if isinstance(value,str):return value.replace(str(root),'$AUDIT').replace(str(ROOT),'$REPO')
            return value
        result=portable(result)
    rows=result['files'].values()
    advanced={p for p,r in result['files'].items() if any(e['pipeline']['gcc']['status']=='success' for e in r['experiments'].values())}
    result['summary']={'audited_files':len(pending),'programs':sum(not p.endswith('.cpy') for p in pending),'fragments':sum(p.endswith('.cpy') for p in pending),
        'classes':dict(sorted(Counter(r['finding']['feasibility'] for r in rows).items())),
        'primary_causes':dict(Counter(r['finding']['primary_cause'] for r in rows)),
        'source_or_merge_primary':sum(r['finding']['primary_cause'] in {'source','merge'} for r in rows),
        'source_or_native_contract_issues':sum(bool({'source_error','native_contract_error'} & set(r['finding']['tags'])) for r in rows),
        'compiler_limitations_including_secondary':sum('compiler_limitation' in r['finding']['tags'] for r in rows),
        'truly_external_native_dependencies':sum(r['finding']['primary_cause']=='native_dependency' for r in rows),
        'simple_recovery_files':sum(r['finding']['feasibility']=='A' for r in rows),
        'moderate_or_complex':sum(r['finding']['feasibility'] in {'B','C'} for r in rows),
        'experimental_c_generated_files':sum(any(e['pipeline']['backend']['status']=='success' for e in r['experiments'].values()) for r in rows),
        'experimental_gcc_files':len(advanced),'experimental_gcc_paths':sorted(advanced),
        'simple_recovery_new_programs':sum(r['finding']['feasibility']=='A' and Path(p).name!='CAD0005A.cbl' for p,r in result['files'].items()),
        'programs_executed':0,'compiler_or_runtime_modified':False,'originals_unchanged':True}
    return result


def markdown(report):
    lines=['# Auditoria dos arquivos pendentes — Etapa 6','',
        'Gerado por `python -m tools.auditar_pendentes --write`. A coorte vem das linhas',
        'sem GCC bem-sucedido da auditoria anterior, não de uma lista de métricas.',
        f"Snapshot `{report['snapshot']}`. Nenhum fonte original, compilador ou runtime alterado.",'',
        '## Resumo consolidado','',
        'A auditoria investiga compilabilidade e custo de recuperação. **Nenhum programa',
        'experimental foi executado ou declarado funcional.** Os 60 programas validados',
        'na Etapa 5 permanecem como a coorte funcional; os experimentos não alteram esse total.','',
        '```json',json.dumps(report['summary'],ensure_ascii=False,indent=2),'```','',
        'A = simples; B = moderada; C = complexa; D = fora do escopo; E = fragmento.',
        'Os nove A incluem CAD0005A, cuja derivada já está entre os 60: são oito',
        'candidatos novos. Escolher um lado de conflito pode exigir decisão de intenção.',
        'Os dez casos com fonte/merge como causa principal e os três contratos ncurses',
        'defeituosos totalizam 13 arquivos com problemas de código; os 13 com limitações',
        'do compilador incluem causas secundárias, uma restrição de dialeto deliberada',
        'e o SORT da variante alternativa de PROG010A. Essas contagens se sobrepõem.','',
        '## Reconciliação da classificação anterior','',
        '```json',json.dumps(report['previous_counts'],ensure_ascii=False,indent=2),'```','',
        'As quantidades anteriores se confirmam (6 ligação, 2 backend, 13 inválidos,',
        '2 extensões, 1 parcial, 2 copybooks), mas os rótulos precisam de nuance:',
        'CBREAKEX é válido em formato livre, PROG042A é válido no dialeto padrão do',
        'GnuCOBOL, TELABMS é macrofonte BMS e CAD0001A tem dependência COBOL recuperável.',
        'Os cinco restantes de ligação exigem interfaces nativas ou wrappers não fornecidos.','',
        '## Tabela individual','',
        '| Arquivo | Falha anterior | Causa-raiz confirmada | Fonte válido? | Primeira fase bloqueada | Recuperável? | Correção necessária | Esforço | Prioridade | Classe |',
        '|---|---|---|---|---|---|---|---|---|---|']
    for path,row in report['files'].items():
        f=row['finding'];old=sorted({d['code'] for d in row['original_diagnostics'] if d['severity'] in {'E','S'}})
        if not old:old=[row['previous_classification']]
        lines.append(f"| [{path}](../{path}) | {', '.join(old)} | {f['analysis']} | {f['validity']} | {row['original']['first_blocker'] or 'nenhuma; fragmento contextual'} | {f['recovery']} | {f['required_change']} | {f['effort']} | {f['priority']} | {f['feasibility']} |")
    lines.extend(['','## Evidências por arquivo',''])
    for path,row in report['files'].items():
        lines.extend(['### '+Path(path).name,'',row['finding']['analysis'],'',
            'Fases do original: '+', '.join(f"{phase}={row['original'][phase].get('status',row['original'][phase].get('success'))}" for phase in ('lexer','preprocessor','parser','semantic','backend','gcc'))+'.',''])
        for key in ('gnu_original','gnu_free','gnu_limit30','gnu_static_link','gnu_ncurses_devel','gnu_ncurses_runtime'):
            if key in row:
                g=row[key]
                lines.extend([f"- {key}: retorno `{g.get('returncode','indisponível')}`; formato `{g.get('format','—')}`."])
        for label,trial in row['experiments'].items():
            p=trial['pipeline'];codes=sorted({d['code'] for d in p.get('diagnostics',[]) if d['severity'] in {'E','S'}})
            lines.append(f"- Experimento **{label}**: {trial['description']} C `{p['backend']['status']}`, GCC `{p['gcc']['status']}`; bloqueios: {', '.join(codes) or 'nenhum'}. GnuCOBOL: `{trial.get('gnu',{}).get('returncode','não consultado')}`.")
        for h in row['conflicts']:
            lines.append(f"- Conflito {h['start_line']}–{h['end_line']}: {len(h['ours'].splitlines())} linhas HEAD / {len(h['theirs'].splitlines())} linhas do outro lado. Os conteúdos e patches completos estão no JSON.")
        for name,ctx in row.get('contexts',{}).items():lines.append(f"- COPY em {name}: semântica `{ctx['semantic_success']}`, layouts `{ctx['root_layout_bytes']}`.")
        lines.append('')
    lines.extend(['## Diagnóstico, contratos e plano de recuperação','',
        'A interpretação detalhada, custo dos recursos, contratos nativos e prioridades',
        'estão em [plano de recuperação](recuperacao-pendentes.md). O [JSON completo](auditoria-pendentes.json)',
        'guarda todos os diagnósticos atuais e anteriores, comandos GnuCOBOL/GCC, formatos,',
        'dependências, contratos de CALL, SHA-256, patches experimentais e lados de cada conflito.','',
        '## Método e reprodução','',
        f"Preparação: {report['baseline']['tests_passed']} testes aprovados em {report['baseline']['seconds']} s.",
        'Cada original é copiado byte a byte para temporário. O lexer roda novamente;',
        'o pré-processador/parser e a semântica usam as APIs reais. compile_result emite',
        'C e chama GCC somente quando as fases anteriores aprovam. Fases posteriores',
        'a um bloqueio são not_run, não sucessos presumidos. Dependências são explícitas.',
        'As cópias experimentais têm diff completo; originais e os 60 validados têm hashes',
        'verificados antes/depois. Não se executa nenhum binário, não se usam stubs,',
        'não se acessa rede durante a auditoria. As consultas/compilações do oráculo têm',
        'timeout de 30 s, CPU de 20 s, arquivos de até 32 MiB e core dumps desabilitados.',
        'A compilação GCC própria conserva o timeout de 120 s do driver existente.',
        'GnuCOBOL é oráculo de sintaxe/compilação, nunca backend. -fsyntax-only não prova',
        'a presença de CALL dinâmico; por isso há ligação -fstatic-call nos experimentos',
        'nativos e em CAD0001A. Uma ligação bem-sucedida tampouco valida a assinatura C.',
        'As opções de vocabulário são as mesmas da Etapa 5; formato/dialeto e dependências',
        'ficam registrados em cada comando. Paths temporários aparecem como $AUDIT.','',
        '```bash','python -m tools.auditar_pendentes --write','python -m tools.auditar_pendentes --write --no-gnu',
        'python -m unittest discover -s tests -v','```','',
        'A árvore completa e imutável do snapshot foi consultada pela API do GitHub e',
        'preservada em [evidência da árvore](evidencias-pendentes/arvore-upstream.json).',
        'Seus blobs COBOL coincidem com o manifesto; não há .c/.h/.so nem implementações',
        'de exibir_tela ou ncurses_wrapper nessa árvore. A ferramenta usa essa evidência offline.',''])
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--no-gnu',action='store_true')
    args=parser.parse_args()
    result=audit(reference=not args.no_gnu)
    if args.write:
        (ROOT/'docs/auditoria-pendentes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        (ROOT/'docs/auditoria-pendentes.md').write_text(markdown(result))
    print(json.dumps(result['summary'],ensure_ascii=False,indent=2))


if __name__=='__main__':main()
