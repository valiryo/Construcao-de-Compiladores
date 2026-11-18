"""Interface para CLI, testes e futura análise semântica."""

from dataclasses import dataclass
from pathlib import Path

from .parser import Parser, ParseResult
from .preprocessor import Preprocessor, PreprocessResult


@dataclass(slots=True)
class FrontendResult:
    preprocessed: PreprocessResult
    parsed: ParseResult | None

    @property
    def success(self):
        return self.preprocessed.success and self.parsed is not None and self.parsed.success

    @property
    def ast(self):
        return self.parsed.ast if self.success else None

    @property
    def diagnostics(self):
        return self.preprocessed.diagnostics + (self.parsed.diagnostics if self.parsed else [])


def _parse(preprocessed, copybook):
    parsed = Parser(preprocessed.tokens, root_file=preprocessed.root_file, source_format=preprocessed.source_format,
                    dialect=preprocessed.dialect).parse(copybook=copybook) if preprocessed.success else None
    return FrontendResult(preprocessed, parsed)


def parse_file(path, *, include_dirs=(), copybook=None, debug_lines=False, source_format='fixed', dialect='project'):
    path = Path(path)
    return _parse(Preprocessor(include_dirs, debug_lines=debug_lines,source_format=source_format,dialect=dialect).process(path),
                  path.suffix.lower() == ".cpy" if copybook is None else copybook)


def parse_source(source, *, filename="<memory>", include_dirs=(), copybook=False, source_format='fixed', dialect='project'):
    return _parse(Preprocessor(include_dirs,source_format=source_format,dialect=dialect).process_text(source, filename=filename), copybook)
