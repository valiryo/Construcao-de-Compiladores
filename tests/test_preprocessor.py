from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cobol_compiler import Preprocessor
from test_lexer import fixed


class PreprocessorTests(unittest.TestCase):
    def test_nested_copy_and_physical_origin(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(fixed("COPY OUTER-BOOK."))
            (root / "outer-book.cpy").write_text(fixed("01 GRP.") + "\n" + fixed("COPY INNER-BOOK."))
            (root / "INNER-BOOK.cpy").write_text(fixed("05 FIELD PIC X(2)."))
            result = Preprocessor().process(root / "p.cbl")
            self.assertTrue(result.success, result.diagnostics)
            field = next(t for t in result.tokens if t.value == "FIELD")
            self.assertEqual((Path(field.span.start.file).name, field.span.start.line, field.span.start.column), ("INNER-BOOK.cpy", 1, 15))
            self.assertEqual((field.token.line, field.token.column), (1, 15))
            self.assertEqual([Path(s.file).name for s in field.span.start.inclusion_stack], ["p.cbl", "outer-book.cpy"])
            self.assertEqual([d.name for d in result.dependencies], ["OUTER-BOOK", "INNER-BOOK"])

    def test_relative_before_include_directory(self):
        with TemporaryDirectory() as d:
            root = Path(d); include = root / "books"; include.mkdir()
            (root / "p.cbl").write_text(fixed('COPY "a.cpy".'))
            (root / "a.cpy").write_text(fixed("01 LOCAL-FIELD PIC X."))
            (include / "a.cpy").write_text(fixed("01 OTHER-FIELD PIC X."))
            result = Preprocessor([include]).process(root / "p.cbl")
            self.assertIn("LOCAL-FIELD", [t.value for t in result.tokens])
            (root / "a.cpy").unlink()
            result = Preprocessor([include]).process(root / "p.cbl")
            self.assertIn("OTHER-FIELD", [t.value for t in result.tokens])

    def test_missing_and_cycle(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "p.cbl"
            p.write_text(fixed("COPY ABSENT."))
            result = Preprocessor().process(p)
            self.assertEqual([d.code for d in result.diagnostics], ["COPY_NOT_FOUND"])
            self.assertEqual(result.diagnostics[0].span.start.column, 12)
            p.write_text(fixed('COPY "p.cbl".'))
            self.assertEqual([d.code for d in Preprocessor().process(p).diagnostics], ["COPY_CYCLE"])

    def test_decimal_context_applies_inside_copybook(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(fixed("DECIMAL-POINT IS COMMA.") + "\n" + fixed("COPY BOOK."))
            (root / "BOOK.cpy").write_text(fixed("01 N PIC 9V99 VALUE 1,25."))
            result = Preprocessor().process(root / "p.cbl")
            self.assertTrue(result.success, result.diagnostics)
            n = next(t for t in result.tokens if t.token.lexeme == "1,25")
            self.assertEqual(n.value, "1.25")
            self.assertEqual(Path(n.span.start.file).name, "BOOK.cpy")

    def test_comments_literals_and_continuation(self):
        result = Preprocessor().process_text("\n".join([
            fixed("COPY ABSENT.", indicator="*"), fixed('DISPLAY "COPY ABSENT.".'),
            fixed("*> COPY ABSENT."), fixed("MOVE LONG-"), fixed("FIELD TO TARGET.", indicator="-"),
        ]))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual(result.dependencies, [])
        token = next(t for t in result.tokens if t.value == "LONG-FIELD")
        self.assertEqual((token.span.start.line, token.span.end.line), (4, 5))

    def test_two_copy_directives_and_surrounding_code(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(fixed("COPY A. COPY A. DISPLAY 'OK'."))
            (root / "A.cpy").write_text(fixed("CONTINUE"))
            result = Preprocessor().process(root / "p.cbl")
            self.assertTrue(result.success, result.diagnostics)
            self.assertEqual([t.value for t in result.tokens], ["CONTINUE", "CONTINUE", "DISPLAY", "OK", "."])
            self.assertEqual(result.tokens[-3].span.start.column, 28)

    def test_lexical_diagnostic_from_copy_has_inclusion_stack(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(fixed("COPY BAD."))
            (root / "BAD.cpy").write_text(fixed("DISPLAY @."))
            result = Preprocessor().process(root / "p.cbl")
            error = result.diagnostics[0]
            self.assertEqual((error.code, error.span.start.column), ("INVALID_CHARACTER", 20))
            self.assertEqual(Path(error.span.start.file).name, "BAD.cpy")
            self.assertIn("incluído de", error.format())

    def test_bad_copy_syntax_and_explicit_unsupported(self):
        for source, code in (("COPY .", "COPY_SYNTAX"), ("COPY A", "COPY_SYNTAX"),
                             ("COPY A REPLACING X BY Y.", "UNSUPPORTED_COPY_REPLACING")):
            result = Preprocessor().process_text(fixed(source))
            self.assertIn(code, [d.code for d in result.diagnostics])
            self.assertFalse(result.success)

    def test_all_known_copybooks_expand(self):
        root = Path(__file__).resolve().parents[1]
        for file, book in (("CAD0002A.cbl", "COPY002A.cpy"), ("PROG024A.cbl", "COD001A.cpy")):
            result = Preprocessor([root / "examples/dependencias"]).process(root / "examples/oficiais" / file)
            self.assertTrue(result.success, result.diagnostics)
            self.assertNotIn("COPY", [t.value for t in result.tokens])
            self.assertTrue(any(Path(t.span.start.file).name == book for t in result.tokens))

    def test_invalid_character_inside_copy_is_not_erased(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(fixed("COPY BOOK @."))
            (root / "BOOK.cpy").write_text(fixed("01 FIELD PIC X."))
            result = Preprocessor().process(root / "p.cbl")
            self.assertFalse(result.success)
            self.assertEqual([(x.code, x.span.start.line, x.span.start.column) for x in result.diagnostics], [("INVALID_CHARACTER", 1, 22)])

    def test_continued_copy_name_and_depth_limit(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(fixed("COPY BO") + "\n" + fixed("OK.", indicator="-"))
            (root / "BOOK.cpy").write_text(fixed("01 FIELD PIC X."))
            result = Preprocessor().process(root / "p.cbl")
            self.assertTrue(result.success, result.diagnostics)
            self.assertEqual(result.dependencies[0].name, "BOOK")
            result = Preprocessor(max_depth=0).process(root / "p.cbl")
            self.assertEqual([d.code for d in result.diagnostics], ["COPY_DEPTH"])

    def test_copybook_can_supply_picture_in_enclosing_context(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(fixed("01 FIELD PIC") + "\n" + fixed("COPY MASK."))
            (root / "MASK.cpy").write_text(fixed("X(10)."))
            result = Preprocessor().process(root / "p.cbl")
            self.assertTrue(result.success, result.diagnostics)
            self.assertEqual([(t.kind, t.value) for t in result.tokens], [
                ("NUMBER", "01"), ("IDENTIFIER", "FIELD"), ("KEYWORD", "PIC"), ("PICTURE", "X(10)"), ("PERIOD", "."),
            ])


if __name__ == "__main__":
    unittest.main()
