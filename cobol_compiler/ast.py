"""AST sintática tipada. Nenhum comando é armazenado como COBOL bruto.

Spans usam posições físicas inclusivas; intervalos de tokens são [start, end).
Cláusulas/listas preservam ordem. A semântica futura poderá usar tabelas laterais
indexadas pelos nós, sem refazer parsing ou resolução no gerador C.
"""

from dataclasses import dataclass, fields, is_dataclass
from typing import Iterator

from .source import SourceSpan


@dataclass(slots=True, kw_only=True)
class Node:
    span: SourceSpan
    token_start: int
    token_end: int


@dataclass(slots=True)
class Expr(Node):
    pass


@dataclass(slots=True)
class Literal(Expr):
    category: str
    value: str
    lexeme: str
    all: bool = False


@dataclass(slots=True)
class ReferenceModification(Node):
    start: Expr
    length: Expr | None


@dataclass(slots=True)
class Reference(Expr):
    name: str
    qualifiers: list[str]
    subscripts: list[Expr]
    modification: ReferenceModification | None


@dataclass(slots=True)
class FunctionCall(Expr):
    name: str
    arguments: list[Expr]


@dataclass(slots=True)
class LengthOf(Expr):
    operand: Reference


@dataclass(slots=True)
class Unary(Expr):
    operator: str
    operand: Expr


@dataclass(slots=True)
class Binary(Expr):
    operator: str
    left: Expr
    right: Expr


@dataclass(slots=True)
class Group(Expr):
    expression: Expr


@dataclass(slots=True)
class Comparison(Expr):
    operator: str
    left: Expr
    right: Expr


@dataclass(slots=True)
class ClassCondition(Expr):
    operand: Expr | None
    category: str
    negated: bool


@dataclass(slots=True)
class AbbreviatedCondition(Expr):
    operator: str
    right: Expr
    inherited_subject: SourceSpan | None


@dataclass(slots=True)
class PictureClause(Node):
    mask: str
    lexeme: str


@dataclass(slots=True)
class ValueRange(Node):
    lower: Expr
    upper: Expr | None


@dataclass(slots=True)
class ValueClause(Node):
    values: list[ValueRange]


@dataclass(slots=True)
class KeyClause(Node):
    role: str
    keys: list[Reference]
    duplicates: bool = False


@dataclass(slots=True)
class OccursClause(Node):
    minimum: Expr
    maximum: Expr | None
    depending: Reference | None
    keys: list[KeyClause]
    indexes: list[Reference]


@dataclass(slots=True)
class UsageClause(Node):
    usage: str


@dataclass(slots=True)
class RedefinesClause(Node):
    target: Reference


@dataclass(slots=True)
class ScreenPosition(Node):
    axis: str
    value: Expr


@dataclass(slots=True)
class ScreenUsing(Node):
    target: Reference


@dataclass(slots=True)
class ScreenBlank(Node):
    mode: str


@dataclass(slots=True)
class DataItem(Node):
    level: int
    name: str | None
    clauses: list[Node]
    children: list["DataItem"]
    declaration_span: SourceSpan


@dataclass(slots=True)
class RecordSizeClause(Node):
    minimum: Expr
    maximum: Expr | None
    unit: str


@dataclass(slots=True)
class FileDescriptor(Node):
    name: Reference
    sort: bool
    clauses: list[Node]
    records: list[DataItem]


@dataclass(slots=True)
class DataSection(Node):
    name: str
    entries: list[Node]


@dataclass(slots=True)
class DataDivision(Node):
    sections: list[DataSection]


@dataclass(slots=True)
class DataFragment(Node):
    entries: list[DataItem]


@dataclass(slots=True)
class AssignClause(Node):
    target: Expr


@dataclass(slots=True)
class OrganizationClause(Node):
    organization: str


@dataclass(slots=True)
class AccessClause(Node):
    mode: str


@dataclass(slots=True)
class FileStatusClause(Node):
    target: Reference


@dataclass(slots=True)
class FileControlEntry(Node):
    name: Reference
    optional: bool
    clauses: list[Node]


@dataclass(slots=True)
class SpecialName(Node):
    setting: str
    value: Expr


@dataclass(slots=True)
class ComputerClause(Node):
    role: str
    name: str
    debugging: bool


@dataclass(slots=True)
class EnvironmentSection(Node):
    name: str
    entries: list[Node]


@dataclass(slots=True)
class EnvironmentDivision(Node):
    sections: list[EnvironmentSection]


@dataclass(slots=True)
class MetadataParagraph(Node):
    name: str
    words: list[str]


@dataclass(slots=True)
class IdentificationDivision(Node):
    program_id: str
    metadata: list[MetadataParagraph]


@dataclass(slots=True)
class Statement(Node):
    pass


@dataclass(slots=True)
class Move(Statement):
    source: Expr
    targets: list[Reference]
    corresponding: bool


@dataclass(slots=True)
class InitializeReplacement(Node):
    category: str
    value: Expr


@dataclass(slots=True)
class Initialize(Statement):
    targets: list[Reference]
    replacements: list[InitializeReplacement]


@dataclass(slots=True)
class Display(Statement):
    operands: list[Expr | ScreenPosition]
    no_advancing: bool
    upon: str | None


@dataclass(slots=True)
class Accept(Statement):
    target: Reference
    source: str | None
    date_format: str | None
    positions: list[ScreenPosition]


@dataclass(slots=True)
class ArithmeticTarget(Node):
    target: Reference
    rounded: bool


@dataclass(slots=True)
class Handler(Node):
    event: str
    negated: bool
    body: list[Statement]


@dataclass(slots=True)
class Arithmetic(Statement):
    operation: str
    sources: list[Expr]
    targets: list[ArithmeticTarget]
    giving: list[ArithmeticTarget]
    remainder: Reference | None
    corresponding: bool
    form: str
    handlers: list[Handler]
    explicit_end: bool


@dataclass(slots=True)
class If(Statement):
    condition: Expr
    then_body: list[Statement]
    else_body: list[Statement]
    explicit_end: bool


@dataclass(slots=True)
class Selection(Node):
    kind: str
    value: Expr | None
    upper: Expr | None


@dataclass(slots=True)
class When(Node):
    alternatives: list[list[Selection]]
    body: list[Statement]
    other: bool


@dataclass(slots=True)
class Evaluate(Statement):
    subjects: list[Expr]
    cases: list[When]
    explicit_end: bool


@dataclass(slots=True)
class Varying(Node):
    target: Reference
    initial: Expr
    step: Expr
    until: Expr


@dataclass(slots=True)
class Perform(Statement):
    target: Reference | None
    through: Reference | None
    times: Expr | None
    until: Expr | None
    varying: list[Varying]
    test: str
    body: list[Statement]
    explicit_end: bool


@dataclass(slots=True)
class GoTo(Statement):
    targets: list[Reference]
    depending: Reference | None


@dataclass(slots=True)
class Exit(Statement):
    scope: str | None


@dataclass(slots=True)
class Continue(Statement):
    pass


@dataclass(slots=True)
class StopRun(Statement):
    pass


@dataclass(slots=True)
class Goback(Statement):
    pass


@dataclass(slots=True)
class NextSentence(Statement):
    pass


@dataclass(slots=True)
class OpenGroup(Node):
    mode: str
    files: list[Reference]


@dataclass(slots=True)
class Open(Statement):
    groups: list[OpenGroup]


@dataclass(slots=True)
class Close(Statement):
    files: list[Reference]


@dataclass(slots=True)
class Read(Statement):
    file: Reference
    into: Reference | None
    next_record: bool
    key: Reference | None
    handlers: list[Handler]
    explicit_end: bool


@dataclass(slots=True)
class Write(Statement):
    record: Reference
    source: Expr | None
    advancing: Expr | None
    timing: str | None
    handlers: list[Handler]
    explicit_end: bool


@dataclass(slots=True)
class Start(Statement):
    file: Reference
    condition: Expr
    handlers: list[Handler]
    explicit_end: bool


@dataclass(slots=True)
class CallParameter(Node):
    mode: str
    value: Expr


@dataclass(slots=True)
class Call(Statement):
    program: Expr
    parameters: list[CallParameter]
    returning: Reference | None
    handlers: list[Handler]
    explicit_end: bool


@dataclass(slots=True)
class InspectPattern(Node):
    mode: str
    value: Expr | None
    replacement: Expr | None


@dataclass(slots=True)
class InspectTally(Node):
    counter: Reference
    patterns: list[InspectPattern]


@dataclass(slots=True)
class Inspect(Statement):
    subject: Expr
    tallies: list[InspectTally]
    replacements: list[InspectPattern]
    converting: tuple[Expr, Expr] | None


@dataclass(slots=True)
class Delimiter(Node):
    value: Expr | None
    all: bool
    size: bool


@dataclass(slots=True)
class StringPart(Node):
    values: list[Expr]
    delimiter: Delimiter


@dataclass(slots=True)
class String(Statement):
    parts: list[StringPart]
    target: Reference
    pointer: Reference | None
    handlers: list[Handler]
    explicit_end: bool


@dataclass(slots=True)
class UnstringTarget(Node):
    target: Reference
    delimiter_in: Reference | None
    count_in: Reference | None


@dataclass(slots=True)
class Unstring(Statement):
    source: Expr
    delimiters: list[Delimiter]
    targets: list[UnstringTarget]
    pointer: Reference | None
    tallying: Reference | None
    handlers: list[Handler]
    explicit_end: bool


@dataclass(slots=True)
class SearchWhen(Node):
    condition: Expr
    body: list[Statement]


@dataclass(slots=True)
class Search(Statement):
    table: Reference
    all: bool
    varying: Reference | None
    at_end: list[Statement]
    cases: list[SearchWhen]
    explicit_end: bool


@dataclass(slots=True)
class Set(Statement):
    targets: list[Reference]
    mode: str
    value: Expr


@dataclass(slots=True)
class AlterPair(Node):
    source: Reference
    target: Reference


@dataclass(slots=True)
class Alter(Statement):
    pairs: list[AlterPair]


@dataclass(slots=True)
class Sort(Statement):
    file: Reference
    keys: list[KeyClause]
    using: list[Reference]
    giving: list[Reference]


@dataclass(slots=True)
class Sentence(Node):
    statements: list[Statement]


@dataclass(slots=True)
class Paragraph(Node):
    name: str
    sentences: list[Sentence]


@dataclass(slots=True)
class ProcedureSection(Node):
    name: str
    body: list[Sentence | Paragraph]


@dataclass(slots=True)
class ProcedureDivision(Node):
    parameters: list[CallParameter]
    body: list[Sentence | Paragraph | ProcedureSection]


@dataclass(slots=True)
class EndProgram(Node):
    name: str


@dataclass(slots=True)
class Program(Node):
    identification: IdentificationDivision
    environment: EnvironmentDivision | None
    data: DataDivision | None
    procedure: ProcedureDivision
    end_program: EndProgram | None


def walk(node: Node) -> Iterator[Node]:
    yield node
    for field in fields(node):
        value = getattr(node, field.name)
        yield from _walk_value(value)


def _walk_value(value):
    if isinstance(value, Node):
        yield from walk(value)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_value(child)


def to_dict(value):
    if is_dataclass(value):
        result = {f.name: to_dict(getattr(value, f.name)) for f in fields(value)}
        if isinstance(value, Node):
            result = {"node": type(value).__name__, **result}
        return result
    if isinstance(value, (tuple, list)):
        return [to_dict(v) for v in value]
    return value


def validate_structure(root: Node, token_count: int) -> list[str]:
    """Invariantes mecânicos, sem validar tipos, símbolos ou comportamento."""
    errors = []
    if (root.token_start, root.token_end) != (0, token_count):
        errors.append("Raiz não cobre todo o fluxo de tokens.")
    for node in walk(root):
        if not 0 <= node.token_start < node.token_end <= token_count:
            errors.append(f"Intervalo inválido em {type(node).__name__}.")
        if node.span.start.line < 1 or node.span.start.column < 1 or node.span.end.line < 1:
            errors.append(f"Origem inválida em {type(node).__name__}.")
        for f in fields(node):
            for child in _direct_nodes(getattr(node, f.name)):
                if not node.token_start <= child.token_start < child.token_end <= node.token_end:
                    errors.append(f"Filho {type(child).__name__} fora de {type(node).__name__}.")
    return errors


def _direct_nodes(value):
    if isinstance(value, Node):
        yield value
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _direct_nodes(child)
