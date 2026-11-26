"""Reconhecimento de comandos. Delimitadores de blocos nunca são descartados."""

from . import ast as A


class StatementParser:
    statement_methods = {
        "MOVE": "move", "INITIALIZE": "initialize", "DISPLAY": "display",
        "ACCEPT": "accept", "COMPUTE": "arithmetic", "ADD": "arithmetic",
        "SUBTRACT": "arithmetic", "MULTIPLY": "arithmetic", "DIVIDE": "arithmetic",
        "IF": "if_statement", "EVALUATE": "evaluate", "PERFORM": "perform",
        "GO": "go_to", "EXIT": "exit_statement", "CONTINUE": "simple",
        "STOP": "simple", "GOBACK": "simple", "NEXT": "simple",
        "OPEN": "open_statement", "CLOSE": "close_statement", "READ": "read",
        "WRITE": "write", "START": "start_statement", "CALL": "call",
        "INSPECT": "inspect", "STRING": "string", "UNSTRING": "unstring",
        "SEARCH": "search", "SET": "set_statement", "ALTER": "alter", "SORT": "sort",
    }

    def statement(self):
        if self.at("EXEC"):
            self.fail("comando do subconjunto COBOL", code="UNSUPPORTED_EXEC",
                      message="EXEC SQL/CICS exige uma gramática de extensão ainda não implementada.")
        if self.at("REWRITE", "DELETE", "MERGE", "RELEASE", "CANCEL"):
            self.fail("comando implementado", code="UNSUPPORTED_STATEMENT",
                      message="Comando COBOL conhecido ainda não implementado pelo parser.")
        method = self.statement_methods.get(self.word())
        if method is None:
            self.fail("comando COBOL reconhecido", code="UNEXPECTED_STATEMENT")
        return getattr(self, method)()

    def block(self, stops):
        if not hasattr(self, "boundaries"):
            self.boundaries = []
        self.boundaries.append(stops)
        result = []
        try:
            while self.current() and not self.at(".") and not self.header():
                if any(self.sequence(*stop) for group in self.boundaries for stop in group):
                    break
                result.append(self.statement())
        finally:
            self.boundaries.pop()
        return result

    def references(self, *, required=True):
        refs = []
        while self.is_reference():
            refs.append(self.reference())
            self.match(",")
        if required and not refs:
            self.fail("identificador de destino")
        return refs

    def operands(self, *, required=True):
        values = []
        while self.is_operand():
            values.append(self.primary())
            self.match(",")
        if required and not values:
            self.fail("operando")
        return values

    def is_operand(self):
        return self.is_reference() or self.kind() in ("NUMBER", "STRING") or self.word() in self.figuratives or self.at("FUNCTION", "LENGTH", "(", "+", "-", "ALL")

    def move(self):
        start = self.i; self.expect("MOVE"); corresponding = bool(self.match("CORR", "CORRESPONDING"))
        source = self.primary(); self.expect("TO"); targets = self.references()
        return self.node(A.Move, start, source=source, targets=targets, corresponding=corresponding)

    def initialize(self):
        start = self.i; self.expect("INITIALIZE"); targets = self.references(); replacements = []
        if self.match("REPLACING"):
            while self.at("ALPHANUMERIC", "NUMERIC", "ALPHABETIC", "NUMERIC-EDITED", "ALPHANUMERIC-EDITED"):
                begin = self.i; category = self.take().value; self.expect("BY")
                value = self.primary()
                replacements.append(self.node(A.InitializeReplacement, begin, category=category, value=value))
            if not replacements:
                self.fail("categoria e BY na cláusula REPLACING")
        self.match("END-INITIALIZE")
        return self.node(A.Initialize, start, targets=targets, replacements=replacements)

    def screen_position(self):
        start = self.i
        if not self.at("LINE", "COLUMN"):
            self.fail("LINE ou COLUMN")
        axis = self.take().value; self.match("NUMBER"); self.match("IS")
        return self.node(A.ScreenPosition, start, axis=axis, value=self.expression())

    def display(self):
        start = self.i; self.expect("DISPLAY"); operands = []; no_advancing = False; upon = None
        while True:
            if self.is_operand():
                operands.append(self.primary()); self.match(",")
            elif self.match("AT"):
                if not self.at("LINE", "COLUMN"):
                    self.fail("LINE ou COLUMN após AT")
                while self.at("LINE", "COLUMN"):
                    operands.append(self.screen_position())
            elif self.at("LINE", "COLUMN"):
                operands.append(self.screen_position())
            elif self.match("WITH"):
                if no_advancing:
                    self.fail("cláusula WITH NO ADVANCING não repetida")
                self.expect("NO"); self.expect("ADVANCING"); no_advancing = True
            elif self.match("UPON"):
                if upon is not None:
                    self.fail("cláusula UPON não repetida")
                if self.kind() not in ("IDENTIFIER", "KEYWORD"):
                    self.fail("dispositivo de saída")
                upon = self.take().value
            else:
                break
        if not any(isinstance(x, A.Expr) for x in operands):
            self.fail("operando de DISPLAY")
        self.match("END-DISPLAY")
        return self.node(A.Display, start, operands=operands, no_advancing=no_advancing, upon=upon)

    def accept(self):
        start = self.i; self.expect("ACCEPT"); target = self.reference(); source = None; date_format = None; positions = []
        if self.match("FROM"):
            if not self.at("DATE", "DAY", "DAY-OF-WEEK", "TIME", "CONSOLE", "COMMAND-LINE", "ARGUMENT-VALUE", "ENVIRONMENT-VALUE"):
                self.fail("fonte de ACCEPT suportada", code="UNSUPPORTED_ACCEPT_SOURCE")
            source = self.take().value
            if self.at("YYYYMMDD", "YYYYDDD"):
                date_format = self.take().value
        if self.match("AT"):
            while self.at("LINE", "COLUMN"):
                positions.append(self.screen_position())
            if not positions:
                self.fail("posição LINE/COLUMN")
        self.match("END-ACCEPT")
        return self.node(A.Accept, start, target=target, source=source, date_format=date_format, positions=positions)

    def arithmetic_targets(self):
        result = []
        while self.is_reference():
            start = self.i; target = self.reference(); rounded = bool(self.match("ROUNDED"))
            result.append(self.node(A.ArithmeticTarget, start, target=target, rounded=rounded)); self.match(",")
        if not result:
            self.fail("destino aritmético")
        return result

    def handlers(self, allowed, end_word):
        handlers = []; seen = set()
        starts = [("AT", "END"), ("NOT", "AT", "END"), ("INVALID", "KEY"), ("NOT", "INVALID", "KEY"),
                  ("ON", "SIZE", "ERROR"), ("SIZE", "ERROR"), ("NOT", "SIZE", "ERROR"), ("NOT", "ON", "SIZE", "ERROR"),
                  ("ON", "OVERFLOW"), ("NOT", "ON", "OVERFLOW"), ("ON", "EXCEPTION"), ("NOT", "ON", "EXCEPTION")]
        while True:
            phrase = next((p for p in starts if self.sequence(*p)), None)
            if phrase is None:
                break
            begin = self.i
            negated = phrase[0] == "NOT"
            event = " ".join(v for v in phrase if v not in ("NOT", "ON", "AT"))
            if event not in allowed:
                self.fail("tratador permitido neste comando")
            if (event, negated) in seen:
                self.fail("tratador não duplicado")
            seen.add((event, negated))
            for _ in phrase:
                self.take()
            body = self.block(starts + [(end_word,)])
            if not body:
                self.fail("comando no tratador")
            handlers.append(self.node(A.Handler, begin, event=event, negated=negated, body=body))
        return handlers

    def arithmetic(self):
        start = self.i; operation = self.take().value
        corresponding = operation in ("ADD", "SUBTRACT") and bool(self.match("CORR", "CORRESPONDING"))
        sources = []; targets = []; giving = []; remainder = None; form = operation
        if operation == "COMPUTE":
            targets = self.arithmetic_targets(); self.expect("="); sources = [self.expression()]
        elif operation in ("ADD", "SUBTRACT"):
            sources = self.operands(); form = "TO" if operation == "ADD" else "FROM"
            if self.match(form):
                targets = self.arithmetic_targets()
            elif operation == "SUBTRACT" or not self.at("GIVING"):
                self.fail(form + " ou GIVING")
        elif operation == "MULTIPLY":
            sources = [self.primary()]; self.expect("BY"); form = "BY"
            if self.is_reference():
                targets = self.arithmetic_targets()
            else:
                sources.append(self.primary())
        else:
            sources = [self.primary()]
            if not self.at("INTO", "BY"):
                self.fail("INTO ou BY")
            form = self.take().value
            # A forma BY admite um divisor literal; INTO requer receptor.
            if form == "BY":
                sources.append(self.primary())
            else:
                if self.is_reference():
                    targets = self.arithmetic_targets()
                else:
                    sources.append(self.primary())
        if operation != "COMPUTE" and self.match("GIVING"):
            giving = self.arithmetic_targets()
        if operation == "DIVIDE" and form == "BY" and not giving:
            self.fail("GIVING após DIVIDE BY")
        if operation in ("MULTIPLY", "DIVIDE") and len(sources) > 1 and not giving:
            self.fail("GIVING quando ambos os operandos são de entrada")
        if operation in ("MULTIPLY", "DIVIDE") and giving and len(targets) > 1:
            self.fail("um único segundo operando na forma GIVING")
        if self.match("REMAINDER"):
            if operation != "DIVIDE" or not giving:
                self.fail("REMAINDER somente em DIVIDE com GIVING")
            remainder = self.reference()
        end_word = "END-" + operation
        handlers = self.handlers({"SIZE ERROR"}, end_word)
        explicit = bool(self.match(end_word))
        return self.node(A.Arithmetic, start, operation=operation, sources=sources, targets=targets,
                         giving=giving, remainder=remainder, corresponding=corresponding, form=form,
                         handlers=handlers, explicit_end=explicit)

    def if_statement(self):
        start = self.i; self.expect("IF"); condition = self.condition(); self.match("THEN")
        then_body = self.block([("ELSE",), ("END-IF",)])
        if not then_body:
            self.fail("comando após IF")
        else_body = []
        if self.match("ELSE"):
            else_body = self.block([("END-IF",)])
            if not else_body:
                self.fail("comando após ELSE")
        explicit = bool(self.match("END-IF"))
        return self.node(A.If, start, condition=condition, then_body=then_body, else_body=else_body, explicit_end=explicit)

    def selection(self):
        start = self.i
        if self.match("ANY"):
            return self.node(A.Selection, start, kind="any", value=None, upper=None)
        if self.at("IS", "LESS", "GREATER", "EQUAL", "<", ">", "<=", ">=", "=", "<>"):
            value = self.relative_condition()
        else:
            value = self.condition()
        upper = self.expression() if self.match("THRU", "THROUGH") else None
        return self.node(A.Selection, start, kind="range" if upper is not None else "test", value=value, upper=upper)

    def evaluate(self):
        start = self.i; self.expect("EVALUATE"); subjects = [self.condition()]
        while self.match("ALSO"):
            subjects.append(self.condition())
        cases = []; had_other = False
        while self.at("WHEN"):
            if had_other:
                self.fail("END-EVALUATE ou ponto após WHEN OTHER")
            begin = self.i; alternatives = []; other = False
            while self.match("WHEN"):
                if self.match("OTHER"):
                    other = True; had_other = True
                    if alternatives:
                        self.fail("WHEN OTHER separado")
                    break
                selections = [self.selection()]
                while self.match("ALSO"):
                    selections.append(self.selection())
                if len(selections) != len(subjects):
                    self.fail("um seletor WHEN para cada sujeito EVALUATE")
                alternatives.append(selections)
            body = self.block([("WHEN",), ("END-EVALUATE",)])
            if not body:
                self.fail("comando após WHEN")
            cases.append(self.node(A.When, begin, alternatives=alternatives, body=body, other=other))
        if not cases:
            self.fail("WHEN")
        explicit = bool(self.match("END-EVALUATE"))
        return self.node(A.Evaluate, start, subjects=subjects, cases=cases, explicit_end=explicit)

    def perform(self):
        start = self.i; self.expect("PERFORM"); target = None; through = None; times = None; until = None; varying = []; test = "BEFORE"
        if self.is_reference() and self.word(1) != "TIMES":
            target = self.reference(suffixes=False)
            if self.match("THRU", "THROUGH"):
                through = self.reference(suffixes=False)
        if self.match("WITH") or self.at("TEST"):
            self.expect("TEST")
            if not self.at("BEFORE", "AFTER"):
                self.fail("BEFORE ou AFTER")
            test = self.take().value
        if self.match("UNTIL"):
            until = self.condition()
        elif self.match("VARYING"):
            while True:
                begin = self.i; variable = self.reference(); self.expect("FROM"); initial = self.expression()
                self.expect("BY"); step = self.expression(); self.expect("UNTIL"); cond = self.condition()
                varying.append(self.node(A.Varying, begin, target=variable, initial=initial, step=step, until=cond))
                if not self.match("AFTER"):
                    break
        elif self.is_operand() and self.word() not in self.statement_methods:
            times = self.expression(); self.expect("TIMES")
        body = []; explicit = False
        if target is None:
            body = self.block([("END-PERFORM",)])
            if not body:
                self.fail("comando no PERFORM inline")
            self.expect("END-PERFORM"); explicit = True
        return self.node(A.Perform, start, target=target, through=through, times=times, until=until,
                         varying=varying, test=test, body=body, explicit_end=explicit)

    def go_to(self):
        start = self.i; self.expect("GO"); self.match("TO"); targets = self.references(); depending = None
        if self.match("DEPENDING"):
            self.match("ON"); depending = self.reference()
        if len(targets) > 1 and depending is None:
            self.fail("DEPENDING ON após lista de destinos GO TO")
        return self.node(A.GoTo, start, targets=targets, depending=depending)

    def exit_statement(self):
        start = self.i; self.expect("EXIT"); scope = None
        if self.at("PERFORM", "PARAGRAPH", "SECTION", "PROGRAM"):
            scope = self.take().value
        returning = self.expression() if scope=="PROGRAM" and self.match("RETURNING", "GIVING") else None
        return self.node(A.Exit, start, scope=scope, returning=returning)

    def simple(self):
        start = self.i; op = self.take().value
        if op == "STOP":
            self.expect("RUN"); cls = A.StopRun
        elif op == "NEXT":
            self.expect("SENTENCE"); cls = A.NextSentence
        else:
            cls = A.Continue if op == "CONTINUE" else A.Goback
        if cls is A.Goback and self.match("RETURNING", "GIVING"):
            return self.node(A.Goback, start, returning=self.expression())
        return self.node(cls, start)

    def open_statement(self):
        start = self.i; self.expect("OPEN"); groups = []
        while self.at("INPUT", "OUTPUT", "I-O", "EXTEND"):
            begin = self.i; mode = self.take().value; refs = self.references()
            groups.append(self.node(A.OpenGroup, begin, mode=mode, files=refs))
        if not groups:
            self.fail("INPUT, OUTPUT, I-O ou EXTEND")
        return self.node(A.Open, start, groups=groups)

    def close_statement(self):
        start = self.i; self.expect("CLOSE")
        return self.node(A.Close, start, files=self.references())

    def read(self):
        start = self.i; self.expect("READ"); file = self.reference(); next_record = bool(self.match("NEXT"))
        self.match("RECORD"); into = self.reference() if self.match("INTO") else None; key = None
        if self.match("KEY"):
            self.match("IS"); key = self.reference()
        handlers = self.handlers({"END", "INVALID KEY"}, "END-READ")
        explicit = bool(self.match("END-READ"))
        return self.node(A.Read, start, file=file, into=into, next_record=next_record, key=key, handlers=handlers, explicit_end=explicit)

    def write(self):
        start = self.i; self.expect("WRITE"); record = self.reference()
        source = self.primary() if self.match("FROM") else None; timing = None; advancing = None
        if self.at("BEFORE", "AFTER"):
            timing = self.take().value; self.expect("ADVANCING"); advancing = self.primary(); self.match("LINE", "LINES")
        handlers = self.handlers({"INVALID KEY"}, "END-WRITE")
        explicit = bool(self.match("END-WRITE"))
        return self.node(A.Write, start, record=record, source=source, timing=timing, advancing=advancing, handlers=handlers, explicit_end=explicit)

    def start_statement(self):
        start = self.i; self.expect("START"); file = self.reference(); self.expect("KEY")
        op_start = self.i; op = self.relation_operator(); right = self.expression()
        condition = self.node(A.AbbreviatedCondition, op_start, operator=op, right=right, inherited_subject=None)
        handlers = self.handlers({"INVALID KEY"}, "END-START"); explicit = bool(self.match("END-START"))
        return self.node(A.Start, start, file=file, condition=condition, handlers=handlers, explicit_end=explicit)

    def parameters(self):
        result = []; mode = "REFERENCE"
        while self.at("BY") or self.is_operand():
            begin = self.i
            if self.match("BY"):
                if not self.at("REFERENCE", "VALUE", "CONTENT"):
                    self.fail("REFERENCE, VALUE ou CONTENT")
                mode = self.take().value
            value = self.primary()
            result.append(self.node(A.CallParameter, begin, mode=mode, value=value)); self.match(",")
        if not result:
            self.fail("parâmetro após USING")
        return result

    def call(self):
        start = self.i; self.expect("CALL"); program = self.primary()
        parameters = self.parameters() if self.match("USING") else []
        returning = self.reference() if self.match("RETURNING", "GIVING") else None
        handlers = self.handlers({"EXCEPTION"}, "END-CALL"); explicit = bool(self.match("END-CALL"))
        return self.node(A.Call, start, program=program, parameters=parameters, returning=returning, handlers=handlers, explicit_end=explicit)

    def inspect_pattern(self, *, replacing=False):
        start = self.i
        if not self.at("ALL", "LEADING", "FIRST", "CHARACTERS", "TRAILING"):
            self.fail("ALL, LEADING, FIRST, TRAILING ou CHARACTERS")
        mode = self.take().value
        value = None if mode == "CHARACTERS" else self.primary()
        replacement = None
        if replacing:
            self.expect("BY"); replacement = self.primary()
        return self.node(A.InspectPattern, start, mode=mode, value=value, replacement=replacement)

    def inspect(self):
        start = self.i; self.expect("INSPECT"); subject = self.primary(); tallies = []; replacements = []; converting = None
        if self.match("TALLYING"):
            while self.is_reference():
                begin = self.i; counter = self.reference(); self.expect("FOR"); patterns = [self.inspect_pattern()]
                while self.at("ALL", "LEADING", "FIRST", "CHARACTERS", "TRAILING"):
                    patterns.append(self.inspect_pattern())
                tallies.append(self.node(A.InspectTally, begin, counter=counter, patterns=patterns))
            if not tallies:
                self.fail("contador e FOR em INSPECT TALLYING")
        if self.match("REPLACING"):
            replacements.append(self.inspect_pattern(replacing=True))
            while self.at("ALL", "LEADING", "FIRST", "CHARACTERS", "TRAILING"):
                replacements.append(self.inspect_pattern(replacing=True))
        if self.match("CONVERTING"):
            if tallies or replacements:
                self.fail("CONVERTING separado de TALLYING/REPLACING")
            first = self.primary(); self.expect("TO"); converting = (first, self.primary())
        if not tallies and not replacements and converting is None:
            self.fail("TALLYING, REPLACING ou CONVERTING")
        return self.node(A.Inspect, start, subject=subject, tallies=tallies, replacements=replacements, converting=converting)

    def delimiter(self):
        start = self.i; all_value = bool(self.match("ALL")); size = bool(self.match("SIZE"))
        value = None if size else self.primary()
        return self.node(A.Delimiter, start, value=value, all=all_value, size=size)

    def string(self):
        start = self.i; self.expect("STRING"); parts = []
        while not self.at("INTO"):
            begin = self.i; values = self.operands(); self.expect("DELIMITED"); self.match("BY")
            delimiter = self.delimiter(); parts.append(self.node(A.StringPart, begin, values=values, delimiter=delimiter))
        if not parts:
            self.fail("origem e DELIMITED antes de INTO")
        self.expect("INTO"); target = self.reference(); pointer = None
        if self.match("WITH"):
            self.expect("POINTER"); pointer = self.reference()
        handlers = self.handlers({"OVERFLOW"}, "END-STRING"); explicit = bool(self.match("END-STRING"))
        return self.node(A.String, start, parts=parts, target=target, pointer=pointer, handlers=handlers, explicit_end=explicit)

    def unstring(self):
        start = self.i; self.expect("UNSTRING"); source = self.primary(); delimiters = []; targets = []
        if self.match("DELIMITED"):
            self.match("BY"); delimiters.append(self.delimiter())
            while self.match("OR"):
                delimiters.append(self.delimiter())
        self.expect("INTO")
        while self.is_reference():
            begin = self.i; target = self.reference(); delimiter_in = None; count_in = None
            if self.match("DELIMITER"):
                self.expect("IN"); delimiter_in = self.reference()
            if self.match("COUNT"):
                self.expect("IN"); count_in = self.reference()
            targets.append(self.node(A.UnstringTarget, begin, target=target, delimiter_in=delimiter_in, count_in=count_in)); self.match(",")
        if not targets:
            self.fail("receptor de UNSTRING")
        pointer = None; tallying = None
        if self.match("WITH"):
            self.expect("POINTER"); pointer = self.reference()
        if self.match("TALLYING"):
            self.match("IN"); tallying = self.reference()
        handlers = self.handlers({"OVERFLOW"}, "END-UNSTRING"); explicit = bool(self.match("END-UNSTRING"))
        return self.node(A.Unstring, start, source=source, delimiters=delimiters, targets=targets,
                         pointer=pointer, tallying=tallying, handlers=handlers, explicit_end=explicit)

    def search(self):
        start = self.i; self.expect("SEARCH"); all_value = bool(self.match("ALL")); table = self.reference()
        varying = self.reference() if self.match("VARYING") else None; at_end = []; cases = []
        if self.match("AT"):
            self.expect("END"); at_end = self.block([("WHEN",), ("END-SEARCH",)])
        while self.match("WHEN"):
            begin = self.i - 1; condition = self.condition(); body = self.block([("WHEN",), ("END-SEARCH",)])
            if not body:
                self.fail("comando após SEARCH WHEN")
            cases.append(self.node(A.SearchWhen, begin, condition=condition, body=body))
        if not cases:
            self.fail("WHEN em SEARCH")
        explicit = bool(self.match("END-SEARCH"))
        return self.node(A.Search, start, table=table, all=all_value, varying=varying, at_end=at_end, cases=cases, explicit_end=explicit)

    def set_statement(self):
        start = self.i; self.expect("SET"); targets = self.references()
        if not self.at("TO", "UP", "DOWN"):
            self.fail("TO, UP BY ou DOWN BY")
        mode = self.take().value
        if mode != "TO":
            self.expect("BY")
        return self.node(A.Set, start, targets=targets, mode=mode, value=self.primary())

    def alter(self):
        start = self.i; self.expect("ALTER"); pairs = []
        while self.is_reference():
            begin = self.i; source = self.reference(suffixes=False); self.expect("TO"); self.expect("PROCEED"); self.expect("TO")
            target = self.reference(suffixes=False)
            pairs.append(self.node(A.AlterPair, begin, source=source, target=target))
        if not pairs:
            self.fail("parágrafo TO PROCEED TO parágrafo")
        return self.node(A.Alter, start, pairs=pairs)

    def sort(self):
        start = self.i; self.expect("SORT"); file = self.reference(); keys = []
        while self.at("ON", "ASCENDING", "DESCENDING"):
            begin = self.i; self.match("ON")
            if not self.at("ASCENDING", "DESCENDING"):
                self.fail("ASCENDING ou DESCENDING")
            role = self.take().value; self.match("KEY"); self.match("IS")
            keys.append(self.node(A.KeyClause, begin, role=role, keys=self.references()))
        self.expect("USING"); using = self.references(); self.expect("GIVING"); giving = self.references()
        return self.node(A.Sort, start, file=file, keys=keys, using=using, giving=giving)
