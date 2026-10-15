"""Tipos de saída do analisador léxico COBOL."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    lexeme: str
    value: str
    line: int
    column: int
    area: str
    end_line: int
    end_column: int


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    line: int
    column: int


@dataclass(slots=True)
class LexerResult:
    tokens: list[Token] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.diagnostics
