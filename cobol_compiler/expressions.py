"""Expressões por precedência e condições abreviadas, sem resolver símbolos."""

from . import ast as A


FIGURATIVES = frozenset("ZERO ZEROS ZEROES SPACE SPACES LOW-VALUE LOW-VALUES HIGH-VALUE HIGH-VALUES QUOTE QUOTES TRUE FALSE".split())
RELATIONS = {"=": "=", "EQUAL": "=", "EQUALS": "=", "<": "<", "LESS": "<",
             ">": ">", "GREATER": ">", "<=": "<=", ">=": ">=", "<>": "<>"}
INVERSE = {"=": "<>", "<>": "=", "<": ">=", ">": "<=", "<=": ">", ">=": "<"}
CLASSES = frozenset("NUMERIC ALPHABETIC ALPHABETIC-LOWER ALPHABETIC-UPPER POSITIVE NEGATIVE ZERO".split())


class ExpressionParser:
    def is_reference(self):
        return (self.kind() == "IDENTIFIER" and self.word() not in self.context_words
                and self.word() not in self.usages) or self.at("RETURN-CODE", "SORT-RETURN")

    def reference(self, *, suffixes=True):
        start = self.i
        if not self.is_reference():
            self.fail("identificador")
        name = self.take().value
        qualifiers = []
        subscripts = []
        modification = None
        while self.match("OF", "IN"):
            if not self.is_reference():
                self.fail("qualificador")
            qualifiers.append(self.take().value)
        if suffixes:
            for _ in range(2):
                begin = self.i
                if not self.match("("):
                    break
                first = self.expression()
                if self.match(":"):
                    if modification is not None:
                        self.fail("uma única referência modificada")
                    length = None if self.at(")") else self.expression()
                    self.expect(")")
                    modification = self.node(A.ReferenceModification, begin, start=first, length=length)
                else:
                    if subscripts or modification:
                        self.fail("referência modificada após subscritos")
                    subscripts.append(first)
                    while not self.at(")"):
                        self.match(",")
                        subscripts.append(self.expression())
                    self.expect(")")
        return self.node(A.Reference, start, name=name, qualifiers=qualifiers, subscripts=subscripts, modification=modification)

    def literal(self):
        start = self.i
        all_value = bool(self.match("ALL"))
        if self.kind() in ("NUMBER", "STRING"):
            t = self.take()
            return self.node(A.Literal, start, category=t.kind.lower(), value=t.value, lexeme=t.token.lexeme, all=all_value)
        if self.word() in FIGURATIVES:
            t = self.take()
            return self.node(A.Literal, start, category="figurative", value=t.value, lexeme=t.token.lexeme, all=all_value)
        self.fail("literal numérico, alfanumérico ou constante figurativa")

    def primary(self):
        start = self.i
        if self.match("("):
            value = self.condition()
            self.expect(")")
            return self.node(A.Group, start, expression=value)
        if self.match("FUNCTION"):
            if self.kind() not in ("IDENTIFIER", "KEYWORD"):
                self.fail("nome de função")
            name = self.take().value
            arguments = []
            if self.match("("):
                if not self.at(")"):
                    arguments.append(self.expression())
                    while not self.at(")"):
                        self.match(",")
                        arguments.append(self.expression())
                self.expect(")")
            return self.node(A.FunctionCall, start, name=name, arguments=arguments)
        if self.match("LENGTH"):
            self.expect("OF")
            return self.node(A.LengthOf, start, operand=self.reference())
        if self.kind() in ("NUMBER", "STRING") or self.word() in FIGURATIVES or self.at("ALL"):
            return self.literal()
        return self.reference()

    def expression(self, minimum=0):
        start = self.i
        if self.at("+", "-"):
            op = self.take().value
            left = self.node(A.Unary, start, operator=op, operand=self.expression(25))
        elif self.kind() == "NUMBER" and self.current().token.lexeme.startswith(("+", "-")):
            token = self.take()
            base = self.node(A.Literal, start, category="number", value=token.value[1:], lexeme=token.token.lexeme[1:])
            base = self._expression_tail(base, start, 25)
            left = self.node(A.Unary, start, operator=token.value[0], operand=base)
        else:
            left = self.primary()
        return self._expression_tail(left, start, minimum)

    def _expression_tail(self, left, start, minimum):
        precedences = {"+": 10, "-": 10, "*": 20, "/": 20, "**": 30}
        while True:
            op = self.word()
            signed = self.kind() == "NUMBER" and self.current().token.lexeme.startswith(("+", "-"))
            if signed:
                op = self.current().value[0]
            if op not in precedences or precedences[op] < minimum:
                break
            priority = precedences[op]
            if signed:
                # O lexer preserva sinal adjacente ao literal. Em contexto infixo
                # ele é o operador, sem alterar a API/fluxo de tokens histórico.
                rhs_start = self.i
                token = self.take()
                right = self.node(A.Literal, rhs_start, category="number", value=token.value[1:], lexeme=token.token.lexeme[1:])
                right = self._expression_tail(right, rhs_start, priority + 1)
            else:
                self.take()
                right = self.expression(priority if op == "**" else priority + 1)
            left = self.node(A.Binary, start, operator=op, left=left, right=right)
        return left

    def relation_operator(self):
        self.match("IS", "ARE")
        negated = bool(self.match("NOT"))
        if self.word() not in RELATIONS:
            self.fail("operador relacional")
        word = self.take().value
        op = RELATIONS[word]
        self.match("THAN", "TO")
        if word in ("GREATER", "LESS") and self.match("OR"):
            self.expect("EQUAL")
            self.match("TO")
            op += "="
        return INVERSE[op] if negated else op

    def condition(self, minimum=0, inherited=None):
        start = self.i
        if self.match("NOT"):
            left = self.node(A.Unary, start, operator="NOT", operand=self.condition(30, inherited))
        elif self.word() in RELATIONS or self.at("IS"):
            if inherited is None:
                self.fail("sujeito à esquerda da condição")
            left = self.relative_condition(inherited)
        else:
            left = self.expression()
            relation_start = self.i
            self.match("IS", "ARE")
            negated = bool(self.match("NOT"))
            if self.word() in CLASSES:
                category = self.take().value
                left = self.node(A.ClassCondition, start, operand=left, category=category, negated=negated)
            else:
                self.i = relation_start
                if self.word() in RELATIONS or self.at("IS", "NOT", "ARE"):
                    op = self.relation_operator()
                    right = self.expression()
                    left = self.node(A.Comparison, start, operator=op, left=left, right=right)
                elif inherited is not None:
                    left = self.node(A.AbbreviatedCondition, start, operator=inherited.operator,
                                     right=left, inherited_subject=inherited.left.span)
        context = left if isinstance(left, A.Comparison) else inherited
        while self.at("AND", "OR"):
            priority = 20 if self.at("AND") else 10
            if priority < minimum:
                break
            op = self.take().value
            right = self.condition(priority + 1, context)
            left = self.node(A.Binary, start, operator=op, left=left, right=right)
        return left

    def relative_condition(self, inherited=None):
        start = self.i
        saved = self.i
        self.match("IS")
        negated = bool(self.match("NOT"))
        if self.word() in CLASSES:
            category = self.take().value
            return self.node(A.ClassCondition, start, operand=None, category=category, negated=negated)
        self.i = saved
        op = self.relation_operator()
        return self.node(A.AbbreviatedCondition, start, operator=op, right=self.expression(),
                         inherited_subject=inherited.left.span if inherited is not None else None)
