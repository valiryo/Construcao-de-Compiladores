"""Descritores físicos sem padding. Offsets referem-se à primeira ocorrência."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class Dimension:
    symbol_id: str
    minimum: int
    maximum: int
    stride: int
    depending_id: str | None = None
    base: int = 1


@dataclass(slots=True)
class StorageLayout:
    symbol_id: str
    area: str
    offset: int
    size: int
    total_size: int
    parent_id: str | None
    local: bool
    dimensions: list[Dimension] = field(default_factory=list)
    redefines: str | None = None
    initial: dict = field(default_factory=dict)


@dataclass(slots=True)
class LayoutResult:
    items: dict[str, StorageLayout] = field(default_factory=dict)
    areas: dict[str, int] = field(default_factory=dict)

    def for_symbol(self, symbol):
        return self.items[symbol.id if hasattr(symbol, "id") else symbol]
