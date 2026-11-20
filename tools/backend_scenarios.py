"""Fixtures explícitas e expectativas derivadas dos oficiais; nenhum dado é
criado pelo compilador. Compartilhado entre testes e auditoria executável.
"""
from dataclasses import dataclass,field
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATE='17/11/2026'
CLOCK='2026-11-17T12:34:56'


def record(*fields):
    return ''.join(str(value).ljust(width)[:width] for value,width in fields).encode('latin-1')


def person(name,age,cpf):return record((name,30),(f'{age:02d}',2),(cpf,11))+b'\n'
def agenda(name,phone):return record((name,30),(phone,15))+b'\n'
def book(code=1,name='Livro',author='Autor',available='S',date=''):
    return record((f'{code:05d}',5),(name,40),(author,20),(available,1),(date,10))+b'\n'
def log(operation,available,loan='',returned='',*,code=1,name='Livro',author='Autor'):
    values=[(operation,10),('|',1),(DATE,10),('|',1),(f'{code:05d}',5),('|',1),(name,40),('|',1),(author,20),('|',1),(available,1),('|',1),(loan,10),('|',1),(returned,10)]
    return record(*values)+b'\n'


@dataclass(slots=True)
class Scenario:
    name:str
    program:str
    stdin:str
    fixtures:dict[str,bytes]=field(default_factory=dict)
    stdout_contains:tuple[str,...]=()
    files:dict[str,bytes]=field(default_factory=dict)
    returncode:int=0
    stderr_contains:str|None=None
    oracle:bool=True
    stdout_exact:bytes|None=None
    environment:dict[str,str]=field(default_factory=dict)
    rationale:str=''
    reference_stdout_exact:bytes|None=None
    oracle_note:str=''


HARNESS='''       IDENTIFICATION DIVISION.
       PROGRAM-ID. CAD0002-DRIVER.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           COPY COPY002A.
       PROCEDURE DIVISION.
           INITIALIZE COPY002A-REGISTRO
           CALL 'CAD0002A' USING COPY002A-REGISTRO
           DISPLAY 'COUNT:' COPY002A-QUANT-REG
           DISPLAY 'NAME:' COPY002A-NOME(1)
           DISPLAY 'AGE:' COPY002A-IDADE(1)
           DISPLAY 'DATE:' COPY002A-DATA-NASC(1)
           DISPLAY 'CARGO:' COPY002A-CARGO(1)
           DISPLAY 'EMAIL:' COPY002A-EMAIL(1)
           DISPLAY 'PHONE:' COPY002A-TELEFONE(1)
           DISPLAY 'CEP:' COPY002A-CEP(1)
           STOP RUN.
'''

SCENARIOS=[
    Scenario('calcmd-basic','CALCMD01','1\n2\n3\n3\n',stdout_contains=('TOTAL   : 00000006,0000\n','VALOR MEDIO: 00000002,0000\n')),
    Scenario('calcmd-retry-and-fraction','CALCMD01','0\n1\n2\n2\n3\n',stdout_contains=('VALOR01 INVALIDO\n','VALOR MEDIO: 00000001,6666\n')),
    Scenario('calcmd-zero-divisor','CALCMD01','1\n2\n3\n0\n',returncode=1,stderr_contains='DIVISION_BY_ZERO',oracle=False),
    Scenario('caixa-no-discount','CAIXAREG','10,50\n20,25\n30,75\nN\n',stdout_contains=('** VALOR TOTAL FINAL.....:          61,50\n',)),
    Scenario('caixa-retries-and-discount','CAIXAREG','0\n10\n20\n30\nS\n0\n5,50\n',stdout_contains=('VALOR DO ITEM 1 ZERADO\n','** VALOR TOTAL FINAL.....:          54,50\n')),
    Scenario('cad4-one','CAD0004A','Ana\n25\n111.222.333-44\nN\n',files={'CADASTRO.dat':record(('Ana',30),('025',3),('111.222.333-44',14))+b'\n'}),
    Scenario('cad4-two','CAD0004A','Ana\n25\n111.222.333-44\nS\nBia\n31\n222.333.444-55\nN\n',files={'CADASTRO.dat':record(('Ana',30),('025',3),('111.222.333-44',14))+b'\n'+record(('Bia',30),('031',3),('222.333.444-55',14))+b'\n'}),
    Scenario('busca-first','BUSCA01A','11111111111\n',{'CADASTRO2.dat':person('Ana',25,'11111111111')+person('Bia',31,'22222222222')},('CPF ENCONTRADO!\n','REGISTROS LIDOS: 01\n')),
    Scenario('busca-last','BUSCA01A','22222222222\n',{'CADASTRO2.dat':person('Ana',25,'11111111111')+person('Bia',31,'22222222222')},('CPF ENCONTRADO!\n','REGISTROS LIDOS: 02\n')),
    Scenario('busca-absent','BUSCA01A','33333333333\n',{'CADASTRO2.dat':person('Ana',25,'11111111111')},('CPF NÃO ENCONTRADO!\n','REGISTROS LIDOS: 01\n')),
    Scenario('busca-empty','BUSCA01A','33333333333\n',{'CADASTRO2.dat':b''},('CPF NÃO ENCONTRADO!\n','REGISTROS LIDOS: 00\n')),
    Scenario('agenda-empty','CAD0005A','2\n',{'CADAGENDA.dat':b''},('NÃO FORAM ENCONTRADOS REGISTROS\n',),{'CADAGENDA.dat':b''}),
    Scenario('agenda-add','CAD0005A','1\nAna\n12345\n',{'CADAGENDA.dat':b''},files={'CADAGENDA.dat':agenda('Ana','12345')}),
    Scenario('agenda-reopen-add','CAD0005A','1\nBia\n67890\n',{'CADAGENDA.dat':agenda('Ana','12345')},files={'CADAGENDA.dat':agenda('Ana','12345')+agenda('Bia','67890')}),
    Scenario('agenda-list','CAD0005A','2\n',{'CADAGENDA.dat':agenda('Ana','12345')+agenda('Bia','67890')},('NOME: Ana','NOME: Bia','QTDE. REGISTROS: 02\n')),
    Scenario('agenda-duplicate','CAD0005A','1\nBia\n12345\n',{'CADAGENDA.dat':agenda('Ana','12345')},('NUMERO DO TELEFONE JA ESTA CADASTRADO\n',),{'CADAGENDA.dat':agenda('Ana','12345')}),
    Scenario('agenda-fim','CAD0005A','1\nFIM\n',{'CADAGENDA.dat':b''},('FIM DE PROGRAMA\n',),{'CADAGENDA.dat':b''}),
    Scenario('agenda-invalid-option','CAD0005A','7\n',stdout_contains=('OPÇÃO INVÁLIDA!\n',)),
    Scenario('biblioteca-empty','PROG024A','9\n',{'BIBLIOTECA.dat':b'','BIBLIOTECA.txt':b''},('FIM DE PROGRAMA\n',),{'BIBLIOTECA.dat':b'','BIBLIOTECA.txt':b''}),
    Scenario('biblioteca-add-loan-return-query','PROG024A','1\n0\n1\n\nLivro\n\nAutor\n2\n1\n4\n3\n1\n5\n1\n9\n',{'BIBLIOTECA.dat':b'','BIBLIOTECA.txt':b''},('CODIGO DO LIVRO NAO PODE SER ZERADO\n','NOME DO LIVRO NAO PODE SER EM BRANCO\n','NOME DO AUTOR NAO PODE SER EM BRANCO\n',DATE),{'BIBLIOTECA.dat':book(date=DATE),'BIBLIOTECA.txt':log('CADASTRAR','S')+log('EMPRESTAR','N',DATE)+log('DEVOLVER','S',DATE,DATE)}),
    Scenario('biblioteca-reopen-list','PROG024A','4\n9\n',{'BIBLIOTECA.dat':book(),'BIBLIOTECA.txt':b''},('LISTA DE LIVROS','00001 | Livro'),{'BIBLIOTECA.dat':book(),'BIBLIOTECA.txt':b''}),
    Scenario('biblioteca-absent','PROG024A','5\n99\n9\n',{'BIBLIOTECA.dat':book(),'BIBLIOTECA.txt':b''},('LIVRO NAO CADASTRADO\n',),{'BIBLIOTECA.dat':book(),'BIBLIOTECA.txt':b''}),
    Scenario('biblioteca-loan-unavailable','PROG024A','2\n1\n9\n',{'BIBLIOTECA.dat':book(available='N',date=DATE),'BIBLIOTECA.txt':b''},('LIVRO NAO DISPONIVEL PARA EMPRESTIMO\n',),{'BIBLIOTECA.dat':book(available='N',date=DATE),'BIBLIOTECA.txt':b''}),
    Scenario('cad2-fim','CAD0002A','FIM\n',stdout_contains=('COUNT:00\n',)),
    Scenario('cad2-validation-and-shared-record','CAD0002A','Ana1\nAna\n17\n25\n32/01/2000\n15/13/2000\n15/05/2000\nDev\nana@\nana@example.com\n123456789\nRua Um\nCidade\nSP\n12345678\nFIM\n',stdout_contains=('NOME INVALIDO\n','MENORES DE 18\n','DIA INVALIDO\n','MES INVALIDO\n','EMAIL INVALIDO\n','COUNT:01\n','NAME:Ana                           \n','AGE:25\n','DATE:15052000\n','CARGO:Dev                 \n','EMAIL:ana@example.com                                   \n','PHONE:123456789\n','CEP:12345678\n')),
]


def inputs_for(program,directory):
    if program=='PROGDATA':
        source=Path(directory)/'progdata-driver.cbl';source.write_text(DATA_HARNESS)
        return source,[ROOT/'examples/dependencias/PROGDATA.cbl']
    if program=='CAD0002A':
        source=Path(directory)/'cad2-driver.cbl';source.write_text(HARNESS)
        return source,[ROOT/'examples/oficiais/CAD0002A.cbl']
    source=ROOT/'examples'/('corrigidos' if program=='CAD0005A' else 'complementares' if program in EXTRA_PROGRAMS else 'oficiais')/(program+'.cbl')
    return source,[ROOT/'examples/dependencias/PROGDATA.cbl'] if program=='PROG024A' else []


def validate_scenario(scenario,process,directory,*,encoding='utf-8'):
    errors=[]
    if process.returncode!=scenario.returncode:errors.append(f'returncode {process.returncode} != {scenario.returncode}')
    stdout=process.stdout.decode(encoding,errors='replace')
    stderr=process.stderr.decode(encoding,errors='replace')
    for expected in scenario.stdout_contains:
        if expected not in stdout:errors.append(f'stdout não contém {expected!r}')
    if scenario.stdout_exact is not None and process.stdout!=scenario.stdout_exact:
        errors.append('stdout binário divergente da expectativa independente')
    if scenario.stderr_contains:
        if scenario.stderr_contains not in stderr:errors.append(f'stderr não contém {scenario.stderr_contains}')
    elif stderr:errors.append('stderr inesperado: '+stderr[:500])
    for name,expected in {**scenario.fixtures,**scenario.files}.items():
        path=Path(directory)/name
        if not path.exists():errors.append(f'arquivo ausente: {name}')
        elif path.read_bytes()!=expected:errors.append(f'bytes divergentes: {name}')
    allowed=set(scenario.fixtures)|set(scenario.files)
    actual={str(p.relative_to(directory)) for p in Path(directory).rglob('*') if p.is_file()}
    for name in sorted(actual-allowed):errors.append(f'arquivo inesperado: {name}')
    return errors

EXTRA_PROGRAMS={'PROG012A','PROG020A','PROG039A'}
SCENARIOS.extend([
    Scenario('extra-refmod-count','PROG012A','',stdout_contains=('QUANTIDADE DE CARACTERES: 07\n',)),
    Scenario('extra-search-found','PROG020A','103\n',stdout_contains=('103 - NOME: MARIA LIMA',)),
    Scenario('extra-search-absent','PROG020A','999\n',stdout_contains=('ID NAO ENCONTRADO\n','ID: 999 NAO ENCONTRADO!\n')),
    Scenario('extra-sequential-delete','PROG039A','1\n',
        {'CADASTRO1.dat':record(('00001',5),('Ana',30),('025',3))+b'\n'+record(('00002',5),('Bia',30),('031',3))+b'\n'},
        ('FIM DE PROGRAMA\n',),{'CADASTRO1.dat':record(('00002',5),('Bia',30),('031',3))+b'\n'}),
])

DATA_HARNESS='''       IDENTIFICATION DIVISION.
       PROGRAM-ID. PROGDATA-DRIVER.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           COPY COD001A.
       PROCEDURE DIVISION.
           INITIALIZE COD001A-REGISTRO
           CALL 'PROGDATA' USING COD001A-REGISTRO
           DISPLAY 'DATE:' COD001A-DATA
           DISPLAY 'WEEKDAY:' COD001A-DIA-SEMANA
           DISPLAY 'MONTH:' COD001A-DESC-MES
           DISPLAY 'WEEK:' COD001A-DESC-SEMANA
           DISPLAY 'YEARDAY:' COD001A-DIAS-ANO
           DISPLAY 'TIME:' COD001A-TIME
           DISPLAY 'PERIOD:' COD001A-PERIODO
           STOP RUN.
'''
SCENARIOS.append(Scenario('progdata-clock','PROGDATA','',stdout_contains=(
    'DATE:20261117\n','WEEKDAY:02\n','MONTH:NOVEMBRO            \n',
    'WEEK:TERCA-FEIRA         \n','YEARDAY:321\n','TIME:00000000\n','PERIOD:                    \n')))
