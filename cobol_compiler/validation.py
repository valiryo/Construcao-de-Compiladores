"""Validação independente de estrutura, spans e representação dos comandos."""

from collections import Counter
from dataclasses import dataclass

from . import ast as A
from .statements import StatementParser


@dataclass(slots=True)
class ASTValidation:
    errors: list[str]
    node_counts: dict[str, int]
    expected_statements: int
    represented_statements: int

    @property
    def success(self):
        return not self.errors


def validate_ast(root, tokens):
    errors = A.validate_structure(root, len(tokens))
    nodes = list(A.walk(root))
    for node in nodes:
        if not 0 <= node.token_start < node.token_end <= len(tokens):
            continue
        expected = (tokens[node.token_start].span.start, tokens[node.token_end - 1].span.end)
        if (node.span.start, node.span.end) != expected:
            errors.append(f"SourceSpan não corresponde ao intervalo em {type(node).__name__}.")
    actual = [n.token_start for n in nodes if isinstance(n, A.Statement)]
    expected = set()
    if isinstance(root, A.Program):
        for i in range(root.procedure.token_start, root.procedure.token_end):
            t = tokens[i]
            if t.kind not in ("KEYWORD", "IDENTIFIER") or t.value not in StatementParser.statement_methods:
                continue
            if t.value == "PERFORM" and i and tokens[i - 1].kind == "KEYWORD" and tokens[i - 1].value == "EXIT":
                continue
            if t.value == "NEXT" and (i + 1 >= len(tokens) or tokens[i + 1].value != "SENTENCE"):
                continue
            expected.add(i)
        missing = expected - set(actual)
        extra = set(actual) - expected
        if missing:
            errors.append(f"Comandos sem nó AST nos índices: {sorted(missing)}.")
        if extra or len(actual) != len(set(actual)):
            errors.append("Comandos duplicados ou com início incorreto na AST.")
    return ASTValidation(errors, dict(sorted(Counter(type(n).__name__ for n in nodes).items())), len(expected), len(actual))
