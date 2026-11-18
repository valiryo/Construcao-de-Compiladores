"""COPY com origem física. Tokeniza pelo lexer existente, sem regex de COBOL.

Uma passagem preliminar identifica diretivas; o texto expandido é tokenizado uma
única vez no contexto do programa (PIC e convenção decimal inclusive).
"""

from dataclasses import dataclass, field, replace
from pathlib import Path

from cobol_lexer import CobolLexer

from .diagnostics import Diagnostic
from .source import IncludeSite, LocatedToken, SourceLocation, SourceSpan, display_path


@dataclass(frozen=True, slots=True)
class SourceLine:
    text: str
    file: str
    line: int
    inclusion_stack: tuple[IncludeSite, ...]


@dataclass(frozen=True, slots=True)
class CopyDependency:
    name: str
    resolved_file: str | None
    span: SourceSpan


@dataclass(slots=True)
class PreprocessResult:
    tokens: list[LocatedToken] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    dependencies: list[CopyDependency] = field(default_factory=list)
    lines: list[SourceLine] = field(default_factory=list)
    root_file: str = ""

    @property
    def success(self) -> bool:
        return not self.diagnostics


class Preprocessor:
    def __init__(self, include_dirs=(), *, debug_lines: bool = False, max_depth: int = 128):
        self.include_dirs = tuple(Path(p).resolve() for p in include_dirs)
        self.debug_lines = debug_lines
        self.max_depth = max_depth

    def process(self, path: str | Path) -> PreprocessResult:
        path = Path(path).resolve()
        result = PreprocessResult(root_file=str(path))
        self._expand(path, (), (), result)
        self._tokenize(result)
        return result

    def process_text(self, source: str, *, filename: str = "<memory>") -> PreprocessResult:
        """Conveniência para testes/ferramentas; COPY relativo usa o diretório indicado."""
        result = PreprocessResult(root_file=filename)
        self._expand(Path(filename), (), (), result, source=source)
        self._tokenize(result)
        return result

    def _resolve(self, name: str, parent: Path) -> Path | None:
        # Ordem determinística: diretório do incluindo, depois -I; literal exato
        # antes de extensões. Caixa flexível apenas quando não há nome exato.
        requested = Path(name)
        candidates = [requested] if requested.suffix else [requested, Path(name + ".cpy"), Path(name + ".cbl"), Path(name + ".cob")]
        for directory in (parent, *self.include_dirs):
            for candidate in candidates:
                target = directory / candidate
                if target.is_file():
                    return target.resolve()
                folder = target.parent
                if folder.is_dir():
                    matches = sorted(p for p in folder.iterdir() if p.is_file() and p.name.casefold() == target.name.casefold())
                    if len(matches) == 1:
                        return matches[0].resolve()
        return None

    @staticmethod
    def _point(path, line, column, stack):
        location = SourceLocation(str(path), line, column, stack)
        return SourceSpan(location, location)

    def _expand(self, path, stack, active, result, *, source=None):
        file = str(path) if str(path).startswith("<") else display_path(path)
        if source is None:
            try:
                source = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                result.diagnostics.append(Diagnostic("SOURCE_READ_ERROR", str(exc), self._point(file, 1, 1, stack), "preprocessor"))
                return
        raw_lines = source.splitlines()
        scan = CobolLexer(debug_lines=self.debug_lines,preserve_literal_padding=True).tokenize(source)
        directives = []
        i = 0
        while i < len(scan.tokens):
            token = scan.tokens[i]
            if token.kind != "KEYWORD" or token.value != "COPY":
                i += 1
                continue
            start = token
            i += 1
            span = self._point(file, token.line, token.column, stack)
            if i >= len(scan.tokens) or scan.tokens[i].kind not in ("IDENTIFIER", "STRING"):
                result.diagnostics.append(Diagnostic("COPY_SYNTAX", "COPY requer nome de copybook e ponto.", span, "preprocessor", "nome de copybook", scan.tokens[i].value if i < len(scan.tokens) else "EOF"))
                continue
            name = scan.tokens[i].value
            if not name:
                result.diagnostics.append(Diagnostic("COPY_SYNTAX", "Nome de copybook vazio.", span, "preprocessor", "nome não vazio", "literal vazio"))
            i += 1
            unsupported = i < len(scan.tokens) and scan.tokens[i].value == "REPLACING"
            if unsupported:
                result.diagnostics.append(Diagnostic("UNSUPPORTED_COPY_REPLACING", "COPY REPLACING não ocorre no corpus e ainda não é implementado.", span, "preprocessor"))
                while i < len(scan.tokens) and scan.tokens[i].kind != "PERIOD":
                    i += 1
            if i >= len(scan.tokens) or scan.tokens[i].kind != "PERIOD":
                result.diagnostics.append(Diagnostic("COPY_SYNTAX", "Diretiva COPY não terminada corretamente.", span, "preprocessor", ".", scan.tokens[i].value if i < len(scan.tokens) else "EOF"))
                continue
            end = scan.tokens[i]
            i += 1
            for error in scan.diagnostics:
                if (start.line, start.column) <= (error.line, error.column) <= (end.end_line, end.end_column):
                    point = self._point(file, error.line, error.column, stack)
                    result.diagnostics.append(Diagnostic(error.code, error.message, point, "lexer"))
            target = None if unsupported else self._resolve(name, path.parent.resolve())
            result.dependencies.append(CopyDependency(name, str(target) if target else None, span))
            included = []
            if not unsupported:
                if target is None:
                    result.diagnostics.append(Diagnostic("COPY_NOT_FOUND", f"Copybook {name!r} não encontrado nos caminhos locais/-I.", span, "preprocessor"))
                elif target in (*active, path.resolve()):
                    result.diagnostics.append(Diagnostic("COPY_CYCLE", f"Ciclo de inclusão de {target.name}.", span, "preprocessor"))
                elif len(stack) >= self.max_depth:
                    result.diagnostics.append(Diagnostic("COPY_DEPTH", f"Limite de {self.max_depth} inclusões excedido.", span, "preprocessor"))
                else:
                    nested = PreprocessResult()
                    self._expand(target, stack + (IncludeSite(file, start.line, start.column),), (*active, path.resolve()), nested)
                    included = nested.lines
                    result.diagnostics.extend(nested.diagnostics)
                    result.dependencies.extend(nested.dependencies)
            directives.append((start, end, included))
        # Partições conservam as colunas originais. Linhas com prefixo/sufixo da
        # diretiva são mascaradas, não reindentadas ou retokenizadas manualmente.
        cursor_line, cursor_col = 1, 0
        def append_piece(line_no, begin, end):
            raw = raw_lines[line_no - 1]
            text = " " * begin + raw[begin:end]
            if begin:
                text = "       " + text[7:]
            result.lines.append(SourceLine(text, file, line_no, stack))
        for start, end, included in directives:
            for line_no in range(cursor_line, start.line):
                append_piece(line_no, cursor_col if line_no == cursor_line else 0, None)
            if start.line == cursor_line:
                begin = cursor_col
            else:
                begin = 0
            if raw_lines[start.line - 1][max(7, begin):start.column - 1].strip():
                append_piece(start.line, begin, start.column - 1)
            result.lines.extend(included)
            cursor_line, cursor_col = end.end_line, end.end_column
        for line_no in range(cursor_line, len(raw_lines) + 1):
            append_piece(line_no, cursor_col if line_no == cursor_line else 0, None)

    def _tokenize(self, result):
        scan = CobolLexer(debug_lines=self.debug_lines,preserve_literal_padding=True).tokenize("\n".join(line.text for line in result.lines))
        def location(line, column):
            row = result.lines[line - 1]
            return SourceLocation(row.file, row.line, column, row.inclusion_stack)
        for t in scan.tokens:
            span = SourceSpan(location(t.line, t.column), location(t.end_line, t.end_column))
            physical = replace(t, line=span.start.line, column=span.start.column,
                               end_line=span.end.line, end_column=span.end.column)
            result.tokens.append(LocatedToken(physical, span))
        for error in scan.diagnostics:
            p = location(error.line, error.column)
            result.diagnostics.append(Diagnostic(error.code, error.message, SourceSpan(p, p), "lexer"))
