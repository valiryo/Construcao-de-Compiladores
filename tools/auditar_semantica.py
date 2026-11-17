"""Auditoria semântica de todos os programas parseáveis do snapshot local.

As unidades de CALL são selecionadas somente entre fontes deste inventário,
por PROGRAM-ID. Não há busca implícita na API do compilador nem execução/rede.
"""

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import json

from cobol_compiler import parse_file, analyze
from cobol_compiler import ast as A
from tools.auditar_parser import ROOT, portable
from tools.auditar_corpus import OFFICIAL_NAMES


def audit_corpus():
    lexical=json.loads((ROOT/'docs/auditoria-lexer-depois.json').read_text(encoding='utf-8'))
    parsed={path:parse_file(ROOT/path,include_dirs=[ROOT/'examples/dependencias']) for path in lexical['files']}
    programs={path:f for path,f in parsed.items() if f.success and isinstance(f.ast,A.Program)}
    by_name=defaultdict(list)
    for path,frontend in programs.items():
        by_name[frontend.ast.identification.program_id.upper()].append(path)

    def dependencies(path):
        seen={path}
        queue=[path]
        while queue:
            current=queue.pop(0)
            for node in A.walk(programs[current].ast.procedure):
                if isinstance(node,A.Call) and isinstance(node.program,A.Literal) and node.program.category=='string':
                    for target in by_name.get(node.program.value.upper(),[]):
                        if target not in seen:
                            seen.add(target);queue.append(target)
        return sorted(seen-{path})

    files={}
    for path,frontend in parsed.items():
        info={'lexing':'error' if any(d.phase=='lexer' for d in frontend.diagnostics) else 'success',
              'parsing':'success' if frontend.success else 'error' if frontend.parsed else 'not_run',
              'semantic':'not_run','success':False,'symbols':0,'resolved_references':0,'layouts':0,
              'areas':{},'errors':0,'warnings':0,'unsupported':[], 'external_calls':[],
              'source_dependencies':[], 'diagnostics':[asdict(d) for d in frontend.diagnostics]}
        if not frontend.success:
            info['classification']='unsupported_extension' if any(d.code.startswith('UNSUPPORTED_') for d in frontend.diagnostics) else 'invalid_source'
            info['errors']=sum(d.severity in {'E','S'} for d in frontend.diagnostics)
        elif isinstance(frontend.ast,A.DataFragment):
            info['classification']='copybook_context_only'
        else:
            deps=dependencies(path)
            result=analyze(frontend,sources=[programs[d] for d in deps])
            errors=[d for d in result.diagnostics if d.severity in {'E','S'}]
            unsupported=[d for d in errors if d.code.startswith(('UNSUPPORTED_','UNANALYZED_'))]
            real_errors=[d for d in errors if d not in unsupported]
            if real_errors: classification='invalid_source'
            elif unsupported: classification='partially_supported'
            elif result.pending_externals: classification='valid_pending_external'
            else: classification='semantic_valid'
            info.update(semantic='success' if result.success else 'error', success=result.success,
                classification=classification,symbols=len(result.table.symbols),
                resolved_references=sum(isinstance(n,A.Reference) and result.annotation(n).symbol_id is not None for n in A.walk(frontend.ast)),
                layouts=len(result.layout.items),areas=result.layout.areas,
                errors=len(errors),warnings=sum(d.severity=='W' for d in result.diagnostics),
                unsupported=sorted({d.code for d in unsupported}),external_calls=result.pending_externals,
                source_dependencies=deps,diagnostics=[asdict(d) for d in result.diagnostics],
                call_bindings=result.calls,parameters=result.parameters,
                data_layouts=[{'name':result.table.symbols[sid].name,'symbol_id':sid,
                    'type':asdict(result.table.symbols[sid].type),**asdict(layout)} for sid,layout in result.layout.items.items()],
                statement_count=sum(isinstance(n,A.Statement) for n in A.walk(frontend.ast)),
                dynamic_checks=sum(len(ann.checks) for ann in result.annotations.values()))
        files[path]=portable(info)
    counts=Counter(v['classification'] for v in files.values())
    analyzed=[v for v in files.values() if v['semantic']!='not_run']
    previous=json.loads((ROOT/'docs/auditoria-parser.json').read_text(encoding='utf-8'))
    expected_programs={p for p,item in previous['files'].items() if item['classification']=='program'}
    known_failures={'examples/complementares/ASCII001.cbl':('invalid_source','UNDEFINED_SYMBOL'),
        'examples/complementares/PROG018A.cbl':('invalid_source','INVALID_ALTER_TARGET'),
        'examples/complementares/PROGVSAM.cbl':('invalid_source','INVALID_FILE_ACCESS'),
        'examples/complementares/PROGTEST.cbl':('partially_supported','UNSUPPORTED_SCREEN')}
    unexpected=[]
    for path in sorted(expected_programs):
        item=files[path]
        if item['success']:
            continue
        expected=known_failures.get(path)
        if not expected or item['classification']!=expected[0] or expected[1] not in {d['code'] for d in item['diagnostics']}:
            unexpected.append(path)
    return {'repository':lexical['repository'],'commit':lexical['commit'],
        'policy':{'mode':'corpus','encoding':'ISO-8859-1','dependencies':'explicit inventory closure by PROGRAM-ID',
                  'copybooks':'analyzed only through COPY in including programs'},
        'summary':{'total_files':len(files),'parser_programs':len(programs),'semantic_programs':len(analyzed),
            'successful_programs':sum(v['success'] for v in analyzed),
            'symbols':sum(v['symbols'] for v in analyzed),'resolved_references':sum(v['resolved_references'] for v in analyzed),
            'layouts':sum(v['layouts'] for v in analyzed),'classifications':dict(sorted(counts.items())),
            'unexpected_failures':unexpected},'files':files}


def markdown(report):
    s=report['summary']
    lines=['# Auditoria semântica e de layout','',
        'Gerado por `python -m tools.auditar_semantica --write`, sem rede, execução COBOL ou GCC.',
        f"Snapshot: `{report['commit']}`. Os fontes originais e hashes permanecem intactos.",'',
        '## Métricas','',
        f"- {s['total_files']} arquivos revisitados; **{s['semantic_programs']}/{s['parser_programs']} programas aceitos pelo parser submetidos à semântica**.",
        f"- **{s['successful_programs']} programas semanticamente válidos**, incluindo pendências externas explicitadas abaixo.",
        f"- {s['symbols']} símbolos, {s['resolved_references']} referências vinculadas e {s['layouts']} descritores físicos.",
        '- Dois copybooks são fragmentos; sua semântica é verificada nas inclusões, sem simular programas independentes.','',
        '| Classificação | Arquivos |','|---|---:|']
    lines += [f'| {key} | {value} |' for key,value in s['classifications'].items()]
    lines += ['', '## Sete oficiais','',
        '| Programa | Estado | Símbolos | Referências | Layouts | Áreas e bytes máximos |',
        '|---|---|---:|---:|---:|---|']
    for name in OFFICIAL_NAMES:
        folder='corrigidos' if name=='CAD0005A.cbl' else 'oficiais'
        item=report['files'][f'examples/{folder}/{name}']
        areas='; '.join(f'{key}={value}' for key,value in item['areas'].items())
        lines.append(f"| {name}{' corrigido' if folder=='corrigidos' else ''} | {item['classification']} | {item['symbols']} | {item['resolved_references']} | {item['layouts']} | {areas} |")
    lines += ['', 'CAD0005A original permanece negativo léxico. PROG024A usa PROGDATA disponível no',
        'inventário, com parâmetros COD001A vinculados. A API/CLI exigem `--source` para fornecer',
        'esse programa explicitamente. CAD0002A tem duas raízes externas de LINKAGE; somente',
        'COPY002A-REGISTRO é parâmetro USING. Não há armazenamento local para essas raízes.','',
        'COPY002A-REGISTRO ocupa **10552 bytes**: contador de 2 bytes e 50 ocorrências de',
        '**211 bytes**, com base 1 e primeiro registro no offset 2. O comentário histórico',
        '`TAMANHO 02125` do copybook não determina o layout e não foi alterado. Os descritores',
        'completos, offsets de cada campo e strides estão no JSON e em `--dump-layout`.','',
        '## Todos os arquivos','',
        '| Arquivo | Lexer | Parser | Semântica | Símbolos | Referências | Layouts | E/S | W | Classificação |',
        '|---|---|---|---|---:|---:|---:|---:|---:|---|']
    for path,item in report['files'].items():
        lines.append(f"| [{path}](../{path}) | {item['lexing']} | {item['parsing']} | {item['semantic']} | {item['symbols']} | {item['resolved_references']} | {item['layouts']} | {item['errors']} | {item['warnings']} | {item['classification']} |")
    lines += ['', '## Diagnósticos e justificativas individuais','',
        'Erro real no fonte prevalece na classificação quando também há recurso não suportado.',
        'Pendência externa é informação (I), preserva a validade local e impede `backend_ready`.',
        'Recursos fora do subconjunto são erros explícitos e nunca contam como sucesso.','',
        '| Arquivo | Posição/código e justificativa |','|---|---|']
    for path,item in report['files'].items():
        if not item['diagnostics'] and not item['external_calls']: continue
        messages=[]
        for d in item['diagnostics']:
            p=d['span']['start']
            message=f"{p['line']}:{p['column']} {d['severity']} `{d['code']}`: {d['message']}"
            if message not in messages: messages.append(message)
        if item['source_dependencies']:
            messages.append('Fontes de ligação: '+', '.join(item['source_dependencies']))
        lines.append(f"| {path} | {'<br>'.join(messages)} |")
    lines += ['', '## Contratos e limites','',
        '- PIC e tipos lógicos separam categoria, precisão, escala, sinal, edição e representação física. Operações usam metadados decimais exatos; divisão/potência mantêm precisão/escala não limitadas até o receptor.',
        '- Não há padding implícito. COMP usa 2/4/8 bytes até 4/9/18 dígitos; acima, largura binária mínima com sinal. COMP-3 reserva nibbles de dígitos e sinal. DISPLAY S usa overpunch sem byte adicional. Ver [contrato semântico](semantica.md).',
        '- REDEFINES e registros alternativos FD são views sobre a mesma área. OCCURS guarda tamanho máximo, mínimo, DEPENDING, stride e verificações dinâmicas.',
        '- SCREEN, ALTER, SORT, START, arquivos INDEXED/RELATIVE/acesso DYNAMIC ou RANDOM, POINTER e COMP-1/2 permanecem fora do subconjunto semântico. As referências alcançáveis são ainda visitadas e os diagnósticos bloqueiam o programa.',
        '- SEARCH ALL aceita condição simples de igualdade sobre chave ordenada e anota o contrato de ordenação; formas mais complexas recebem diagnóstico explícito.',
        '- CALL externo conserva grafia, modos e argumentos, incluindo literais por referência em temporários. Unidades disponíveis validam assinatura e estrutura física; falhas do chamado bloqueiam o chamador.',
        '- FILE STATUS, SELECT/FD e modos declarados são conferidos. O estado efetivo de OPEN em cada caminho é uma verificação de runtime anotada, sem simular entrada ou fluxo nesta etapa.',
        '- ISO-8859-1 define bytes de literais/registros; UTF-8 do arquivo fonte continua decodificado pelo front-end. Valores não representáveis são diagnosticados.',
        '- Ausência de VALUE usa zeros numéricos/espaços textuais em armazenamento local; LINKAGE preserva bytes do chamador. `--strict` exige VALUE sem alterar os fontes.',
        '- SQL/CICS, vazio e negativos léxicos preservam suas classificações anteriores; não chegam artificialmente à semântica.','',
        'A classificação atesta análise estática deste subconjunto. Runtime, conversões reais,',
        'geração C, dispatcher/PERFORM, I/O, passagem de parâmetros e GCC são a próxima etapa.',
        'Nenhum resultado desta auditoria é uma prova de execução dos programas.','',
        '## Reprodução','', '```bash','python -m tools.auditar_semantica --write',
        'python -m unittest discover -s tests -v','```','',
        'O [JSON completo](auditoria-semantica.json) inclui diagnósticos com origem/inclusão,',
        'dependências, layouts por símbolo, parâmetros e vínculos de chamadas. Não editar as',
        'tabelas ou JSON manualmente.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    report=audit_corpus()
    if args.write:
        (ROOT/'docs/auditoria-semantica.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (ROOT/'docs/auditoria-semantica.md').write_text(markdown(report),encoding='utf-8')
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
    return 0 if not report['summary']['unexpected_failures'] else 1


if __name__=='__main__':
    raise SystemExit(main())
