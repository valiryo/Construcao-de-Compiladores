"""Análise em passagens: declarações, armazenamento, vínculos e operações.

A AST permanece sintática. IDs em pré-ordem são determinísticos para a mesma
árvore; Annotation/Binding guardam tudo que a próxima fase pode consumir.
"""

from dataclasses import dataclass, field, asdict, replace
from decimal import Decimal, InvalidOperation
from struct import calcsize

from . import ast as A
from .diagnostics import Diagnostic, RelatedLocation
from .frontend import FrontendResult, parse_file, parse_source
from .layout import Dimension, StorageLayout, LayoutResult
from .symbols import Symbol, SymbolTable
from .types import (CobolType, ERROR, BOOLEAN, INDEX, PictureError, parse_picture,
                    numeric_type, arithmetic_type)


@dataclass(slots=True)
class Annotation:
    type: CobolType | None = None
    symbol_id: str | None = None
    role: str | None = None
    writable: bool = False
    layout_id: str | None = None
    checks: list[dict] = field(default_factory=list)
    conversions: list[dict] = field(default_factory=list)
    details: dict = field(default_factory=dict)


@dataclass(slots=True)
class SemanticResult:
    frontend: FrontendResult
    table: SymbolTable = field(default_factory=SymbolTable)
    layout: LayoutResult = field(default_factory=LayoutResult)
    annotations: dict[str, Annotation] = field(default_factory=dict)
    node_ids: dict[int, str] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    files: dict[str, dict] = field(default_factory=dict)
    calls: dict[str, dict] = field(default_factory=dict)
    controls: dict[str, dict] = field(default_factory=dict)
    parameters: list[dict] = field(default_factory=list)
    storage_shapes: dict[str, list] = field(default_factory=dict)
    source_results: list["SemanticResult"] = field(default_factory=list)

    @property
    def success(self):
        return self.frontend.success and not any(d.severity in {"E", "S"} for d in self.diagnostics)

    @property
    def ast(self):
        return self.frontend.ast if self.success else None

    @property
    def pending_externals(self):
        return [c for c in self.calls.values() if c["status"] in {"external", "dynamic"} or c.get("pending_dependencies")]

    @property
    def backend_ready(self):
        return self.success and (self.frontend.preprocessed.dialect=="gnucobol" or not self.pending_externals)

    def annotation(self, node):
        return self.annotations[self.node_ids[id(node)]]

    def dump_symbols(self):
        return {"success": self.success, "backend_ready": self.backend_ready,
                "symbols": [asdict(s) for s in self.table.symbols.values()],
                "parameters": self.parameters, "files": self.files, "calls": self.calls,
                "controls": self.controls,
                "annotations": {k: asdict(v) for k, v in self.annotations.items()}}

    def dump_layout(self):
        return asdict(self.layout)


class Analyzer:
    def __init__(self, frontend, *, strict=False):
        self.r = SemanticResult(frontend)
        self.root = frontend.ast
        self.strict = strict
        self.compatibility = frontend.preprocessed.dialect=='gnucobol'
        self.nodes = {}
        self.declarations = {}
        self.file_descriptors = {}
        self.file_selects = {}
        self.procedures = []
        self.screen = set()
        if self.root:
            for i, node in enumerate(A.walk(self.root)):
                nid = f"n{i}"
                self.r.node_ids[id(node)] = nid
                self.nodes[nid] = node
                self.r.annotations[nid] = Annotation()
        self.table = self.r.table
        self.decimal_comma = bool(self.root and any(isinstance(n, A.SpecialName) and n.setting == "DECIMAL-POINT" and n.value.value == "COMMA" for n in A.walk(self.root)))
        self.by_span = {repr(n.span): n for n in self.nodes.values() if isinstance(n, A.Expr)}

    def nid(self, node):
        return self.r.node_ids[id(node)]

    def ann(self, node):
        return self.r.annotation(node)

    def diagnostic(self, code, message, node, severity="E", related=()):
        span = node if not isinstance(node, A.Node) else node.span
        if any(d.code==code and d.span==span and d.message==message for d in self.r.diagnostics):
            return
        self.r.diagnostics.append(Diagnostic(code, message, span, "semantic", severity=severity,
                                            related=tuple(RelatedLocation(s.span, "Declaração relacionada.") for s in related)))

    def unsupported(self, resource, node):
        self.diagnostic("UNSUPPORTED_"+resource, f"Recurso fora do subconjunto semântico: {resource}.", node)

    def add(self, name, namespace, node, *, parent=None, section=None, level=None, file_id=None, table_id=None):
        sid = f"s{len(self.table.symbols)}"
        original = name
        if isinstance(node, A.DataItem):
            # Nome normalizado pelo parser; recuperar grafia do token original.
            tokens = self.r.frontend.preprocessed.tokens
            if node.token_start+1 < len(tokens) and name:
                original = tokens[node.token_start+1].token.lexeme
        elif isinstance(node, (A.Paragraph, A.ProcedureSection, A.Reference)):
            original = self.r.frontend.preprocessed.tokens[node.token_start].token.lexeme
        elif isinstance(node,(A.FileControlEntry,A.FileDescriptor)):
            original = self.r.frontend.preprocessed.tokens[node.name.token_start].token.lexeme
        elif isinstance(node,A.IdentificationDivision):
            tokens = self.r.frontend.preprocessed.tokens[node.token_start:node.token_end]
            original = next((token.token.lexeme if token.token.kind=="IDENTIFIER" else token.token.value for token in tokens if token.token.kind in {"IDENTIFIER","STRING"} and token.token.value.upper()==name.upper()),name)
        symbol = Symbol(sid, (name or f"<FILLER:{sid}>").upper(), original or "FILLER", namespace,
                        self.nid(node), node.declaration_span if isinstance(node, A.DataItem) else node.span,
                        parent, section, level=level, file_id=file_id, table_id=table_id)
        if namespace in {"file", "program", "section", "paragraph"}:
            symbol.type = CobolType(namespace)
        peers = [s for s in self.table.candidates(symbol.name, [namespace]) if s.parent == parent]
        if peers and name:
            self.diagnostic("DUPLICATE_SYMBOL", f"Declaração duplicada de {name} no mesmo escopo.", symbol.span, related=peers)
        self.table.add(symbol)
        self.declarations[id(node)] = sid
        self.ann(node).symbol_id = sid
        self.ann(node).role = "declaration"
        return symbol

    def declaration_ref(self, ref, symbol):
        ann = self.ann(ref)
        ann.symbol_id, ann.type, ann.role = symbol.id, symbol.type, "declaration"

    def declare(self):
        if not isinstance(self.root, A.Program):
            if self.root:
                self.diagnostic("COPYBOOK_CONTEXT_REQUIRED", "Copybook exige inclusão COPY no contexto de um programa.", self.root)
            return
        self.add(self.root.identification.program_id, "program", self.root.identification)
        for name in ("RETURN-CODE", "SORT-RETURN"):
            symbol = self.add(name, "special", self.root.procedure)
            symbol.type = parse_picture("S9(9)", "COMP")
        if self.root.environment:
            for n in A.walk(self.root.environment):
                if isinstance(n, A.FileControlEntry):
                    symbol = self.add(n.name.name, "file", n)
                    self.declaration_ref(n.name, symbol)
                    self.file_selects[symbol.id] = n
        if self.root.data:
            for section in self.root.data.sections:
                for entry in section.entries:
                    if isinstance(entry, A.FileDescriptor):
                        candidates = self.table.candidates(entry.name.name, ["file"])
                        if not candidates:
                            symbol = self.add(entry.name.name, "file", entry)
                            if not entry.sort:
                                self.diagnostic("MISSING_SELECT", f"FD {entry.name.name} não tem SELECT.", entry.name)
                        else:
                            symbol = candidates[0]
                        if symbol.id in self.file_descriptors:
                            self.diagnostic("DUPLICATE_FD", "Descritor de arquivo duplicado.", entry)
                        self.file_descriptors[symbol.id] = entry
                        self.declaration_ref(entry.name, symbol)
                        for item in entry.records:
                            self.declare_item(item, None, section.name, symbol.id)
                    else:
                        self.declare_item(entry, None, section.name, None)
        self.declare_procedures(self.root.procedure.body)

    def declare_item(self, item, parent, section, file_id):
        namespace = "condition" if item.level == 88 else "filler" if item.name is None else "data"
        symbol = self.add(item.name, namespace, item, parent=parent, section=section, level=item.level, file_id=file_id)
        if section == "SCREEN":
            self.screen.add(symbol.id)
        for clause in item.clauses:
            if isinstance(clause, A.OccursClause):
                for ref in clause.indexes:
                    index = self.add(ref.name, "index", ref, parent=symbol.id, section=section, table_id=symbol.id)
                    index.type = INDEX
                    self.declaration_ref(ref, index)
        for child in item.children:
            self.declare_item(child, symbol.id, section, file_id)

    def declare_procedures(self, body, parent=None):
        for node in body:
            if isinstance(node, (A.Paragraph, A.ProcedureSection)):
                ns = "section" if isinstance(node, A.ProcedureSection) else "paragraph"
                symbol = self.add(node.name, ns, node, parent=parent)
                self.procedures.append(symbol)
                self.r.controls[symbol.id] = {"kind": ns, "entry_node": self.nid(node),
                                             "token_start": node.token_start, "token_end": node.token_end,
                                             "parent": parent, "fallthrough": None}
                if isinstance(node, A.ProcedureSection):
                    self.declare_procedures(node.body, symbol.id)
        for i, symbol in enumerate(self.procedures):
            following = next((s for s in self.procedures[i+1:] if self.nodes[s.node_id].token_start >= self.nodes[symbol.node_id].token_end), None)
            self.r.controls[symbol.id]["fallthrough"] = following.id if following else None

    def clause(self, item, cls):
        matches = [c for c in item.clauses if isinstance(c, cls)]
        if len(matches) > 1:
            self.diagnostic("DUPLICATE_CLAUSE", f"Cláusula {cls.__name__} repetida.", matches[1])
        return matches[0] if matches else None

    def build_layout(self):
        if not isinstance(self.root, A.Program):
            return
        if self.root.data:
            for section in self.root.data.sections:
                if section.name == "SCREEN" and not self.compatibility:
                    self.unsupported("SCREEN", section)
                if section.name == "FILE":
                    for fd in section.entries:
                        file_id = self.ann(fd.name).symbol_id
                        area = "FILE:"+file_id
                        maximum = 0
                        for record in fd.records:
                            maximum = max(maximum, self.place(record, area, 0, []))
                        self.r.layout.areas[area] = maximum
                else:
                    area = section.name
                    offset = 0
                    for item in section.entries:
                        # Cada raiz LINKAGE é uma área externa independente.
                        item_area = "LINKAGE:"+self.declarations[id(item)] if area == "LINKAGE" else area
                        end = self.place(item, item_area, 0 if area == "LINKAGE" else offset, [])
                        if area == "LINKAGE":
                            actual_area = self.r.layout.items[self.declarations[id(item)]].area
                            self.r.layout.areas[actual_area] = max(self.r.layout.areas.get(actual_area,0),end)
                        else:
                            offset = max(offset, end)
                    if area != "LINKAGE":
                        self.r.layout.areas[area] = offset
        for symbol in self.table.symbols.values():
            if symbol.namespace == "index":
                area = "INDEXES"
                offset = self.r.layout.areas.get(area, 0)
                self.r.layout.items[symbol.id] = StorageLayout(symbol.id, area, offset, 8, 8, symbol.parent, True, initial={"policy":"index-base-one", "value":1})
                self.r.layout.areas[area] = offset+8
        # Segunda passagem: resolve DEPENDING, chaves e valores após todos os tipos.
        for node in self.nodes.values():
            if isinstance(node, A.DataItem):
                self.validate_declaration(node)
        for param in self.root.procedure.parameters:
            typ = self.expr(param.value, whole=True)
            sid = self.ann(param.value).symbol_id
            symbol = self.table.symbols.get(sid)
            if symbol and (symbol.section != "LINKAGE" or symbol.parent is not None):
                self.diagnostic("FORMAL_NOT_LINKAGE", "USING deve referenciar raiz da LINKAGE SECTION.", param.value, related=[symbol])
            self.r.parameters.append({"node_id": self.nid(param), "symbol_id": sid, "mode":param.mode,
                                      "type":asdict(typ), "layout":asdict(self.r.layout.items[sid]) if sid in self.r.layout.items else None})
            if typ.category=="group":
                self.r.storage_shapes[self.nid(param)]=self.storage_signature(sid)

    def place(self, item, area, offset, dimensions):
        symbol = self.table.symbols[self.declarations[id(item)]]
        picture = self.clause(item, A.PictureClause)
        usage = self.clause(item, A.UsageClause)
        occurs = self.clause(item, A.OccursClause)
        redef = self.clause(item, A.RedefinesClause)
        value = self.clause(item, A.ValueClause)
        regular = [c for c in item.children if c.level != 88]
        if item.level == 88:
            symbol.type = BOOLEAN
            self.ann(item).type = BOOLEAN
            if picture or occurs or usage or regular or not symbol.parent:
                self.diagnostic("INVALID_CONDITION_DECLARATION", "Nível 88 exige campo associado e não admite armazenamento próprio.", item)
            return offset
        if (symbol.parent is None and item.level not in {1,77}) or (symbol.parent and item.level in {1,77}):
            self.diagnostic("INVALID_DATA_LEVEL", "Nível incompatível com a hierarquia de dados.", item)
        if item.level == 77 and (regular or occurs):
            self.diagnostic("INVALID_LEVEL_77", "Nível 77 deve ser elementar, sem OCCURS.", item)
        if picture and regular:
            self.diagnostic("GROUP_WITH_PICTURE", "Grupo não pode possuir PIC elementar.", picture)
        if picture:
            try:
                typ = parse_picture(picture.mask, usage.usage if usage else "DISPLAY", decimal_comma=self.decimal_comma,
                                    allow_floating=self.compatibility)
            except PictureError as exc:
                code = "UNSUPPORTED_USAGE" if usage and usage.usage in {"COMP-1","COMP-2","POINTER"} else "INVALID_PICTURE"
                self.diagnostic(code, str(exc), picture)
                typ = ERROR
        elif regular:
            typ = CobolType("screen" if symbol.id in self.screen and self.compatibility else "group")
            if usage:
                self.unsupported("GROUP_USAGE", usage)
        elif usage and usage.usage in {"INDEX", "POINTER"}:
            typ = INDEX if usage.usage == "INDEX" else CobolType("pointer", calcsize("P"), usage="POINTER", representation="opaque-pointer")
            if usage.usage == "POINTER" and not self.compatibility:
                self.unsupported("POINTER", usage)
        elif symbol.id in self.screen:
            literal = value.values[0].lower if value and value.values else None
            typ = CobolType("alphanumeric", len(literal.value.encode("latin-1", errors="replace"))) if isinstance(literal,A.Literal) and literal.category == "string" else CobolType("screen", 0)
        else:
            self.diagnostic("MISSING_PICTURE", "Item elementar exige PIC.", item)
            typ = ERROR
        symbol.type = typ
        redefines_id = None
        if redef:
            candidates = [s for s in self.table.candidates(redef.target.name,["data","filler"],redef.target.qualifiers)
                          if s.parent == symbol.parent and s.section == symbol.section and s.file_id == symbol.file_id and s.id in self.r.layout.items]
            if len(candidates) != 1:
                self.diagnostic("INVALID_REDEFINES", "REDEFINES exige item anterior no mesmo escopo e área.", redef.target)
            else:
                target = candidates[0]
                target_layout = self.r.layout.items[target.id]
                if target.level != symbol.level:
                    self.diagnostic("INVALID_REDEFINES", "REDEFINES exige o mesmo nível do item redefinido.", redef.target)
                if target_layout.area != area and not (area.startswith("LINKAGE:") and target_layout.area.startswith("LINKAGE:")):
                    self.diagnostic("INVALID_REDEFINES", "REDEFINES atravessa áreas independentes.", redef.target)
                else:
                    area = target_layout.area
                    offset = target_layout.offset
                    redefines_id = target.id
                self.bind(redef.target, target, "redefines")
            if value:
                self.diagnostic("VALUE_ON_REDEFINES", "Visão REDEFINES não admite VALUE próprio.", value)
        own_dim = None
        dims = list(dimensions)
        if occurs:
            lo = self.integer_constant(occurs.minimum)
            hi = self.integer_constant(occurs.maximum) if occurs.maximum else lo
            if lo is None or hi is None or lo < 0 or hi < max(1,lo) or hi > 1000000 or (lo == 0 and not occurs.depending):
                self.diagnostic("INVALID_OCCURS", "OCCURS requer faixa válida, máximo entre 1 e 1000000.", occurs)
                lo,hi = 1,1
            if occurs.maximum and not occurs.depending:
                self.diagnostic("MISSING_DEPENDING", "OCCURS variável exige DEPENDING ON.", occurs)
            own_dim = Dimension(symbol.id,lo,hi,0)
            dims.append(own_dim)
        cursor = offset
        for child in regular:
            cursor = max(cursor,self.place(child,area,cursor,dims))
        size = cursor-offset if regular else typ.length or 0
        if regular:
            symbol.type = replace(typ,length=size)
        if own_dim:
            own_dim.stride = size
        total = size*(own_dim.maximum if own_dim else 1)
        initial = {"policy":"external" if area.startswith("LINKAGE:") else "alias" if redefines_id else "group" if regular else "zero" if typ.numeric else "spaces"}
        if value and not area.startswith("LINKAGE:"):
            initial = {"policy":"explicit", "value_node":self.nid(value)}
        self.r.layout.items[symbol.id] = StorageLayout(symbol.id,area,offset,size,total,symbol.parent,
                                                       not area.startswith("LINKAGE:"),dims,redefines_id,initial)
        ann = self.ann(item)
        ann.type,ann.layout_id = symbol.type,symbol.id
        for child in item.children:
            if child.level == 88:
                self.place(child,area,offset,dims)
        return offset+total

    def validate_declaration(self, item):
        symbol = self.table.symbols[self.declarations[id(item)]]
        value = next((c for c in item.clauses if isinstance(c,A.ValueClause)),None)
        if item.level == 88:
            if not value:
                self.diagnostic("CONDITION_WITHOUT_VALUE", "Nível 88 exige VALUE.", item)
            target_type = self.table.symbols[symbol.parent].type if symbol.parent else ERROR
            if target_type.category == "group":
                self.diagnostic("INVALID_CONDITION_PARENT", "Nível 88 exige item elementar associado.", item)
        else:
            target_type = symbol.type
            if self.strict and not value and target_type.category not in {"group","screen","error"}:
                self.diagnostic("MISSING_VALUE", "Modo estrito exige VALUE em item elementar.", item)
        if value:
            if item.level != 88 and (len(value.values)!=1 or value.values[0].upper):
                self.diagnostic("INVALID_VALUE_LIST", "Lista/faixa VALUE é exclusiva do nível 88.", value)
            for interval in value.values:
                for expr in (interval.lower, interval.upper):
                    if expr:
                        source = self.expr(expr)
                        self.compatible(source,target_type,expr,initial=True)
                        self.validate_initial(expr,target_type)
                if interval.upper:
                    low,high=self.constant(interval.lower),self.constant(interval.upper)
                    if low is not None and high is not None and type(low) is type(high) and low>high:
                        self.diagnostic("REVERSED_VALUE_RANGE", "Faixa VALUE invertida.", interval)
        for clause in item.clauses:
            if isinstance(clause,A.OccursClause):
                layout = self.r.layout.items.get(symbol.id)
                if clause.depending:
                    self.require_integer(clause.depending)
                    sid=self.ann(clause.depending).symbol_id
                    counter = self.table.symbols.get(sid)
                    if counter and (counter.namespace != "data" or counter.id==symbol.id or symbol.id in [s.id for s in self.table.ancestors(counter)]):
                        self.diagnostic("INVALID_DEPENDING_COUNTER", "DEPENDING exige campo inteiro externo à própria tabela.",clause.depending)
                    if layout and layout.dimensions:
                        layout.dimensions[-1].depending_id=sid
                    self.ann(clause).checks.append({"kind":"occurs-depending", "symbol_id":sid,"minimum":layout.dimensions[-1].minimum if layout and layout.dimensions else None,"maximum":layout.dimensions[-1].maximum if layout and layout.dimensions else None})
                for key in clause.keys:
                    for ref in key.keys:
                        local = [candidate for candidate in self.table.candidates(ref.name,["data"],ref.qualifiers) if symbol.id in [s.id for s in self.table.ancestors(candidate)]]
                        if len(local)==1:
                            self.bind(ref,local[0],"table-key")
                        self.expr(ref,whole=True)
                        key_sid=self.ann(ref).symbol_id
                        if key_sid and symbol.id not in [s.id for s in self.table.ancestors(self.table.symbols[key_sid])]:
                            self.diagnostic("TABLE_KEY_OUTSIDE_TABLE", "Chave deve ser subordinada à tabela.", ref)
            elif isinstance(clause,A.ScreenUsing):
                using=self.expr(clause.target,write=True)
                if self.compatibility:
                    if not self.clause(item,A.PictureClause):
                        self.diagnostic('SCREEN_PICTURE_REQUIRED','Campo USING exige PIC explícito neste perfil.',clause)
                    elif target_type.numeric and (target_type.scale or target_type.signed) or target_type.edited:
                        self.unsupported('SCREEN_PICTURE',clause)
                    else:self.compatible(using,target_type,clause)
            elif isinstance(clause,A.ScreenPosition):
                self.require_integer(clause.value)

    def validate_initial(self, expr, typ):
        value=self.constant(expr)
        if value is None or typ.category == "error":
            return
        if typ.numeric and isinstance(value,Decimal):
            if (not typ.signed and value < 0) or (typ.precision is not None and value.copy_abs() >= Decimal(10)**(typ.precision-typ.scale)):
                self.diagnostic("VALUE_OUT_OF_RANGE", "VALUE não cabe na precisão/sinal do campo.",expr)
            digits = value.as_tuple().digits
            trailing = len(digits) - len(''.join(map(str,digits)).rstrip('0'))
            effective_scale = max(0,-value.as_tuple().exponent-trailing) if value else 0
            if typ.scale is not None and effective_scale > typ.scale:
                self.diagnostic("VALUE_SCALE_LOSS", "VALUE excede a escala declarada.",expr)
        elif isinstance(value,str) and typ.length is not None and len(value.encode("latin-1",errors="replace"))>typ.length and not (isinstance(expr,A.Literal) and expr.all):
            self.diagnostic("VALUE_TOO_LONG", "VALUE excede a largura física do campo.",expr)

    def bind(self, ref, symbol, role="data"):
        ann=self.ann(ref)
        ann.symbol_id,ann.type,ann.role=symbol.id,symbol.type,role
        ann.layout_id=symbol.id if symbol.id in self.r.layout.items else None
        ann.writable=symbol.namespace in {"data","index","special"}
        return symbol.type or ERROR

    def resolve(self, ref, namespaces=("data","condition","index","special"), role="data"):
        candidates=self.table.candidates(ref.name,namespaces,ref.qualifiers)
        if not candidates:
            self.diagnostic("UNDEFINED_SYMBOL", f"{ref.name} não declarado em {'/'.join(namespaces)}.",ref)
        elif len(candidates)>1:
            self.diagnostic("AMBIGUOUS_REFERENCE", f"Referência ambígua a {ref.name}; qualifique por OF/IN.",ref,related=candidates)
        else:
            self.bind(ref,candidates[0],role)
            return candidates[0]
        self.ann(ref).type=ERROR
        return None

    def constant(self, expr):
        if isinstance(expr,A.Group):
            return self.constant(expr.expression)
        if isinstance(expr,A.Unary) and expr.operator in {"+","-"}:
            v=self.constant(expr.operand)
            return (-v if expr.operator=="-" else v) if isinstance(v,Decimal) else None
        if isinstance(expr,A.Literal):
            if expr.category=="number":
                try: return Decimal(expr.value)
                except InvalidOperation: return None
            if expr.category=="string": return expr.value
            if expr.value in {"ZERO","ZEROS","ZEROES"}: return Decimal(0)
        return None

    def integer_constant(self, expr):
        value=self.constant(expr)
        return int(value) if isinstance(value,Decimal) and value==value.to_integral_value() else None

    def require_numeric(self, expr, *, write=False):
        typ=self.expr(expr,write=write)
        if typ.category!="error" and not typ.numeric:
            self.diagnostic("NUMERIC_REQUIRED", "Operando deve ser numérico não editado.",expr)
        return typ

    def require_integer(self, expr, *, write=False):
        typ=self.require_numeric(expr,write=write)
        if typ.numeric and typ.scale!=0:
            self.diagnostic("INTEGER_REQUIRED", "Operando deve ter escala zero.",expr)
        return typ

    def condition(self, expr, subject=None):
        typ=self.expr(expr,subject=subject)
        if typ.category not in {"boolean","error"}:
            self.diagnostic("CONDITION_REQUIRED", "Condição exige comparação, classe, booleano ou condition-name 88.",expr)
        return typ

    def expr(self, node, *, write=False, whole=False, subject=None):
        ann=self.ann(node)
        # Expressões podem ser visitadas em contextos distintos; referências só
        # resolvem uma vez, mas validam escrita e acesso em todo contexto.
        typ=ann.type
        if isinstance(node,A.Reference):
            symbol=self.table.symbols.get(ann.symbol_id) if ann.symbol_id else self.resolve(node)
            typ=symbol.type if symbol else ERROR
            if symbol:
                self.bind(node,symbol)
                layout=self.r.layout.items.get(symbol.id)
                dims=layout.dimensions if layout else []
                if not whole and len(node.subscripts)!=len(dims):
                    self.diagnostic("SUBSCRIPT_COUNT", f"{node.name} exige {len(dims)} subscrito(s), recebeu {len(node.subscripts)}.",node)
                if whole and node.subscripts and len(node.subscripts)!=len(dims):
                    self.diagnostic("SUBSCRIPT_COUNT", "Quantidade de subscritos incompatível.",node)
                for index,sub in enumerate(node.subscripts):
                    self.require_integer(sub)
                    if index<len(dims):
                        dim=dims[index]
                        index_sid = self.ann(sub).symbol_id
                        index_symbol = self.table.symbols.get(index_sid)
                        if index_symbol and index_symbol.namespace == "index" and index_symbol.table_id != dim.symbol_id:
                            other = self.r.layout.items.get(index_symbol.table_id)
                            compatible = other and other.dimensions and (other.dimensions[-1].maximum,other.dimensions[-1].stride)==(dim.maximum,dim.stride)
                            if not compatible:
                                self.diagnostic("INDEX_TABLE_MISMATCH", "Índice de tabela com quantidade/stride incompatíveis.", sub, related=[index_symbol])
                        value=self.integer_constant(sub)
                        if value is not None and not 1<=value<=dim.maximum:
                            self.diagnostic("SUBSCRIPT_BOUNDS", f"Subscrito {value} fora de 1..{dim.maximum}.",sub)
                        elif value is None or dim.depending_id:
                            check={"kind":"subscript", "expression":self.nid(sub), **asdict(dim)}
                            if check not in ann.checks: ann.checks.append(check)
                ann.details["address"]={"area":layout.area,"offset":layout.offset,"size":layout.size,
                    "dimensions":[asdict(d) for d in dims],"subscripts":[self.nid(s) for s in node.subscripts],
                    "whole_table":whole and not node.subscripts} if layout else None
                if whole and not node.subscripts and layout:
                    typ=replace(typ,length=layout.total_size)
                if node.modification:
                    mod=node.modification
                    if not typ.textual and not (typ.numeric and typ.usage=="DISPLAY"):
                        self.diagnostic("REFMOD_CATEGORY", "Referência modificada exige campo de caracteres ou numérico DISPLAY.",mod)
                    self.require_integer(mod.start)
                    if mod.length: self.require_integer(mod.length)
                    start=self.integer_constant(mod.start)
                    length=self.integer_constant(mod.length) if mod.length else (typ.length-start+1 if typ.length is not None and start is not None else None)
                    if (start is not None and (start<1 or typ.length is not None and start>typ.length)) or (length is not None and length<1) or (None not in (start,length,typ.length) and start+length-1>typ.length):
                        self.diagnostic("REFMOD_BOUNDS", "Referência modificada fora dos limites físicos.",mod)
                    if start is None or length is None:
                        check={"kind":"refmod", "start":self.nid(mod.start),"length":self.nid(mod.length) if mod.length else None,"capacity":typ.length}
                        if check not in ann.checks: ann.checks.append(check)
                    typ=CobolType("alphanumeric",length)
                    ann.details["refmod"]={"start":self.nid(mod.start),"length":self.nid(mod.length) if mod.length else None}
                if write and not ann.writable:
                    self.diagnostic("NOT_WRITABLE", f"{node.name} não é destino gravável.",node,related=[symbol])
        elif isinstance(node,A.Literal):
            if node.category=="number":
                value=Decimal(node.value)
                tup=value.as_tuple()
                scale=max(0,-tup.exponent)
                typ=numeric_type(max(len(tup.digits),scale),scale, value<0 or node.value.startswith(("+","-")))
            elif node.value in {"TRUE","FALSE"} and node.category=="figurative": typ=BOOLEAN
            elif node.value in {"ZERO","ZEROS","ZEROES"} and node.category=="figurative": typ=numeric_type(1,0,False)
            elif node.category=="setting": typ=CobolType("setting")
            else:
                try: length=len(node.value.encode("latin-1")) if node.category=="string" else 1
                except UnicodeEncodeError:
                    self.diagnostic("UNSUPPORTED_CHARACTER_ENCODING", "Literal não representável em ISO-8859-1.",node)
                    length=None
                typ=CobolType("alphanumeric",length)
            ann.details.update({"figurative":node.value if node.category=="figurative" else None,"all":node.all})
        elif isinstance(node,A.Group): typ=self.expr(node.expression,subject=subject)
        elif isinstance(node,A.LengthOf):
            target=self.expr(node.operand,whole=True)
            if target.category in {"boolean","screen","index"}:
                self.diagnostic("LENGTH_REQUIRES_STORAGE", "LENGTH OF exige campo com armazenamento de dados.",node.operand)
            sid = self.ann(node.operand).symbol_id
            layout = self.r.layout.items.get(sid)
            length = target.length if node.operand.modification or not layout else layout.size
            dynamic = self.variable_length_dimensions(sid) if sid else []
            typ=numeric_type(len(str(length)) if length is not None else None)
            ann.details.update({"constant_length":None if dynamic else length,"maximum_length":length,
                                "dynamic_dimensions":dynamic,"unit":"one-occurrence"})
        elif isinstance(node,A.FunctionCall): typ=self.function(node)
        elif isinstance(node,A.Unary):
            if node.operator=="NOT":
                self.condition(node.operand,subject);typ=BOOLEAN
            else: typ=replace(self.require_numeric(node.operand),signed=True)
        elif isinstance(node,A.Binary):
            if node.operator in {"AND","OR"}:
                self.condition(node.left,subject);self.condition(node.right,subject);typ=BOOLEAN
            else:
                left=self.require_numeric(node.left);right=self.require_numeric(node.right)
                typ=arithmetic_type(node.operator,left,right) if left.numeric and right.numeric else ERROR
                if node.operator in {"/","**"}:
                    ann.checks.append({"kind":"arithmetic-domain","operator":node.operator})
        elif isinstance(node,A.Comparison):
            left=self.expr(node.left);right=self.expr(node.right)
            self.comparable(left,right,node)
            ann.details["comparison"]={"left":self.nid(node.left),"right":self.nid(node.right),"padding":"spaces", "operator":node.operator}
            typ=BOOLEAN
        elif isinstance(node,A.AbbreviatedCondition):
            inherited=self.by_span.get(repr(node.inherited_subject)) if node.inherited_subject else subject
            if inherited:
                left=self.expr(inherited);right=self.expr(node.right)
                self.comparable(left,right,node)
                ann.details["subject"]=self.nid(inherited)
            else:
                self.diagnostic("MISSING_CONDITION_SUBJECT", "Condição abreviada sem sujeito vinculável.",node)
                self.expr(node.right)
            typ=BOOLEAN
        elif isinstance(node,A.ClassCondition):
            operand=node.operand or subject
            if operand:
                typ_operand=self.expr(operand)
                ann.details["subject"]=self.nid(operand)
                if node.category in {"POSITIVE","NEGATIVE","ZERO"} and not typ_operand.numeric and typ_operand!=ERROR:
                    self.diagnostic("NUMERIC_REQUIRED", "Teste de sinal requer numérico.",node)
            else: self.diagnostic("MISSING_CONDITION_SUBJECT", "Teste de classe sem sujeito.",node)
            typ=BOOLEAN
        else:
            self.unsupported(type(node).__name__.upper(),node);typ=ERROR
        if write and not isinstance(node,A.Reference):
            self.diagnostic("NOT_WRITABLE", "Destino deve ser referência gravável.",node)
        ann.type=typ or ERROR
        return ann.type

    def comparable(self,left,right,node):
        if "error" in {left.category,right.category}: return
        if "boolean" in {left.category,right.category} and left.category!=right.category:
            self.diagnostic("INCOMPARABLE_TYPES", "Booleano não é comparável a campo numérico/textual.",node)
        self.ann(node).details["comparison_mode"]="numeric" if left.numeric and right.numeric else "padded-bytes"

    def variable_length_dimensions(self,sid):
        symbol = self.table.symbols.get(sid)
        if not symbol:
            return []
        result = []
        for child_id in symbol.children:
            layout = self.r.layout.items.get(child_id)
            if layout:
                result.extend(asdict(d) for d in layout.dimensions if d.symbol_id==child_id and d.depending_id)
                result.extend(self.variable_length_dimensions(child_id))
        return result

    def compatible(self, source, target, node, *, initial=False, target_id=None):
        if "error" in {source.category,target.category}: return
        if source.category=="alphabetic" and target.numeric:
            self.diagnostic("MOVE_ALPHABETIC_TO_NUMERIC", "PIC A não pode ser movido para campo numérico.",node)
        elif target.category in {"boolean","screen","pointer","index"}:
            self.diagnostic("INCOMPATIBLE_MOVE", f"MOVE/VALUE incompatível com {target.category}.",node)
        elif source.category=="boolean":
            self.diagnostic("INCOMPATIBLE_MOVE", "Booleano exige SET de condition-name.",node)
        elif initial and target.numeric and source.textual:
            # Literal textual só é inicialização numérica se contém dígitos válidos.
            value=self.constant(node)
            if not isinstance(value,str) or not value.isascii() or not value.isdigit():
                self.diagnostic("INVALID_NUMERIC_VALUE", "VALUE textual não é numérico válido.",node)
        conversion={"source_type":asdict(source),"target_type":asdict(target),"target_id":target_id,
                    "operation":"group-bytes" if "group" in {source.category,target.category} else "numeric" if target.numeric else "format-or-pad",
                    "padding":"spaces", "truncation":"receiver", "encoding":"ISO-8859-1"}
        if conversion not in self.ann(node).conversions: self.ann(node).conversions.append(conversion)

    def function(self,node):
        args=[self.expr(v) for v in node.arguments]
        name=node.name.upper()
        signatures={"REVERSE":(1,1,"text"),"UPPER-CASE":(1,1,"text"),"LOWER-CASE":(1,1,"text"),
            "LENGTH":(1,1,"any"),"MOD":(2,2,"integer"),"ORD":(1,1,"text"),"INTEGER":(1,1,"numeric"),
            "INTEGER-OF-DATE":(1,1,"integer"),"DATE-OF-INTEGER":(1,1,"integer"),"RANDOM":(0,1,"integer")}
        if name not in signatures:
            self.unsupported("FUNCTION_"+name,node);return ERROR
        minimum,maximum,category=signatures[name]
        if not minimum<=len(args)<=maximum:
            self.diagnostic("FUNCTION_ARITY", f"{name} exige {minimum}..{maximum} argumento(s).",node)
        for expr,typ in zip(node.arguments,args):
            if typ==ERROR: continue
            if category=="text" and not typ.textual:
                self.diagnostic("FUNCTION_ARGUMENT_TYPE", f"{name} exige argumento textual.",expr)
            elif category in {"integer","numeric"} and (not typ.numeric or category=="integer" and not typ.integral):
                self.diagnostic("FUNCTION_ARGUMENT_TYPE", f"{name} exige argumento {category}.",expr)
        self.ann(node).details["intrinsic"]=name
        if name in {"REVERSE","UPPER-CASE","LOWER-CASE"}:
            return CobolType("alphanumeric",args[0].length if args else None)
        if name=="LENGTH": return numeric_type(None)
        if name=="ORD":
            if args and args[0].length is not None and args[0].length != 1:
                self.diagnostic("FUNCTION_ARGUMENT_LENGTH", "ORD exige exatamente um byte.",node.arguments[0])
            return numeric_type(3,0,False)
        if name=="RANDOM": return numeric_type(None,None,False)
        if name in {"INTEGER-OF-DATE","DATE-OF-INTEGER"}:
            self.ann(node).checks.append({"kind":"date-domain","function":name})
            return numeric_type(8 if name=="DATE-OF-INTEGER" else 7,0,False)
        if name=="MOD":
            self.ann(node).checks.append({"kind":"nonzero-divisor","expression":self.nid(node.arguments[1]) if len(args)>1 else None})
        return numeric_type(None,0)

    def bind_files(self):
        for symbol in list(self.table.symbols.values()):
            if symbol.namespace!="file": continue
            select=self.file_selects.get(symbol.id)
            fd=self.file_descriptors.get(symbol.id)
            if select and not fd:
                self.diagnostic("MISSING_FD", f"SELECT {symbol.name} não tem FD/SD.",select)
            organization="SEQUENTIAL"
            access="SEQUENTIAL"
            assignment=None
            status=None
            keys=[]
            if select:
                seen_clauses = set()
                for clause in select.clauses:
                    if isinstance(clause,(A.AssignClause,A.OrganizationClause,A.AccessClause,A.FileStatusClause)):
                        if type(clause) in seen_clauses:
                            self.diagnostic("DUPLICATE_FILE_CLAUSE", "Cláusula de arquivo repetida.", clause)
                        seen_clauses.add(type(clause))
                    if isinstance(clause,A.OrganizationClause): organization=clause.organization
                    elif isinstance(clause,A.AccessClause): access=clause.mode
                    elif isinstance(clause,A.AssignClause):
                        assignment=self.nid(clause.target)
                        if isinstance(clause.target,A.Reference) and not self.table.candidates(clause.target.name,["data"]):
                            self.ann(clause.target).role="external-assignment-name"
                            self.ann(clause.target).type=CobolType("external-name")
                        else: self.expr(clause.target)
                    elif isinstance(clause,A.FileStatusClause):
                        typ=self.expr(clause.target,write=True)
                        status=self.ann(clause.target).symbol_id
                        if typ!=ERROR and (typ.length!=2 or typ.category not in {"numeric","alphanumeric"} or typ.usage!="DISPLAY"):
                            self.diagnostic("INVALID_FILE_STATUS", "FILE STATUS exige dois bytes DISPLAY numéricos ou alfanuméricos.",clause)
                    elif isinstance(clause,A.KeyClause):
                        for ref in clause.keys:
                            local = [candidate for candidate in self.table.candidates(ref.name,["data"],ref.qualifiers) if candidate.file_id==symbol.id]
                            if len(local)==1:
                                self.bind(ref,local[0],"file-key")
                            self.expr(ref,whole=True)
                            sid=self.ann(ref).symbol_id
                            keys.append({"symbol_id":sid,"role":clause.role,"duplicates":clause.duplicates})
                            if sid and self.table.symbols[sid].file_id!=symbol.id:
                                self.diagnostic("FILE_KEY_OUTSIDE_RECORD", "Chave não pertence ao registro do arquivo.",ref)
                    else: self.unsupported(type(clause).__name__.upper(),clause)
            if organization in {"INDEXED","RELATIVE"} or access not in {"SEQUENTIAL"}:
                self.unsupported("FILE_ORGANIZATION",select or fd)
            if organization=="INDEXED" and not keys:
                self.diagnostic("MISSING_RECORD_KEY", "Arquivo INDEXED exige RECORD KEY.",select or fd)
            if organization in {"SEQUENTIAL","LINE SEQUENTIAL"} and keys:
                self.diagnostic("KEY_ON_SEQUENTIAL_FILE", "RECORD KEY/ALTERNATE KEY exige arquivo INDEXED/RELATIVE.",select or fd)
            if organization in {"SEQUENTIAL","LINE SEQUENTIAL"} and access != "SEQUENTIAL":
                self.diagnostic("INVALID_FILE_ACCESS", "Arquivo sequencial exige ACCESS SEQUENTIAL.",select or fd)
            records=[self.declarations[id(item)] for item in fd.records] if fd else []
            self.r.files[symbol.id]={"name":symbol.name,"select_node":self.nid(select) if select else None,
                "descriptor_node":self.nid(fd) if fd else None,"sort":fd.sort if fd else False,
                "organization":organization,"access":access,"assignment_node":assignment,
                "status_symbol":status,"keys":keys,"records":records,
                "record_lengths":[self.r.layout.items[s].total_size for s in records],"open_modes":[]}
            if fd:
                for clause in fd.clauses:
                    if isinstance(clause,A.DataRecordsClause):
                        for ref in clause.records:
                            self.expr(ref,whole=True)
                            if self.ann(ref).symbol_id not in records:
                                self.diagnostic('INVALID_DATA_RECORD','DATA RECORD deve nomear registro raiz deste FD.',ref)
                    if isinstance(clause,A.RecordSizeClause):
                        lo=self.integer_constant(clause.minimum)
                        hi=self.integer_constant(clause.maximum) if clause.maximum else lo
                        for sid in records:
                            length=self.r.layout.items[sid].total_size
                            if lo is not None and hi is not None and not lo<=length<=hi:
                                self.diagnostic("RECORD_SIZE_MISMATCH", f"Registro de {length} bytes fora de RECORD CONTAINS {lo}..{hi}.",clause)
        for node in A.walk(self.root.procedure):
            if isinstance(node,A.Open):
                for group in node.groups:
                    for ref in group.files:
                        candidates=self.table.candidates(ref.name,["file"],ref.qualifiers)
                        if len(candidates)==1 and candidates[0].id in self.r.files:
                            self.r.files[candidates[0].id]["open_modes"].append(group.mode)
        if self.root.environment:
            for node in A.walk(self.root.environment):
                if isinstance(node,A.SpecialName):
                    typ=self.expr(node.value,write=isinstance(node.value,A.Reference))
                    if self.compatibility and node.setting=='CURSOR' and typ.length not in {4,6}:
                        self.diagnostic('INVALID_CURSOR_FIELD','CURSOR exige quatro ou seis posições neste perfil.',node)
                    if self.compatibility and node.setting=='CRT STATUS' and not (typ.numeric and typ.integral and (typ.precision or 0)>=4):
                        self.diagnostic('INVALID_CRT_STATUS','CRT STATUS exige campo inteiro com pelo menos quatro dígitos.',node)

    def file_ref(self,ref,operation):
        symbol=self.resolve(ref,("file",),"file")
        if not symbol: return None
        if ref.subscripts or ref.modification:
            self.diagnostic("INVALID_FILE_REFERENCE", "Nome de arquivo não admite subscritos/refmod.",ref)
        info=self.r.files[symbol.id]
        self.ann(ref).details["file_id"]=symbol.id
        if info["sort"]:
            self.diagnostic("SORT_FILE_IO", "SD não admite OPEN/READ/WRITE/CLOSE convencional.",ref)
        modes=set(info["open_modes"])
        allowed={"READ":{"INPUT","I-O"},"WRITE":{"OUTPUT","EXTEND","I-O"},"START":{"INPUT","I-O"}}
        if operation in allowed:
            self.ann(ref).checks.append({"kind":"file-mode","file_id":symbol.id,"allowed":sorted(allowed[operation])})
            if modes and not modes & allowed[operation]:
                self.diagnostic("INVALID_FILE_MODE", f"{operation} incompatível com OPEN {', '.join(sorted(modes))}.",ref)
        return symbol

    def control_ref(self,ref):
        symbol=self.resolve(ref,("section","paragraph"),"control")
        if ref.subscripts or ref.modification:
            self.diagnostic("INVALID_CONTROL_REFERENCE", "Destino de controle não admite subscritos/refmod.",ref)
        if symbol: self.ann(ref).details.update(self.r.controls[symbol.id])
        return symbol

    def move(self,source,targets,node,corresponding=False):
        source_type=self.expr(source)
        for ref in targets:
            target_type=self.expr(ref,write=True)
            if corresponding:
                self.corresponding(source,ref,node,arithmetic=False)
            else:
                self.compatible(source_type,target_type,node,target_id=self.ann(ref).symbol_id)

    def corresponding(self,source,target,node,arithmetic=False):
        source_sid=self.ann(source).symbol_id
        target_sid=self.ann(target).symbol_id
        if not source_sid or not target_sid: return
        if any(self.table.symbols[s].type.category!="group" for s in (source_sid,target_sid)):
            self.diagnostic("CORRESPONDING_REQUIRES_GROUPS", "CORRESPONDING exige dois grupos.",node);return
        def leaves(sid,path=()):
            result={}
            for child_id in self.table.symbols[sid].children:
                child=self.table.symbols[child_id]
                if child.namespace!="data": continue
                item=self.nodes[child.node_id]
                if any(isinstance(c,(A.OccursClause,A.RedefinesClause)) for c in item.clauses): continue
                if child.type.category=="group": result.update(leaves(child_id,path+(child.name,)))
                else: result[(child.name,)+path]=child
            return result
        left,right=leaves(source_sid),leaves(target_sid)
        pairs=[]
        for key in left.keys() & right.keys():
            src,dst=left[key],right[key]
            if arithmetic and not (src.type.numeric and dst.type.numeric): continue
            if not arithmetic: self.compatible(src.type,dst.type,node,target_id=dst.id)
            pairs.append({"source":src.id,"target":dst.id})
        self.ann(node).details.setdefault("corresponding",[]).extend(sorted(pairs,key=lambda p:p["target"]))

    def arithmetic(self,node):
        if node.corresponding:
            for source in node.sources: self.expr(source)
            for target in node.targets+node.giving: self.expr(target.target,write=True)
            if len(node.sources)!=1 or not node.targets:
                self.diagnostic("INVALID_CORRESPONDING", "Aritmética CORRESPONDING exige grupo fonte e receptor.",node)
            else:
                self.corresponding(node.sources[0],node.targets[0].target,node,arithmetic=True)
            return
        source_types=[self.require_numeric(e) for e in node.sources]
        read_types=[]
        for receiver in node.targets:
            # Com GIVING, targets representam operandos lidos, não receptores.
            read_types.append(self.require_numeric(receiver.target,write=not bool(node.giving)))
        for receiver in node.giving: self.require_numeric(receiver.target,write=True)
        if node.remainder: self.require_numeric(node.remainder,write=True)
        all_types=source_types+(read_types if node.operation!="COMPUTE" else [])
        typ=source_types[0] if source_types else ERROR
        for other in all_types[1:]:
            if typ.numeric and other.numeric:
                typ=arithmetic_type({"ADD":"+","SUBTRACT":"-","MULTIPLY":"*","DIVIDE":"/"}.get(node.operation,"+"),typ,other)
        if node.operation=="DIVIDE": typ=numeric_type(scale=None)
        self.ann(node).type=typ
        for target in node.giving or node.targets:
            receiver_type=self.ann(target.target).type
            self.ann(target).type=receiver_type
            self.ann(target).details={"result_type":asdict(typ),"rounded":target.rounded,
                "receiving_scale":receiver_type.scale,"overflow":"size-error" if any(h.event=="SIZE ERROR" for h in node.handlers) else "runtime-diagnostic"}
            self.ann(target).checks.append({"kind":"numeric-capacity","precision":receiver_type.precision,"scale":receiver_type.scale,"signed":receiver_type.signed})
        if node.operation=="DIVIDE": self.ann(node).checks.append({"kind":"division-by-zero","form":node.form})

    def statement(self,node, *, section=None,paragraph=None,inline=0):
        ann=self.ann(node)
        ann.role="statement"
        context={"section":section,"paragraph":paragraph,"inline":inline}
        if isinstance(node,A.Move): self.move(node.source,node.targets,node,node.corresponding)
        elif isinstance(node,A.Initialize):
            receivers=[]
            for ref in node.targets:
                typ = self.expr(ref,write=True,whole=True)
                if typ.category in {"boolean","index","pointer","screen"}:
                    self.diagnostic("INVALID_INITIALIZE_TARGET", "INITIALIZE exige item de dados alfanumérico, numérico ou grupo.",ref)
                sid=self.ann(ref).symbol_id
                if sid:
                    def collect(symbol):
                        if symbol.namespace not in {"data","filler"}: return
                        layout=self.r.layout.items.get(symbol.id)
                        if layout and layout.redefines: return
                        if symbol.type.category=="group":
                            for child in symbol.children: collect(self.table.symbols[child])
                        elif symbol.namespace!="filler": receivers.append(symbol.id)
                    collect(self.table.symbols[sid])
            for replacement in node.replacements:
                typ=self.expr(replacement.value)
                category=replacement.category.lower()
                if category == "numeric" and typ.category not in {"numeric","error"}:
                    self.diagnostic("INVALID_INITIALIZE_REPLACEMENT", "Reposição NUMERIC exige valor numérico.",replacement)
                for sid in receivers:
                    target=self.table.symbols[sid]
                    match=target.type.category==category or (category=="alphanumeric" and target.type.category=="alphabetic")
                    if match: self.compatible(typ,target.type,replacement,target_id=sid)
                if category=="numeric" and typ.category=="alphabetic":
                    self.diagnostic("INVALID_INITIALIZE_REPLACEMENT", "Reposição numérica incompatível com PIC A.",replacement)
            ann.details["initialize_receivers"]=receivers
        elif isinstance(node,A.Display):
            for operand in node.operands:
                if isinstance(operand,A.ScreenPosition): self.require_integer(operand.value)
                else: self.expr(operand)
            ann.details.update({"no_advancing":node.no_advancing,"upon":node.upon,"encoding":"ISO-8859-1"})
        elif isinstance(node,A.Accept):
            typ=self.expr(node.target,write=True)
            for position in node.positions: self.require_integer(position.value)
            source_width={"DATE":8 if node.date_format=="YYYYMMDD" else 6,"DAY":7 if node.date_format=="YYYYDDD" else 5,"DAY-OF-WEEK":1,"TIME":8}.get(node.source)
            if source_width and typ.category!="error":
                self.compatible(numeric_type(source_width,0,False),typ,node,target_id=self.ann(node.target).symbol_id)
            elif typ.category != "screen":
                self.compatible(CobolType("alphanumeric"),typ,node,target_id=self.ann(node.target).symbol_id)
                ann.checks.append({"kind":"accept-conversion","target":self.ann(node.target).symbol_id,"category":typ.category})
            if typ.category=="screen" and not self.compatibility: self.unsupported("SCREEN_EXECUTION",node)
            ann.details.update({"source":node.source,"date_format":node.date_format,"width":source_width})
        elif isinstance(node,A.Arithmetic): self.arithmetic(node)
        elif isinstance(node,A.If):
            self.condition(node.condition)
            self.statements(node.then_body,**context);self.statements(node.else_body,**context)
        elif isinstance(node,A.Evaluate):
            for subject in node.subjects: self.expr(subject)
            for case in node.cases:
                for alternative in case.alternatives:
                    for subject,selection in zip(node.subjects,alternative):
                        if selection.value:
                            typ=self.expr(selection.value,subject=subject)
                            if not isinstance(selection.value,(A.ClassCondition,A.AbbreviatedCondition)):
                                self.comparable(self.ann(subject).type,typ,selection)
                            self.ann(selection).details["kind"] = "predicate" if isinstance(selection.value,(A.ClassCondition,A.AbbreviatedCondition)) else selection.kind
                            self.ann(selection).details["subject"]=self.nid(subject)
                        if selection.upper:
                            typ=self.expr(selection.upper)
                            self.comparable(self.ann(subject).type,typ,selection)
                self.statements(case.body,**context)
        elif isinstance(node,A.Perform):
            if node.target:
                target=self.control_ref(node.target)
                end=self.control_ref(node.through) if node.through else target
                if target and end:
                    first,last=self.r.controls[target.id],self.r.controls[end.id]
                    if first["token_start"]>last["token_start"]:
                        self.diagnostic("REVERSED_PERFORM_RANGE", "PERFORM THRU tem destinos em ordem inversa.",node)
                    ann.details["perform"]={"entry_symbol":target.id,"limit_symbol":end.id,"entry_node":first["entry_node"],
                        "limit_token":last["token_end"],"return_after_node":self.nid(node),"stack":"explicit-perform", "test":node.test}
            if node.times:
                self.require_integer(node.times)
                value=self.integer_constant(node.times)
                if value is not None and value<0: self.diagnostic("NEGATIVE_TIMES", "PERFORM TIMES não admite contagem negativa.",node.times)
                ann.checks.append({"kind":"nonnegative-times","expression":self.nid(node.times)})
            if node.until: self.condition(node.until)
            for varying in node.varying:
                target=self.require_numeric(varying.target,write=True)
                for expr in (varying.initial,varying.step):
                    typ=self.require_numeric(expr);self.compatible(typ,replace(target,category="numeric") if target.category=="index" else target,varying,target_id=self.ann(varying.target).symbol_id)
                self.condition(varying.until)
                ann.checks.append({"kind":"varying-overflow","symbol_id":self.ann(varying.target).symbol_id})
            self.statements(node.body,section=section,paragraph=paragraph,inline=inline+1)
        elif isinstance(node,A.GoTo):
            for target in node.targets: self.control_ref(target)
            if node.depending: self.require_integer(node.depending)
            ann.details["goto"]={"targets":[self.ann(t).symbol_id for t in node.targets],"depending":self.nid(node.depending) if node.depending else None,"stack":"preserve-perform-until-limit"}
        elif isinstance(node,A.Exit):
            if node.returning:self.require_integer(node.returning)
            if node.scope=="PERFORM" and not inline: self.diagnostic("EXIT_CONTEXT", "EXIT PERFORM exige PERFORM inline.",node)
            if node.scope=="SECTION" and not section: self.diagnostic("EXIT_CONTEXT", "EXIT SECTION exige seção.",node)
            if node.scope=="PARAGRAPH" and not paragraph: self.diagnostic("EXIT_CONTEXT", "EXIT PARAGRAPH exige parágrafo.",node)
            ann.details["exit"]={"effect":"noop" if node.scope is None else node.scope.lower(),"section":section,"paragraph":paragraph}
        elif isinstance(node,(A.Continue,A.StopRun,A.Goback,A.NextSentence)):
            if isinstance(node,A.Goback) and node.returning:self.require_integer(node.returning)
            ann.details["effect"]={A.Continue:"noop",A.StopRun:"terminate-run-unit",A.Goback:"return-caller-or-host",A.NextSentence:"next-sentence"}[type(node)]
            if isinstance(node,A.NextSentence):
                next_sentence=next((s for s in sorted((n for n in A.walk(self.root.procedure) if isinstance(n,A.Sentence)),key=lambda s:s.token_start) if s.token_start>node.token_end),None)
                ann.details["next_sentence"]=self.nid(next_sentence) if next_sentence else None
        elif isinstance(node,A.Open):
            for group in node.groups:
                for ref in group.files:
                    symbol=self.file_ref(ref,"OPEN")
                    if symbol and group.mode=="I-O" and self.r.files[symbol.id]["organization"]=="LINE SEQUENTIAL":
                        self.diagnostic("INVALID_FILE_MODE", "LINE SEQUENTIAL não admite I-O neste ABI.",group)
        elif isinstance(node,A.Close):
            for ref in node.files: self.file_ref(ref,"CLOSE")
        elif isinstance(node,A.Read):
            symbol=self.file_ref(node.file,"READ")
            if node.into:
                target=self.expr(node.into,write=True)
                if symbol and self.r.files[symbol.id]["records"]:
                    record=self.table.symbols[self.r.files[symbol.id]["records"][0]]
                    self.compatible(record.type,target,node,target_id=self.ann(node.into).symbol_id)
            if node.key: self.expr(node.key)
            if symbol:
                info=self.r.files[symbol.id]
                ann.details["file_id"]=symbol.id
                ann.details["records"]=info["records"]
                if node.key and info["organization"] not in {"INDEXED","RELATIVE"}:
                    self.diagnostic("INVALID_READ_KEY", "READ KEY exige organização INDEXED/RELATIVE.",node.key)
                if any(h.event=="INVALID KEY" for h in node.handlers) and info["organization"] not in {"INDEXED","RELATIVE"}:
                    self.diagnostic("INVALID_FILE_HANDLER", "INVALID KEY não se aplica ao arquivo sequencial.",node)
        elif isinstance(node,A.Write):
            target=self.expr(node.record,write=True,whole=True)
            sid=self.ann(node.record).symbol_id
            record=self.table.symbols.get(sid)
            if record and (not record.file_id or record.parent):
                self.diagnostic("WRITE_NOT_RECORD", "WRITE exige registro raiz de FD.",node.record,related=[record])
            elif record:
                info=self.r.files[record.file_id]
                ann.details["file_id"]=record.file_id
                ann.checks.append({"kind":"file-mode","file_id":record.file_id,"allowed":["OUTPUT","EXTEND","I-O"]})
                if info["sort"]: self.diagnostic("SORT_FILE_IO", "WRITE não se aplica a SD.",node)
                if info["open_modes"] and not set(info["open_modes"]) & {"OUTPUT","EXTEND","I-O"}:
                    self.diagnostic("INVALID_FILE_MODE", "WRITE exige arquivo aberto para saída.",node)
                if any(h.event=="INVALID KEY" for h in node.handlers) and info["organization"] not in {"INDEXED","RELATIVE"}:
                    self.diagnostic("INVALID_FILE_HANDLER", "INVALID KEY não se aplica ao arquivo sequencial.",node)
            if node.source: self.compatible(self.expr(node.source),target,node,target_id=sid)
            if node.advancing:
                if not isinstance(node.advancing,A.Literal) or node.advancing.value!="PAGE": self.require_integer(node.advancing)
        elif isinstance(node,A.Start):
            symbol=self.file_ref(node.file,"START")
            subject=None
            if symbol:
                keys=self.r.files[symbol.id]["keys"]
                if keys and keys[0]["symbol_id"]:
                    key=self.table.symbols[keys[0]["symbol_id"]]
                    # Vínculo de sujeito implícito sem criar um nó sintático falso.
                    self.ann(node.condition).details["file_key_symbol"]=key.id
                else: self.diagnostic("START_WITHOUT_KEY", "START exige chave de arquivo.",node)
            if isinstance(node.condition,A.AbbreviatedCondition): self.expr(node.condition.right)
            else: self.condition(node.condition,subject)
            self.unsupported("START",node)
        elif isinstance(node,A.Call): self.call(node)
        elif isinstance(node,A.Inspect):
            typ=self.expr(node.subject,write=bool(node.replacements or node.converting))
            if not typ.textual and not (typ.numeric and typ.usage=="DISPLAY") and typ!=ERROR:
                self.diagnostic("INSPECT_CATEGORY", "INSPECT exige bytes de caracteres DISPLAY.",node.subject)
            for tally in node.tallies:
                self.require_integer(tally.counter,write=True)
                for pattern in tally.patterns: self.inspect_pattern(pattern)
            for pattern in node.replacements: self.inspect_pattern(pattern)
            if node.converting:
                left,right=(self.expr(e) for e in node.converting)
                if left.length is not None and right.length is not None and left.length!=right.length:
                    self.diagnostic("INSPECT_CONVERTING_LENGTH", "CONVERTING exige mapas de mesmo tamanho.",node)
                elif left.length is None or right.length is None: ann.checks.append({"kind":"equal-converting-length"})
        elif isinstance(node,A.String):
            self.text_target(node.target)
            for part in node.parts:
                for expr in part.values: self.expr(expr)
                if part.delimiter.value: self.expr(part.delimiter.value)
            if node.pointer: self.require_integer(node.pointer,write=True)
            ann.checks.append({"kind":"string-capacity","target":self.ann(node.target).symbol_id})
        elif isinstance(node,A.Unstring):
            source=self.expr(node.source)
            if not source.textual and source!=ERROR: self.diagnostic("UNSTRING_CATEGORY", "UNSTRING exige fonte textual.",node.source)
            for delimiter in node.delimiters:
                if delimiter.value: self.expr(delimiter.value)
            for target in node.targets:
                typ=self.expr(target.target,write=True)
                self.compatible(CobolType("alphanumeric"),typ,target,target_id=self.ann(target.target).symbol_id)
                if target.delimiter_in: self.expr(target.delimiter_in,write=True)
                if target.count_in: self.require_integer(target.count_in,write=True)
            if node.pointer: self.require_integer(node.pointer,write=True)
            if node.tallying: self.require_integer(node.tallying,write=True)
            ann.checks.append({"kind":"unstring-capacity"})
        elif isinstance(node,A.Search):
            self.expr(node.table,whole=True)
            sid=self.ann(node.table).symbol_id
            layout=self.r.layout.items.get(sid)
            indexes=[s.id for s in self.table.symbols.values() if s.namespace=="index" and s.table_id==sid]
            if layout and not layout.dimensions: self.diagnostic("SEARCH_NOT_TABLE", "SEARCH exige tabela OCCURS.",node.table)
            if not indexes: self.diagnostic("SEARCH_WITHOUT_INDEX", "SEARCH exige INDEXED BY na tabela.",node.table)
            ann.details["indexes"]=indexes
            if node.varying: self.require_integer(node.varying,write=True)
            if node.all:
                declaration=self.nodes[self.table.symbols[sid].node_id] if sid else None
                occurs=next((c for c in declaration.clauses if isinstance(c,A.OccursClause)),None) if declaration else None
                if not occurs or not occurs.keys: self.diagnostic("SEARCH_ALL_WITHOUT_KEY", "SEARCH ALL exige chave ordenada.",node)
                ann.details["search_all"]={"table":sid,"keys":[{"role":key.role,"symbols":[self.ann(ref).symbol_id for ref in key.keys]} for key in occurs.keys] if occurs else []}
                ann.checks.append({"kind":"ordered-search-table","table":sid})
                for case in node.cases:
                    if not isinstance(case.condition,A.Comparison) or case.condition.operator!="=":
                        self.unsupported("SEARCH_ALL_CONDITION",case.condition)
            self.statements(node.at_end,**context)
            for case in node.cases:
                self.condition(case.condition);self.statements(case.body,**context)
                if node.all and isinstance(case.condition,A.Comparison) and case.condition.operator=="=":
                    keys={self.ann(ref).symbol_id for key in occurs.keys for ref in key.keys} if occurs else set()
                    operands=(case.condition.left,case.condition.right)
                    if not any(isinstance(operand,A.Reference) and self.ann(operand).symbol_id in keys for operand in operands):
                        self.diagnostic("SEARCH_ALL_KEY_REQUIRED", "SEARCH ALL exige comparação com uma chave ordenada da tabela.",case.condition)
        elif isinstance(node,A.Set):
            value=self.expr(node.value)
            for target in node.targets:
                symbol=self.resolve(target)
                if symbol and symbol.namespace=="condition":
                    if node.mode!="TO" or not isinstance(node.value,A.Literal) or node.value.value not in {"TRUE","FALSE"}:
                        self.diagnostic("INVALID_SET_CONDITION", "SET de condição exige TO TRUE/FALSE.",node)
                    elif node.value.value=="FALSE": self.unsupported("SET_FALSE",node)
                    ann.details.setdefault("condition_targets",[]).append({"symbol_id":symbol.id,"parent":symbol.parent})
                elif symbol:
                    if node.mode in {"UP","DOWN"}: self.require_integer(node.value)
                    elif not value.integral and value!=ERROR: self.diagnostic("INVALID_SET_INDEX", "SET de índice exige inteiro ou índice.",node.value)
                    if symbol.namespace!="index" and symbol.type.category not in {"index","pointer"}:
                        self.diagnostic("INVALID_SET_TARGET", "SET exige índice ou condition-name.",target)
                    self.expr(target,write=True)
        elif isinstance(node,A.Alter):
            for pair in node.pairs:
                source=self.control_ref(pair.source);self.control_ref(pair.target)
                if source:
                    declaration=self.nodes[source.node_id]
                    statements=[n for n in A.walk(declaration) if isinstance(n,A.Statement)]
                    if source.namespace!="paragraph" or len(statements)!=1 or not isinstance(statements[0],A.GoTo):
                        self.diagnostic("INVALID_ALTER_TARGET", "Parágrafo alterável deve conter somente GO TO.",pair.source)
            self.unsupported("ALTER",node)
        elif isinstance(node,A.Sort):
            symbol=self.resolve(node.file,("file",),"sort-file")
            if symbol and not self.r.files[symbol.id]["sort"]: self.diagnostic("SORT_REQUIRES_SD", "SORT exige SD.",node.file)
            for key in node.keys:
                for ref in key.keys: self.expr(ref,whole=True)
            for ref in node.using+node.giving: self.file_ref(ref,"SORT")
            self.unsupported("SORT",node)
        else:
            self.unsupported(type(node).__name__.upper(),node)
        for handler in getattr(node,"handlers",[]): self.statements(handler.body,**context)

    def inspect_pattern(self,pattern):
        if pattern.value: self.expr(pattern.value)
        if pattern.replacement:
            right=self.expr(pattern.replacement)
            if pattern.value:
                left=self.ann(pattern.value).type
                if None not in (left.length,right.length) and left.length!=right.length:
                    self.diagnostic("INSPECT_REPLACEMENT_LENGTH", "Padrão e reposição INSPECT devem ter mesma largura.",pattern)

    def text_target(self,ref):
        typ=self.expr(ref,write=True)
        if not typ.textual and typ!=ERROR: self.diagnostic("TEXT_TARGET_REQUIRED", "Destino deve ser textual/grupo.",ref)
        return typ

    def statements(self,body,**context):
        for node in body: self.statement(node,**context)

    def body(self,body,section=None,paragraph=None):
        for node in body:
            if isinstance(node,A.ProcedureSection): self.body(node.body,self.declarations[id(node)])
            elif isinstance(node,A.Paragraph): self.body(node.sentences,section,self.declarations[id(node)])
            elif isinstance(node,A.Sentence): self.statements(node.statements,section=section,paragraph=paragraph)

    def call(self,node):
        program_type=self.expr(node.program)
        if not program_type.textual and program_type!=ERROR:
            self.diagnostic("INVALID_CALL_TARGET", "Nome de programa deve ser textual.",node.program)
        name=node.program.value.upper() if isinstance(node.program,A.Literal) and node.program.category=="string" else None
        arguments=[]
        for parameter in node.parameters:
            typ=self.expr(parameter.value,whole=True)
            if parameter.mode=="REFERENCE" and not isinstance(parameter.value,(A.Reference,A.Literal)):
                self.diagnostic("CALL_REFERENCE_REQUIRES_DATA", "BY REFERENCE exige dados ou literal em área temporária.",parameter)
            if isinstance(parameter.value,A.Reference):
                symbol=self.table.symbols.get(self.ann(parameter.value).symbol_id)
                if symbol and symbol.namespace not in {"data","special","index"}:
                    self.diagnostic("INVALID_CALL_ARGUMENT", "Argumento não representa armazenamento de dados.",parameter)
            if typ.category=="group" and isinstance(parameter.value,A.Reference):
                self.r.storage_shapes[self.nid(parameter.value)]=self.storage_signature(
                    self.ann(parameter.value).symbol_id,len(parameter.value.subscripts))
            arguments.append({"mode":parameter.mode,"node_id":self.nid(parameter.value),"symbol_id":self.ann(parameter.value).symbol_id,
                              "type":asdict(typ),"length":typ.length,
                              "temporary":isinstance(parameter.value,A.Literal) and parameter.mode!="VALUE"})
        returning_type=self.expr(node.returning,write=True) if node.returning else None
        if returning_type and (not self.compatibility or returning_type.category!="pointer"):
            self.require_integer(node.returning,write=True)
        candidates=self.units.get(name,[]) if name else []
        info={"name":name,"original_name":node.program.value if isinstance(node.program,A.Literal) else None,
              "status":"dynamic" if name is None else "external","arguments":arguments,
              "returning_symbol":self.ann(node.returning).symbol_id if node.returning else None,"callee_program":None}
        if len(candidates)>1:
            self.diagnostic("AMBIGUOUS_PROGRAM", f"Mais de uma definição de {name} entre os fontes fornecidos.",node)
            info["status"]="invalid"
        elif candidates:
            callee=candidates[0]
            info["status"]="resolved"
            info["callee_program"]=callee.root.identification.program_id
            info["callee_file"]=callee.root.span.start.file
            if returning_type and returning_type.category=="pointer":
                self.diagnostic("INVALID_CALL_RETURN_TYPE","Subprograma COBOL deste perfil retorna inteiro.",node.returning)
            formal=callee.r.parameters
            if len(formal)!=len(arguments):
                self.diagnostic("CALL_ARITY", f"CALL {name}: {len(arguments)} argumentos para {len(formal)} parâmetros.",node)
                info["status"]="invalid"
            for argument,param in zip(arguments,formal):
                actual=CobolType(**argument["type"]);expected=CobolType(**param["type"])
                argnode=self.nodes[argument["node_id"]]
                content_copy=self.compatibility and argument["mode"]=="CONTENT" and param["mode"]=="REFERENCE"
                if argument["mode"]!=param["mode"] and not content_copy:
                    self.diagnostic("CALL_MODE_MISMATCH", "Modos de passagem incompatíveis.",argnode);info["status"]="invalid"
                literal_numeric = isinstance(argnode,A.Literal) and actual.numeric and expected.numeric
                by_value_numeric = argument["mode"]=="VALUE" and actual.numeric and expected.numeric
                subscripts = len(argnode.subscripts) if isinstance(argnode,A.Reference) else 0
                group_mismatch = actual.category==expected.category=="group" and self.storage_signature(argument["symbol_id"],subscripts) != callee.storage_signature(param["symbol_id"])
                mismatch = (argument["length"]!=expected.length or (actual.category!="group" and expected.category!="group" and (actual.category,actual.scale,actual.signed,actual.usage)!=(expected.category,expected.scale,expected.signed,expected.usage)))
                if (mismatch and not (literal_numeric or by_value_numeric)) or group_mismatch:
                    self.diagnostic("CALL_LAYOUT_MISMATCH", "Comprimento, categoria, escala ou representação incompatível com parâmetro LINKAGE.",argnode)
                    info["status"]="invalid"
                if literal_numeric:
                    self.validate_initial(argnode,expected)
                info.setdefault("parameter_bindings",[]).append({"actual_symbol":argument["symbol_id"],"formal_symbol":param["symbol_id"],"formal_type":param["type"],"actual_node":argument["node_id"],"mode":argument["mode"]})
        else:
            policy="resolução em execução no perfil gnucobol" if self.compatibility else "assinatura pendente para ligação"
            self.diagnostic("EXTERNAL_CALL_PENDING", f"CALL {name or '(dinâmico)'}: {policy}.",node,"I")
        self.r.calls[self.nid(node)]=info
        self.ann(node).details["call"]=info

    def storage_signature(self, sid, consumed_dimensions=0):
        """ABI estrutural sem nomes: posição, categoria e representação das folhas."""
        layout = self.r.layout.items.get(sid)
        if not layout:
            return None
        base = layout.offset
        result = []
        def visit(symbol):
            if symbol.namespace not in {"data","filler"}:
                return
            item = self.r.layout.items.get(symbol.id)
            if not item or item.redefines and symbol.id != sid:
                return
            if symbol.type.category == "group":
                for child in symbol.children:
                    visit(self.table.symbols[child])
            else:
                typ = symbol.type
                result.append((item.offset-base,item.size,item.total_size,typ.category,typ.precision,
                               typ.scale,typ.signed,typ.usage,typ.representation,
                               [(d.minimum,d.maximum,d.stride) for d in item.dimensions[consumed_dimensions:]]))
        visit(self.table.symbols[sid])
        return result

    def analyze_operations(self,units):
        self.units=units
        if not isinstance(self.root,A.Program): return
        self.bind_files()
        self.body(self.root.procedure.body)
        if self.root.end_program and self.root.end_program.name.upper()!=self.root.identification.program_id.upper():
            self.diagnostic("END_PROGRAM_MISMATCH", "END PROGRAM não corresponde a PROGRAM-ID.",self.root.end_program)
        # Cobertura independente: todo Expr precisa de tipo ou papel declarado.
        # Um novo nó/cláusula não pode tornar-se semanticamente válido por omissão.
        for node in self.nodes.values():
            if isinstance(node,A.Expr) and self.ann(node).type is None:
                if isinstance(node,A.Literal): self.expr(node)
                else:
                    self.diagnostic("UNANALYZED_EXPRESSION", f"Expressão sem vínculo semântico: {type(node).__name__}.",node)
            if isinstance(node,A.Statement) and self.ann(node).role!="statement":
                self.diagnostic("UNANALYZED_STATEMENT", "Comando sem análise semântica.",node)


def analyze(frontend, *, sources=(), strict=False):
    """Analisa um FrontendResult e fontes adicionais já parseados, sem busca implícita."""
    analyzers=[Analyzer(f,strict=strict) for f in (frontend,*sources)]
    units={}
    for analyzer in analyzers:
        analyzer.r.diagnostics.extend(analyzer.r.frontend.diagnostics)
        analyzer.declare()
        analyzer.build_layout()
        if isinstance(analyzer.root,A.Program):
            units.setdefault(analyzer.root.identification.program_id.upper(),[]).append(analyzer)
    for analyzer in analyzers: analyzer.analyze_operations(units)
    # Falha em unidade disponível impede validar como executável o chamador.
    for _ in analyzers:
        changed=False
        for analyzer in analyzers:
            for nid,call in analyzer.r.calls.items():
                if call["status"]=="resolved":
                    callee=units[call["name"]][0]
                    if not callee.r.success:
                        analyzer.diagnostic("INVALID_CALLEE", f"Programa chamado {call['name']} contém erros.",analyzer.nodes[nid])
                        call["status"]="invalid";changed=True
        if not changed: break
    for analyzer in analyzers:
        analyzer.r.source_results = [other.r for other in analyzers if other is not analyzer]
        for other in analyzers:
            if other is not analyzer and not other.r.frontend.success:
                analyzer.r.diagnostics.extend(other.r.frontend.diagnostics)
    # Propagar pendências transitivas sem considerar recursão como erro de ligação.
    for _ in analyzers:
        for analyzer in analyzers:
            for call in analyzer.r.calls.values():
                if call["status"] == "resolved":
                    callee = units[call["name"]][0]
                    pending = sorted({c["name"] or "(dynamic)" for c in callee.r.pending_externals if c is not call})
                    if pending:
                        call["pending_dependencies"] = pending
    primary = analyzers[0].r
    for analyzer in analyzers[1:]:
        for diagnostic in analyzer.r.diagnostics:
            if diagnostic not in primary.diagnostics:
                primary.diagnostics.append(diagnostic)
    return analyzers[0].r


def check_file(path, *, include_dirs=(), source_paths=(), strict=False, debug_lines=False, source_format='fixed', dialect='project'):
    frontend=parse_file(path,include_dirs=include_dirs,debug_lines=debug_lines,source_format=source_format,dialect=dialect)
    sources=[parse_file(p,include_dirs=include_dirs,debug_lines=debug_lines,source_format=source_format,dialect=dialect) for p in source_paths]
    result=analyze(frontend,sources=sources,strict=strict)
    return result


def check_source(source, *, filename="<memory>", include_dirs=(), sources=(), strict=False, source_format='fixed', dialect='project'):
    return analyze(parse_source(source,filename=filename,include_dirs=include_dirs,source_format=source_format,dialect=dialect),sources=sources,strict=strict)
