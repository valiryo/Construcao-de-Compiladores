"""PTY isolado e interpretação estrita de células ANSI; bytes originais preservados."""
import fcntl
import os
import pty
import select
import signal
import struct
import subprocess
import termios
import time

from tools.functional_execution import environment, execution_limits, blob


def cells(data,rows=40,columns=100):
    text=data.decode('utf-8');grid=[[' ']*columns for _ in range(rows)]
    row=col=0;last=' ';saved=(0,0);wrap=False;autowrap=True;i=0
    def put(ch):
        nonlocal row,col,last,wrap
        if wrap:
            row+=1;col=0;wrap=False
            if row>=rows:grid.pop(0);grid.append([' ']*columns);row=rows-1
        grid[row][col]=ch;last=ch
        if col==columns-1:wrap=autowrap
        else:col+=1
    while i<len(text):
        ch=text[i];i+=1
        if ch=='\x1b':
            wrap=False
            if i>=len(text):raise ValueError('Truncated escape')
            ch=text[i];i+=1
            if ch=='[':
                start=i
                while i<len(text) and not ('@'<=text[i]<='~'):i+=1
                if i==len(text):raise ValueError('Truncated CSI')
                params=text[start:i];op=text[i];i+=1
                private=params.startswith('?');params=params.lstrip('?')
                args=[int(v or '0') for v in params.split(';')] if params else [0]
                n=args[0] or 1
                if op in 'Hf':row=(args[0] or 1)-1;col=((args[1] if len(args)>1 else 1) or 1)-1
                elif op=='d':row=n-1
                elif op in 'G`':col=n-1
                elif op=='A':row-=n
                elif op=='B':row+=n
                elif op=='C':col+=n
                elif op=='D':col-=n
                elif op=='E':row+=n;col=0
                elif op=='F':row-=n;col=0
                elif op=='I':col=(col//8+n)*8
                elif op=='Z':col=max(0,((col-1)//8-n+1)*8)
                elif op=='J':
                    for r in range(rows):
                        for c in range(columns):
                            if args[0]==2 or args[0]==0 and (r,c)>=(row,col) or args[0]==1 and (r,c)<=(row,col):grid[r][c]=' '
                elif op=='K':
                    for c in range(columns):
                        if args[0]==2 or args[0]==0 and c>=col or args[0]==1 and c<=col:grid[row][c]=' '
                elif op=='X':grid[row][col:min(columns,col+n)]=[' ']*min(n,columns-col)
                elif op=='@':grid[row][col:]=([' ']*n+grid[row][col:])[:columns-col]
                elif op=='P':grid[row][col:]=(grid[row][col+n:]+[' ']*n)[:columns-col]
                elif op=='b':
                    for _ in range(n):put(last)
                elif op=='m':pass # Attributes retained in raw bytes; this view compares text cells.
                elif op in 'hl' and private and set(args)<={7,25}:
                    if 7 in args:autowrap=op=='h'
                elif op=='s':saved=(row,col)
                elif op=='u':row,col=saved
                else:raise ValueError(f'Unsupported CSI {params!r}{op}')
                row=max(0,min(rows-1,row));col=max(0,min(columns-1,col))
            elif ch in '()':
                if i>=len(text) or text[i] not in 'B0':raise ValueError('Unsupported character set')
                i+=1
            elif ch=='7':saved=(row,col)
            elif ch=='8':row,col=saved
            elif ch=='D':row=min(rows-1,row+1)
            elif ch=='E':row=min(rows-1,row+1);col=0
            else:raise ValueError(f'Unsupported escape {ch!r}')
        elif ch=='\r':col=0;wrap=False
        elif ch=='\n':
            row+=1;wrap=False
            if row>=rows:grid.pop(0);grid.append([' ']*columns);row=rows-1
        elif ch=='\b':col=max(0,col-1);wrap=False
        elif ch=='\t':col=min(columns-1,(col//8+1)*8);wrap=False
        elif ch=='\a':pass
        elif ch>=' ':put(ch)
        else:raise ValueError(f'Unsupported control {ord(ch)}')
    return [''.join(r) for r in grid]


def run_terminal(executable,stdin,directory,*,extra=(),rows=40,columns=100,timeout=8):
    master,slave=pty.openpty();process=None
    try:
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',rows,columns,0,0))
        before=termios.tcgetattr(slave)
        env=environment({'TERM':'ansi','COB_EXIT_WAIT':'off',**dict(extra)})
        process=subprocess.Popen([str(executable)],stdin=slave,stdout=slave,stderr=subprocess.PIPE,
            cwd=directory,env=env,start_new_session=True,preexec_fn=execution_limits)
        output=b'';start=last=time.monotonic();sent=False;timed_out=False
        while True:
            if select.select([master],[],[],.02)[0]:
                try:chunk=os.read(master,65536)
                except OSError:chunk=b''
                if chunk:output+=chunk;last=time.monotonic()
            if not sent and time.monotonic()-start>.1 and time.monotonic()-last>.05:
                os.write(master,stdin);sent=True
            if process.poll() is not None:
                while select.select([master],[],[],.01)[0]:
                    try:chunk=os.read(master,65536)
                    except OSError:break
                    if not chunk:break
                    output+=chunk
                break
            if time.monotonic()-start>timeout or len(output)>16*1024*1024:
                timed_out=True;os.killpg(process.pid,signal.SIGKILL);break
        process.wait();stderr=process.stderr.read();process.stderr.close();after=termios.tcgetattr(slave)
        mask=termios.ICANON|termios.ECHO
        result={'returncode':process.returncode,'timeout':timed_out,'stdout':blob(output),'stderr':blob(stderr),
            'stdin':blob(stdin),'terminal_encoding':'UTF-8','rows':rows,'columns':columns,
            'terminal_restored':before[3]&mask==after[3]&mask,'environment':{'TERM':'ansi','COB_EXIT_WAIT':'off'}}
        try:result['cells']=cells(output,rows,columns)
        except ValueError as error:result['decode_error']=str(error)
        return result
    finally:
        if process and process.poll() is None:process.kill();process.wait()
        os.close(master);os.close(slave)
