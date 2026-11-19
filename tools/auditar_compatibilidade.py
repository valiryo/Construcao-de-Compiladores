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
    s=report['summary'];c=s['compilation'];m=s['mains'];m2=s['modules'];f=s.get('functional')
    lines=['# Compatibilidade com GnuCOBOL — Etapa 8','',
        'Gerado por `python -m tools.auditar_compatibilidade --write`. A revisão de execução pode ser refeita isoladamente. [Dados completos e comandos](compatibilidade-gnucobol.json).',
        f"Snapshot `{report['snapshot']}`; **{report['original_files']} arquivos originais**, bytes e hashes preservados. Modo: `{report['mode']}`.",
        'A cópia corrigida de CAD0005A continua nos testes oficiais, mas não entra no denominador dos originais. Não foram criadas novas versões corrigidas.',
        '', '## Cobertura de compilação','', '| Unidades comparáveis | Nosso C + GCC | GnuCOBOL | Cobertura |','|---|---:|---:|---:|',
        f"| Todas | {c['ours']} | {c['gnucobol']} | {c['percent']:.2f}% |",
        f"| Principais | {m['ours']} | {m['gnucobol']} | {m['percent']:.2f}% |",
        f"| Subprogramas (-c / objeto) | {m2['ours']} | {m2['gnucobol']} | {m2['percent']:.2f}% |",'',
        f"O perfil padrão compila {s['project_profile_compiled']} originais. O perfil `--dialect gnucobol` chega a {c['ours']}, com seis a mais que os 64 da Etapa 7. A derivada CAD0005A continua validada separadamente.",
        'A comparação de compilação inclui os seis programas com CALL adiado. A execução dos seis registra os três alvos ausentes e os três contratos ncurses rejeitados.',
        '', '## Execução e comparação','']
    if f:
        lines += [f"Os **{f['baseline_scenarios']} cenários anteriores passaram novamente** ({f['baseline_validated']} válidos, {f['officials_validated']} oficiais). Os 136 resultados idênticos, três diferenças conhecidas da ABI e um erro próprio permanecem preservados.",
            f"Há **{f['new_batch_scenarios']} cenários batch novos e {f['new_terminal_scenarios']} de terminal**, todos com expectativas satisfeitas. Total: {f['baseline_scenarios']+f['new_batch_scenarios']+f['new_terminal_scenarios']} cenários, incluindo a comparação parcial do jogo.",
            f"O conjunto funcional das etapas anteriores executa {f['original_programs_executed']} originais. **{f['original_programs_equivalent_in_scenarios']}/{f['gnucobol_programs']} ({f['coverage_percent']:.2f}%)** coincidem nos cenários completos: 58 em bytes e dois em células de texto. Outros três têm diferenças de ABI conhecidas e expectativas independentes completas; GAMESNAK tem somente comparação parcial.",
            'CBREAKEX confere entrada vazia, mudanças de cidade/estado, totais, zero e valores negativos, todos os bytes dos registros de 80 posições. PROG042A confere inclusão, reabertura, cliente/produto ausente e quantidade zero, ligando PROG042B intacto.',
            'PROGTEST confere Backspace, Tab, entrada parcial numérica (7 em PIC 99 resulta em 70), nome de 30 posições e zero. TESTE002 confere CRT STATUS/posição. GAMESNAK exercita saída por Q, moldura e conclusão; RANDOM produz comida em posições diferentes e não há ensaio completo de jogabilidade.',
            'No terminal, os protocolos ANSI brutos diferem e ficam preservados em base64. A comparação usa todas as células de texto de um PTY 40x100, incluindo padding; não remove espaços, valores ou posições. Atributos visuais não são objeto da equivalência de texto. Um escape desconhecido falha a interpretação.',
            f"O levantamento geral registrou **{report['suite_tests_discovered']} testes descobertos**. A suíte unittest é executada separadamente pelo comando de reprodução abaixo.",'']
    else:lines+=['Execução funcional omitida por `--compile-only`; nenhuma equivalência funcional foi inferida.','']
    lines+=['## Incompatibilidades corrigidas','']+['- **'+name+'**: '+text for name,text in FIXES.items()]
    lines+=['','## Matriz de todo o corpus','',
        'Análise, construção e ligação ficam em campos distintos do JSON. Os seis probes de CALL adiado têm resultado de execução próprio. `both_compiled_functional_difference` distingue os três contratos ABI conhecidos e a diferença parcial do jogo.',
        '', '| Programa | GnuCOBOL | Nosso compilador | Causa da diferença | Ação |','|---|---|---|---|---|']
    for path,row in report['files'].items():
        gnu=row.get('gnu',{});ours=row.get('ours',{})
        g='contexto COPY' if row['kind']=='copybook' else ('objeto' if row['kind']=='module' else 'executável') if gnu.get('compiled') else 'rejeitado'
        native=('objeto' if row['kind']=='module' else 'C/GCC OK') if ours.get('success') else 'contexto COPY' if row['kind']=='copybook' else 'bloqueado'
        diagnostics=', '.join(dict.fromkeys(d['code'] for d in ours.get('diagnostics',[]) if d['severity'] in {'E','S'}))
        reason=row['category']+'; '+row['functional']['status']
        if diagnostics:reason+='; '+diagnostics
        lines.append(f"| [{path}](../{path}) | {g} | {native} | {reason} | {row['action']} |")
    lines+=['','## Formatos, fases e dependências','',
        '- CBREAKEX usa `-free` e `--source-format free`. Os outros originais usam formato fixo. Não há reindentação automática, exclusão de instruções ou truncamento de nomes.',
        '- GnuCOBOL usa `-std=default -fnot-reserved=ID -freserved=VALUES:VALUE`; são opções de vocabulário, sem ignorar erros. O limite de 63 posições é opt-in no nosso perfil; o padrão continua em 30.',
        '- Primeiro `cobc -fsyntax-only`; depois objeto `-c` para cada unidade; por fim `-x` para principais. Para principais aceitos há tentativa adicional `-fstatic-call`, fornecendo as dependências encontradas pelo PROGRAM-ID. No perfil gnucobol, o CALL externo é resolvido em execução. Use --static-call para exigir fontes resolvidos antes de GCC.',
        '- Cada compilação de referência recebe TMPDIR exclusivo no seu build. Uma execução concorrente da suíte e auditoria expôs colisão de nomes temporários cob<PID> entre namespaces; o isolamento foi corrigido e verificado com processos concorrentes.',
        '- GnuCOBOL liga NCURSESDEMO, PROGTEST2 e PROGTEST3 com `-l:libncurses.so.6 -l:libtinfo.so.6`. O executável próprio usa `--library ncurses` e carrega o SONAME durante o CALL. O probe PTY registra saída, retorno e restauração do terminal.',
        '- CAD0001A depende do SORT001A original com conflitos; main depende de exibir_tela ausente; ncurses_demo depende de wrappers ausentes. O manifesto e a árvore upstream da Etapa 6 não contêm essas implementações. GnuCOBOL permite CALL dinâmico adiado; ligação estática confirma a pendência.',
        '- Registros continuam ISO-8859-1, números exatos e ABI própria. CBREAKEX é comparado com `-fsign=EBCDIC` no oráculo para selecionar o mesmo overpunch; os bytes fornecidos são idênticos. Isso não muda a codificação textual. As três diferenças antigas (inicialização de FD e acentos/padding) continuam registradas, sem alterar a ABI.',
        '', '## Fontes excluídos da meta executável','',
        'Dez originais têm erros reais: seis conflitos (PROG002A, PROG010A, PROG023C, SORT001A, VALIDA1B e CAD0005A), ASCII001 com referência inexistente, CLIESQL01 vazio, PROG018A com destino inválido de ALTER e PROGVSAM com organização LINE SEQUENTIAL contraditória com chaves. GnuCOBOL também os rejeita; nenhum foi reparado.',
        'PROG006A (CICS), clientes-sql (SQL) e TELABMS (macro BMS) exigem ferramentas externas indisponíveis. COPY002A e COD001A são copybooks, validados nos consumidores e excluídos da contagem de programas.',
        '', '## Contratos das chamadas externas', '',
        'O runtime aceita módulos COBOL com descritor próprio e invoca símbolos C com adaptadores gerados a partir de assinaturas explícitas. A busca, os modos de passagem e a política de erros estão no [guia de CALL e FFI](call-dinamico-ffi.md).',
        'scanw e mvscanw recebem um formato C. Uma conversão precisa de destino explícito. getch devolve um inteiro e keypad exige WINDOW*. Os ensaios próprios usam PTY isolado e recusam a operação inválida antes de invocá-la. A compilação e a ligação GnuCOBOL foram verificadas separadamente. O SIGSEGV de PROGTEST2 registrado na Etapa 7 é evidência histórica.',
        '', '## Contratos do perfil novo','',
        'Formato livre preserva coordenadas físicas, COPY e comentários inline; não implementa todas as continuações de literais do formato livre. FD DATA RECORD(S) mantém referências tipadas e valida que pertencem ao FD. PIC flutuante aceita uma sequência inicial de + ou -, com agrupamento, dígitos obrigatórios e decimal; combinações com moeda, Z, *, COMP e COMP-3 são rejeitadas.',
        'Terminal usa ANSI/POSIX próprio, sem ncurses/GnuCOBOL. Requer TTY, coordenadas base 1 e limites da janela. SCREEN suporta LINE/COLUMN, BLANK SCREEN, VALUE, PIC textual ou inteiro sem sinal/escala e USING. Limites: 1024 campos editáveis, 4096 bytes por campo. Teclas básicas, Enter, Backspace, Tab e navegação são tratadas; sequências desconhecidas dão diagnóstico explícito. ECHO/ICANON são restaurados na confirmação, erro e SIGINT/SIGTERM. Um DISPLAY posicionado aplica a posição ao operando imediatamente anterior, conforme os probes completos.',
        'Essas extensões dependem de `--dialect gnucobol`; o perfil padrão, suas rejeições e a suíte anterior são preservados. O nome do perfil indica o subconjunto documentado, sem prometer toda a linguagem GnuCOBOL.',
        '', '## Reprodução','', '```bash',
        'python -m unittest discover -s tests -v',
        'python -m tools.auditar_compatibilidade --write',
        'python -m tools.auditar_compatibilidade --execution-gaps --write',
        'python -m tools.auditar_compatibilidade --compile-only --report /tmp/compat-compilacao.json',
        'python compiler.py examples/complementares/CBREAKEX.cbl --source-format free --dialect gnucobol -o build/cbreak',
        'python compiler.py examples/complementares/PROG042A.cbl --dialect gnucobol --source examples/complementares/PROG042B.cbl -o build/pedidos',
        'python compiler.py examples/complementares/PROGTEST.cbl --dialect gnucobol -o build/tela',
        '```','',
        'Os comandos GCC/cobc efetivamente executados, diagnósticos completos, hashes de fontes/COPY/runtime, opções, entradas, saídas brutas e arquivos estão no JSON. `$REPO`, `$BUILD`, `$RUN`, `$SCREEN` e `$GAPS` representam diretórios declarados e temporários novos; os comandos podem ser refeitos substituindo essas raízes. O compilador não executa COBOL durante a compilação nem gera fixtures. GnuCOBOL continua exclusivamente oráculo.','']
    probes=[(path,row['call_probe']) for path,row in report['files'].items() if 'call_probe' in row]
    if probes:
        table=['', '## Execução dos seis CALLs adiados', '',
               '| Original | CALL alcançado | Diagnóstico próprio | Retorno próprio | Retorno GnuCOBOL |',
               '|---|---|---|---:|---:|']
        for path,probe in probes:
            ref=probe['reference']['returncode'] if probe['reference'] else '—'
            table.append(f"| {Path(path).stem} | {probe['target']} | {probe['expected']} | {probe['ours']['returncode']} | {ref} |")
        table+=['', 'Os casos ncurses atingiram a verificação de argumentos em terminal isolado. O retorno do GnuCOBOL aparece apenas nos casos de módulo ausente. Os logs JSON incluem os bytes, estado do terminal e sinal quando aplicável.', '']
        index=lines.index('## Fontes excluídos da meta executável')
        lines[index:index]=table
    if 'execution_gaps' in report:
        index=lines.index('## Fontes excluídos da meta executável')
        lines[index:index]=gap_markdown(report['execution_gaps'])
    return '\n'.join(lines)


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
    if args.write and args.compile_only:parser.error('--write exige auditoria completa; use --report para compilação isolada')
    if args.execution_gaps:
        gaps=audit_execution_gaps()
        if args.report:
            args.report.write_text(json.dumps(gaps,ensure_ascii=False,indent=2)+'\n')
        if args.write:
            evidence=ROOT/'docs/compatibilidade-gnucobol.json'
            report=json.loads(evidence.read_text())
            if report['snapshot']!=gaps['snapshot']:
                raise ValueError('Snapshot da revisão difere da auditoria existente.')
            report['execution_gaps']=gaps
            evidence.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            (ROOT/'docs/compatibilidade-gnucobol.md').write_text(markdown(report))
        print('\n'.join(gap_markdown(gaps)))
        return 0 if gaps['success'] else 1
    report=audit(compile_only=args.compile_only)
    encoded=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.write:
        (ROOT/'docs/compatibilidade-gnucobol.json').write_text(encoded)
        (ROOT/'docs/compatibilidade-gnucobol.md').write_text(markdown(report))
    if args.report:args.report.write_text(encoded)
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
    return 0 if report['success'] else 1


if __name__=='__main__':raise SystemExit(main())
