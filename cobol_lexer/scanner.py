"""Scanner do subconjunto COBOL descrito na seção 2 da especificação.

A camada de posições de colunas fica em fixed_format.py. Este scanner
reconhece lexemas, produz tokens e acumula erros recuperáveis.
"""

from dataclasses import dataclass, field
import re

from .fixed_format import FixedLine, read_fixed_lines
from .model import Diagnostic, LexerResult, Token


# Lista EXPRESSA de palavras reservadas da seção 2.2.
# Outras palavras da gramática (por exemplo, PROGRAM-ID, PIC, VALUE) são,
# nesta etapa, IDENTIFIER. Isso pode ser estendido após os testes oficiais.
RESERVED_WORDS = frozenset(
    "IDENTIFICATION ENVIRONMENT DATA PROCEDURE DIVISION SECTION "
    "DISPLAY ACCEPT PERFORM STOP RUN IF ELSE MOVE".split()
)

PUNCTUATION = {".": "PERIOD", ",": "COMMA", ";": "SEMICOLON", "(": "LPAREN", ")": "RPAREN"}
WORD_RE = re.compile(r"[A-Za-z0-9-]+")
SIGNED_NUMBER_RE = re.compile(r"[+-][0-9]+(?:\.[0-9]+)?")
DECIMAL_RE = re.compile(r"[0-9]+\.[0-9]+")


@dataclass(slots=True)
class _OpenString:
    quote: str
    start_line: int
    start_column: int
    characters: list[str] = field(default_factory=list)


class CobolLexer:
    """Lexer sem validação de gramática: separa tokens e aponta erros léxicos.

    debug_lines=False ignora linhas com 'D' na coluna 7, por padrão.
    Por não haver regra explícita de execução de debug na seção 2,
    a política é configurável.
    """

    def __init__(self, *, debug_lines: bool = False) -> None:
        self.debug_lines = debug_lines

    def tokenize(self, source: str) -> LexerResult:
        result = LexerResult()
        pending: _OpenString | None = None

        for physical in read_fixed_lines(source):
            indicator = physical.indicator.upper()

            if physical.tab_column is not None:
                self._error(result, "TAB_IN_SOURCE", "TAB não permitido em formato fixo; use espaços.", physical.line_number, physical.tab_column)
                continue

            # Comentários e linhas de debugging desabilitadas são descartados.
            if indicator in ("*", "/") or (indicator == "D" and not self.debug_lines):
                continue

            if indicator == "":
                self._error(result, "INVALID_LINE", "Linha não vazia tem menos de 7 colunas.", physical.line_number, 1)
                continue

            if indicator not in (" ", "-", "D"):
                self._error(result, "INVALID_INDICATOR", f"Indicador {physical.indicator!r} desconhecido na coluna 7.", physical.line_number, 7)
                continue

            if pending is not None and indicator != "-":
                self._error(
                    result, "UNTERMINATED_STRING",
                    "Literal não terminado; a continuação exige '-' na coluna 7.",
                    pending.start_line, pending.start_column,
                )
                pending = None

            if indicator == "-":
                if pending is None:
                    self._error(result, "UNEXPECTED_CONTINUATION", "Continuação sem literal aberto na linha anterior.", physical.line_number, 7)
                    continue
                # Na continuação, ignoram-se a indentação e uma eventual
                # repetição da aspa delimitadora (convenção COBOL).
                code = physical.code
                position = len(code) - len(code.lstrip(" "))
                if position < len(code) and code[position] == pending.quote:
                    position += 1
                pending = self._scan_code(physical, position, result, pending)
            else:
                pending = self._scan_code(physical, 0, result, None)

        if pending is not None:
            self._error(result, "UNTERMINATED_STRING", "Literal alfanumérico não terminado até o fim do arquivo.", pending.start_line, pending.start_column)

        return result

    @staticmethod
    def _error(result: LexerResult, code: str, message: str, line: int, column: int) -> None:
        result.diagnostics.append(Diagnostic(code, message, line, column))

    @staticmethod
    def _area(column: int) -> str:
        return "A" if 8 <= column <= 11 else "B"

    @classmethod
    def _emit(cls, result: LexerResult, kind: str, lexeme: str, value: str, line: int, column: int, end_line: int, end_column: int) -> None:
        result.tokens.append(Token(kind, lexeme, value, line, column, cls._area(column), end_line, end_column))

    def _scan_code(
        self, physical: FixedLine, position: int, result: LexerResult, pending: _OpenString | None
    ) -> _OpenString | None:
        code = physical.code
        n = len(code)
        i = position

        while i < n:
            current = code[i]
            col = i + 8

            if pending is not None:
                if current == pending.quote:
                    # Aspas duplicadas representam uma única aspa no valor.
                    if i + 1 < n and code[i + 1] == pending.quote:
                        pending.characters.append(current)
                        i += 2
                        continue
                    value = "".join(pending.characters)
                    canonical_lexeme = pending.quote + value.replace(pending.quote, pending.quote * 2) + pending.quote
                    self._emit(result, "STRING", canonical_lexeme, value, pending.start_line, pending.start_column, physical.line_number, col)
                    pending = None
                    i += 1
                    continue
                pending.characters.append(current)
                i += 1
                continue

            if current == " ":
                i += 1
                continue

            if current in ("'", '"'):
                pending = _OpenString(current, physical.line_number, col)
                i += 1
                continue

            if current in PUNCTUATION:
                self._emit(result, PUNCTUATION[current], current, current, physical.line_number, col, physical.line_number, col)
                i += 1
                continue

            if current in ("+", "-") and i + 1 < n and code[i + 1].isdigit():
                match = SIGNED_NUMBER_RE.match(code, i)
                assert match is not None
                lexeme = match.group(0)
                # Um sinal não pode iniciar uma palavra definida pelo usuário.
                if match.end() < n and (code[match.end()].isalpha() or code[match.end()] == "-"):
                    end = match.end()
                    while end < n and (code[end].isalnum() or code[end] == "-"):
                        end += 1
                    self._error(result, "INVALID_WORD", f"Palavra inválida: {code[i:end]!r}.", physical.line_number, col)
                    i = end
                    continue
                self._emit(result, "NUMBER", lexeme, lexeme, physical.line_number, col, physical.line_number, 8 + match.end() - 1)
                i = match.end()
                continue

            if current.isascii() and current.isalnum():
                word = WORD_RE.match(code, i)
                assert word is not None
                lexeme = word.group(0)
                end = word.end()

                # Inteiro seguido de .dígitos constitui um único literal decimal.
                if lexeme.isdigit() and end < n and code[end] == ".":
                    decimal = DECIMAL_RE.match(code, i)
                    if decimal is not None:
                        lexeme = decimal.group(0)
                        end = decimal.end()
                        self._emit(result, "NUMBER", lexeme, lexeme, physical.line_number, col, physical.line_number, end + 7)
                        i = end
                        continue

                if lexeme.isdigit():
                    kind, value = "NUMBER", lexeme
                elif lexeme.startswith("-") or lexeme.endswith("-"):
                    self._error(result, "INVALID_IDENTIFIER", f"Identificador não pode iniciar/terminar com hífen: {lexeme!r}.", physical.line_number, col)
                    i = end
                    continue
                elif len(lexeme) > 30:
                    self._error(result, "IDENTIFIER_TOO_LONG", f"Identificador contém {len(lexeme)} caracteres (máximo 30).", physical.line_number, col)
                    i = end
                    continue
                elif lexeme.upper() in RESERVED_WORDS:
                    kind, value = "KEYWORD", lexeme.upper()
                else:
                    kind, value = "IDENTIFIER", lexeme.upper()

                self._emit(result, kind, lexeme, value, physical.line_number, col, physical.line_number, end + 7)
                i = end
                continue

            self._error(result, "INVALID_CHARACTER", f"Caractere {current!r} não reconhecido.", physical.line_number, col)
            i += 1

        return pending
