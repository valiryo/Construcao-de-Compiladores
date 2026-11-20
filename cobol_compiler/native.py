"""Validate explicit C ABI contracts and emit typed POSIX symbol adapters."""

from dataclasses import dataclass
import json
from pathlib import Path
import re


@dataclass(frozen=True)
class Signature:
    name: str
    library: str | None
    returns: str
    params: tuple[str, ...]
    varargs: tuple[str, ...] | None = None
    format_kind: str | None = None
    terminal: int = 0


TYPES = {
    'int': 'int', 'bool': '_Bool', 'pointer': 'void *',
    'window': 'struct _win_st *', 'cstring': 'const char *',
    'out-int': 'int *', 'void': 'void',
}
RESULTS = {'int': 'CB_RESULT_INT', 'pointer': 'CB_RESULT_POINTER',
           'window': 'CB_RESULT_POINTER', 'void': 'CB_RESULT_VOID'}


def signatures(manifests, libraries):
    result = {}
    if 'ncurses' in libraries:
        soname = 'libncurses.so.6'
        for name in ('cbreak', 'noecho', 'clear', 'refresh', 'getch', 'endwin'):
            result[name] = Signature(name, soname, 'int', (), terminal=2 if name == 'endwin' else 0)
        result['initscr'] = Signature('initscr', soname, 'window', (), terminal=1)
        result['keypad'] = Signature('keypad', soname, 'int', ('window', 'bool'))
        result['mvprintw'] = Signature('mvprintw', soname, 'int', ('int', 'int', 'cstring'), (), 'printf')
        result['scanw'] = Signature('scanw', soname, 'int', ('cstring',), (), 'scanf')
        result['mvscanw'] = Signature('mvscanw', soname, 'int', ('int', 'int', 'cstring'), (), 'scanf')
    declared = set()
    for path in manifests:
        path = Path(path).resolve()
        entries = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(entries, list):
            raise ValueError('O manifesto FFI deve ser uma lista de assinaturas.')
        for item in entries:
            if not isinstance(item, dict) or set(item)-{'name','library','returns','params','varargs','format','abi'}:
                raise ValueError('Campos inválidos no manifesto FFI.')
            name = item.get('name')
            if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,254}',name) or name in declared:
                raise ValueError(f'Símbolo FFI inválido ou duplicado: {name!r}.')
            library = item.get('library')
            if library is not None and (not isinstance(library,str) or not library or '\0' in library):
                raise ValueError(f'Biblioteca FFI inválida para {name}.')
            if library and (not library.isascii() or '/' in library):
                library = str((path.parent/library).resolve())
            returns = item.get('returns')
            params = item.get('params')
            varargs = item.get('varargs')
            fmt = item.get('format')
            if (not isinstance(returns,str) or returns not in RESULTS or not isinstance(params,list)
                or ('varargs' in item and not isinstance(varargs,list)) or item.get('abi','c')!='c'):
                raise ValueError(f'Protótipo C inválido para {name}.')
            valid = lambda t: isinstance(t,str) and (t in TYPES.keys()-{'void','window'} or re.fullmatch(r'raw:[1-9][0-9]{0,7}',t))
            if not all(valid(t) for t in params+(varargs or [])) or len(params)+len(varargs or [])>64:
                raise ValueError(f'Tipos de parâmetros inválidos para {name}.')
            if varargs is not None and (not params or 'bool' in varargs):
                raise ValueError(f'Varargs exige parâmetros fixos e tipos já promovidos em {name}.')
            if 'out-int' in params+(varargs or []) and returns!='int':
                raise ValueError(f'out-int exige retorno int em {name}.')
            if fmt is not None and (fmt not in ('printf','scanf') or varargs is None or params[-1]!='cstring'
                or any(t not in ({'int','cstring'} if fmt=='printf' else {'out-int'}) for t in varargs)):
                raise ValueError(f'Contrato de formato inválido para {name}.')
            declared.add(name)
            result[name] = Signature(name,library,returns,tuple(params),None if varargs is None else tuple(varargs),fmt)
    return list(result.values())


def library_paths(libraries):
    paths=[]
    for library in libraries:
        if not library or '\0' in library:
            raise ValueError('Nome de biblioteca vazio ou inválido.')
        if library=='ncurses':
            library='libncurses.so.6'
        elif '/' in library:
            library=str(Path(library).resolve())
        elif not re.fullmatch(r'[A-Za-z0-9_.+-]+\.so(?:\.[0-9]+)*',library):
            raise ValueError('Use um caminho, SONAME válido ou ncurses para --library.')
        if library not in paths:
            paths.append(library)
    return paths


def emit(signatures, quote):
    definitions = ['struct _win_st;'] if signatures else []
    entries = []
    for index, sig in enumerate(signatures):
        wrapper = f'cb_adapter_{index}'
        all_types = sig.params+(sig.varargs or ())
        lines = [f'static cb_call_result {wrapper}(cb_runtime *rt, void *address, cb_call_arg *args, size_t count) {{',
                 '    (void)rt; (void)args;',
                 f'    if (count != {len(all_types)}) return (cb_call_result){{.error="CALL_ARITY"}};']
        values = []
        outputs = []
        fail = 'return (cb_call_result){.error="CALL_NATIVE_ARGUMENT"};'
        for i, typ in enumerate(all_types):
            arg = f'args[{i}]'
            variable = f'p{i}'
            values.append(variable)
            if typ in {'int','bool'}:
                lines += [f'    int {variable};',f'    if (!cb_native_int(&{arg}, &{variable})) {fail}']
                if typ=='bool':
                    lines.append(f'    if ({variable} != 0 && {variable} != 1) {fail}')
            elif typ in {'pointer','window'}:
                lines += [f'    if ({arg}.mode != CB_VALUE || !{arg}.field.desc || {arg}.field.desc->category != 4) {fail}',
                          f'    {TYPES[typ]} {variable} = cb_pointer_load({arg}.field);']
            elif typ=='cstring':
                lines += [f'    const char *{variable} = cb_native_string(rt, &{arg});',f'    if (!{variable}) {fail}']
            elif typ=='out-int':
                lines += [f'    if ({arg}.mode != CB_REFERENCE || !{arg}.field.desc || {arg}.field.desc->category != 1 || {arg}.field.desc->scale) {fail}',
                          f'    int out{i} = 0;']
                values[-1] = f'&out{i}'
                outputs.append((i,arg))
            else:
                minimum = int(typ.split(':')[1])
                lines += [f'    if ({arg}.mode == CB_VALUE || !{arg}.field.p || {arg}.field.n < {minimum}) {fail}',
                          f'    void *{variable} = {arg}.field.p;']
        if sig.format_kind:
            scan = sig.format_kind=='scanf'
            codes = ''.join('s' if t=='cstring' else 'i' for t in sig.varargs)
            check = f'!cb_native_format(p{len(sig.params)-1}, "{codes}", {int(scan)})'
            if scan and not codes:
                check = '1'  # No writable conversion destinations were declared.
            lines.append(f'    if ({check}) return (cb_call_result){{.error="CALL_NATIVE_FORMAT"}};')
        fixed = [TYPES.get(t,'void *') for t in sig.params]
        if sig.varargs is not None:
            fixed.append('...')
        lines += [f'    {TYPES[sig.returns]} (*function)({", ".join(fixed) or "void"});',
                  '    _Static_assert(sizeof function == sizeof address, "Unsupported POSIX symbol ABI");',
                  '    memcpy(&function, &address, sizeof function);']
        call = f'function({", ".join(values)})'
        if sig.returns=='int':
            lines.append(f'    int result = {call};')
            for sequence,(i,arg) in enumerate(outputs):
                condition = f'if (result > {sequence}) ' if sig.format_kind=='scanf' else ''
                lines += [f'    {condition}{{ char number[32]; snprintf(number, sizeof number, "%d", out{i});',
                          f'        if (cb_store({arg}.field, cb_decimal(number), 0, 1)) return (cb_call_result){{.error="CALL_NATIVE_OUTPUT_RANGE"}}; }}']
            lines.append('    return (cb_call_result){.status=result};')
        elif sig.returns in {'pointer','window'}:
            lines.append(f'    return (cb_call_result){{.pointer={call}}};')
        else:
            lines += [f'    {call};','    return (cb_call_result){0};']
        definitions.append('\n'.join(lines+['}']))
        library = quote(sig.library,encoding='utf-8') if sig.library else 'NULL'
        entries.append(f'{{{quote(sig.name)}, {library}, {wrapper}, {RESULTS[sig.returns]}, {sig.terminal}}}')
    if entries:
        definitions.append('static const cb_native cb_native_entries[] = {\n    '+',\n    '.join(entries)+'\n};')
    return definitions
