import json
from ctypes.util import find_library
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from cobol_compiler.driver import compile_file
from tools.functional_execution import environment, execution_limits
from tools.terminal_probe import run_terminal


def unit(name, body, *, data='', using=''):
    return f"""IDENTIFICATION DIVISION.
PROGRAM-ID. {name}.
{data}
PROCEDURE DIVISION{using}.
{body}
"""


class DynamicCallTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mods = self.root/'modules'
        self.mods.mkdir()

    def write(self, name, text):
        path = self.root/name
        path.write_text(text, encoding='utf-8')
        return path

    def build(self, name, text, *, output=None, **options):
        source = self.write(name+'.cob',text)
        return compile_file(source,output or self.root/name,source_format='free',dialect='gnucobol',**options)

    def good(self, result):
        self.assertTrue(result.success,[d.format() for d in result.diagnostics]+[result.gcc_stderr])
        return Path(result.output)

    def run_program(self, program, **extra):
        return subprocess.run([program],cwd=self.root,env=environment(extra),input=b'',
                              capture_output=True,timeout=8,preexec_fn=execution_limits)

    def module(self, name, body, *, data='', using=''):
        return self.good(self.build(name,unit(name,body,data=data,using=using),
                                    output=self.mods/(name.upper()+'.so'),module=True))

    def test_install_later_variable_case_returning_and_gnucobol(self):
        caller = unit('CALLER',"""
MOVE 17 TO RETURN-CODE
CALL DEST RETURNING ANSWER
  ON EXCEPTION MOVE 1 TO MARKER
  NOT ON EXCEPTION MOVE 2 TO MARKER
END-CALL
DISPLAY MARKER ':' ANSWER ':' RETURN-CODE
MOVE 0 TO RETURN-CODE
STOP RUN.
""",data="""DATA DIVISION.
WORKING-STORAGE SECTION.
01 DEST PIC X(16) VALUE 'piece'.
01 ANSWER PIC 99 VALUE 42.
01 MARKER PIC 9.""")
        main = self.good(self.build('caller',caller,module_dirs=[self.mods]))
        miss = self.run_program(main)
        self.assertEqual((miss.returncode,miss.stdout,miss.stderr),(0,b'1:42:+000000017\n',b''))
        piece = self.module('piece','GOBACK RETURNING 7.')
        self.assertIn('cobol_project_module_v1',subprocess.check_output(['nm','-D',piece],text=True))
        found = self.run_program(main)
        self.assertEqual((found.returncode,found.stdout,found.stderr),(0,b'2:07:+000000017\n',b''))
        if shutil.which('cobc'):
            ref = self.root/'ref'
            env = environment({'TMPDIR':str(self.root)})
            subprocess.run(['cobc','-free','-x',self.root/'caller.cob','-o',ref],cwd=self.root,env=env,check=True,capture_output=True)
            subprocess.run(['cobc','-free','-m',self.root/'piece.cob','-o',self.mods/'piece.so'],cwd=self.root,env=env,check=True,capture_output=True)
            oracle = self.run_program(ref,COB_LIBRARY_PATH=str(self.mods))
            self.assertEqual((oracle.returncode,oracle.stdout,oracle.stderr),(found.returncode,found.stdout,found.stderr))

    def test_reference_content_value_and_state_across_modules(self):
        data = """DATA DIVISION.
WORKING-STORAGE SECTION.
01 VALUE-A PIC 99 VALUE 10.
01 VALUE-B PIC 99 VALUE 20.
01 VALUE-C PIC 99 VALUE 30.
01 ANSWER PIC 99."""
        params = """DATA DIVISION.
WORKING-STORAGE SECTION.
01 COUNTER PIC 99.
LINKAGE SECTION.
01 RECEIVER-A PIC 99.
01 RECEIVER-B PIC 99.
01 RECEIVER-C PIC 99."""
        body = """ADD 1 TO COUNTER
ADD 1 TO RECEIVER-A RECEIVER-B RECEIVER-C
DISPLAY RECEIVER-A ':' RECEIVER-B ':' RECEIVER-C
EXIT PROGRAM RETURNING COUNTER."""
        for name in ('FIRST-MOD','SECOND-MOD'):
            self.module(name,body,data=params,using=' USING RECEIVER-A RECEIVER-B BY VALUE RECEIVER-C')
        calls = [f"CALL '{name}' USING BY REFERENCE VALUE-A BY CONTENT VALUE-B BY VALUE VALUE-C RETURNING ANSWER\nDISPLAY ANSWER"
                 for name in ('first-mod','FiRsT-mOd','SECOND-MOD')]
        main = self.good(self.build('caller',unit('CALLER','\n'.join(calls)+
            '\nDISPLAY VALUE-A ":" VALUE-B ":" VALUE-C STOP RUN.',data=data)))
        run = self.run_program(main,COBOL_MODULE_PATH=str(self.mods))
        self.assertEqual((run.returncode,run.stdout,run.stderr),
                         (0,b'11:21:31\n01\n12:21:31\n02\n13:21:31\n01\n13:20:30\n',b''))

    def test_transitive_module_uses_linked_and_dynamic_programs(self):
        self.module('SECOND-MOD','DISPLAY "second" GOBACK.')
        self.module('FIRST-MOD','CALL "LiNkEd" CALL "SECOND-MOD" GOBACK.')
        linked = self.write('linked.cob',unit('LINKED','DISPLAY "linked" GOBACK.'))
        main = self.good(self.build('caller',unit('CALLER','CALL "FIRST-MOD" STOP RUN.'),
                                    source_paths=[linked], module_dirs=[self.mods]))
        run=self.run_program(main)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'linked\nsecond\n',b''))

    def test_unchosen_path_and_unhandled_missing(self):
        main = self.good(self.build('caller',unit('CALLER',"""
DISPLAY "before"
IF 1 = 2 CALL "SKIPPED" END-IF
DISPLAY "reached"
CALL "ABSENT"
DISPLAY "after"
STOP RUN.
""")))
        run=self.run_program(main)
        self.assertEqual((run.returncode,run.stdout),(1,b'before\nreached\n'))
        self.assertIn(b"CALL_NOT_FOUND: CALL 'ABSENT'",run.stderr)
        result=self.build('strict',unit('STRICT','CALL "ABSENT" STOP RUN.'),static_call=True)
        self.assertFalse(result.command)
        self.assertIn('LINK_UNRESOLVED_CALL',{d.code for d in result.diagnostics})

    def test_module_abi_and_argument_layout_are_checked(self):
        foreign=self.write('foreign.c','int FOREIGN(void) {return 0;}')
        subprocess.run(['gcc','-shared','-fPIC',foreign,'-o',self.mods/'FOREIGN.so'],check=True,capture_output=True)
        self.module('FORMAL','DISPLAY "callee entered" GOBACK.',
                    data='DATA DIVISION. LINKAGE SECTION. 01 SLOT PIC 99.',using=' USING SLOT')
        for target,using,code in [('FOREIGN','','CALL_MODULE_ABI'),('FORMAL','USING SMALL','CALL_LAYOUT_MISMATCH'),
                                  ('FORMAL','','CALL_ARITY'),('FORMAL','USING BY VALUE 1','CALL_MODE_MISMATCH')]:
            with self.subTest(target=target,code=code):
                caller=unit('PARENT',f"CALL '{target}' {using} STOP RUN.",
                            data='DATA DIVISION. WORKING-STORAGE SECTION. 01 SMALL PIC 9.')
                run=self.run_program(self.good(self.build('parent',caller,module_dirs=[self.mods])))
                self.assertEqual((run.returncode,run.stdout),(1,b''))
                self.assertIn(code.encode(),run.stderr)

    def test_internal_error_does_not_take_resolution_handler(self):
        self.module('BAD','DISPLAY "entered" OPEN INPUT INPUT-FILE GOBACK.',data="""
DATA DIVISION.
FILE SECTION.
FD INPUT-FILE.
01 INPUT-REC PIC X.
""".strip().replace('DATA DIVISION.',"""ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
SELECT INPUT-FILE ASSIGN TO "missing.dat" ORGANIZATION LINE SEQUENTIAL.
DATA DIVISION."""))
        prog=self.good(self.build('caller',unit('CALLER',
            'CALL "BAD" ON EXCEPTION DISPLAY "caught" END-CALL STOP RUN.'),module_dirs=[self.mods]))
        run=self.run_program(prog)
        self.assertEqual((run.returncode,run.stdout),(1,b'entered\n'))
        self.assertIn(b'FILE_OPEN',run.stderr)

    def native_library(self):
        source=self.write('fixture.c',r"""
#include <stdarg.h>
#include <string.h>
static int token=21;
int answer(void) { return 7; }
int twice(int a) { return 2*a; }
void *token_address(void) { return &token; }
int token_value(void *p) { return p==&token ? token : -1; }
int raw_update(void *p) {
    unsigned char *bytes=p;
    if (bytes[0]!='A'||bytes[1]!='B'||bytes[2]!='C') return -1;
    bytes[2]='!'; return 3;
}
int text_width(const char *text) {return (int)strlen(text);}
int variadic_sum(int count, ...) {
    va_list args;
    va_start(args,count);
    int result=0;
    for(int i=0;i<count;++i)result+=va_arg(args,int);
    va_end(args);
    return result;
}
""")
        lib=self.root/'fixture.so'
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',source,'-o',lib],
                       check=True,capture_output=True)
        entries=[]
        for name,returns,params in [('answer','int',[]),('twice','int',['int']),('token_address','pointer',[]),
            ('token_value','int',['pointer']),('raw_update','int',['raw:3']),('text_width','int',['cstring']),
            ('variadic_sum','int',['int']),('no_symbol','int',[])]:
            item={'name':name,'library':'./fixture.so','returns':returns,'params':params}
            if name=='variadic_sum':item['varargs']=['int','int']
            entries.append(item)
        return lib,self.write('ffi.json',json.dumps(entries))

    def test_typed_native_values_pointers_buffers_and_varargs(self):
        lib,manifest=self.native_library()
        data="""DATA DIVISION.
WORKING-STORAGE SECTION.
01 ANSWER PIC 99.
01 OPAQUE USAGE POINTER.
01 BUFFER-A PIC XXX VALUE 'ABC'.
01 NATIVE-NAME PIC X(12) VALUE 'twice'."""
        body="""
CALL 'answer' RETURNING ANSWER DISPLAY ANSWER
CALL NATIVE-NAME USING BY VALUE 9 RETURNING ANSWER DISPLAY ANSWER
CALL 'token_address' RETURNING OPAQUE
CALL 'token_value' USING BY VALUE OPAQUE RETURNING ANSWER DISPLAY ANSWER
CALL 'raw_update' USING BY CONTENT BUFFER-A RETURNING ANSWER DISPLAY BUFFER-A
CALL 'raw_update' USING BUFFER-A RETURNING ANSWER DISPLAY BUFFER-A
CALL 'text_width' USING BUFFER-A RETURNING ANSWER DISPLAY ANSWER ':' BUFFER-A
CALL 'variadic_sum' USING BY VALUE 2 10 12 RETURNING ANSWER DISPLAY ANSWER
CALL 'no_symbol' ON EXCEPTION MOVE 1 TO ANSWER END-CALL DISPLAY ANSWER
STOP RUN.
"""
        main=self.good(self.build('caller',unit('CALLER',body,data=data),ffi_manifests=[manifest]))
        run=self.run_program(main)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'07\n18\n21\nABC\nAB!\n03:AB!\n22\n01\n',b''))
        self.assertTrue(lib.is_file())

    def test_unknown_signature_symbol_case_and_invalid_pointer_are_rejected(self):
        lib,manifest=self.native_library()
        for name,options,code in [
            ('answer',{'libraries':[str(lib)]},'CALL_SIGNATURE_REQUIRED'),
            ('Answer',{'libraries':[str(lib)]},'CALL_NOT_FOUND'),
            ('token_value',{'ffi_manifests':[manifest]},'CALL_NATIVE_ARGUMENT'),
            ('no_symbol',{'ffi_manifests':[manifest]},'CALL_SYMBOL_NOT_FOUND'),
            ('broken',{'ffi_manifests':[self.write('missing.json',json.dumps([
                {'name':'broken','library':'./absent.so','returns':'int','params':[]}]))]},'CALL_LIBRARY_LOAD'),
        ]:
            with self.subTest(name=name):
                args=' USING BY VALUE 1' if name=='token_value' else ''
                main=self.good(self.build('caller',unit('CALLER',f"CALL '{name}'{args} STOP RUN."),**options))
                run=self.run_program(main)
                self.assertEqual(run.returncode,1)
                self.assertIn(code.encode(),run.stderr)

    def test_native_process_symbol_and_malformed_manifest(self):
        manifest=self.write('process.json',json.dumps([{'name':'abs','returns':'int','params':['int']}]))
        src=unit('CALLER',"CALL 'abs' USING BY VALUE -9 RETURNING REPLY DISPLAY REPLY STOP RUN.",
                 data='DATA DIVISION. WORKING-STORAGE SECTION. 01 REPLY PIC 99.')
        main=self.good(self.build('caller',src,ffi_manifests=[manifest]))
        self.assertEqual(self.run_program(main).stdout,b'09\n')
        manifest.write_text('[{"name":"bad","returns":"int","params":[],"varargs":["int"]}]')
        result=self.build('caller',src,ffi_manifests=[manifest])
        self.assertFalse(result.command)
        self.assertIn('CALL_CONFIGURATION',{d.code for d in result.diagnostics})

    def test_checked_variadic_format_and_output_temporary(self):
        manifest=self.write('format.json',json.dumps([
            {'name':'sscanf','returns':'int','params':['cstring','cstring'],
             'varargs':['out-int'],'format':'scanf'},
        ]))
        data="""DATA DIVISION.
WORKING-STORAGE SECTION.
01 CAPTURED PIC 99 VALUE 42.
01 STATUS-CODE PIC 99."""
        body="""CALL 'sscanf' USING '31' '%d' CAPTURED RETURNING STATUS-CODE
DISPLAY STATUS-CODE ':' CAPTURED
CALL 'sscanf' USING '9' '%n' CAPTURED RETURNING STATUS-CODE
    ON EXCEPTION MOVE 8 TO STATUS-CODE
END-CALL
DISPLAY STATUS-CODE ':' CAPTURED
STOP RUN."""
        main=self.good(self.build('caller',unit('CALLER',body,data=data),ffi_manifests=[manifest]))
        run=self.run_program(main)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'01:31\n08:31\n',b''))

    @unittest.skipUnless(shutil.which('cobc'),'GnuCOBOL oracle missing')
    def test_native_integers_and_varargs_agree_with_gnucobol(self):
        _,manifest=self.native_library()
        data='DATA DIVISION. WORKING-STORAGE SECTION. 01 REPLY PIC 99.'
        body="""CALL 'twice' USING BY VALUE 6 RETURNING REPLY DISPLAY REPLY
CALL 'variadic_sum' USING BY VALUE 2 10 12 RETURNING REPLY DISPLAY REPLY
STOP RUN."""
        main=self.good(self.build('caller',unit('CALLER',body,data=data),ffi_manifests=[manifest]))
        reference=self.root/'oracle'
        subprocess.run(['cobc','-free','-x','-fstatic-call',self.root/'caller.cob',
                        self.root/'fixture.c','-o',reference],cwd=self.root,
                       env=environment({'TMPDIR':str(self.root)}),check=True,capture_output=True)
        ours=self.run_program(main)
        gnu=self.run_program(reference)
        self.assertEqual((ours.returncode,ours.stdout,ours.stderr),(0,b'12\n22\n',b''))
        self.assertEqual((gnu.returncode,gnu.stdout,gnu.stderr),(ours.returncode,ours.stdout,ours.stderr))

    @unittest.skipUnless(find_library('ncurses')=='libncurses.so.6','ncurses ABI 6 missing')
    def test_ncurses_window_and_getch_use_the_native_types(self):
        data="""DATA DIVISION.
WORKING-STORAGE SECTION.
01 WIN-HANDLE USAGE POINTER.
01 KEY-CODE PIC 999."""
        body="""CALL 'initscr' RETURNING WIN-HANDLE
CALL 'keypad' USING BY VALUE WIN-HANDLE 1
CALL 'cbreak'
CALL 'noecho'
CALL 'mvprintw' USING BY VALUE 2 3 BY REFERENCE 'ready'
CALL 'refresh'
CALL 'getch' RETURNING KEY-CODE
CALL 'endwin'
DISPLAY KEY-CODE
STOP RUN."""
        main=self.good(self.build('caller',unit('CALLER',body,data=data),libraries=['ncurses']))
        trial=run_terminal(main,b'Q',self.root)
        self.assertEqual((trial['returncode'],trial['stderr']['bytes']),(0,0))
        self.assertTrue(trial['terminal_restored'])
        import base64
        stdout=base64.b64decode(trial['stdout']['base64'])
        self.assertIn(b'ready',stdout)
        self.assertIn(b'081\r\n',stdout)
