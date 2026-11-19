"""C11 direto da AST validada. Casos do dispatcher são emitidos na visita,
sem bytecode, interpretação de COBOL ou representação intermediária executável.
"""

from dataclasses import asdict, dataclass, field
import hashlib
import json

from . import native

from . import ast as A
from .diagnostics import Diagnostic


def c_string(value, *, encoding='latin-1'):
    data=value.encode(encoding) if isinstance(value,str) else value
    return '"'+''.join(chr(byte) if 32<=byte<127 and byte not in (34,92) else f'\\{byte:03o}' for byte in data)+'"'


def function_name(name):
    return 'cob_p_'+hashlib.sha256(name.upper().encode()).hexdigest()[:16]


def descriptor(typ):
    category = {'numeric':1, 'index':1, 'group':2, 'numeric-edited':3, 'pointer':4}.get(typ['category'],0)
    usage = {'binary-le':1, 'packed-decimal':2}.get(typ['representation'],0)
    return ('{'+f'{category}, {typ["precision"] or 0}, {typ["scale"] or 0}, {int(typ["signed"])}, '
            f'{usage}, {ord(typ["decimal_point"])}, {c_string(typ["expanded_picture"] or "")}'+'}')


def shape_text(shape):
    if shape is None:return 'NULL'
    return c_string(hashlib.sha256(json.dumps(shape).encode()).hexdigest())


@dataclass(slots=True)
class CodegenResult:
    c_source: str | None
    diagnostics: list = field(default_factory=list)
    programs: list[str] = field(default_factory=list)
    entry: str | None = None

    @property
    def success(self):
        return self.c_source is not None and not any(d.severity in {'E','S'} for d in self.diagnostics)


class CodegenError(Exception):
    def __init__(self,code,message,node):
        self.code,self.message,self.node=code,message,node


class UnitGenerator:
    def __init__(self,result,*,is_main=False,native_count=0,module_dirs=(),library_count=0):
        self.r=result
        self.is_main=is_main
        self.root=result.ast
        self.symbols=result.table.symbols
        self.nodes={result.node_ids[id(node)]:node for node in A.walk(self.root)}
        self.index=0
        self.cases=[]
        self.labels={}
        self.declarations=[]
        self.areas={area:f'a{i}' for i,area in enumerate(result.layout.areas)}
        self.name=function_name(self.root.identification.program_id)
        self.sections=[]
        self.paragraphs=[]
        self.inline=[]
        self.inline_ranges=[]
        self.compatibility=result.frontend.preprocessed.dialect=='gnucobol'
        self.screen_index=0
        self.native_count=native_count
        self.module_dirs=module_dirs
        self.library_count=library_count

    def error(self,resource,node,message=None):
        raise CodegenError('UNSUPPORTED_BACKEND_'+resource,message or f'Backend não implementado: {resource}.',node)

    def ann(self,node):return self.r.annotation(node)
    def nid(self,node):return self.r.node_ids[id(node)]
    def desc(self,sid):return f'd_{sid}'
    def int_value(self,n):return f'cb_number("{n}")'
    def num_int(self,n):return f'cb_decimal("{n}")'

    def screen(self, reference, *, accept=False):
        sid=self.ann(reference).symbol_id
        root=self.nodes[self.symbols[sid].node_id]
        self.screen_index+=1; prefix=f'screen_{self.screen_index}'
        lines=[f'long long {prefix}_line=1, {prefix}_column=1;']
        inputs=[]
        for item in A.walk(root):
            if not isinstance(item,A.DataItem):continue
            clauses=item.clauses
            for clause in clauses:
                if isinstance(clause,A.ScreenPosition):
                    lines.append(f'{prefix}_{clause.axis.lower()}=cb_int({self.value(clause.value)});')
                if isinstance(clause,A.ScreenBlank):
                    if clause.mode!='SCREEN':self.error('SCREEN_BLANK_MODE',clause)
                    lines.extend(['cb_terminal_clear(rt);',f'{prefix}_line=1; {prefix}_column=1;'])
                if isinstance(clause,(A.OccursClause,A.RedefinesClause,A.UsageClause)):
                    self.error('SCREEN_CLAUSE',clause)
            if item.children:continue
            field_sid=self.ann(item).symbol_id
            layout=self.r.layout.items[field_sid]
            if not layout.size:continue
            field=self.symbol_field(field_sid)
            binding=next((c for c in clauses if isinstance(c,A.ScreenUsing)),None)
            if binding:lines.append(f'cb_move(rt, {self.value(binding.target)}, {field});')
            lines.extend([f'cb_terminal_at(rt, {prefix}_line, {prefix}_column);',
                          f'cb_display(rt, cb_field_value({field}));'])
            if binding and accept:
                if layout.size>4096:self.error('SCREEN_CAPACITY',item)
                inputs.append((field,self.field(binding.target)))
                lines.append(f'{prefix}_inputs[{len(inputs)-1}] = (cb_screen_field){{{field}, {self.field(binding.target)}, {prefix}_line, {prefix}_column}};')
            lines.append(f'{prefix}_column += {layout.size};')
        if inputs:
            if len(inputs)>1024:self.error('SCREEN_CAPACITY',root)
            lines.insert(0,f'cb_screen_field {prefix}_inputs[{len(inputs)}];')
            lines.append(f'cb_screen_accept(rt, {prefix}_inputs, {len(inputs)});')
        lines.append('cb_display_end(1);')
        return lines

    def require_text_format(self,node):
        typ=self.ann(node).type
        if typ.numeric and not isinstance(node,A.Reference) and typ.scale!=0:
            self.error('EXPRESSION_TEXT_FORMAT',node,'Expressão fracionária exige receptor PIC numérico para definir escala antes da conversão textual.')

    def reserve(self):
        result=self.index;self.index+=1;return result

    def case(self,pc,lines,node=None):
        origin=''
        if node:
            p=node.span.start
            origin=f'cb_origin(rt, {c_string(p.file,encoding="utf-8")}, {p.line}, {p.column});'
        self.cases.append(f'case {pc}: {{\n    {origin}\n    '+'\n    '.join(lines)+'\n    break;\n}')

    def simple(self,lines,next_pc,node):
        pc=self.reserve();self.case(pc,[*lines,*([f'pc = {next_pc};'] if next_pc!='pc' else [])],node);return pc

    def field(self,node):
        sid=self.ann(node).symbol_id
        field=self.symbol_field(sid,subscripts=node.subscripts)
        if not node.modification:
            length=self.ann(node).type.length
            if length is not None and sid in self.r.layout.items and length!=self.r.layout.items[sid].size:
                field=self.symbol_field(sid,subscripts=node.subscripts,size=length)
        if node.modification:
            start=f'cb_int({self.value(node.modification.start)})'
            length=f'cb_int({self.value(node.modification.length)})' if node.modification.length else f'((long long)({field}).n - ({start}) + 1)'
            field=f'cb_refmod({field}, {start}, {length})'
        return field

    def symbol_field(self,sid,*,subscripts=(),offsets=(),whole=False,size=None):
        symbol=self.symbols[sid]
        if symbol.namespace=='special':
            member='return_code' if symbol.name=='RETURN-CODE' else 'sort_return'
            return f'cb_field_at({member}, 4, 0, 4, &{self.desc(sid)})'
        layout=self.r.layout.items[sid]
        area=self.areas[layout.area]
        terms=[str(layout.offset)]
        for dim,sub in zip(layout.dimensions,subscripts):
            upper=str(dim.maximum)
            if dim.depending_id:
                counter=f'cb_int(cb_field_value({self.symbol_field(dim.depending_id)}))'
                upper=f'cb_bound({counter}, {dim.minimum}, {dim.maximum})'
            terms.append(f'cb_index({self.value(sub)}, {upper}) * {dim.stride}')
        terms.extend(offsets)
        if size is None:size=layout.total_size if whole and not subscripts else layout.size
        return f'cb_field_at({area}, {area}_size, {" + ".join(terms)}, {size}, &{self.desc(sid)})'

    def value(self,node):
        if isinstance(node,A.Reference):
            symbol=self.symbols[self.ann(node).symbol_id]
            if symbol.namespace=='condition':
                self.error('CONDITION_AS_VALUE',node)
            return f'cb_field_value({self.field(node)})'
        if isinstance(node,A.Literal):
            if node.category=='number':return f'cb_number({c_string(node.value)})'
            if node.category=='string':return f'cb_text({c_string(node.value)}, {len(node.value.encode("latin-1"))}, {int(node.all)})'
            if node.category=='figurative':
                mapping={'ZERO':48,'ZEROS':48,'ZEROES':48,'SPACE':32,'SPACES':32,'LOW-VALUE':0,'LOW-VALUES':0,'HIGH-VALUE':255,'HIGH-VALUES':255,'QUOTE':34,'QUOTES':34}
                if node.value in mapping:return f'cb_fill({mapping[node.value]})'
                if node.value in {'TRUE','FALSE'}:return self.int_value(int(node.value=='TRUE'))
            self.error('LITERAL',node)
        if isinstance(node,A.Group):return self.value(node.expression)
        if isinstance(node,A.LengthOf):
            info=self.ann(node).details
            if info.get('dynamic_dimensions'):self.error('DYNAMIC_LENGTH',node)
            length=info.get('constant_length')
            if length is None:
                return self.length_value(node.operand)
            return self.int_value(length)
        if isinstance(node,A.FunctionCall):
            if node.name=='LENGTH' and node.arguments and self.ann(node.arguments[0]).type.numeric and not isinstance(node.arguments[0],A.Reference):
                self.error('LENGTH_NONSTORAGE_NUMERIC',node)
            args=', '.join(self.value(arg) for arg in node.arguments)
            array=f'(cb_value[]){{{args}}}' if args else 'NULL'
            return f'cb_function(rt, {c_string(node.name)}, {array}, {len(node.arguments)})'
        if isinstance(node,(A.Binary,A.Unary)):
            if isinstance(node,A.Binary) and node.operator in {'AND','OR'} or isinstance(node,A.Unary) and node.operator=='NOT':return self.bool_value(node)
            return f'cb_numeric_value({self.number(node)})'
        if isinstance(node,(A.Comparison,A.ClassCondition,A.AbbreviatedCondition)):return self.bool_value(node)
        self.error(type(node).__name__.upper(),node)

    def length_value(self,ref):
        # Dynamic reference modification has a concrete runtime slice length.
        if ref.modification:
            return f'cb_function(rt, "LENGTH", (cb_value[]){{{self.value(ref)}}}, 1)'
        self.error('LENGTH',ref)

    def bool_value(self,node):
        return f'(({self.condition(node)}) ? cb_number("1") : cb_number("0"))'

    def number(self,node):
        if isinstance(node,A.Group):return self.number(node.expression)
        if isinstance(node,A.Binary):
            operation={'+':'cb_add','-':'cb_sub','*':'cb_mul','/':'cb_div','**':'cb_power'}.get(node.operator)
            if operation:return f'{operation}({self.number(node.left)}, {self.number(node.right)})'
        if isinstance(node,A.Unary) and node.operator in {'+','-'}:
            operand=self.number(node.operand);return f'cb_negate({operand})' if node.operator=='-' else operand
        return f'cb_as_num({self.value(node)})'

    def compare(self,left,right,operator):
        return f'(cb_compare(rt, {left}, {right}) {operator} 0)'

    def condition_values(self,symbol):
        declaration=self.nodes[symbol.node_id]
        value=next(c for c in declaration.clauses if isinstance(c,A.ValueClause))
        return value.values

    def condition(self,node,subject=None):
        if isinstance(node,A.Group):return self.condition(node.expression,subject)
        if isinstance(node,A.Literal) and node.value in {'TRUE','FALSE'}:return '1' if node.value=='TRUE' else '0'
        if isinstance(node,A.Reference):
            symbol=self.symbols[self.ann(node).symbol_id]
            if symbol.namespace=='condition':
                parent=f'cb_field_value({self.symbol_field(symbol.parent)})'
                conditions=[]
                for interval in self.condition_values(symbol):
                    lower=self.compare(parent,self.value(interval.lower),'>=' if interval.upper else '==')
                    conditions.append(f'({lower} && {self.compare(parent,self.value(interval.upper),"<=")})' if interval.upper else lower)
                return '('+' || '.join(conditions)+')'
        if isinstance(node,A.Unary) and node.operator=='NOT':return f'!({self.condition(node.operand,subject)})'
        if isinstance(node,A.Binary) and node.operator in {'AND','OR'}:
            return f'({self.condition(node.left,subject)} {"&&" if node.operator=="AND" else "||"} {self.condition(node.right,subject)})'
        if isinstance(node,A.Comparison):return self.compare(self.value(node.left),self.value(node.right),{'=':'==','<>':'!='}.get(node.operator,node.operator))
        if isinstance(node,A.AbbreviatedCondition):
            inherited=self.ann(node).details.get('subject')
            left=subject if subject else self.value(self.nodes[inherited])
            return self.compare(left,self.value(node.right),{'=':'==','<>':'!='}.get(node.operator,node.operator))
        if isinstance(node,A.ClassCondition):
            inherited=self.ann(node).details.get('subject')
            operand=self.value(node.operand) if node.operand else subject or self.value(self.nodes[inherited])
            result=f'cb_class(rt, {operand}, {c_string(node.category)})'
            return f'!({result})' if node.negated else result
        # EVALUATE TRUE can compare literal/non-condition selections to subjects.
        return f'(cb_int({self.value(node)}) != 0)'

    def initialization(self,*,local=False):
        lines=[]
        for sid,layout in self.r.layout.items.items():
            symbol=self.symbols[sid]
            if not layout.local or symbol.type.category=='group' or (layout.area=='LOCAL-STORAGE')!=local:continue
            alias=layout.redefines
            parent=symbol.parent
            while parent:
                p=self.r.layout.items.get(parent)
                alias=alias or (p.redefines if p else None)
                parent=self.symbols[parent].parent
            if alias:continue
            if symbol.type.category=='pointer':
                lines.extend(self.for_field(sid,lambda f:f'cb_pointer_store({f}, NULL);'))
                continue
            source=self.int_value(1) if symbol.namespace=='index' else self.int_value(0) if symbol.type.numeric or symbol.type.edited else 'cb_fill(32)'
            lines.extend(self.for_field(sid,lambda f:f'cb_move(rt, {source}, {f});'))
        # Default initialization precedes all explicit VALUE clauses, in source order.
        for node in A.walk(self.root.data) if self.root.data else ():
            if not isinstance(node,A.DataItem) or node.level==88:continue
            sid=self.ann(node).symbol_id
            layout=self.r.layout.items.get(sid)
            if not layout or layout.initial.get('policy')!='explicit' or (layout.area=='LOCAL-STORAGE')!=local:continue
            value=self.nodes[layout.initial['value_node']]
            source=self.value(value.values[0].lower)
            lines.extend(self.for_field(sid,lambda f:f'cb_move(rt, {source}, {f});'))
        return lines

    def for_field(self,sid,operation,*,prefix_subscripts=()):
        layout=self.r.layout.items[sid]
        loops=[];offsets=[]
        for i,dim in enumerate(layout.dimensions[len(prefix_subscripts):]):
            name=f'j_{sid}_{i}'
            loops.append(f'for (size_t {name}=0; {name}<{dim.maximum}; ++{name}) {{')
            offsets.append(f'{name} * {dim.stride}')
        field=self.symbol_field(sid,subscripts=prefix_subscripts,offsets=offsets)
        return [*loops,operation(field),*('}' for _ in loops)]

    def body(self,body,next_pc):
        entry=next_pc
        for node in reversed(body):
            if isinstance(node,(A.ProcedureSection,A.Paragraph)):
                sid=self.ann(node).symbol_id
                stack=self.sections if isinstance(node,A.ProcedureSection) else self.paragraphs
                stack.append(sid)
                child=node.body if isinstance(node,A.ProcedureSection) else node.sentences
                start=self.body(child,entry)
                stack.pop()
                wrapper=self.reserve();self.case(wrapper,[f'pc = {start};'],node)
                self.labels[sid]=(wrapper,entry)
                entry=wrapper
            elif isinstance(node,A.Sentence):
                self.sentence_next=entry
                entry=self.body(node.statements,entry)
            else:entry=self.statement(node,entry)
        return entry

    def handlers(self,handlers,event,positive,negative,next_pc):
        yes=next_pc;no=next_pc
        for handler in handlers:
            if handler.event==event:
                entry=self.body(handler.body,next_pc)
                if handler.negated:no=entry
                else:yes=entry
        return [f'pc = ({positive}) ? {yes} : ({negative}) ? {no} : {next_pc};']

    def call_targets(self,node,next_pc):
        target={handler.negated:self.body(handler.body,next_pc) for handler in node.handlers}
        return target.get(False),target.get(True,next_pc)

    def program_return(self,expression):
        if not expression:return ''
        return f'cb_move(rt, {self.value(expression)}, cb_field_at(return_code, 4, 0, 4, &d_s1));'

    def call_return(self,node,status):
        lines=[]
        if node.returning and self.ann(node.returning).type.category=='pointer':
            lines.append(f'if (!rt->stop) cb_pointer_store({self.field(node.returning)}, call_result.pointer);')
            return lines
        lines.append(f'char return_text[32]; snprintf(return_text, sizeof return_text, "%d", {status});')
        if node.returning:
            lines.append(f'if (!rt->stop) cb_move(rt, cb_number(return_text), {self.field(node.returning)});')
        if not node.returning or not self.compatibility:
            lines.append('cb_store(cb_field_at(return_code, 4, 0, 4, &d_s1), cb_decimal(return_text), 0, 0);')
        else:
            lines.append('if (rt->stop) cb_store(cb_field_at(return_code, 4, 0, 4, &d_s1), cb_decimal(return_text), 0, 0);')
        return lines

    def dynamic_call(self,node,info,next_pc):
        lines=[f'cb_slice call_name = cb_bytes(rt, {self.value(node.program)});']
        args=[]
        for i,parameter in enumerate(node.parameters):
            typ=info['arguments'][i]['type']
            is_reference=isinstance(parameter.value,A.Reference)
            is_number=typ['category'] in {'numeric','index','numeric-edited'}
            field='{0}'
            number='NULL'
            if is_reference:
                lines.append(f'cb_field actual_{i} = {self.field(parameter.value)};')
                field=f'actual_{i}'
            elif not is_number:
                lines.append(f'cb_slice bytes_{i} = cb_bytes(rt, {self.value(parameter.value)});')
                lines.append(f'cb_field actual_{i} = {{cb_alloc(rt, bytes_{i}.n), bytes_{i}.n, &cb_text_desc}};')
                lines.append(f'memcpy(actual_{i}.p, bytes_{i}.p, bytes_{i}.n);')
                field=f'actual_{i}'
            if is_number:
                expr=f'cb_field_value(actual_{i})' if is_reference else self.value(parameter.value)
                lines.append(f'cb_value number_{i} = {expr};')
                number=f'&number_{i}'
            if is_reference and parameter.mode in {'CONTENT','VALUE'}:
                lines.append(f'unsigned char *copy_{i} = cb_alloc(rt, {field}.n);')
                lines.append(f'memcpy(copy_{i}, {field}.p, {field}.n); {field}.p = copy_{i};')
            shape=shape_text(self.r.storage_shapes.get(self.nid(parameter.value)))
            args.append(f'{{{field}, {number}, {shape}, CB_{parameter.mode}, {int(is_number and isinstance(parameter.value,A.Literal))}}}')
        arguments='(cb_call_arg[]){'+', '.join(args)+'}' if args else 'NULL'
        result_kind=-1 if not node.returning else int(self.ann(node.returning).type.category=='pointer')
        table='cb_native_entries' if self.native_count else 'NULL'
        libraries='cb_native_libraries' if self.library_count else 'NULL'
        dirs=c_string(':'.join(self.module_dirs),encoding='utf-8') if self.module_dirs else 'NULL'
        lines.append(f'cb_call_result call_result = cb_call(rt, call_name, {arguments}, {len(args)}, {result_kind}, cb_programs, sizeof cb_programs/sizeof *cb_programs, {table}, {self.native_count}, {dirs}, {libraries}, {self.library_count});')
        failure,success=self.call_targets(node,next_pc)
        loc=node.span.start
        lines.append(f'cb_origin(rt, {c_string(loc.file,encoding="utf-8")}, {loc.line}, {loc.column});')
        failed=f'pc = {failure};' if failure is not None else 'cb_call_fail(rt, call_name, call_result.error);'
        lines += ['if (call_result.error) {',failed,'} else {']
        if node.returning:
            lines += self.call_return(node,'call_result.status')
        else:
            lines += ['if (call_result.kind == CB_RESULT_INT) {',*self.call_return(node,'call_result.status'),'}']
        lines += [f'pc = {success};','}']
        return self.simple(lines,'pc',node)

    def statement(self,node,next_pc):
        lines=[]
        if isinstance(node,A.Move):
            if any(not (self.ann(target).type.numeric or self.ann(target).type.edited) for target in node.targets):
                self.require_text_format(node.source)
            pairs=self.ann(node).details.get('corresponding')
            if node.corresponding:
                for pair in pairs:lines.append(f'cb_move(rt, cb_field_value({self.symbol_field(pair["source"])}), {self.symbol_field(pair["target"])});')
            else:
                lines.append(f'cb_value source = {self.value(node.source)};')
                # Snapshot the source before writing any overlapping receiver.
                lines.append('if (source.kind == 0) { unsigned char *copy = cb_alloc(rt, source.f.n); memcpy(copy, source.f.p, source.f.n); source.f.p = copy; }')
                lines.extend(f'cb_move(rt, source, {self.field(target)});' for target in node.targets)
        elif isinstance(node,A.Initialize):
            receivers=self.ann(node).details['initialize_receivers']
            for sid in receivers:
                typ=self.symbols[sid].type
                source=self.int_value(0) if typ.numeric else 'cb_fill(32)'
                for replacement in node.replacements:
                    if replacement.category.lower()==typ.category or replacement.category=='ALPHANUMERIC' and typ.category=='alphabetic':source=self.value(replacement.value)
                target=next((ref for ref in node.targets if self.ann(ref).symbol_id==sid or self.ann(ref).symbol_id in [s.id for s in self.r.table.ancestors(self.symbols[sid])]),None)
                lines.extend(self.for_field(sid,lambda f:f'cb_move(rt, {source}, {f});',prefix_subscripts=target.subscripts if target else ()))
        elif isinstance(node,A.Display):
            if node.upon not in {None,'CONSOLE','SYSOUT','CRT'}:self.error('DISPLAY_DEVICE',node)
            positions=[p for p in node.operands if isinstance(p,A.ScreenPosition)]
            screen=any(isinstance(o,A.Reference) and self.symbols[self.ann(o).symbol_id].section=='SCREEN' for o in node.operands if not isinstance(o,A.ScreenPosition))
            if self.compatibility and not positions and not screen:lines.append('cb_terminal_stream_begin(rt);')
            if positions and not self.compatibility:self.error('SCREEN_POSITION',positions[0])
            for i,operand in enumerate(node.operands):
                if isinstance(operand,A.ScreenPosition):continue
                following=[]
                for item in node.operands[i+1:]:
                    if not isinstance(item,A.ScreenPosition):break
                    following.append(item)
                if following:
                    axes={p.axis:self.value(p.value) for p in following}
                    lines.append(f'cb_terminal_at(rt, cb_int({axes.get("LINE",self.int_value(0))}), cb_int({axes.get("COLUMN",self.int_value(0))}));')
                if isinstance(operand,A.Reference) and self.symbols[self.ann(operand).symbol_id].section=='SCREEN':
                    lines.extend(self.screen(operand));continue
                if isinstance(operand,A.Literal) and operand.category=='number':
                    value=f'cb_text({c_string(operand.lexeme)}, {len(operand.lexeme)}, 0)'
                else:
                    self.require_text_format(operand)
                    value=self.value(operand)
                lines.append(f'cb_display(rt, {value});')
            lines.append(f'cb_display_end({int(node.no_advancing or bool(positions) or screen)});')
        elif isinstance(node,A.Accept):
            if node.positions:
                if not self.compatibility:self.error('SCREEN_POSITION',node)
                typ=self.ann(node.target).type
                if typ.edited or typ.numeric and (typ.scale or typ.signed or typ.usage!='DISPLAY'):
                    self.error('SCREEN_PICTURE',node,'ACCEPT posicionado exige texto ou inteiro DISPLAY sem sinal/escala.')
                axes={p.axis:self.value(p.value) for p in node.positions}
                lines.append(f'cb_terminal_at(rt, cb_int({axes.get("LINE",self.int_value(0))}), cb_int({axes.get("COLUMN",self.int_value(0))}));')
            if node.source not in {None,'CONSOLE','DATE','DAY','DAY-OF-WEEK','TIME'}:self.error('ACCEPT_SOURCE',node)
            if self.symbols[self.ann(node.target).symbol_id].section=='SCREEN':lines.extend(self.screen(node.target,accept=True))
            else:lines.append(f'cb_accept(rt, {self.field(node.target)}, {c_string(node.source) if node.source else "NULL"}, {c_string(node.date_format) if node.date_format else "NULL"});')
        elif isinstance(node,A.Arithmetic):return self.arithmetic(node,next_pc)
        elif isinstance(node,A.If):
            yes=self.body(node.then_body,next_pc);no=self.body(node.else_body,next_pc)
            return self.simple([f'pc = ({self.condition(node.condition)}) ? {yes} : {no};'], 'pc',node)
        elif isinstance(node,A.Evaluate):
            alternatives=[]
            for case in node.cases:
                target=self.body(case.body,next_pc)
                if case.other:alternatives.append(('1',target));continue
                options=[]
                for option in case.alternatives:
                    tests=[]
                    for subject,selection in zip(node.subjects,option):
                        if selection.kind=='any':continue
                        left=self.bool_value(subject) if self.ann(subject).type.category=='boolean' else self.value(subject)
                        if isinstance(selection.value,(A.AbbreviatedCondition,A.ClassCondition)):
                            test=self.condition(selection.value,left)
                        elif self.ann(subject).type.category=='boolean':
                            if isinstance(selection.value,A.Literal) and selection.value.value in {'TRUE','FALSE'}:
                                test=f'(({self.condition(subject)}) == ({self.condition(selection.value)}))'
                            else:test=f'(({self.condition(subject)}) == ({self.condition(selection.value)}))'
                        else:
                            test=self.compare(left,self.value(selection.value),'>=' if selection.upper else '==')
                            if selection.upper:test=f'({test} && {self.compare(left,self.value(selection.upper),"<=")})'
                        tests.append(test)
                    options.append(' && '.join(tests) or '1')
                alternatives.append((' || '.join(f'({x})' for x in options),target))
            code=f'pc = {next_pc};'
            branches=[f'{"if" if i==0 else "else if"} ({test}) pc = {target};' for i,(test,target) in enumerate(alternatives)]
            return self.simple([code,*branches],'pc',node)
        elif isinstance(node,A.Perform):return self.perform(node,next_pc)
        elif isinstance(node,A.GoTo):
            targets=[self.ann(ref).symbol_id for ref in node.targets]
            if self.inline_ranges:
                start,end=self.inline_ranges[-1]
                if any(not start<=self.nodes[self.symbols[sid].node_id].token_start<end for sid in targets):
                    self.error('GO_ESCAPE_INLINE',node,'GO TO que sai de PERFORM inline exige suporte adicional de desenrolamento.')
            if node.depending:
                lines=[f'switch (cb_int({self.value(node.depending)})) {{']
                lines.extend(f'case {i+1}: pc = ENTRY_{sid}; break;' for i,sid in enumerate(targets))
                lines.extend([f'default: pc = {next_pc}; break;','}'])
            else:lines=[f'pc = ENTRY_{targets[0]};']
            return self.simple(lines,'pc',node)
        elif isinstance(node,A.Exit):
            if node.scope=='PERFORM':
                if not self.inline:self.error('EXIT_PERFORM_CONTEXT',node)
                return self.simple([],self.inline[-1],node)
            if node.scope in {'SECTION','PARAGRAPH'}:
                context=self.sections if node.scope=='SECTION' else self.paragraphs
                return self.simple([],f'END_{context[-1]}',node)
            if node.scope=='PROGRAM':
                result=self.program_return(node.returning)
                return self.simple([f'if ({int(not self.is_main)} || rt->call_depth > 1) {{ {result} depth = 0; pc = -1; }} else pc = {next_pc};'],'pc',node)
        elif isinstance(node,A.Continue):pass
        elif isinstance(node,A.Goback):return self.simple([self.program_return(node.returning),'depth = 0;'], -1,node)
        elif isinstance(node,A.StopRun):return self.simple(['rt->stop = 1;'],-1,node)
        elif isinstance(node,A.NextSentence):return self.simple([],self.sentence_next,node)
        elif isinstance(node,A.Call):
            info=self.r.calls[self.nid(node)]
            if info["status"]!="resolved":return self.dynamic_call(node,info,next_pc)
            fields=[]
            for i,parameter in enumerate(node.parameters):
                formal=info['parameter_bindings'][i]['formal_type']
                numeric_temporary=parameter.mode=='VALUE' and formal['category'] in {'numeric','index'} or isinstance(parameter.value,A.Literal) and parameter.value.category=='number'
                if numeric_temporary:
                    usage=1 if formal['representation']=='binary-le' else 2 if formal['representation']=='packed-decimal' else 0
                    lines.append(f'const cb_desc parameter_desc_{i} = {{1, {formal["precision"]}, {formal["scale"]}, {int(formal["signed"])}, {usage}, {ord(formal["decimal_point"])}, {c_string(formal["expanded_picture"] or "")}}};')
                    lines.append(f'cb_field numeric_parameter_{i} = {{cb_alloc(rt, {formal["length"]}), {formal["length"]}, &parameter_desc_{i}}};')
                    lines.append(f'cb_move(rt, {self.value(parameter.value)}, numeric_parameter_{i});')
                    f=f'numeric_parameter_{i}'
                elif isinstance(parameter.value,A.Reference):
                    f=self.field(parameter.value)
                else:
                    actual=info['arguments'][i]
                    value=self.value(parameter.value)
                    lines.append(f'cb_slice literal_{i} = cb_bytes(rt, {value});')
                    lines.append(f'cb_field temporary_{i} = {{cb_alloc(rt, literal_{i}.n), literal_{i}.n, &cb_text_desc}};')
                    lines.append(f'memcpy(temporary_{i}.p, literal_{i}.p, literal_{i}.n);')
                    f=f'temporary_{i}'
                if parameter.mode in {'CONTENT','VALUE'} and not numeric_temporary:
                    lines.append(f'cb_field copy_{i} = {f};')
                    lines.append(f'unsigned char *data_{i} = cb_alloc(rt, copy_{i}.n); memcpy(data_{i}, copy_{i}.p, copy_{i}.n); copy_{i}.p = data_{i};')
                    f=f'copy_{i}'
                fields.append(f)
            args=f'(cb_field[]){{{", ".join(fields)}}}' if fields else 'NULL'
            lines.append(f'int return_status = {function_name(info["callee_program"])}(rt, {args}, {len(fields)});')
            lines.extend(self.call_return(node,'return_status'))
            _,next_pc=self.call_targets(node,next_pc) if node.handlers else (None,next_pc)
        elif isinstance(node,A.Open):
            modes={'INPUT':1,'OUTPUT':2,'EXTEND':3,'I-O':4}
            for group in node.groups:
                for ref in group.files:
                    sid=self.ann(ref).symbol_id;info=self.r.files[sid]
                    assignment=self.nodes[info['assignment_node']]
                    path=self.value(assignment) if self.ann(assignment).role!='external-assignment-name' else f'cb_text({c_string(assignment.name)}, {len(assignment.name)}, 0)'
                    record=self.symbol_field(info['records'][0])
                    status=self.symbol_field(info['status_symbol']) if info['status_symbol'] else '(cb_field){0}'
                    lines.append(f'(void)cb_open(rt, &f_{sid}, {path}, {modes[group.mode]}, {int(info["organization"]=="LINE SEQUENTIAL")}, {record}, {status});')
        elif isinstance(node,A.Read):
            sid=self.ann(node.file).symbol_id
            lines.append(f'int io = cb_read(&f_{sid});')
            if node.into:lines.append(f'if (io == 0) cb_move(rt, cb_field_value(f_{sid}.record), {self.field(node.into)});')
            if not node.handlers and not self.r.files[sid]['status_symbol']:lines.append('if (io == 1) cb_fail("UNHANDLED_EOF", "READ reached EOF without AT END or FILE STATUS.");')
            lines.extend(self.handlers(node.handlers,'END','io == 1','io == 0',next_pc))
            return self.simple(lines,'pc',node)
        elif isinstance(node,A.Write):
            sid=self.ann(node).details['file_id']
            lines.append(f'f_{sid}.record = {self.field(node.record)};')
            if node.source:lines.append(f'cb_move(rt, {self.value(node.source)}, f_{sid}.record);')
            if node.advancing:self.error('WRITE_ADVANCING',node)
            lines.append(f'cb_write(&f_{sid});')
        elif isinstance(node,A.Close):
            lines.extend(f'cb_close(&f_{self.ann(ref).symbol_id});' for ref in node.files)
        elif isinstance(node,A.Inspect):
            self.require_text_format(node.subject)
            lines.append(f'cb_value inspected = {self.value(node.subject)};')
            for tally in node.tallies:
                count=' + '.join(f'cb_inspect_count(rt, inspected, {c_string(p.mode)}, {self.value(p.value) if p.value else "cb_fill(32)"})' for p in tally.patterns)
                lines.append(f'long long count_{self.nid(tally)} = {count};')
                lines.append(f'char text_{self.nid(tally)}[32]; snprintf(text_{self.nid(tally)}, sizeof text_{self.nid(tally)}, "%lld", count_{self.nid(tally)});')
                target=self.field(tally.counter)
                lines.append(f'cb_store({target}, cb_add(cb_load({target}), cb_decimal(text_{self.nid(tally)})), 0, 0);')
            if len(node.replacements)>1:self.error('MULTIPLE_INSPECT_REPLACEMENTS',node)
            for pattern in node.replacements:
                lines.append(f'cb_inspect_replace(rt, inspected.f, {c_string(pattern.mode)}, {self.value(pattern.value) if pattern.value else "cb_fill(32)"}, {self.value(pattern.replacement)});')
            if node.converting:lines.append(f'cb_inspect_convert(rt, inspected.f, {self.value(node.converting[0])}, {self.value(node.converting[1])});')
        elif isinstance(node,A.Set):
            for ref in node.targets:
                symbol=self.symbols[self.ann(ref).symbol_id]
                if symbol.namespace=='condition':
                    if node.value.value!='TRUE':self.error('SET_FALSE',node)
                    value=self.value(self.condition_values(symbol)[0].lower)
                    lines.append(f'cb_move(rt, {value}, {self.symbol_field(symbol.parent)});')
                elif node.mode=='TO':lines.append(f'cb_store({self.field(ref)}, {self.number(node.value)}, 0, 0);')
                else:lines.append(f'cb_store({self.field(ref)}, {"cb_add" if node.mode=="UP" else "cb_sub"}(cb_load({self.field(ref)}), {self.number(node.value)}), 0, 0);')
        elif isinstance(node,A.String):return self.string(node,next_pc)
        elif isinstance(node,A.Unstring):return self.unstring(node,next_pc)
        elif isinstance(node,A.Search):return self.search(node,next_pc)
        else:self.error(type(node).__name__.upper(),node)
        return self.simple(lines,next_pc,node)

    def arithmetic(self,node,next_pc):
        lines=['int size_error = 0;',f'cb_math_begin({int(bool(node.handlers))});']
        if node.corresponding:
            for pair in self.ann(node).details['corresponding']:
                source=self.symbol_field(pair['source']);target=self.symbol_field(pair['target'])
                op='cb_add' if node.operation=='ADD' else 'cb_sub'
                lines.append(f'size_error |= cb_store({target}, {op}(cb_load({target}), cb_load({source})), 0, 1);')
        else:
            for i,source in enumerate(node.sources):lines.append(f'cb_num src_{i} = {self.number(source)};')
            for i,target in enumerate(node.targets):
                if node.operation!='COMPUTE':lines.append(f'cb_num operand_{i} = {self.number(target.target)};')
            source='src_0'
            if node.operation in {'ADD','SUBTRACT'}:
                for i in range(1,len(node.sources)):source=f'cb_add({source}, src_{i})'
            receivers=node.giving or node.targets
            for i,receiver in enumerate(receivers):
                if node.operation=='COMPUTE':expression=source
                elif node.operation=='ADD':expression=f'cb_add({source}, operand_0)' if node.giving and node.targets else source if node.giving else f'cb_add({source}, operand_{i})'
                elif node.operation=='SUBTRACT':expression=f'cb_sub(operand_{0 if node.giving else i}, {source})'
                elif node.operation=='MULTIPLY':expression=f'cb_mul({source}, {"src_1" if len(node.sources)>1 else "operand_"+str(0 if node.giving else i)})'
                else:
                    expression=f'cb_div({source}, src_1)' if node.form=='BY' else f'cb_div({"src_1" if len(node.sources)>1 else "operand_"+str(0 if node.giving else i)}, {source})'
                lines.append(f'cb_num result_{i} = {expression};')
                lines.append(f'size_error |= cb_store({self.field(receiver.target)}, result_{i}, {int(receiver.rounded)}, 1);')
            if node.remainder:
                if any(r.rounded for r in node.giving):self.error('ROUNDED_REMAINDER',node)
                dividend='src_0' if node.form=='BY' else 'src_1' if len(node.sources)>1 else 'operand_0'
                divisor='src_1' if node.form=='BY' else 'src_0'
                quotient=f'cb_load({self.field(node.giving[0].target)})'
                lines.append(f'if (!size_error) size_error |= cb_store({self.field(node.remainder)}, cb_sub({dividend}, cb_mul({divisor}, {quotient})), 0, 1);')
        lines.extend(['size_error |= cb_math_failed();','cb_math_end();'])
        if node.handlers:
            if not any(not handler.negated for handler in node.handlers):
                lines.append('if (size_error) cb_fail("SIZE_ERROR", "Arithmetic error without ON SIZE ERROR handler.");')
            lines.extend(self.handlers(node.handlers,'SIZE ERROR','size_error','!size_error',next_pc))
            return self.simple(lines,'pc',node)
        lines.append('if (size_error) cb_fail("SIZE_ERROR", "Arithmetic result exceeds receiving precision.");')
        return self.simple(lines,next_pc,node)

    def perform(self,node,next_pc):
        controlled=bool(node.until or node.times or node.varying)
        if not controlled:
            if node.target:
                sid=self.ann(node.target).symbol_id;end=self.ann(node.through).symbol_id if node.through else sid
                return self.simple([f'cb_push(frames, &depth, {next_pc}, END_{end});',f'pc = ENTRY_{sid};'],'pc',node)
            self.inline.append(next_pc);self.inline_ranges.append((node.token_start,node.token_end))
            start=self.body(node.body,next_pc)
            self.inline.pop();self.inline_ranges.pop();return start
        finish=self.reserve()
        self.case(finish,['if (loop_depth <= 0) cb_fail("LOOP_STACK", "Missing active loop.");','--loop_depth;',f'pc = {next_pc};'],node)
        self.inline.append(finish)
        if not node.target:self.inline_ranges.append((node.token_start,node.token_end))
        def inner(body_next):
            if node.target:
                sid=self.ann(node.target).symbol_id;end=self.ann(node.through).symbol_id if node.through else sid
                return self.simple([f'cb_push(frames, &depth, {body_next}, END_{end});',f'pc = ENTRY_{sid};'],'pc',node)
            return self.body(node.body,body_next)
        if node.varying:
            def varying_at(index,after):
                vary=node.varying[index];check=self.reserve();step=self.reserve()
                after_body=check if node.test=='AFTER' else step
                begin=inner(after_body) if index+1==len(node.varying) else varying_at(index+1,after_body)
                false_target=step if node.test=='AFTER' else begin
                self.case(check,[f'pc = ({self.condition(vary.until)}) ? {after} : {false_target};'],node)
                target=self.field(vary.target)
                self.case(step,[f'if (cb_store({target}, cb_add(cb_load({target}), {self.number(vary.step)}), 0, 1)) cb_fail("SIZE_ERROR", "PERFORM VARYING overflow.");',f'pc = {begin if node.test=="AFTER" else check};'],node)
                entry=begin if node.test=='AFTER' else check
                return self.simple([f'cb_store({target}, {self.number(vary.initial)}, 0, 0);'],entry,node)
            start=varying_at(0,finish)
        else:
            check=self.reserve();step=self.reserve();begin=inner(step)
            if node.times:
                cond='loops[loop_depth-1].remaining <= 0'
                self.case(step,['--loops[loop_depth-1].remaining;',f'pc = {check};'],node)
            else:
                cond=self.condition(node.until)
                self.case(step,[f'pc = {check};'],node)
            self.case(check,[f'pc = ({cond}) ? {finish} : {begin};'],node)
            start=begin if node.test=='AFTER' and not node.times else check
        self.inline.pop()
        if not node.target:self.inline_ranges.pop()
        count=f'cb_int({self.value(node.times)})' if node.times else '0'
        return self.simple([f'long long count = {count};','if (count < 0) cb_fail("NEGATIVE_TIMES", "Negative PERFORM count.");',f'cb_loop_push(loops, &loop_depth, {self.nid(node)[1:]}, {finish}, depth, count);'],start,node)

    def string(self,node,next_pc):
        pointer=f'cb_int({self.value(node.pointer)})' if node.pointer else '1'
        lines=[f'long long pointer = {pointer};','int overflow = 0;',f'cb_field target = {self.field(node.target)};']
        for part in node.parts:
            delimiter=self.value(part.delimiter.value) if part.delimiter.value else 'cb_fill(32)'
            for value in part.values:
                self.require_text_format(value)
                lines.append(f'if (!overflow) overflow = cb_string_part(rt, target, &pointer, {self.value(value)}, {delimiter}, {int(part.delimiter.size)});')
        if node.pointer:lines.append(f'char p[32]; snprintf(p, sizeof p, "%lld", pointer); cb_store({self.field(node.pointer)}, cb_decimal(p), 0, 0);')
        if node.handlers:return self.simple([*lines,*self.handlers(node.handlers,'OVERFLOW','overflow','!overflow',next_pc)],'pc',node)
        lines.append('if (overflow) cb_fail("STRING_OVERFLOW", "STRING receiver overflow.");')
        return self.simple(lines,next_pc,node)

    def unstring(self,node,next_pc):
        pointer=f'cb_int({self.value(node.pointer)})' if node.pointer else '1'
        values=', '.join(self.value(d.value) for d in node.delimiters)
        alls=', '.join(str(int(d.all)) for d in node.delimiters)
        if not node.delimiters:self.error('UNSTRING_WITHOUT_DELIMITER',node)
        lines=[f'long long pointer = {pointer}, count = 0;',f'cb_value source = {self.value(node.source)};',f'cb_value delimiters[] = {{{values}}};',f'int alls[] = {{{alls}}};']
        for target in node.targets:
            delimiter=self.field(target.delimiter_in) if target.delimiter_in else '(cb_field){0}'
            count=self.field(target.count_in) if target.count_in else '(cb_field){0}'
            lines.append(f'count += cb_unstring_next(rt, source, &pointer, delimiters, alls, {len(node.delimiters)}, {self.field(target.target)}, {delimiter}, {count});')
        for ref,expression in [(node.pointer,'pointer'),(node.tallying,'count')]:
            if ref:lines.append(f'{{ char n[32]; snprintf(n, sizeof n, "%lld", {expression}); cb_store({self.field(ref)}, {"cb_add(cb_load("+self.field(ref)+"), cb_decimal(n))" if ref is node.tallying else "cb_decimal(n)"}, 0, 0); }}')
        lines.append('int overflow = pointer <= (long long)cb_bytes(rt, source).n;')
        lines.append('(void)count;')
        if node.handlers:return self.simple([*lines,*self.handlers(node.handlers,'OVERFLOW','overflow','!overflow',next_pc)],'pc',node)
        lines.append('if (overflow) cb_fail("UNSTRING_OVERFLOW", "More source fields than UNSTRING receivers.");')
        return self.simple(lines,next_pc,node)

    def search(self,node,next_pc):
        indexes=self.ann(node).details['indexes']
        if not indexes:self.error('SEARCH_INDEX',node)
        sid=self.ann(node.table).symbol_id
        layout=self.r.layout.items[sid];dim=layout.dimensions[-1]
        if len(layout.dimensions)!=1:self.error('NESTED_SEARCH',node)
        index=indexes[0];index_field=self.symbol_field(index)
        end=self.body(node.at_end,next_pc);check=self.reserve();step=self.reserve()
        branch=step
        for case in reversed(node.cases):
            body=self.body(case.body,next_pc)
            branch=self.simple([f'pc = ({self.condition(case.condition)}) ? {body} : {branch};'],'pc',case)
        self.case(check,[f'pc = (cb_int(cb_field_value({index_field})) > {dim.maximum}) ? {end} : {branch};'],node)
        lines=[f'cb_store({index_field}, cb_add(cb_load({index_field}), cb_decimal("1")), 0, 0);']
        if node.varying:lines.append(f'cb_store({self.field(node.varying)}, cb_add(cb_load({self.field(node.varying)}), cb_decimal("1")), 0, 0);')
        self.case(step,[*lines,f'pc = {check};'],node)
        if node.all:
            keys=self.ann(node).details['search_all']['keys']
            if len(keys)!=1 or len(keys[0]['symbols'])!=1:self.error('COMPOSITE_SEARCH_ALL',node)
            key=keys[0]['symbols'][0]
            left=self.symbol_field(key,offsets=[f'(j-1)*{dim.stride}'])
            right=self.symbol_field(key,offsets=[f'j*{dim.stride}'])
            sign='>' if keys[0]['role']=='ASCENDING' else '<'
            order=[f'for (size_t j=1; j<{dim.maximum}; ++j) {{',
                f'if (cb_compare(rt, cb_field_value({left}), cb_field_value({right})) {sign} 0) cb_fail("SEARCH_ORDER", "SEARCH ALL table violates declared key order.");','}']
            return self.simple([*order,f'cb_store({index_field}, cb_decimal("1"), 0, 0);'],check,node)
        return check

    def generate(self):
        # Fixed resource limits have diagnostics before GCC, never truncated storage.
        for symbol in self.symbols.values():
            if symbol.type and symbol.type.precision and symbol.type.precision>128:
                self.error('FIELD_PRECISION',self.nodes[symbol.node_id],'Backend suporta até 128 dígitos por campo; intermediários têm capacidade checada de 512.')
            if symbol.type and symbol.type.edited and set(symbol.type.expanded_picture or '') & set('0B/*$'):
                self.error('PICTURE_EDITING',self.nodes[symbol.node_id],'Backend suporta edição Z, sinais fixos e separadores; outras inserções exigem implementação adicional.')
        if any(size>64*1024*1024 for size in self.r.layout.areas.values()):
            self.error('STORAGE_CAPACITY',self.root,'Área de armazenamento excede o limite de 64 MiB do backend.')
        for node in A.walk(self.root):
            if isinstance(node,A.FileControlEntry) and node.optional:self.error('OPTIONAL_FILE',node)
        entry=self.body(self.root.procedure.body,-1)
        global_lines=[]
        for sid,symbol in self.symbols.items():
            typ=symbol.type
            if symbol.namespace not in {'data','filler','index','special'}:continue
            global_lines.append(f'static const cb_desc {self.desc(sid)} = {descriptor(asdict(typ))};')
            global_lines.append(f'(void)&{self.desc(sid)};')
        area_lines=[];reset=[]
        for area,name in self.areas.items():
            size=self.r.layout.areas[area]
            if area.startswith('LINKAGE:'):
                sid=area.split(':',1)[1]
                param=next((i for i,p in enumerate(self.r.parameters) if p['layout'] and p['layout']['area']==area),None)
                if param is None:area_lines.extend([f'unsigned char *{name} = NULL;',f'size_t {name}_size = {size};'])
                else:area_lines.extend([f'if (argc <= {param} || args[{param}].n < {size}) cb_fail("CALL_LAYOUT", "Missing or undersized LINKAGE argument.");',f'unsigned char *{name} = args[{param}].p;',f'size_t {name}_size = {size};'])
            else:
                storage='' if area=='LOCAL-STORAGE' else 'static '
                area_lines.extend([f'{storage}unsigned char {name}[{max(1,size)}];',f'const size_t {name}_size = {size};'])
                if size:reset.append(f'memset({name}, 32, {size});')
        for sid in self.r.files:area_lines.append(f'static cb_file f_{sid};')
        for area,name in self.areas.items():area_lines.extend([f'(void){name};',f'(void){name}_size;'])
        for sid in self.r.files:area_lines.append(f'(void)&f_{sid};')
        enums=[]
        for sid,(start,end) in self.labels.items():enums.append(f'ENTRY_{sid} = {start}, END_{sid} = {end}')
        init=self.initialization()
        local_init=self.initialization(local=True)
        local_reset=[f'memset({name}, 32, {self.r.layout.areas[area]});' for area,name in self.areas.items() if area=='LOCAL-STORAGE' and self.r.layout.areas[area]]
        reset=[line for line in reset if not any(line.startswith(f'memset({name},') for area,name in self.areas.items() if area=='LOCAL-STORAGE')]
        terminal_bind=[]
        if self.compatibility:
            names={n.setting:n.value for n in A.walk(self.root.environment) if isinstance(n,A.SpecialName)} if self.root.environment else {}
            empty='(cb_field){NULL,0,&cb_text_desc}'
            if 'CURSOR' in names or 'CRT STATUS' in names:
                terminal_bind=[f'cb_terminal_bind(rt, {self.field(names["CURSOR"]) if "CURSOR" in names else empty}, {self.field(names["CRT STATUS"]) if "CRT STATUS" in names else empty});']
        # One static descriptor namespace per function avoids collisions across units.
        lines=[f'int {self.name}(cb_runtime *rt, cb_field *args, size_t argc) {{',*global_lines,*area_lines,
            'if (++rt->call_depth > 16) cb_fail("CALL_STACK", "CALL nesting exceeds 16 activations.");',
            'cb_mem *activation_mark = rt->memory;',
            'unsigned char return_code[4] = {0}, sort_return[4] = {0};',
            '(void)return_code; (void)sort_return;',
            '(void)args; (void)argc;', 'static int initialized = 0;',
            'if (!initialized) {',*reset,*init,'initialized = 1;','}',
            *local_reset,*local_init,*terminal_bind,
            'enum { '+', '.join(enums)+' };' if enums else '',
            f'int pc = {entry}, depth = 0, loop_depth = 0;',
            'cb_frame frames[CB_STACK]; cb_loop loops[CB_STACK];',
            '(void)frames; (void)loops;',
            'while (pc >= 0 && !rt->stop) {','cb_mem *mark = rt->memory;',
            'switch (pc) {',*self.cases,'default: cb_fail("DISPATCH_POSITION", "Invalid execution position.");','}',
            'cb_release(rt, mark);',
            'while (depth > 0 && pc == frames[depth-1].limit) { pc = frames[--depth].ret; }','}',
            '(void)loop_depth;',
            'cb_release(rt, activation_mark);',
            '--rt->call_depth;',
            'return (int)cb_int(cb_field_value(cb_field_at(return_code, 4, 0, 4, &d_s1)));','}']
        return '\n'.join(lines)


def generate_c(result,*,module=False,shared=False,static_call=None,signatures=(),module_dirs=(),libraries=()):
    diagnostics=[]
    if not result.success:return CodegenResult(None,list(result.diagnostics))
    units=[];seen=set()
    for unit in [result,*result.source_results]:
        path=unit.frontend.preprocessed.root_file
        if path not in seen:
            units.append(unit);seen.add(path)
    if static_call is None:
        static_call=result.frontend.preprocessed.dialect!='gnucobol' and not shared
    pending=False
    for unit in units:
        for node in A.walk(unit.ast):
            if isinstance(node,A.Call):
                info=unit.calls[unit.node_ids[id(node)]]
                if info['status']=='resolved':continue
                pending=True
                if static_call:
                    diagnostics.append(Diagnostic('LINK_UNRESOLVED_CALL',f'Implementação ausente para CALL {info["original_name"] or "dinâmico"}.',node.span,'link'))
    program_names=set()
    for unit in units:
        name=unit.ast.identification.program_id.upper()
        if name in program_names:
            diagnostics.append(Diagnostic('LINK_DUPLICATE_PROGRAM',f'Mais de uma definição de PROGRAM-ID {name}.',unit.ast.identification.span,'link'))
        program_names.add(name)
    if result.parameters and not module:
        diagnostics.append(Diagnostic('MAIN_REQUIRES_USING','Programa com USING deve ser compilado com --module ou chamado por um programa principal.',result.ast.procedure.span,'backend'))
    if diagnostics:return CodegenResult(None,diagnostics)
    try:
        generators=[UnitGenerator(unit,is_main=unit is result and not module,native_count=len(signatures),
                                  module_dirs=module_dirs,library_count=len(libraries)) for unit in units]
        definitions=[generator.generate() for generator in generators]
        prototypes=[f'int {generator.name}(cb_runtime *, cb_field *, size_t);' for generator in generators]
        source=['/* Generated from validated COBOL AST. Project runtime; no COBOL interpreter. */',
            '#include "cobol_runtime.h"','#include <string.h>','#include <stdio.h>',*prototypes]
        if pending or shared:
            entries=[]
            for unit,generator in zip(units,generators):
                formals=[]
                for param in unit.parameters:
                    typ=param['type']
                    shape=shape_text(unit.storage_shapes.get(param['node_id']))
                    formals.append(f'{{{typ["length"] or 0}, {descriptor(typ)}, {shape}, CB_{param["mode"]}}}')
                formal_table='NULL'
                if formals:
                    formal_table=f'{generator.name}_formals'
                    source.append(f'static const cb_formal {formal_table}[] = {{'+', '.join(formals)+'};')
                entries.append(f'{{{c_string(unit.ast.identification.program_id.upper())}, {generator.name}, {formal_table}, {len(formals)}}}')
            source.append('static const cb_program cb_programs[] = {\n'+',\n'.join(entries)+'\n};')
        if pending:
            source.extend(native.emit(signatures,c_string))
            if libraries:
                source.append('static const char *const cb_native_libraries[] = {'+
                              ', '.join(c_string(p,encoding='utf-8') for p in libraries)+'};')
        if shared:
            source.append('__attribute__((visibility("default"))) const cb_module cobol_project_module_v1 = '
                          '{CB_MODULE_ABI, sizeof(cb_runtime), sizeof cb_programs/sizeof *cb_programs, cb_programs};')
        source.extend(definitions)
        if not module:
            source.extend(['int main(void) {','cb_runtime runtime; cb_runtime_init(&runtime);'])
            if pending:
                source.append('runtime.linked_programs = cb_programs; runtime.linked_count = sizeof cb_programs/sizeof *cb_programs;')
                if module_dirs:
                    source.append(f'runtime.module_dirs = {c_string(":".join(module_dirs),encoding="utf-8")};')
            source.extend([f'int status = {generators[0].name}(&runtime, NULL, 0);',
                           'cb_runtime_destroy(&runtime);','return status;','}'])
        return CodegenResult('\n\n'.join(source)+'\n',[],[u.ast.identification.program_id for u in units],generators[0].name)
    except CodegenError as error:
        return CodegenResult(None,[Diagnostic(error.code,error.message,error.node.span,'backend')])
