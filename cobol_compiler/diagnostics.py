"""Diagnósticos do front-end; a API histórica do lexer permanece independente."""

from dataclasses import dataclass

from .source import SourceSpan


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    span: SourceSpan
    phase: str
    expected: str | None = None
    unexpected: str | None = None
    severity: str = "E"

    def format(self) -> str:
        p = self.span.start
        text = f"{p.file}:{p.line}:{p.column}: {self.severity} {self.code}: {self.message}"
        if self.expected is not None:
            text += f" (esperado: {self.expected}; encontrado: {self.unexpected})"
        for site in reversed(p.inclusion_stack):
            text += f"\n  incluído de {site.file}:{site.line}:{site.column}"
        return text
