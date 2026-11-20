"""Novos cenários sobre originais intactos; expectativas independentes do backend."""
from decimal import Decimal
from itertools import groupby
from pathlib import Path
import tempfile

from tools.backend_scenarios import ROOT,Scenario,record
from tools.functional_execution import copy_sources,clean_compile,run_cases
from tools.compatibility_corpus import gnu_build,FORMATS
from tools.terminal_probe import run_terminal


def money(cents,width):
    return f'{Decimal(cents)/100:,.2f}'.rjust(width)


def sales(rows):
    result=b''
    for state,city,name,cents in rows:
        digits=f'{abs(cents):08d}'
        # ABI própria: caracteres de overpunch EBCDIC, codificados em Latin-1.
        if cents<0:digits=digits[:-1]+'}JKLMNOPQR'[int(digits[-1])]
        result+=record((state,2),(city,20),(name,30),(digits,8))+b'\n'
    return result


def sales_report(rows):
    lines=[];cities=states=0
    def emit(text):lines.append(text.ljust(80)[:80].encode('latin1')+b'\n')
    for state,state_rows in groupby(rows,key=lambda r:r[0]):
        state_rows=list(state_rows);states+=1;city_count=0
        emit(' STATE '+state)
        for city,city_rows in groupby(state_rows,key=lambda r:r[1]):
            city_rows=list(city_rows);cities+=1;city_count+=1
            emit(' CITY '.ljust(9)+city.ljust(20))
            for _,_,name,cents in city_rows:emit(' '*5+name.ljust(30)+' '*5+money(cents,len('----,--9.99')))
            emit(' CITY '+city.ljust(20)+' '*5+money(sum(r[3] for r in city_rows),14)+' '*5+str(len(city_rows)).rjust(7)+' CUSTOMERS '.ljust(12))
        emit(' STATE '.ljust(10)+state+' '*5+money(sum(r[3] for r in state_rows),14)+' '*5+str(city_count).rjust(7)+' CITIES '.ljust(9)+str(len(state_rows)).rjust(7)+' CUSTOMERS '.ljust(12))
    emit(' FEDERAL '+money(sum(r[3] for r in rows),14)+' '*5+str(len(rows)).rjust(7)+' CUSTOMERS '.ljust(12)+str(cities).rjust(7)+' CITIES '.ljust(9)+str(states).rjust(7)+' STATES '.ljust(9))
    return b''.join(lines)


def order(code=1,client=1,product=2,qty=3):
    return record((f'{code:05}',5),(f'{client:05}',5),('Ana',30),(f'{product:05}',5),('Livro',30),(f'{qty:03}',3),('0001250',7),(f'{qty*1250:07}',7))+b'\n'


SALES=[('CA','Oakland','Ana',123456),('CA','Oakland','Bia',-23456),('CA','Sacramento','Cris',0),('NY','Albany','Dan',99999999)]
BATCH=[]
for name,rows in [('empty',[]),('breaks-signed-zero',SALES)]:
    BATCH.append(Scenario('compat-cbreak-'+name,'CBREAKEX','',{'INFILE':sales(rows)},files={'PRNTFILE':sales_report(rows)},stdout_exact=b''))
for name,client,product,qty,existing in [('create',1,2,3,b''),('append',1,2,2,order(8)),('missing-client',9,2,1,b''),('missing-product',1,9,1,b''),('zero-quantity',1,2,0,b'')]:
    fixtures={'CADASTRO1.dat':record(('00001',5),('Ana',30),('025',3))+b'\n',
        'CADASTRO2.dat':record(('00002',5),('Livro',30),('0001250',7))+b'\n',
        'PEDENT01.dat':f'00004{client:05}{product:05}{qty:03}\n'.encode(), 'CADASTRO3.dat':existing}
    valid=client==1 and product==2 and qty>0
    stdout=(b'FIM DE PROGRAMA\n'*2 if valid else
        ('CLIENTE NAO ENCONTRADO.\n' if client!=1 else 'PRODUTO NAO ENCONTRADO.\n' if product!=2 else 'QUANTIDADE INVALIDA.\n').encode()+b'FIM DE PROGRAMA\n')
    BATCH.append(Scenario('compat-order-'+name,'PROG042A','',fixtures,files={'CADASTRO3.dat':existing+(order(9 if existing else 4,qty=qty) if valid else b'')},stdout_exact=stdout))


def inputs(program,directory):
    return ROOT/f'examples/complementares/{program}.cbl',([ROOT/'examples/complementares/PROG042B.cbl'] if program=='PROG042A' else [])


def run_batch():
    return run_cases(BATCH,inputs,compiler_options={p:{'source_format':FORMATS.get(p+'.cbl','fixed'),'dialect':'gnucobol'} for p in {s.program for s in BATCH}},reference_options={'CBREAKEX':['-fsign=EBCDIC']})


TERMINAL=[('screen-edit','PROGTEST',b'Ax\x7fna\t7\r','Ana','70'),
    ('screen-full','PROGTEST',b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcd\t25\r','ABCDEFGHIJKLMNOPQRSTUVWXYZabcd','25'),
    ('screen-zero','PROGTEST',b'Bia\t00\r','Bia','00'),
    ('position-status','TESTE002',b'7\r',None,None),
    ('game-quit','GAMESNAK',b'Q\r',None,None)]


def run_screens():
    report={'programs':{},'scenarios':{}}
    with tempfile.TemporaryDirectory(prefix='cobol-screen-') as td:
        root=Path(td)
        for program in sorted({s[1] for s in TERMINAL}):
            build=root/program;build.mkdir()
            source,deps,include,hashes,_=copy_sources(ROOT/f'examples/complementares/{program}.cbl',[],build/'sources',frontend_options={'dialect':'gnucobol'})
            ours,proof=clean_compile(source,deps,include,build/'ours',compiler_options={'dialect':'gnucobol'})
            ref=gnu_build(source,deps,include,build/'gnu',fmt='fixed',module=False)
            report['programs'][program]={'ours':proof,'gnu':ref,'sources':hashes}
            for name,p,stdin,person,age in TERMINAL:
                if p!=program:continue
                row={'program':program,'errors':[],'runs':{},'comparison':'partial-random' if p=='GAMESNAK' else 'full-text-cells'}
                for tag,executable in [('ours',ours.output),('reference',ref.get('artifact'))]:
                    directory=build/name/tag;directory.mkdir(parents=True)
                    if not executable:
                        row['errors'].append(tag+' compilation failed');continue
                    run=run_terminal(executable,stdin,directory);row['runs'][tag]=run
                    if run['returncode'] or run['timeout'] or not run['terminal_restored'] or run['stderr']['bytes'] or 'decode_error' in run:
                        row['errors'].append(tag+' failed terminal contract')
                    grid=run.get('cells',[])
                    if p=='PROGTEST':
                        checks=[(4,17,person.ljust(30,'_')),(6,18,age),(12,10,'Usuario cadastrado sucesso!'),(13,10,'Nome: '+person.ljust(30)),(14,10,'Idade: '+age)]
                    elif p=='TESTE002':checks=[(5,10,'Tela limpa!')]
                    else:
                        text='\n'.join(grid)
                        checks=[]
                        if not all(t in text for t in ['FIM DE PROGRAMA','GAME OVER','Pontos:','############################################################']):row['errors'].append(tag+' missing game completion')
                    for line,column,text in checks:
                        if len(grid)<line or grid[line-1][column-1:column-1+len(text)]!=text:row['errors'].append(tag+f' cells {line},{column} != {text!r}')
                    if any(directory.iterdir()):row['errors'].append(tag+' unexpected files')
                if len(row['runs'])==2:
                    a,b=row['runs']['ours'],row['runs']['reference']
                    row['raw_match']=a['stdout']==b['stdout']
                    row['cells_match']=a.get('cells')==b.get('cells')
                    if p!='GAMESNAK' and not row['cells_match']:row['errors'].append('text cells differ')
                row['validated']=not row['errors'];row['fully_compared']=row['validated'] and p!='GAMESNAK'
                report['scenarios'][name]=row
        def portable(value):
            if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
            if isinstance(value,list):return [portable(v) for v in value]
            if isinstance(value,str):return value.replace(str(root),'$SCREEN').replace(str(ROOT),'$REPO')
            return value
        return portable(report)
