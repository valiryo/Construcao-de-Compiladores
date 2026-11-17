"""Front-end COBOL: pré-processamento localizado e análise sintática."""

from .preprocessor import Preprocessor, PreprocessResult
from .source import LocatedToken, SourceLocation, SourceSpan
from .frontend import FrontendResult, parse_file, parse_source
from .parser import Parser, ParseResult
from .semantic import SemanticResult, analyze, check_file, check_source

__all__ = ["Preprocessor", "PreprocessResult", "LocatedToken", "SourceLocation", "SourceSpan",
           "Parser", "ParseResult", "FrontendResult", "parse_file", "parse_source",
           "SemanticResult", "analyze", "check_file", "check_source"]
