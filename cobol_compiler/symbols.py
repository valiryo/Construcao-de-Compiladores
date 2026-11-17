"""Namespaces e resolução hierárquica; nenhum nome substitui a identidade do nó."""

from dataclasses import dataclass, field
from .source import SourceSpan
from .types import CobolType


@dataclass(slots=True)
class Symbol:
    id: str
    name: str
    original_name: str
    namespace: str
    node_id: str | None
    span: SourceSpan
    parent: str | None = None
    section: str | None = None
    type: CobolType | None = None
    children: list[str] = field(default_factory=list)
    level: int | None = None
    file_id: str | None = None
    table_id: str | None = None


class SymbolTable:
    def __init__(self):
        self.symbols: dict[str, Symbol] = {}
        self.names: dict[tuple[str, str], list[str]] = {}

    def add(self, symbol):
        self.symbols[symbol.id] = symbol
        self.names.setdefault((symbol.namespace, symbol.name.upper()), []).append(symbol.id)
        if symbol.parent:
            self.symbols[symbol.parent].children.append(symbol.id)

    def ancestors(self, symbol):
        while symbol.parent:
            symbol = self.symbols[symbol.parent]
            yield symbol

    def candidates(self, name, namespaces, qualifiers=()):
        result = []
        for namespace in namespaces:
            for sid in self.names.get((namespace, name.upper()), []):
                symbol = self.symbols[sid]
                chain = iter(s.name for s in self.ancestors(symbol))
                if all(any(n == q.upper() for n in chain) for q in qualifiers):
                    result.append(symbol)
        return result
