"""Origem física dos tokens, inclusive expansões COPY aninhadas."""

from dataclasses import dataclass
from pathlib import Path

from cobol_lexer import Token


@dataclass(frozen=True, slots=True)
class IncludeSite:
    file: str
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceLocation:
    file: str
    line: int
    column: int
    inclusion_stack: tuple[IncludeSite, ...] = ()


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start: SourceLocation
    end: SourceLocation


@dataclass(frozen=True, slots=True)
class LocatedToken:
    token: Token
    span: SourceSpan

    @property
    def value(self) -> str:
        return self.token.value

    @property
    def kind(self) -> str:
        return self.token.kind


def display_path(path: Path) -> str:
    return str(path.resolve())
