"""Driver GCC com publicação atômica da saída; nunca executa COBOL ao compilar."""

from dataclasses import dataclass, field
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from .c_codegen import generate_c
from .diagnostics import Diagnostic
from .semantic import check_file

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'runtime'
RUNTIME_SOURCES=[RUNTIME/name for name in ('decimal.c','fields.c','files.c')]


@dataclass(slots=True)
class CompilationResult:
    semantic: object
    generated: object | None = None
    diagnostics: list = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    gcc_stdout: str = ''
    gcc_stderr: str = ''
    output: str | None = None
    c_path: str | None = None
    success: bool = False


def compile_result(semantic,output=None,*,emit_c=None,keep_c=False,module=False,check_backend=False,gcc='gcc',sanitize=False):
    result=CompilationResult(semantic,diagnostics=list(semantic.diagnostics))
    if not semantic.success:return result
    result.generated=generate_c(semantic,module=module)
    result.diagnostics.extend(result.generated.diagnostics)
    if not result.generated.success:return result
    if check_backend:
        result.success=True
        return result
    span=semantic.ast.span
    destination=Path(output or Path(semantic.frontend.preprocessed.root_file).stem.lower()).absolute()
    try:
        destination.parent.mkdir(parents=True,exist_ok=True)
        if emit_c or keep_c:
            c_path=Path(emit_c or str(destination)+'.c').absolute()
            if c_path==destination:
                result.diagnostics.append(Diagnostic('OUTPUT_PATH_COLLISION','C e executável precisam de caminhos distintos.',span,'driver'))
                return result
            c_path.parent.mkdir(parents=True,exist_ok=True)
            c_path.write_text(result.generated.c_source,encoding='utf-8')
            result.c_path=str(c_path)
        executable=shutil.which(gcc)
        if not executable:
            result.diagnostics.append(Diagnostic('GCC_NOT_FOUND',f'Compilador GCC não encontrado: {gcc}.',span,'driver'))
            return result
        with tempfile.TemporaryDirectory(prefix='.cobol-build-',dir=destination.parent) as td:
            temporary=Path(td)
            source=temporary/'program.c'
            source.write_text(result.generated.c_source,encoding='utf-8')
            artifact=temporary/('program.o' if module else 'program')
            command=[executable,'-std=c11','-Wall','-Wextra','-I',str(RUNTIME)]
            if sanitize:command+=['-fsanitize=undefined,address','-fno-omit-frame-pointer','-g']
            if module:command+=['-c',str(source)]
            else:command+=[str(source),*(str(p) for p in RUNTIME_SOURCES)]
            command+=['-o',str(artifact)]
            result.command=command
            process=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
            result.gcc_stdout,result.gcc_stderr=process.stdout,process.stderr
            if process.returncode:
                if not result.c_path:
                    failed=Path(str(destination)+'.failed.c')
                    failed.write_text(result.generated.c_source,encoding='utf-8')
                    result.c_path=str(failed)
                result.diagnostics.append(Diagnostic('GCC_FAILED',f'GCC terminou com status {process.returncode}; C preservado em {result.c_path}.',span,'gcc'))
                return result
            os.replace(artifact,destination)
            result.output=str(destination)
            result.success=True
    except (OSError,subprocess.TimeoutExpired) as error:
        result.diagnostics.append(Diagnostic('BUILD_FAILED',str(error),span,'driver'))
    return result


def compile_file(path,output=None,*,include_dirs=(),source_paths=(),strict=False,debug_lines=False,**options):
    semantic=check_file(path,include_dirs=include_dirs,source_paths=source_paths,strict=strict,debug_lines=debug_lines)
    return compile_result(semantic,output,**options)
