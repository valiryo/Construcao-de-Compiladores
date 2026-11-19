"""Scanner COBOL em formato fixo, incluindo os corpora ebasso e COBOL Dicas."""

from dataclasses import dataclass
import re

from .fixed_format import LogicalLine, read_logical_lines, read_free_lines
from .model import Diagnostic, LexerResult, Token


RESERVED_WORDS = frozenset(
    "IDENTIFICATION ENVIRONMENT DATA PROCEDURE DIVISION SECTION "
    "DISPLAY ACCEPT PERFORM STOP RUN IF ELSE MOVE "
    "ACCESS ADD ADVANCING AFTER ALL ALTERNATE AND ASSIGN AT AUTHOR BEFORE "
    "BLOCK BY CHARACTERS CLOSE COMPUTE CONFIGURATION CONTAINS CONVERTING "
    "COPY DATE-COMPILED DATE-WRITTEN DIVIDE DYNAMIC END END-EVALUATE END-IF "
    "END-SEARCH EQUAL ERROR EVALUATE FD FILE FILE-CONTROL FIRST FOR FROM "
    "FUNCTION GIVING I-O INDEXED INITIAL INPUT INPUT-OUTPUT INSPECT "
    "INSTALLATION INTO INVALID IS KEY LEADING LOW-VALUE LOW-VALUES MODE "
    "MULTIPLY NO NOT OCCURS OF ON OPEN OR ORGANIZATION OTHER OUTPUT "
    "PIC PICTURE PROGRAM PROGRAM-ID READ RECORD RECORDS REMAINDER REMARKS "
    "REPLACING SEARCH SECURITY SELECT SET SIZE SPACE SPACES START STATUS "
    "STRING SUBTRACT TALLYING TIMES TO UNTIL UPPER-CASE VALUE VALUES "
    "WHEN WITH WORKING-STORAGE WRITE ZERO ZEROES ZEROS "
    # Construções do corpus COBOL Dicas. Ver docs/recursos-suportados.md.
    "ALPHANUMERIC ALTER ASCENDING BLANK CALL COLUMN COMMA COMP CONTINUE "
    "CORR CORRESPONDING CRT DATE DAY DAY-OF-WEEK DECIMAL-POINT DELIMITED "
    "DUPLICATES END-EXEC END-PERFORM END-READ EXEC EXIT EXTEND FALSE FILLER "
    "GO GOBACK GREATER INITIALIZE LENGTH LESS LINE LINKAGE NORMAL NUMERIC "
    "PROCEED REDEFINES REFERENCE RETURN RETURN-CODE ROUNDED SCREEN SD "
    "SEQUENTIAL SORT SPECIAL-NAMES THAN THEN TRUE UNSTRING USING VARYING "
    "TIME YYYYDDD YYYYMMDD".split()
)

PUNCTUATION = {".": "PERIOD", ",": "COMMA", ";": "SEMICOLON", "(": "LPAREN", ")": "RPAREN", ":": "COLON"}
OPERATORS = {
    "**": "POWER", "<=": "LESS_EQUAL", ">=": "GREATER_EQUAL", "<>": "NOT_EQUAL",
    "=": "EQUAL", "<": "LESS_THAN", ">": "GREATER_THAN",
    "+": "PLUS", "-": "MINUS", "*": "MULTIPLY", "/": "DIVIDE",
}
WORD_RE = re.compile(r"[A-Za-z0-9_-]+")
SIGNED_NUMBER_RE = re.compile(r"[+-][0-9]+(?:\.[0-9]+)?")
DECIMAL_RE = re.compile(r"[0-9]+\.[0-9]+")
COMMA_SIGNED_NUMBER_RE = re.compile(r"[+-][0-9]+(?:,[0-9]+)?")
COMMA_DECIMAL_RE = re.compile(r"[0-9]+,[0-9]+")
PICTURE_RE = re.compile(r"(?:(?:CR|DB|[AX9SVPZ0B/,.+*$-])(?:\([0-9]+\))?)+", re.IGNORECASE)
REPETITION_RE = re.compile(r"\(([0-9]+)\)")


@dataclass(slots=True)
class _ScanState:
    picture_expected: bool = False
    decimal_point: str = "."


class CobolLexer:
    """Produz tokens e diagnósticos com posições físicas, sem validar a gramática."""

    def __init__(self, *, debug_lines: bool = False, preserve_literal_padding: bool = False,
                 source_format: str = 'fixed', dialect: str = 'project') -> None:
        if source_format not in {'fixed','free'}:raise ValueError('Formato deve ser fixed ou free')
        if dialect not in {'project','gnucobol'}:raise ValueError('Dialeto deve ser project ou gnucobol')
        self.debug_lines = debug_lines
        self.preserve_literal_padding = preserve_literal_padding
        self.source_format = source_format
        self.max_identifier = 63 if dialect == 'gnucobol' else 30

    def tokenize(self, source: str) -> LexerResult:
        result = LexerResult()
        state = _ScanState()
        lines = read_free_lines(source, result.diagnostics) if self.source_format == 'free' else read_logical_lines(
            source, result.diagnostics, debug_lines=self.debug_lines, preserve_literal_padding=self.preserve_literal_padding)
        for logical in lines:
            self._scan_code(logical, result, state)
        result.diagnostics.sort(key=lambda error: (error.line, error.column))
        return result

    @staticmethod
    def _error(result: LexerResult, source: LogicalLine, index: int, code: str, message: str) -> None:
        line, column = source.positions[index]
        result.diagnostics.append(Diagnostic(code, message, line, column))

    @staticmethod
    def _emit(
        result: LexerResult, source: LogicalLine, start: int, end: int,
        kind: str, lexeme: str, value: str,
    ) -> None:
        line, column = source.positions[start]
        end_line, end_column = source.positions[end - 1]
        area = "A" if 8 <= column <= 11 else "B"
        result.tokens.append(Token(kind, lexeme, value, line, column, area, end_line, end_column))

    def _scan_code(self, source: LogicalLine, result: LexerResult, state: _ScanState) -> None:
        code = source.code
        index = 0
        while index < len(code):
            current = code[index]
            if current == " ":
                index += 1
                continue

            if state.picture_expected:
                word = WORD_RE.match(code, index)
                if word is not None and word.group().upper() == "COPY":
                    # O copybook pode fornecer a própria máscara. A expansão
                    # ocorre antes da tokenização definitiva do programa.
                    state.picture_expected = False
                    continue
                if word is not None and word.group().upper() == "IS":
                    self._emit(result, source, index, word.end(), "KEYWORD", word.group(), "IS")
                    index = word.end()
                    continue
                state.picture_expected = False
                if current != ".":
                    end = code.find(" ", index)
                    if end == -1:
                        end = len(code)
                    lexeme = code[index:end].rstrip(".,;")
                    end = index + len(lexeme)
                    if PICTURE_RE.fullmatch(lexeme) and all(
                        count.strip("0") for count in REPETITION_RE.findall(lexeme)
                    ):
                        self._emit(result, source, index, end, "PICTURE", lexeme, lexeme.upper())
                    else:
                        self._error(result, source, index, "INVALID_PICTURE", f"Máscara PIC inválida: {lexeme!r}.")
                    index = end
                    continue

            if current in ("'", '"'):
                start = index
                quote = current
                characters: list[str] = []
                index += 1
                while index < len(code):
                    if code[index] == quote:
                        if index + 1 < len(code) and code[index + 1] == quote:
                            characters.append(quote)
                            index += 2
                            continue
                        index += 1
                        value = "".join(characters)
                        self._emit(result, source, start, index, "STRING", code[start:index], value)
                        break
                    characters.append(code[index])
                    index += 1
                else:
                    self._error(
                        result, source, start, "UNTERMINATED_STRING",
                        "Literal não terminado; a continuação exige '-' na coluna 7.",
                    )
                continue

            if current in PUNCTUATION:
                self._emit(result, source, index, index + 1, PUNCTUATION[current], current, current)
                index += 1
                continue

            signed_pattern = COMMA_SIGNED_NUMBER_RE if state.decimal_point == "," else SIGNED_NUMBER_RE
            signed_number = signed_pattern.match(code, index)
            if signed_number is not None and (index == 0 or code[index - 1] in " (=<>*/,:+-"):
                end = signed_number.end()
                if end < len(code) and (code[end].isalpha() or code[end] in "-_"):
                    while end < len(code) and (code[end].isalnum() or code[end] in "-_"):
                        end += 1
                    self._error(result, source, index, "INVALID_WORD", f"Palavra inválida: {code[index:end]!r}.")
                else:
                    lexeme = signed_number.group()
                    self._emit(result, source, index, end, "NUMBER", lexeme, lexeme.replace(",", "."))
                index = end
                continue

            # Preserve a palavra inteira para diagnosticar hífens iniciais em nomes.
            word = WORD_RE.match(code, index)
            leading_hyphen_word = (
                current == "-" and word is not None
                and any(character.isalpha() or character == "_" for character in word.group())
            )
            operator = code[index:index + 2]
            if operator not in OPERATORS:
                operator = current
            if operator in OPERATORS and not leading_hyphen_word:
                end = index + len(operator)
                self._emit(result, source, index, end, OPERATORS[operator], operator, operator)
                index = end
                continue

            if word is not None:
                lexeme = word.group()
                end = word.end()
                decimal_pattern = COMMA_DECIMAL_RE if state.decimal_point == "," else DECIMAL_RE
                decimal = decimal_pattern.match(code, index) if lexeme.isdigit() else None
                if decimal is not None:
                    lexeme = decimal.group()
                    end = decimal.end()
                    if end < len(code) and (code[end].isalpha() or code[end] in "-_"):
                        while end < len(code) and (code[end].isalnum() or code[end] in "-_"):
                            end += 1
                        self._error(result, source, index, "INVALID_WORD", f"Palavra inválida: {code[index:end]!r}.")
                        index = end
                        continue
                    kind, value = "NUMBER", lexeme.replace(",", ".")
                elif lexeme.isdigit():
                    kind, value = "NUMBER", lexeme
                elif lexeme.startswith(("-", "_")) or lexeme.endswith(("-", "_")):
                    self._error(
                        result, source, index, "INVALID_IDENTIFIER",
                        f"Identificador não pode iniciar/terminar com hífen ou underscore: {lexeme!r}.",
                    )
                    index = end
                    continue
                elif len(lexeme) > self.max_identifier:
                    self._error(
                        result, source, index, "IDENTIFIER_TOO_LONG",
                        f"Identificador contém {len(lexeme)} caracteres (máximo {self.max_identifier}).",
                    )
                    index = end
                    continue
                else:
                    value = lexeme.upper()
                    kind = "KEYWORD" if value in RESERVED_WORDS else "IDENTIFIER"
                self._emit(result, source, index, end, kind, lexeme, value)
                state.picture_expected = kind == "KEYWORD" and value in ("PIC", "PICTURE")
                if kind == "KEYWORD" and value == "PROGRAM-ID":
                    state.decimal_point = "."
                # Configuração lexical; a legalidade/posição da cláusula é do parser.
                if [(t.kind, t.value) for t in result.tokens[-3:]] == [
                    ("KEYWORD", "DECIMAL-POINT"), ("KEYWORD", "IS"), ("KEYWORD", "COMMA"),
                ]:
                    state.decimal_point = ","
                index = end
                continue

            self._error(result, source, index, "INVALID_CHARACTER", f"Caractere {current!r} não reconhecido.")
            index += 1
