"""Front-end COBOL: pré-processamento localizado e análise sintática."""

from .preprocessor import Preprocessor, PreprocessResult
from .source import LocatedToken, SourceLocation, SourceSpan

__all__ = ["Preprocessor", "PreprocessResult", "LocatedToken", "SourceLocation", "SourceSpan"]
