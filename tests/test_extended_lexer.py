import json
from pathlib import Path
import subprocess
import sys
import unittest

from cobol_lexer import CobolLexer
from test_lexer import fixed


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_NAMES = (
    "prog001_divisoes.cob", "prog002_operacoes.cob", "prog003_calculadora.cob",
    "prog004_folha_pgto.cob", "prog005_strings.cob", "prog006_files.cob", "prog007_loja.cob",
)


class ExtendedLexerTests(unittest.TestCase):
    def scan(self, *lines: str):
        return CobolLexer().tokenize("\n".join(lines))

    def test_extended_keywords(self):
        for word in (
            "PROGRAM-ID", "WORKING-STORAGE", "ADD", "COMPUTE", "END-IF",
            "INSPECT", "EVALUATE", "READ", "WRITE", "VALUE", "UPPER-CASE",
        ):
            with self.subTest(word=word):
                result = self.scan(fixed(word.lower()))
                self.assertTrue(result.success, result.diagnostics)
                self.assertEqual([(t.kind, t.value) for t in result.tokens], [("KEYWORD", word)])

    def test_underscore_identifier_is_one_token(self):
        result = self.scan(fixed("PROGRAM-ID. prog007_loja."))
        self.assertTrue(result.success, result.diagnostics)
        token = result.tokens[2]
        self.assertEqual((token.kind, token.lexeme, token.value), ("IDENTIFIER", "prog007_loja", "PROG007_LOJA"))
        self.assertEqual((token.line, token.column, token.end_column), (1, 24, 35))

    def test_invalid_underscore_identifiers(self):
        for word in ("_NAME", "NAME_", "_"):
            with self.subTest(word=word):
                result = self.scan(fixed(word))
                self.assertEqual([error.code for error in result.diagnostics], ["INVALID_IDENTIFIER"])
                self.assertEqual(result.tokens, [])

    def test_operators_use_longest_match(self):
        result = self.scan(fixed("= < > <= >= <> + - * / **"))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([t.kind for t in result.tokens], [
            "EQUAL", "LESS_THAN", "GREATER_THAN", "LESS_EQUAL", "GREATER_EQUAL",
            "NOT_EQUAL", "PLUS", "MINUS", "MULTIPLY", "DIVIDE", "POWER",
        ])
        self.assertEqual([t.lexeme for t in result.tokens], "= < > <= >= <> + - * / **".split())

    def test_expression_and_signed_literals(self):
        result = self.scan(fixed("COMPUTE TOTAL = (COUNT+1) ** -2 / +3."))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([(t.kind, t.value) for t in result.tokens], [
            ("KEYWORD", "COMPUTE"), ("IDENTIFIER", "TOTAL"), ("EQUAL", "="),
            ("LPAREN", "("), ("IDENTIFIER", "COUNT"), ("PLUS", "+"),
            ("NUMBER", "1"), ("RPAREN", ")"), ("POWER", "**"),
            ("NUMBER", "-2"), ("DIVIDE", "/"), ("NUMBER", "+3"), ("PERIOD", "."),
        ])

    def test_invalid_signed_word(self):
        result = self.scan(fixed("MOVE +12_BAD TO TARGET."))
        self.assertEqual([error.code for error in result.diagnostics], ["INVALID_WORD"])
        self.assertEqual([t.value for t in result.tokens], ["MOVE", "TO", "TARGET", "."])

    def test_unicode_digit_after_sign_does_not_crash(self):
        result = self.scan(fixed("MOVE +١ TO TARGET."))
        self.assertEqual([error.code for error in result.diagnostics], ["INVALID_CHARACTER"])
        self.assertEqual(result.tokens[-2].value, "TARGET")

    def test_picture_masks_are_single_tokens(self):
        for picture in ("X(10)", "A(01)", "9", "9(5)V99", "S9(05)V9(02)", "-ZZZZZZZZZ9.99", "ZZ,ZZ9.99CR"):
            with self.subTest(picture=picture):
                result = self.scan(fixed(f"PIC {picture}."))
                self.assertTrue(result.success, result.diagnostics)
                self.assertEqual([(t.kind, t.value) for t in result.tokens], [
                    ("KEYWORD", "PIC"), ("PICTURE", picture), ("PERIOD", "."),
                ])
                token = result.tokens[1]
                self.assertEqual((token.column, token.end_column), (16, 15 + len(picture)))

    def test_picture_is_on_next_line(self):
        result = self.scan(fixed("PICTURE"), fixed("IS"), fixed("s9(05)v99 VALUE -1."))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([(t.kind, t.value) for t in result.tokens], [
            ("KEYWORD", "PICTURE"), ("KEYWORD", "IS"), ("PICTURE", "S9(05)V99"),
            ("KEYWORD", "VALUE"), ("NUMBER", "-1"), ("PERIOD", "."),
        ])
        self.assertEqual((result.tokens[2].line, result.tokens[2].column), (3, 12))

    def test_picture_context_does_not_leak(self):
        lexer = CobolLexer()
        lexer.tokenize(fixed("PIC"))
        result = lexer.tokenize(fixed("X(10)."))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([t.kind for t in result.tokens], ["IDENTIFIER", "LPAREN", "NUMBER", "RPAREN", "PERIOD"])

    def test_invalid_pictures_recover(self):
        for picture in ("X(0)", "X(00)", "X(-2)", "X(2", "X(2))", "X(Q)", "X@"):
            with self.subTest(picture=picture):
                result = self.scan(fixed(f"PIC {picture} VALUE 1."))
                self.assertEqual([error.code for error in result.diagnostics], ["INVALID_PICTURE"])
                self.assertEqual([t.value for t in result.tokens], ["PIC", "VALUE", "1", "."])

    def test_continued_word_has_physical_span(self):
        result = self.scan(fixed("MOVE 1 TO T"), fixed("AB-TRABALHADOR.", indicator="-", area="A"))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([t.value for t in result.tokens], ["MOVE", "1", "TO", "TAB-TRABALHADOR", "."])
        token = result.tokens[3]
        self.assertEqual((token.line, token.column, token.end_line, token.end_column), (1, 22, 2, 21))
        self.assertEqual((result.tokens[4].line, result.tokens[4].column), (2, 22))

    def test_continuation_after_closed_literal(self):
        result = self.scan(fixed('DISPLAY "TOTAL:"'), fixed("WRK-TOTAL.", indicator="-"))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([t.value for t in result.tokens], ["DISPLAY", "TOTAL:", "WRK-TOTAL", "."])
        self.assertEqual((result.tokens[2].line, result.tokens[2].column), (2, 12))

    def test_keyword_and_number_continuation(self):
        result = self.scan(fixed("DIS"), fixed("PLAY 12", indicator="-"), fixed("3.45.", indicator="-"))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([(t.kind, t.value) for t in result.tokens], [
            ("KEYWORD", "DISPLAY"), ("NUMBER", "123.45"), ("PERIOD", "."),
        ])

    def test_picture_continuation(self):
        result = self.scan(fixed("PIC S9(5)V"), fixed("99.", indicator="-"))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual(result.tokens[1].value, "S9(5)V99")
        self.assertEqual((result.tokens[1].line, result.tokens[1].end_line, result.tokens[1].end_column), (1, 2, 13))

    def test_comments_and_debug_lines_between_continuations(self):
        result = self.scan(
            fixed("MOVE TAB-"), fixed("IGNORED", indicator="*"),
            fixed("IGNORED", indicator="D"), fixed("TRABALHADOR TO TARGET.", indicator="-"),
        )
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([t.value for t in result.tokens], ["MOVE", "TAB-TRABALHADOR", "TO", "TARGET", "."])
        self.assertEqual(result.tokens[1].end_line, 4)

    def test_continued_word_length_is_validated_after_joining(self):
        result = self.scan(fixed("X" * 20), fixed("X" * 11 + ".", indicator="-"))
        self.assertEqual([error.code for error in result.diagnostics], ["IDENTIFIER_TOO_LONG"])
        self.assertEqual([t.kind for t in result.tokens], ["PERIOD"])

    def test_ignored_lines_between_continuations(self):
        for ignored in (
            "000100", fixed("COMMENT\t'", indicator="*"),
            fixed("COMMENT\t'", indicator="/"), fixed("DISPLAY\t'IGNORED'", indicator="D"),
        ):
            with self.subTest(ignored=ignored):
                string_result = self.scan(fixed('DISPLAY "AB'), ignored, fixed('"CD".', indicator="-"))
                self.assertTrue(string_result.success, string_result.diagnostics)
                self.assertEqual([t.value for t in string_result.tokens], ["DISPLAY", "ABCD", "."])
                token = string_result.tokens[1]
                self.assertEqual((token.line, token.column, token.end_line, token.end_column), (1, 20, 3, 15))
                word_result = self.scan(fixed("MOVE TAB-"), ignored, fixed("TRABALHADOR TO TARGET.", indicator="-"))
                self.assertTrue(word_result.success, word_result.diagnostics)
                self.assertEqual([t.value for t in word_result.tokens], ["MOVE", "TAB-TRABALHADOR", "TO", "TARGET", "."])
                self.assertEqual((word_result.tokens[1].line, word_result.tokens[1].end_line), (1, 3))

    def test_error_in_continuation_has_physical_position(self):
        result = self.scan(fixed('DISPLAY "TEXT"'), fixed("@ STOP RUN.", indicator="-"))
        self.assertEqual([(e.code, e.line, e.column) for e in result.diagnostics], [("INVALID_CHARACTER", 2, 12)])
        self.assertEqual([t.value for t in result.tokens], ["DISPLAY", "TEXT", "STOP", "RUN", "."])

    def test_continued_string_with_escaped_quote(self):
        result = self.scan(fixed('DISPLAY "A""B'), fixed('"C".', indicator="-"))
        self.assertTrue(result.success, result.diagnostics)
        token = result.tokens[1]
        self.assertEqual((token.lexeme, token.value), ('"A""BC"', 'A"BC'))
        self.assertEqual((token.line, token.column, token.end_line, token.end_column), (1, 20, 2, 14))

    def test_examples_via_json_cli(self):
        for name in EXAMPLE_NAMES:
            with self.subTest(name=name):
                process = subprocess.run(
                    [sys.executable, "-m", "cobol_lexer", str(PROJECT_ROOT / "examples" / "ebasso" / name), "--json"],
                    cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10,
                )
                self.assertEqual(process.returncode, 0, process.stderr or process.stdout)
                payload = json.loads(process.stdout)
                self.assertEqual(payload["diagnostics"], [])
                self.assertGreater(len(payload["tokens"]), 0)
                self.assertEqual(payload["tokens"][0]["value"], "IDENTIFICATION")

    def test_imported_split_identifiers_are_reassembled(self):
        for name, start_line, end_line in (("prog004_folha_pgto.cob", 27, 28), ("prog006_files.cob", 48, 49)):
            with self.subTest(name=name):
                source = (PROJECT_ROOT / "examples" / "ebasso" / name).read_text(encoding="utf-8-sig")
                result = CobolLexer().tokenize(source)
                tokens = [t for t in result.tokens if t.line == start_line and t.column == 72]
                self.assertEqual(len(tokens), 1)
                token = tokens[0]
                self.assertEqual((token.kind, token.value, token.end_line, token.end_column),
                                 ("IDENTIFIER", "TAB-TRABALHADOR", end_line, 21))


if __name__ == "__main__":
    unittest.main()
