"""Entradas e expectativas do corpus, derivadas dos fontes preservados.

Não executa programas para descobrir resultados esperados. Os construtores abaixo
descrevem registros físicos e relatórios; o mesmo conteúdo alimenta os dois lados.
"""
from decimal import Decimal, ROUND_DOWN

from tools.backend_scenarios import Scenario, SCENARIOS as PREVIOUS, record, person

SCENARIOS=list(PREVIOUS)


def add(program,name,stdin='',fixtures=None,contains=(),files=None,**options):
    SCENARIOS.append(Scenario(f'{program.lower()}-{name}',program,stdin,fixtures or {},tuple(contains),files or {},
        rationale=options.pop('rationale',name),**options))


def line(*fields):
    return record(*fields)+b'\n'


def client(code=1,name='Ana',age=25):
    return line((f'{code:05d}',5),(name,30),(f'{age:03d}',3))


def product(code=1,name='Livro',cents=1250):
    return line((f'{code:05d}',5),(name,30),(f'{cents:07d}',7))


def order(code=1,customer='Ana',item='Livro',quantity=2,cents=1250):
    return line((f'{code:05d}',5),('00001',5),(customer,30),('00001',5),(item,30),
        (f'{quantity:03d}',3),(f'{cents:07d}',7),(f'{quantity*cents:07d}',7))


def shared_user(code=1):
    return line((f'{code:02d}',2),('Ana',30),('25',2),('01012000',8),('Dev',20),
        ('a@example.com',50),('123456789',9),('Rua Um',50),('Cidade',30),('SP',2),('12345678',8))


def salary(name='Ana',age=25,cents=100000):
    return line((name,30),(f'{age:02d}',2),(f'{cents:07d}',7))


def stock(program,*,quantity=10,status='S'):
    fields=[('00001',5),('Livro',20),(f'{quantity:05d}',5)]
    if program=='PROG023E':fields=[('00001',5),*fields,('00002',5)]
    if program!='PROG023A':fields.append(('00000000000001250',17))
    if program in {'PROG023D','PROG023E'}:fields.append((status,1))
    return line(*fields)


def stock_log(operation,old_quantity,new_quantity,old_cents,new_cents):
    return line(('17/11/2026',10),('|',1),('12:34',5),('|',1),(operation,10),('|',1),
        ('00001',5),('|',1),('Livro',20),('|',1),(f'{old_quantity:05d}',5),('|',1),
        (f'{new_quantity:05d}',5),('|',1),(f'{old_cents:017d}',17),('|',1),(f'{new_cents:017d}',17))


def money(number,width):
    value=Decimal(number).quantize(Decimal('.01'),rounding=ROUND_DOWN)
    if not value:return ' '*width
    text=format(value,',.2f').replace(',','_').replace('.',',').replace('_','.')
    if 0<value<1:text=text[1:]  # Z suprime também o zero à esquerda da vírgula.
    return text.rjust(width)


add('MEU-PROGRAMA','message',stdout_exact=b'API COBOL funcionando!'.ljust(50,b' ')+b'\n')
add('PROG001A','clock',contains=('DATA: 17/11/2026\n','HORA: 12:34','NOME: JOSE ROBERTO'))
add('PROG001A','leap-clock',contains=('DATA: 29/02/2024\n','HORA: 23:59'),
    environment={'COBOL_DATETIME':'2024-02-29T23:59:58','COB_CURRENT_DATE':'20240229235958'})
add('PROG003A','arithmetic',contains=('VALOR FINAL SIMP5: 083\n','VALOR SOBRADO    : 001\n',
    'VALOR COMPUTE SIMP7: 167\n','VALOR TOTAL DEC3: 0000004,03\n','WRK-VALOR-CORR2: 08 02 AB\n','CORR2-2: 99\n'))
add('PROG004A','register','Ana\n25\nDev\nBia\n31\nQA\nFIM\n',contains=('Nome: Ana','Nome: Bia','Idade: 31\n'))
add('PROG004A','empty','FIM\n',stdout_exact=b"SIMULACAO DE CADASTRO - DIGITE 'FIM' PARA SAIR\nNome: \nLISTA DE CADASTROS:\n")
row5=line(('00001',5),('|',1),('Ana',15),('|',1),('25',2),('|',1),('Dev',15),('|',1),('Cidade',15),('|',1),('SP',2))
add('PROG005A','record',fixtures={'SEQENT02.dat':row5},contains=('COD: 00001, NOME: Ana','IDADE: 25','WRK-NOME: '+15*' '+'\n'))
add('PROG005A','empty',fixtures={'SEQENT02.dat':b''},
    stdout_exact=(b'WRK-NOME: '+b' '*15+b'\n')*2+b'FIM DO PROGRAMA\n',
    reference_stdout_exact=b'WRK-NOME: '+b'\0'*15+b'\nWRK-NOME: '+b' '*15+b'\nFIM DO PROGRAMA\n',
    oracle_note='O fonte exibe o buffer FD depois de READ AT END em arquivo vazio. A ABI do projeto inicializa texto com espaços; GnuCOBOL 3.2 mantém NUL no FD ainda não lido. Ambos os stdout são verificados integralmente.')
for suffix,name,age in [('normal','Ana',25),('limit','ABCDEFGHIJKLMNOPQRSTUV',99)]:
    add('PROG007A',suffix,f'{name}\n{age}\n',contains=('Nome: '+name[:20].ljust(20)+'\n',f'Idade: {age:02d}\n'))
add('LEARQDAT','records',fixtures={'SEQENT01.dat':line(('00001',5),('Ana',20),('25',2))+line(('00002',5),('Bia',20),('31',2))},contains=('ID: 00001, Nome: Ana','ID: 00002, Nome: Bia'))
add('LEARQDAT','empty',fixtures={'SEQENT01.dat':b''},stdout_exact=b'')
add('LER0002A','records',fixtures={'CADASTRO2.dat':person('Ana',25,'11111111111')+person('Bia',31,'22222222222')},contains=('NOME....: Ana','NUM CPF.: 22222222222\n'))
add('LER0002A','empty',fixtures={'CADASTRO2.dat':b''},stdout_exact=b'')
add('PROG009A','one','1\nAna\n25\nN\n',files={'SEQSAI01.dat':line(('01',2),('Ana',20),('25',2))},contains=('Arquivo Gravado com Sucesso!\n',))
add('PROG009A','two','1\nAna\n25\nS\n2\nBia\n31\nN\n',files={'SEQSAI01.dat':line(('01',2),('Ana',20),('25',2))+line(('02',2),('Bia',20),('31',2))})
add('PROG011A','initialize',stdout_exact=('ANTES DO INITIALIZE'+'JOSE ROBERTO'.ljust(20)+'2012345\n'+'DEPOIS DO INITIALIZE'+' '*20+'0000000\n').encode())
add('PROG014A','reverse-tally',contains=('TAMANHO DO CAMPO: 012\n',))
add('PROG015A','inspect',contains=('QUANTIDADE DE ESPACOS ANTES: 08\n','QUANTIDADE DE CARACTERES FINAL: 30\n'))
add('PROG016A','clock',contains=('DATA DO DIA FORMATADO: 17/11/2026\n','HORA FORMATADA: 12:34\n','PERIODO: BOM DIA!'))
add('PROG016A','afternoon',contains=('DATA DO DIA FORMATADO: 29/02/2024\n','HORA FORMATADA: 15:10\n','PERIODO: BOA TARDE!'),environment={'COBOL_DATETIME':'2024-02-29T15:10:20','COB_CURRENT_DATE':'20240229151020'})
add('PROG017A','approved','1\n',contains=('PEDIDO APROVADO!\n','STATUS-PEDIDO: A\n','WRK-CODIGO :ABCDE\n'))
add('PROG017A','cancelled','2\n',contains=('PEDIDO CANCELADO!\n','STATUS-PEDIDO: C\n','WRK-CODIGO :TUVXZ\n'))
add('PROG017A','invalid','9\n',contains=('ERRO NO PEDIDO!\n',))
add('PROG019A','found','105\n',contains=('105 - NOME: LUCAS COSTA',))
add('PROG019A','absent','999\n',contains=('ID NAO ENCONTRADO\n','ID: 999 NAO ENCONTRADO!\n'))
for program in ('LOGIN01A','PROG021A'):
    users=line(('ana',20),('secret',10))+line(('bia',20),('password',10))
    add(program,'valid','bia\npassword\n',{'USUARIO.dat':users},('LOGIN REALIZADO COM SUCESSSO!' if program=='LOGIN01A' else 'Login realizado com sucesso!',))
    kwargs={}
    if program=='PROG021A':
        prefix=b'DIGITE USUARIO: \nDIGITE SENHA: \n'
        message='Usuário ou senha inválidos.'
        kwargs={'stdout_exact':prefix+(message.ljust(50)+'\n').encode(),
            'reference_stdout_exact':prefix+message.encode().ljust(50,b' ')+b'\n',
            'oracle_note':'Acentos no VALUE PIC X(50): o projeto armazena ISO-8859-1 e converte para UTF-8 no terminal; GnuCOBOL armazena os bytes UTF-8 do literal. Verificação integral dos dois paddings, sem normalização.'}
    add(program,'invalid','ana\nwrong\n',{'USUARIO.dat':users},('USUARIO E SENHA INVALIDOS!' if program=='LOGIN01A' else 'Usuário ou senha inválidos.',),**kwargs)
    add(program,'missing','ana\nsecret\n',contains=('35',))
add('MINICALC','addition','1,25\n+\n2,50\nN\n',contains=('3,750000\n','FIM DE PROGRAMA\n'))
add('MINICALC','negative-division','2\n/\n-4\nN\n',contains=('-          ,500000\n',))
add('MINICALC','zero','1\n/\n0\n',contains=('ERRO: DIVISÃO POR ZERO NÃO PERMITIDA\n',))
add('PROG022A','normal','Ana\n25\n',contains=('NOME INFORMADO: Ana','IDADE INFORMADA: 25 ANOS\n'))
add('PROG022A','retry','\nAna1\nAna\n0\n25\n',contains=('CAMPO NOME OBRIGATORIO','NAO PODE CONTER NUMERAL','IDADE NAO PODE SER ZERO','CADASTRO EFETUADO COM SUCESSO!'))

for program in ('PROG023A','PROG023B','PROG023D','PROG023E'):
    fixtures={'ESTOQUE.dat':b''}
    if program in ('PROG023D','PROG023E'):fixtures['ARQLOG1.dat']=b''
    add(program,'empty','9\n',fixtures,('FIM DE PROGRAMA\n',),dict(fixtures))
    full={**fixtures,'ESTOQUE.dat':stock(program)}
    add(program,'list-existing','4\n9\n',full,('00001 | Livro','00010'),dict(full))
    if program=='PROG023A':
        add(program,'add-and-move','1\n1\nLivro\n10\n2\n1\n5\n3\n1\n2\n4\n9\n',fixtures,
            ('LISTA DE PRODUTOS','00013'),{'ESTOQUE.dat':stock(program,quantity=13)})
    elif program=='PROG023B':
        add(program,'delete','5\n1\nS\n9\n',full,('EXCLUIR PRODUTOS',),{'ESTOQUE.dat':b''})
    else:
        minimum='2\n' if program=='PROG023E' else ''
        add(program,'register-log','1\n1\nLivro\n10\n'+minimum+'12,50\n9\n',fixtures,
            files={'ESTOQUE.dat':stock(program),'ARQLOG1.dat':stock_log('CADASTRAR',0,10,0,1250)})
        if program=='PROG023D':
            add(program,'deactivate-log','5\n1\nS\n9\n',full,files={
                'ESTOQUE.dat':stock(program,status='N'),'ARQLOG1.dat':stock_log('EXCLUIR',10,0,1250,0)})
        else:
            add(program,'minimum-stock','3\n1\n8\n9\n',full,('ALERTA: ESTOQUE NO NIVEL MINIMO',),
                {'ESTOQUE.dat':stock(program,quantity=2),'ARQLOG1.dat':b''},
                rationale='Ao atingir exatamente o mínimo, o IF da linha 521 não entra no ELSE que contém a gravação do log (linha 542). Preservar o escopo real do fonte.')
            add(program,'below-minimum','3\n1\n9\n9\n',full,('ALERTA: ESTOQUE ABAIXO DO NIVEL MINIMO',),
                {'ESTOQUE.dat':stock(program,quantity=1),'ARQLOG1.dat':stock_log('SAIDA',10,1,0,1250)})

add('PROG028A','entry','1\nE\n',{'FUNCIONARIO.dat':line(('00001',5),('Ana',30)),'PONTO.dat':b''},
    ('FIM DE PROGRAMA',),{'PONTO.dat':line(('00001',5),('Ana',30),('20261117',10),('12345600',8),('E',1))})
add('PROG028A','reject-first-exit','1\nS\n',{'FUNCIONARIO.dat':line(('00001',5),('Ana',30)),'PONTO.dat':b''},('REGISTRO NAO PERMITIDO!!',),{'PONTO.dat':b''})
entry=line(('00001',5),('Ana',30),('20261117',10),('12345600',8),('E',1))
add('PROG028A','exit-after-entry','1\nS\n',{'FUNCIONARIO.dat':line(('00001',5),('Ana',30)),'PONTO.dat':entry},
    files={'PONTO.dat':entry+line(('00001',5),('Ana',30),('20261117',10),('12345600',8),('S',1))})
add('PROG028A','reject-duplicate','1\nE\n',{'FUNCIONARIO.dat':line(('00001',5),('Ana',30)),'PONTO.dat':entry},
    ('REGISTRO NAO PERMITIDO!',),{'PONTO.dat':entry})
add('PROG029A','convert','537\n',contains=('DOLAR.: '+money(100,12)+'\n','EURO..: '+money('85.92',12)+'\n'))
add('PROG029A','zero','0\n',contains=('VALOR INVALIDO INFORMADO.',))
add('PROG033A','exit','3\n',contains=('FIM DE PROGRAMA\n',))
add('PROG033A','list-empty','2\n',{'CADASTRO1.dat':b''},('ARQUIVO VAZIO','FIM DE PROGRAMA'))
add('PROG033A','register','1\n',{'CADENT001.dat':client(),'CADASTRO1.dat':b''},('FIM DE PROGRAMA',),{'CADASTRO1.dat':client()})
add('PROG034A','append',fixtures={'CADENT001.dat':client(),'CADASTRO1.dat':client(2,'Bia',31)},files={'CADASTRO1.dat':client(2,'Bia',31)+client()})
add('PROG034A','empty-input',fixtures={'CADENT001.dat':b'','CADASTRO1.dat':b''},files={'CADASTRO1.dat':client(0,'',0)})
add('PROG035A','records',fixtures={'CADASTRO1.dat':client()+client(2,'Bia',31)},stdout_exact=b'FIM DE PROGRAMA\n')
add('PROG035A','empty',fixtures={'CADASTRO1.dat':b''},contains=('ARQUIVO VAZIO',))
for mode in (1,2,3):
    # ID/name/age choose different permutations so each branch is observable.
    items=[client(3,'Bia',21),client(1,'Cris',40),client(2,'Ana',31)]
    expected={1:[items[1],items[2],items[0]],2:[items[2],items[0],items[1]],3:[items[0],items[2],items[1]]}[mode]
    add('PROG036A',f'sort-{mode}',fixtures={'CLASSENT.dat':f'{mode}\n'.encode(),'CADASTRO1.dat':b''.join(items)},files={'CADASTRO1.dat':b''.join(expected)})
add('PROG037A','change',fixtures={'ALTENT01.dat':client(1,'Alice',35),'CADASTRO1.dat':client()+client(2,'Bia',31)},files={'CADASTRO1.dat':client(1,'Alice',35)+client(2,'Bia',31)})
add('PROG037A','preserve',fixtures={'ALTENT01.dat':client(1,'',0),'CADASTRO1.dat':client()},files={'CADASTRO1.dat':client()})
add('PROG038A','found',fixtures={'ALTCONS01.dat':b'00001\n','CADASTRO1.dat':client()},files={'ALTRET01.dat':client()})
add('PROG038A','absent',fixtures={'ALTCONS01.dat':b'00099\n','CADASTRO1.dat':client()},files={'ALTRET01.dat':client(99,'',0)})
add('PROG040A','append','1\nLivro\n12,50\n',{'CADASTRO2.dat':b''},files={'CADASTRO2.dat':product()})
add('PROG040A','retry','0\n2\n\nCaneta\n3,25\n',{'CADASTRO2.dat':product()},('NAO PODE SER ZERO','NAO PODE SER VAZIO'),{'CADASTRO2.dat':product()+product(2,'Caneta',325)})
add('PROG041A','records',fixtures={'CADASTRO2.dat':product()+product(2,'Caneta',325)},contains=('QTDE. REGISTROS: 00002\n',))
add('PROG041A','empty',fixtures={'CADASTRO2.dat':b''},contains=('ARQUIVO VAZIO',))
add('PROG043A','found',fixtures={'PRODCONS01.dat':b'00001\n','CADASTRO2.dat':product()},files={'PRODRET01.dat':product()})
add('PROG043A','absent',fixtures={'PRODCONS01.dat':b'00099\n','CADASTRO2.dat':product()},files={'PRODRET01.dat':product(99,'',0)})
add('PROG044A','records',fixtures={'CADASTRO3.dat':order()+order(2,'Bia','Caneta',3,325)},contains=('00001 Ana','00002 Bia','QTDE. REGISTROS: 00002\n'))
add('PROG044A','empty',fixtures={'CADASTRO3.dat':b''},contains=('ARQUIVO VAZIO',))
add('PROG045A','found',fixtures={'PEDDET01.dat':b'00002\n','CADASTRO3.dat':order()+order(2,'Bia')},files={'CADASTRO4.dat':order(2,'Bia')})
add('PROG045A','absent',fixtures={'PEDDET01.dat':b'00099\n','CADASTRO3.dat':order()},contains=('FIM DE PROGRAMA',))
add('PROGTEST4','search',stdout_exact=('CLIENTE ENCONTRADO: '+'JOÃO SILVA'.ljust(20)+'\n').encode(),
    reference_stdout_exact=b'CLIENTE ENCONTRADO: '+'JOÃO SILVA'.encode().ljust(20,b' ')+b'\n',
    oracle_note='PIC X(20) com JOÃO SILVA: ISO-8859-1 interno no projeto versus bytes UTF-8 no GnuCOBOL. Uma posição de padding difere; expectativas binárias independentes para os dois lados.')
for mode in ('N','I','S'):
    original=[salary('Bia',21,200000),salary('Ana',31,100000)]
    empty=salary('',0,0)
    ordered=original if mode=='I' else list(reversed(original))
    expected=(b'TABELA ANTES DA ORDENACAO:\n'+b''.join(original)+empty*18+
        b'DEFINA MODO DE CLASSIFICACAO\n[N] NOME [I] IDADE [S] SALARIO\n'+
        b'TABELA DEPOIS DA ORDENACAO:\n'+empty*18+b''.join(ordered)+b'FIM DE PROGRAMA\n')
    add('SORT002A','sort-'+mode,mode+'\n',{'CADASTRO3.dat':b''.join(original)},stdout_exact=expected)
add('VALCNPJ','digits','11222333000181\n\n',contains=('WS-LEN : 40\n','CNPJ invalido.\n'),rationale='O fonte conta as 40 posições de WS-RAW e sai antes do cálculo de DV; não corrige esse defeito do fonte.')
add('VALCNPJ','exit','\n',stdout_exact=b'=== Validador de CNPJ (mod 11) ===\nDigite um CNPJ (vazio para sair):\n')
add('VALCPF01','formatted','123.456.789-01\n',contains=('CPF COM FORMATO VALIDO\n',))
add('VALCPF01','bad-format','12345678901\n',contains=('FORMATO INVALIDO: PONTOS E TRACOS FORA DO PADRAO',))
add('VALIDA1A','cpf','12345678901\n',contains=('CPF: 123.456.789-01\n',))
add('VALIDA1A','cnpj','11222333000181\n',contains=('CNPJ: 11.222.333/0001-81\n',))
add('VALIDA1A','bad-branch','11222333000081\n',contains=('FILIAL COM FORMATO INVALIDO',))

add('GRAV001A','empty','0\n',contains=('COUNT:00\n','RC:+000000000\n'),files={'SEQSAI02.dat':b''})
add('GRAV001A','two','2\n',contains=('COUNT:02\n','RC:+000000000\n'),files={'SEQSAI02.dat':shared_user(1)+shared_user(2)})
add('LER0001A','empty',fixtures={'SEQENT01.dat':b''},contains=('COUNT:00\n','RC:+000000000\n'))
add('LER0001A','two',fixtures={'SEQENT01.dat':shared_user(1)+shared_user(2)},contains=('COUNT:02\n','FIRST:01:Ana','SECOND:02:Ana','RC:+000000000\n'))
add('PROG042B','empty',fixtures={'CADASTRO3.dat':b''},contains=('NEXT:00010\n','RC:+000000000\n'))
add('PROG042B','next',fixtures={'CADASTRO3.dat':order(5)+order(2)},contains=('NEXT:00006\n','RC:+000000000\n'))
add('PROGTIME','noon',contains=('TIME:12345600\n','PERIOD:BOM DIA!','RC:+000000000\n'))
add('PROGTIME','afternoon',contains=('TIME:15102000\n','PERIOD:BOA TARDE!'),environment={'COBOL_DATETIME':'2024-02-29T15:10:20','COB_CURRENT_DATE':'20240229151020'})
add('PROGTIME','night-source-condition',contains=('TIME:20102000\n','PERIOD:MADRUGADA!'),environment={'COBOL_DATETIME':'2024-02-29T20:10:20','COB_CURRENT_DATE':'20240229201020'},rationale='O AND >=19 e <=00 do fonte é impossível; preservar MADRUGADA às 20h.')


def report_rows(rows,width=100):
    return b''.join(row[:width].ljust(width,b' ')+b'\n' for row in rows)


def fields(*segments):
    return record(*segments)


def report_header(program,page=1):
    border=('**'+'-'*76+'**').encode()
    caption='                RELATORIO CADASTRO '+('USUARIO' if program=='REL0001A' else 'CLIENTE')
    return [border,fields((f'** {program}                    COBOL DICAS',67),('17/11/2026',10),(' **',3)),
        fields(('** PAG: ',8),(f'{page:02d}',2),(caption,62),('12:34',5),(' **',3)),border]


def user_report(count):
    rows=report_header('REL0001A')
    for i in range(1,count+1):
        if i==3:rows.extend([b' '*80,*report_header('REL0001A',2)])
        rows.extend([
            fields(('NOME: ',6),('Ana',30),(' - CODIGO: ',11),(f'{i:02d}',2)),
            # O fonte escreve DET2 antes de mover TELEFONE. O primeiro é zero.
            fields(('IDADE: ',8),('25',2),(' - DATA NASC.: ',15),('01/01/2000',10),(' - TELEFONE: ',13),('000000000' if i==1 else '123456789',9)),
            fields(('CARGO: ',7),('Dev',20),(' - E-MAIL: ',11),('a@example.com',30)),
            fields(('ENDERECO: ',10),('Rua Um',50)),
            fields(('CIDADE: ',14),('Cidade',30),(' - ESTADO: ',11),('SP',2),(' - CEP: ',8),('12345678',8)),
            ('**'+'-'*76+'**').encode()])
    return report_rows(rows)


add('REL0001A','empty','0\n',contains=('RELATORIO GERADO COM SUCESSO!','COUNT:00'),files={'REL0001A.txt':user_report(0)})
add('REL0001A','pagination','3\n',contains=('COUNT:03','RC:+000000000'),files={'REL0001A.txt':user_report(3)})


def salary_report(items):
    rows=report_header('REL0002A')+[fields(('NOME  ',6),('',25),('   IDADE  ',10),('     SALARIO',12))]
    total=0
    for name,age,cents in items:
        rows.append(fields((name,30),('',7),(f'{age:02d}',2),('',6),(money(Decimal(cents)/100,9),9)))
        total+=cents
    rows.extend([b' '*80,fields(('',2),('QTDE. REG.: ',12),(f'{len(items):02d}',2),('',7),('TOTAL SALARIO: R$',17),(money(Decimal(total)/100,14),14))])
    return report_rows(rows)


add('REL0002A','empty',fixtures={'CADASTRO3.dat':b''},contains=('QTDE. REG.: 0000\n',),files={'REL0002A.txt':salary_report([])})
add('REL0002A','total',fixtures={'CADASTRO3.dat':salary()+salary('Bia',31,125050)},contains=('QTDE. REG.: 0002\n','2.250,50'),files={'REL0002A.txt':salary_report([('Ana',25,100000),('Bia',31,125050)])})


def invoice(items):
    border=('*'+'-'*78+'*').encode()
    rows=[border,fields(('* ',2),('',4),('SIMULADOR DE NOTAS FISCAIS - SIMPLIFICADAS',42),('',6),('DATA EMISSAO: ',14),('17/11/2026',10),(' *',2)),border,
        fields(('* ',2),('COD.',4),('',2),('DESCRICAO',9),('',28),('VALOR',5),('',5),('IMPOSTOS',8),('',8),('TOTAL',5),('',2),(' *',2))]
    total=Decimal(0)
    for code,name,cents in items:
        price=Decimal(cents)/100
        tax=(price*Decimal('.18')).quantize(Decimal('.01'),rounding=ROUND_DOWN)+(price*Decimal('.05')).quantize(Decimal('.01'),rounding=ROUND_DOWN)
        amount=price+tax;total+=amount
        rows.append(fields(('* ',2),(f'{code:05d}',5),('',1),(name,30),('',2),(money(price,10),10),('',3),(money(tax,10),10),('',3),(money(amount,10),10),('',2),(' *',2)))
    rows.extend([border,fields(('* ',2),('VALOR TOTAL DA NOTA:',20),('',44),(money(total,10),10),('',2),(' *',2)),border])
    return report_rows(rows,80)


add('PROG027A','empty',fixtures={'PRODUTOS.dat':b''},files={'NOTAFISCAL.dat':invoice([])})
add('PROG027A','tax',fixtures={'PRODUTOS.dat':line(('00001',5),('Livro',30),('00010000',8))},files={'NOTAFISCAL.dat':invoice([(1,'Livro',10000)])})


def boleto(days):
    border=('*'+'-'*78+'*').encode()
    multa=Decimal(2) if days else Decimal(0)
    juros=Decimal(days)/10
    rows=[border,fields(('* ',2),('',16),('BOLETO FICTICIO - NAO UTILIZAR PARA PAGAMENTO',45),('',15),(' *',2)),border,
        fields(('* ',2),('Cedente: ',9),('Empresa',43),('| Vencimento: ',14),(f'{17-days:02d}/11/2026',10),(' *',2)),
        fields(('* ',2),('Nosso Numero: ',14),('1',20),('',18),('|------------------------',25),('*',1)),
        fields(('* ',2),('Base de calculo (hoje): ',24),('17/11/2026',10),('',18),('| Valor:    ',12),(money(100,12),12),(' *',2)),border,
        fields(('* ',2),('',41),('| Multa (',9),(money(2,6),6),('%):     ',8),(money(multa,12),12),(' *',2)),
        fields(('* ',2),('Dias de atraso: ',16),(f'{days:05d}',6),('',19),('| Juros (',9),('   ,100',7),('%/dia):',7),(money(juros,12),12),(' *',2)),
        fields(('* ',2),('',41),('|-----------------------------------',36),('*',1)),
        fields(('* ',2),('',41),('| Total a pagar:       ',23),(money(Decimal(100)+multa+juros,12),12),(' *',2)),border,
        fields(('* ',2),('Sacado : ',9),('Ana',60),('',7),(' *',2)),border,
        fields(('* ',2),('Linha digitavel:       ',24),('00190.00009 01234.5678900 00000.000000 0 00000000000000',52),(' *',2)),border,b' '*80]
    return report_rows(rows,80)


for days in (0,7):
    title=f'1|Ana|Empresa|10000|202611{17-days:02d}|00000000'.encode().ljust(256,b' ')+b'\n'
    add('PROG025A','on-time' if not days else 'late',fixtures={'TITULOS.dat':title,'PARAMETROS.dat':b'2,00|0,100'.ljust(64,b' ')+b'\n'},
        contains=('TITULOS PROCESSADOS:      01','REGISTROS GRAVADOS :      01'),files={'BOLETOS.dat':boleto(days)})
