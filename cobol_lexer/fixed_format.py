"""Leitura de linhas físicas COBOL em formato fixo (colunas 1 a 80)."""

from dataclasses import dataclass
from typing import Iterator

from .model import Diagnostic


@dataclass(frozen=True, slots=True)
class FixedLine:
    line_number: int
    indicator: str
    code: str
    tab_column: int | None = None


def read_fixed_lines(source: str) -> Iterator[FixedLine]:
    """Extrai só as colunas 8-72, preservando os indicadores da coluna 7.

    Área 1-6 e 73 em diante são ignoradas. O lexer interpreta os indicadores.
    A ausência de colunas ao fim da linha equivale a espaços em branco.
    Linhas restritas às colunas 1-6 não contêm código e são ignoradas.
    """
    for n, raw in enumerate(source.splitlines(), start=1):
        if len(raw) <= 6 or not raw.strip():
            continue

        tab_index = raw[:72].find("\t")
        tab_column = tab_index + 1 if tab_index >= 0 else None
        yield FixedLine(n, raw[6], raw[7:72].rstrip(" "), tab_column)


@dataclass(frozen=True, slots=True)
class LogicalLine:
    """Código com continuações unidas e posições físicas de cada caractere."""

    code: str
    positions: tuple[tuple[int, int], ...]


def _quote_after(code: str, quote: str | None) -> str | None:
    index = 0
    while index < len(code):
        character = code[index]
        if quote is None:
            if character in ("'", '"'):
                quote = character
        elif character == quote:
            if index + 1 < len(code) and code[index + 1] == quote:
                index += 1
            else:
                quote = None
        index += 1
    return quote


def read_logical_lines(
    source: str, diagnostics: list[Diagnostic], *, debug_lines: bool = False
) -> Iterator[LogicalLine]:
    """Une linhas com '-' e preserva um mapa das coordenadas originais.

    Espaços finais e a indentação da continuação são descartados. Uma aspa
    repetida no início da continuação de uma string aberta também é removida.
    Comentários e linhas de debugging desabilitadas não interrompem a união.
    """
    chunks: list[str] = []
    positions: list[tuple[int, int]] = []
    quote: str | None = None

    for physical in read_fixed_lines(source):
        indicator = physical.indicator.upper()
        if indicator in ("*", "/") or (indicator == "D" and not debug_lines):
            continue
        if physical.tab_column is not None:
            diagnostics.append(Diagnostic(
                "TAB_IN_SOURCE", "TAB não permitido em formato fixo; use espaços.",
                physical.line_number, physical.tab_column,
            ))
            continue
        if indicator not in (" ", "-", "D"):
            diagnostics.append(Diagnostic(
                "INVALID_INDICATOR",
                f"Indicador {physical.indicator!r} desconhecido na coluna 7.",
                physical.line_number, 7,
            ))
            continue

        code = physical.code
        if not code.strip():
            continue
        start = 0
        if indicator == "-":
            if not chunks:
                diagnostics.append(Diagnostic(
                    "UNEXPECTED_CONTINUATION", "Continuação sem linha de código anterior.",
                    physical.line_number, 7,
                ))
                continue
            start = len(code) - len(code.lstrip(" "))
            if quote is not None and code[start] == quote:
                start += 1
        else:
            if chunks:
                yield LogicalLine("".join(chunks), tuple(positions))
            chunks = []
            positions = []
            quote = None

        fragment = code[start:]
        chunks.append(fragment)
        positions.extend((physical.line_number, index + 8) for index in range(start, len(code)))
        quote = _quote_after(fragment, quote)

    if chunks:
        yield LogicalLine("".join(chunks), tuple(positions))
