"""Driver GCC com publicação atômica da saída; nunca executa COBOL ao compilar."""

from dataclasses import dataclass, field
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile

from .c_codegen import CodegenResult, generate_c
from .diagnostics import Diagnostic
from .native import library_paths, signatures
from .semantic import SemanticResult, check_file

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'runtime'
RUNTIME_SOURCES=[RUNTIME/name for name in ('decimal.c','fields.c','files.c','calls.c')]


@dataclass(slots=True)
class CompilationResult:
    semantic: SemanticResult
    generated: CodegenResult | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    gcc_stdout: str = ''
    gcc_stderr: str = ''
    output: str | None = None
    c_path: str | None = None
    success: bool = False


def compile_result(semantic,output=None,*,emit_c=None,keep_c=False,module=False,shared=False,
                   check_backend=False,gcc='gcc',sanitize=False,static_call=None,module_dirs=(),
                   libraries=(),ffi_manifests=()):
    result=CompilationResult(semantic,diagnostics=list(semantic.diagnostics))
    if not semantic.success:return result
    shared=shared or bool(module and output and Path(output).suffix=='.so')
    module=module or shared
    try:
        native=signatures(ffi_manifests,libraries)
        native_libraries=library_paths(libraries)
        dirs=tuple(str(Path(p).resolve()) for p in module_dirs)
        if any(':' in p for p in dirs):
            raise ValueError('Diretório de módulos não pode conter dois-pontos.')
    except (OSError,ValueError) as error:
        result.diagnostics.append(Diagnostic('CALL_CONFIGURATION',str(error),semantic.ast.span,'driver'))
        return result
    result.generated=generate_c(semantic,module=module,shared=shared,static_call=static_call,
                                signatures=native,module_dirs=dirs,libraries=native_libraries)
    result.diagnostics.extend(result.generated.diagnostics)
    if not result.generated.success:return result
    if check_backend:
        result.success=True
        return result
    span=semantic.ast.span
    source_stem=Path(semantic.frontend.preprocessed.root_file).stem
    program_id=semantic.ast.identification.program_id.upper()
    module_name=program_id if re.fullmatch(r'[A-Z0-9_-]+',program_id) else source_stem.upper()
    default_name=module_name+'.so' if shared else source_stem.lower()
    destination=Path(output or default_name).absolute()
    try:
        protected={path.resolve() for path in [*RUNTIME_SOURCES,RUNTIME/'cobol_runtime.h']}
        protected.update(Path(path).resolve() for path in ffi_manifests)
        protected.update(Path(path).resolve() for path in [*native_libraries,*(s.library for s in native)]
                         if path and Path(path).is_absolute())
        for unit in [semantic,*semantic.source_results]:
            protected.add(Path(unit.frontend.preprocessed.root_file).resolve())
            protected.update(Path(dep.resolved_file).resolve() for dep in unit.frontend.preprocessed.dependencies if dep.resolved_file)
        c_destination=Path(emit_c or str(destination)+'.c').absolute() if emit_c or keep_c else None
        if destination.resolve() in protected or c_destination and c_destination.resolve() in protected:
            result.diagnostics.append(Diagnostic('OUTPUT_SOURCE_COLLISION','A saída não pode sobrescrever fontes COBOL, COPY ou runtime.',span,'driver'))
            return result
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
            artifact=temporary/('program.so' if shared else 'program.o' if module else 'program')
            command=[executable,'-std=c11','-Wall','-Wextra','-I',str(RUNTIME)]
            if sanitize:command+=['-fsanitize=undefined,address','-fno-omit-frame-pointer','-g']
            if shared:command+=['-shared','-fPIC','-fvisibility=hidden',str(source)]
            elif module:command+=['-c',str(source)]
            else:command+=['-rdynamic',str(source),*(str(p) for p in RUNTIME_SOURCES),'-ldl']
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


def compile_file(path,output=None,*,include_dirs=(),source_paths=(),strict=False,debug_lines=False,source_format='fixed',dialect='project',**options):
    semantic=check_file(path,include_dirs=include_dirs,source_paths=source_paths,strict=strict,debug_lines=debug_lines,source_format=source_format,dialect=dialect)
    return compile_result(semantic,output,**options)
