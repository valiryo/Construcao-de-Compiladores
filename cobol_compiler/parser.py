"""Parser descendente recursivo, com sincronização por sentenças/declarações."""

from dataclasses import dataclass, field

from . import ast as A
from .diagnostics import Diagnostic
from .expressions import ExpressionParser
from .source import SourceLocation, SourceSpan
from .statements import StatementParser
from .validation import validate_ast


class ParseError(Exception):
    """Transferência interna para o ponto de recuperação mais próximo."""


@dataclass(slots=True)
class ParseResult:
    ast: A.Program | A.DataFragment | None
    diagnostics: list[Diagnostic]
    consumed_tokens: int
    token_count: int
    skipped_tokens: int = 0
    structural_errors: list[str] = field(default_factory=list)
    partial_ast: A.Program | A.DataFragment | None = None

    @property
    def success(self):
        return self.ast is not None and not self.diagnostics and not self.structural_errors and self.consumed_tokens == self.token_count and not self.skipped_tokens


class Parser(ExpressionParser, StatementParser):
    # Palavras contextuais ausentes da tabela reservada histórica do lexer.
    context_words = frozenset("""
        IN ALSO ANY END-WRITE END-UNSTRING END-STRING END-CALL END-COMPUTE
        END-ADD END-SUBTRACT END-MULTIPLY END-DIVIDE END-START END-ACCEPT
        END-DISPLAY END-INITIALIZE USAGE COMP-3 COMP-5 BINARY DISPLAY-1
        PACKED-DECIMAL POINTER RETURNING DEPENDING THRU THROUGH TEST
        OPTIONAL DESCENDING DELIMITER OVERFLOW UP DOWN NEXT SENTENCE
        UPON CONTENT PARAGRAPH DEBUGGING SOURCE-COMPUTER OBJECT-COMPUTER
    """.split())
    data_sections = frozenset("FILE WORKING-STORAGE LOCAL-STORAGE LINKAGE SCREEN".split())
    usages = frozenset("DISPLAY COMP COMP-1 COMP-2 COMP-3 COMP-4 COMP-5 COMPUTATIONAL BINARY PACKED-DECIMAL INDEX POINTER".split())

    def __init__(self, tokens, *, root_file="<memory>"):
        self.tokens = tokens
        self.root_file = root_file
        self.i = 0
        self.diagnostics = []
        self.skipped = 0

    def current(self, offset=0):
        index = self.i + offset
        return self.tokens[index] if 0 <= index < len(self.tokens) else None

    def kind(self, offset=0):
        token = self.current(offset)
        return token.kind if token else "EOF"

    def word(self, offset=0):
        token = self.current(offset)
        return token.value if token and token.kind not in ("STRING", "NUMBER", "PICTURE") else "<" + self.kind(offset) + ">"

    def at(self, *words):
        return self.word() in words

    def sequence(self, *words):
        return all(self.word(i) == word for i, word in enumerate(words))

    def take(self):
        token = self.current()
        if token is None:
            self.fail("token")
        self.i += 1
        return token

    def match(self, *words):
        if self.at(*words):
            return self.take()
        return None

    def expect(self, word):
        if not self.at(word):
            self.fail(word)
        return self.take()

    def eof_span(self):
        if self.tokens:
            end = self.tokens[-1].span.end
            p = SourceLocation(end.file, end.line, end.column + 1, end.inclusion_stack)
        else:
            p = SourceLocation(self.root_file, 1, 1)
        return SourceSpan(p, p)

    def fail(self, expected, *, code="SYNTAX_ERROR", message="Construção sintática inesperada."):
        token = self.current()
        self.diagnostics.append(Diagnostic(code, message, token.span if token else self.eof_span(), "parser", expected,
                                           repr(token.token.lexeme) if token else "EOF"))
        raise ParseError

    def node(self, cls, begin, **attributes):
        if self.i <= begin:
            raise AssertionError(f"Nó vazio: {cls.__name__}")
        return cls(span=SourceSpan(self.tokens[begin].span.start, self.tokens[self.i - 1].span.end),
                   token_start=begin, token_end=self.i, **attributes)

    def extend(self, node):
        node.token_end = self.i
        node.span = SourceSpan(node.span.start, self.tokens[self.i - 1].span.end)

    def area_a(self):
        if self.current() and self.current().token.area != "A":
            self.fail("cabeçalho na área A (colunas 8–11)", code="INVALID_HEADER_AREA")

    def header(self):
        return self.kind() == "IDENTIFIER" and self.current().token.area == "A" and (
            self.word(1) == "." or self.word(1) == "SECTION"
        )

    def recover(self, begin, *, declaration=False):
        if begin < len(self.tokens) and self.tokens[begin].value == "EXEC":
            while self.current() and not self.at("END-EXEC"):
                self.take(); self.skipped += 1
            if self.match("END-EXEC"):
                self.skipped += 1
            if self.match("."):
                self.skipped += 1
            return
        while self.current():
            if self.at("."):
                self.take(); self.skipped += 1
                return
            if self.i > begin and (self.header() or self.at("PROCEDURE", "ENVIRONMENT", "DATA", "IDENTIFICATION")
                                   or declaration and self.declaration_start()):
                return
            self.take(); self.skipped += 1

    def declaration_start(self):
        return self.kind() == "NUMBER" and (self.i == 0 or
            self.tokens[self.i - 1].span.end.file != self.current().span.start.file or
            self.tokens[self.i - 1].span.end.line != self.current().span.start.line)

    def parse(self, *, copybook=False):
        root = None
        try:
            if copybook:
                entries = self.data_entries()
                if not entries:
                    self.fail("declaração de dados no copybook")
                root = self.node(A.DataFragment, 0, entries=entries)
            else:
                root = self.program()
            if self.current():
                self.fail("fim do arquivo", code="TRAILING_TOKENS")
        except ParseError:
            self.recover(self.i)
            while self.current():
                self.recover(self.i)
        except RecursionError:
            token = self.current()
            self.diagnostics.append(Diagnostic("PARSER_DEPTH", "Aninhamento excede a capacidade do parser.",
                                               token.span if token else self.eof_span(), "parser"))
        structural = validate_ast(root, self.tokens).errors if root is not None and not self.diagnostics else []
        valid = not self.diagnostics and not structural and self.i == len(self.tokens) and not self.skipped
        return ParseResult(root if valid else None, self.diagnostics, self.i, len(self.tokens), self.skipped,
                           structural, root if not valid else None)

    def program(self):
        start = self.i
        self.area_a()
        self.expect("IDENTIFICATION"); self.expect("DIVISION"); self.expect(".")
        self.area_a()
        self.expect("PROGRAM-ID"); self.expect(".")
        if self.kind() not in ("IDENTIFIER", "STRING"):
            self.fail("nome do programa")
        name = self.take().value
        self.expect(".")
        metadata = []
        while self.at("AUTHOR", "INSTALLATION", "DATE-WRITTEN", "DATE-COMPILED", "SECURITY", "REMARKS"):
            begin = self.i; key = self.take().value; self.expect(".")
            words = []
            while self.current() and not self.at("."):
                words.append(self.take().token.lexeme)
            self.expect(".")
            metadata.append(self.node(A.MetadataParagraph, begin, name=key, words=words))
        identification = self.node(A.IdentificationDivision, start, program_id=name, metadata=metadata)
        environment = self.environment() if self.at("ENVIRONMENT") else None
        data = self.data() if self.at("DATA") else None
        procedure = self.procedure()
        end_program = None
        if self.match("END"):
            begin = self.i - 1
            self.expect("PROGRAM")
            if self.kind() != "IDENTIFIER":
                self.fail("nome do programa após END PROGRAM")
            end_name = self.take().value; self.expect(".")
            end_program = self.node(A.EndProgram, begin, name=end_name)
        return self.node(A.Program, start, identification=identification, environment=environment,
                         data=data, procedure=procedure, end_program=end_program)

    def environment(self):
        start = self.i; self.area_a()
        self.expect("ENVIRONMENT"); self.expect("DIVISION"); self.expect(".")
        sections = []
        while self.at("CONFIGURATION", "INPUT-OUTPUT"):
            begin = self.i; self.area_a(); name = self.take().value
            self.expect("SECTION"); self.expect("."); entries = []
            while self.current() and not self.at("DATA", "PROCEDURE", "CONFIGURATION", "INPUT-OUTPUT"):
                entry_start = self.i
                try:
                    if self.match("SPECIAL-NAMES"):
                        self.expect(".")
                        while not self.at("."):
                            s = self.i
                            if self.match("DECIMAL-POINT"):
                                self.expect("IS"); self.expect("COMMA")
                                value = self.node(A.Literal, self.i - 1, category="setting", value="COMMA", lexeme="COMMA")
                                entries.append(self.node(A.SpecialName, s, setting="DECIMAL-POINT", value=value))
                            elif self.match("CURSOR"):
                                self.match("IS")
                                entries.append(self.node(A.SpecialName, s, setting="CURSOR", value=self.reference()))
                            elif self.match("CRT"):
                                self.expect("STATUS"); self.match("IS")
                                entries.append(self.node(A.SpecialName, s, setting="CRT STATUS", value=self.reference()))
                            else:
                                self.fail("DECIMAL-POINT, CURSOR ou CRT STATUS", code="UNSUPPORTED_SPECIAL_NAME")
                        self.expect(".")
                    elif self.match("FILE-CONTROL"):
                        self.expect(".")
                    elif self.at("SELECT"):
                        entries.append(self.file_control())
                    elif self.at("SOURCE-COMPUTER", "OBJECT-COMPUTER"):
                        s = self.i; role = self.take().value; self.expect(".")
                        if self.kind() not in ("IDENTIFIER", "KEYWORD"):
                            self.fail("nome de computador")
                        computer = self.take().value; debug = False
                        if self.match("WITH"):
                            self.expect("DEBUGGING"); self.expect("MODE"); debug = True
                        self.expect(".")
                        entries.append(self.node(A.ComputerClause, s, role=role, name=computer, debugging=debug))
                    else:
                        self.fail("cláusula de configuração ou SELECT")
                except ParseError:
                    self.recover(entry_start)
            sections.append(self.node(A.EnvironmentSection, begin, name=name, entries=entries))
        return self.node(A.EnvironmentDivision, start, sections=sections)

    def file_control(self):
        start = self.i; self.expect("SELECT"); optional = bool(self.match("OPTIONAL"))
        name = self.reference(suffixes=False); clauses = []
        while not self.at("."):
            begin = self.i
            if self.match("ASSIGN"):
                self.match("TO")
                clauses.append(self.node(A.AssignClause, begin, target=self.primary()))
            elif self.match("ORGANIZATION"):
                self.match("IS"); organization = ""
                if self.match("LINE"):
                    organization = "LINE "
                if not self.at("SEQUENTIAL", "INDEXED", "RELATIVE"):
                    self.fail("organização de arquivo")
                organization += self.take().value
                clauses.append(self.node(A.OrganizationClause, begin, organization=organization))
            elif self.match("ACCESS"):
                self.expect("MODE"); self.match("IS")
                if not self.at("SEQUENTIAL", "DYNAMIC", "RANDOM"):
                    self.fail("modo de acesso")
                clauses.append(self.node(A.AccessClause, begin, mode=self.take().value))
            elif self.at("RECORD", "ALTERNATE"):
                alternate = bool(self.match("ALTERNATE")); self.expect("RECORD"); self.expect("KEY"); self.match("IS")
                key = self.reference(suffixes=False); duplicates = False
                if self.match("WITH"):
                    self.expect("DUPLICATES"); duplicates = True
                clauses.append(self.node(A.KeyClause, begin, role="ALTERNATE" if alternate else "RECORD", keys=[key], duplicates=duplicates))
            elif self.match("FILE"):
                self.expect("STATUS"); self.match("IS")
                clauses.append(self.node(A.FileStatusClause, begin, target=self.reference(suffixes=False)))
            else:
                self.fail("ASSIGN, ORGANIZATION, ACCESS, RECORD KEY ou FILE STATUS")
        if not any(isinstance(c, A.AssignClause) for c in clauses):
            self.fail("ASSIGN no SELECT")
        self.expect(".")
        return self.node(A.FileControlEntry, start, name=name, optional=optional, clauses=clauses)

    def data(self):
        start = self.i; self.area_a(); self.expect("DATA"); self.expect("DIVISION"); self.expect(".")
        sections = []
        while self.word() in self.data_sections:
            begin = self.i; self.area_a(); name = self.take().value; self.expect("SECTION"); self.expect(".")
            entries = []
            while self.current() and not self.at("PROCEDURE") and self.word() not in self.data_sections:
                entry_start = self.i
                try:
                    if self.at("EXEC"):
                        self.fail("declaração COBOL", code="UNSUPPORTED_EXEC", message="SQL/CICS embutido ainda não é suportado.")
                    if self.at("FD", "SD"):
                        if name != "FILE":
                            self.fail("FD/SD somente na FILE SECTION")
                        fd_start = self.i; sort = self.take().value == "SD"; fd_name = self.reference(suffixes=False); clauses = []
                        if self.match("RECORD"):
                            c_start = self.i - 1; self.match("CONTAINS"); low = self.integer_literal()
                            high = self.integer_literal() if self.match("TO") else None
                            unit = self.expect("CHARACTERS").value
                            clauses.append(self.node(A.RecordSizeClause, c_start, minimum=low, maximum=high, unit=unit))
                        self.expect(".")
                        records = self.data_entries()
                        if not records:
                            self.fail("registro de nível 01 após FD/SD")
                        entries.append(self.node(A.FileDescriptor, fd_start, name=fd_name, sort=sort, clauses=clauses, records=records))
                    elif self.kind() == "NUMBER":
                        if name == "FILE":
                            self.fail("FD/SD antes de registros na FILE SECTION")
                        entries.extend(self.data_entries(screen=name == "SCREEN"))
                    else:
                        self.fail("nível de dados, FD ou seção")
                except ParseError:
                    self.recover(entry_start, declaration=True)
            sections.append(self.node(A.DataSection, begin, name=name, entries=entries))
        return self.node(A.DataDivision, start, sections=sections)

    def data_entries(self, *, screen=False):
        roots = []; stack = []; last = None
        while self.kind() == "NUMBER":
            begin = self.i
            try:
                t = self.current()
                if not t.value.isdigit() or int(t.value) not in (*range(1, 50), 66, 77, 88):
                    self.fail("nível 01–49, 66, 77 ou 88", code="INVALID_DATA_LEVEL")
                self.take()
                level = int(t.value)
                if self.match("FILLER"):
                    name = None
                elif self.is_reference():
                    name = self.take().value
                elif screen and self.at("BLANK", "LINE", "COLUMN", "PIC", "PICTURE", "VALUE", "USING"):
                    name = None
                else:
                    self.fail("nome de campo ou FILLER")
                clauses = []
                while not self.at("."):
                    clauses.append(self.data_clause())
                self.expect(".")
                item = self.node(A.DataItem, begin, level=level, name=name, clauses=clauses, children=[], declaration_span=SourceSpan(t.span.start, self.tokens[self.i - 1].span.end))
                if level == 88:
                    if last is None:
                        self.fail("item anterior à condição 88")
                    last.children.append(item)
                else:
                    while stack and (stack[-1].level >= level or level in (1, 77)):
                        stack.pop()
                    if stack:
                        stack[-1].children.append(item)
                    else:
                        roots.append(item)
                    stack.append(item); last = item
                # Pais incluem o span dos filhos, inclusive condições 88.
                for parent in stack:
                    self.extend(parent)
            except ParseError:
                self.recover(begin, declaration=True)
        return roots

    def integer_literal(self):
        if self.kind() != "NUMBER" or not self.current().value.isdigit():
            self.fail("inteiro sem sinal")
        return self.literal()

    def data_clause(self):
        begin = self.i
        if self.match("PIC", "PICTURE"):
            self.match("IS")
            if self.kind() != "PICTURE":
                self.fail("máscara PIC")
            t = self.take()
            return self.node(A.PictureClause, begin, mask=t.value, lexeme=t.token.lexeme)
        if self.match("VALUE", "VALUES"):
            self.match("IS", "ARE"); values = []
            while self.kind() in ("NUMBER", "STRING") or self.word() in self.figuratives or self.at("ALL"):
                s = self.i; lower = self.literal(); upper = self.literal() if self.match("THRU", "THROUGH") else None
                values.append(self.node(A.ValueRange, s, lower=lower, upper=upper)); self.match(",")
            if not values:
                self.fail("valor da cláusula VALUE")
            return self.node(A.ValueClause, begin, values=values)
        if self.match("REDEFINES"):
            return self.node(A.RedefinesClause, begin, target=self.reference(suffixes=False))
        if self.at("USAGE") or self.word() in self.usages:
            self.match("USAGE"); self.match("IS")
            if self.word() not in self.usages:
                self.fail("tipo USAGE")
            return self.node(A.UsageClause, begin, usage=self.take().value)
        if self.match("OCCURS"):
            low = self.integer_literal(); high = self.integer_literal() if self.match("TO") else None
            self.match("TIMES"); depending = None; keys = []; indexes = []
            if self.match("DEPENDING"):
                self.expect("ON"); depending = self.reference(suffixes=False)
            while self.at("ASCENDING", "DESCENDING"):
                s = self.i; role = self.take().value; self.match("KEY"); self.match("IS")
                refs = self.references()
                keys.append(self.node(A.KeyClause, s, role=role, keys=refs))
            if self.match("INDEXED"):
                self.expect("BY"); indexes = self.references()
            return self.node(A.OccursClause, begin, minimum=low, maximum=high, depending=depending, keys=keys, indexes=indexes)
        if self.at("LINE", "COLUMN"):
            return self.screen_position()
        if self.match("USING"):
            return self.node(A.ScreenUsing, begin, target=self.reference())
        if self.match("BLANK"):
            mode = self.expect("SCREEN").value
            return self.node(A.ScreenBlank, begin, mode=mode)
        if self.at("RENAMES"):
            self.fail("cláusula implementada", code="UNSUPPORTED_RENAMES")
        self.fail("PIC, VALUE, OCCURS, USAGE, REDEFINES ou cláusula SCREEN")

    def procedure(self):
        start = self.i; self.area_a(); self.expect("PROCEDURE"); self.expect("DIVISION")
        parameters = self.parameters() if self.match("USING") else []
        if any(not isinstance(p.value, A.Reference) for p in parameters):
            self.fail("identificadores formais em PROCEDURE DIVISION USING")
        self.expect(".")
        body = []; section = None; paragraph = None
        while self.current() and not self.sequence("END", "PROGRAM"):
            begin = self.i
            try:
                if self.header():
                    label = self.take().value
                    if self.match("SECTION"):
                        self.expect(".")
                        section = self.node(A.ProcedureSection, begin, name=label, body=[])
                        paragraph = None; body.append(section)
                    else:
                        self.expect(".")
                        paragraph = self.node(A.Paragraph, begin, name=label, sentences=[])
                        (section.body if section else body).append(paragraph)
                else:
                    statements = []
                    while self.current() and not self.at(".") and not self.header():
                        statements.append(self.statement())
                    self.expect(".")
                    sentence = self.node(A.Sentence, begin, statements=statements)
                    if paragraph:
                        paragraph.sentences.append(sentence)
                    else:
                        (section.body if section else body).append(sentence)
                if paragraph:
                    self.extend(paragraph)
                if section:
                    self.extend(section)
            except ParseError:
                self.recover(begin)
        return self.node(A.ProcedureDivision, start, parameters=parameters, body=body)

    @property
    def figuratives(self):
        from .expressions import FIGURATIVES
        return FIGURATIVES
