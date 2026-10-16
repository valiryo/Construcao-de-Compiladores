"""Leitura de linhas físicas COBOL em formato fixo (colunas 1 a 80)."""

from dataclasses import dataclass
from typing import Iterator


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
    """
    for n, raw in enumerate(source.splitlines(), start=1):
        if not raw.strip():
            continue
        
        tab_index = raw[:72].find("\t")
        tab_column = tab_index + 1 if tab_index >= 0 else None
        if len(raw) < 7:
            yield FixedLine(n, "", "", tab_column)
            continue
        yield FixedLine(n, raw[6], raw[7:72].rstrip(" "), tab_column)
