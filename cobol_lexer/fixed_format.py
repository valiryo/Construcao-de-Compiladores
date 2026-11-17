"""Leitura de linhas físicas COBOL em formato fixo (colunas 1 a 80)."""

from dataclasses import dataclass
import re
from typing import Iterator

from .model import Diagnostic


@dataclass(frozen=True, slots=True)
class FixedLine:
    line_number: int
    indicator: str
    code: str
    tab_column: int | None = None
    conflict_column: int | None = None


CONFLICT_RE = re.compile(r"^(?:<{7,}|={7,}|>{7,}|\|{7,})(?:\s|$)")


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
        code = raw[7:72].rstrip(" ")
        conflict_column = None
        if CONFLICT_RE.match(raw):
            conflict_column = 1
        elif raw[6] in (" ", "-") and CONFLICT_RE.match(code.lstrip(" ")):
            conflict_column = 8 + len(code) - len(code.lstrip(" "))
        yield FixedLine(n, raw[6], code, tab_column, conflict_column)


@dataclass(frozen=True, slots=True)
class LogicalLine:
    """Código com continuações unidas e posições físicas de cada caractere."""

    code: str
    positions: tuple[tuple[int, int], ...]


def _without_inline_comment(code: str, quote: str | None) -> tuple[str, str | None]:
    index = 0
    while index < len(code):
        character = code[index]
        if quote is None:
            if code.startswith("*>", index):
                return code[:index].rstrip(" "), quote
            if character in ("'", '"'):
                quote = character
        elif character == quote:
            if index + 1 < len(code) and code[index + 1] == quote:
                index += 1
            else:
                quote = None
        index += 1
    return code, quote


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
        if physical.conflict_column is not None and not (
            physical.indicator == "-" and quote is not None
        ):
            diagnostics.append(Diagnostic(
                "MERGE_CONFLICT", "Marcador de conflito Git não resolvido no fonte.",
                physical.line_number, physical.conflict_column,
            ))
            continue
        indicator = physical.indicator.upper()
        if indicator in ("*", "/") or (indicator == "D" and not debug_lines):
            continue
        if physical.tab_column is not None and physical.tab_column <= 7:
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
            if quote is not None and start < len(code) and code[start] == quote:
                start += 1
        fragment, next_quote = _without_inline_comment(
            code[start:], quote if indicator == "-" else None,
        )
        if physical.tab_column is not None and physical.tab_column <= start + len(fragment) + 7:
            diagnostics.append(Diagnostic(
                "TAB_IN_SOURCE", "TAB não permitido em formato fixo; use espaços.",
                physical.line_number, physical.tab_column,
            ))
            continue
        if not fragment.strip():
            continue
        if indicator != "-":
            if chunks:
                yield LogicalLine("".join(chunks), tuple(positions))
            chunks = []
            positions = []
            quote = None

        chunks.append(fragment)
        positions.extend((physical.line_number, index + 8) for index in range(start, start + len(fragment)))
        quote = next_quote

    if chunks:
        yield LogicalLine("".join(chunks), tuple(positions))
