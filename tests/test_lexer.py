import unittest

from cobol_lexer import CobolLexer


def fixed(body: str, *, indicator: str = " ", seq: str = "000100", area: str = "B", tail: str = "") -> str:
    assert len(seq) == 6
    indent = "    " if area == "B" else ""
    beginning = seq + indicator + indent + body
    assert len(beginning) <= 72, f"Linha de teste excede col. 72: {beginning!r}"
    return beginning.ljust(72) + tail


class CobolLexerTests(unittest.TestCase):
    def scan(self, *lines, debug_lines=False):
        return CobolLexer(debug_lines=debug_lines).tokenize("\n".join(lines))

    def test_keywords_and_period(self):
        result = self.scan(fixed("IDENTIFICATION DIVISION.", area="A"))
        self.assertTrue(result.success)
        self.assertEqual([(t.kind, t.value) for t in result.tokens],
                         [("KEYWORD", "IDENTIFICATION"), ("KEYWORD", "DIVISION"), ("PERIOD", ".")])
        self.assertEqual((result.tokens[0].line, result.tokens[0].column, result.tokens[0].area), (1, 8, "A"))

    def test_case_insensitive_keywords(self):
        result = self.scan(fixed("display 'oi'."))
        self.assertTrue(result.success)
        self.assertEqual(result.tokens[0].kind, "KEYWORD")
        self.assertEqual(result.tokens[0].value, "DISPLAY")

    def test_all_reserved_words(self):
        for word in ["IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE", "DIVISION", "SECTION", "DISPLAY", "ACCEPT", "PERFORM", "STOP", "RUN", "IF", "ELSE", "MOVE"]:
            with self.subTest(word=word):
                r = self.scan(fixed(word))
                self.assertEqual(r.tokens[0].kind, "KEYWORD")

    def test_identifiers_and_hyphens(self):
        result = self.scan(fixed("PROGRAM-ID TESTE-123 A--B"))
        self.assertTrue(result.success)
        self.assertEqual([(x.kind, x.lexeme) for x in result.tokens], [("IDENTIFIER", "PROGRAM-ID"), ("IDENTIFIER", "TESTE-123"), ("IDENTIFIER", "A--B")])

    def test_numbers_signed_decimals_and_period(self):
        result = self.scan(fixed("01 -123.45 +8 42. 1.2"))
        self.assertTrue(result.success)
        self.assertEqual([(t.kind, t.lexeme) for t in result.tokens], [
            ("NUMBER", "01"), ("NUMBER", "-123.45"), ("NUMBER", "+8"),
            ("NUMBER", "42"), ("PERIOD", "."), ("NUMBER", "1.2")])

    def test_punctuation(self):
        result = self.scan(fixed("A,B;C(10)."))
        self.assertEqual([t.kind for t in result.tokens], ["IDENTIFIER", "COMMA", "IDENTIFIER", "SEMICOLON", "IDENTIFIER", "LPAREN", "NUMBER", "RPAREN", "PERIOD"])

    def test_quotes_and_doubled_quote(self):
        result = self.scan(fixed('DISPLAY "ELE DISSE ""OI""" \'TEXTO\'.'))
        self.assertTrue(result.success)
        self.assertEqual([t.value for t in result.tokens if t.kind == "STRING"], ['ELE DISSE "OI"', 'TEXTO'])

    def test_columns_1_to_6_and_73_onward_ignored(self):
        result = self.scan(fixed("MOVE 10.", seq="999999", tail="NADA-AQUI"))
        self.assertTrue(result.success)
        self.assertEqual([t.lexeme for t in result.tokens], ["MOVE", "10", "."])
        self.assertEqual(result.tokens[0].column, 12)

    def test_comment_lines_ignored(self):
        result = self.scan(fixed("INVALID @ CONTENT", indicator="*"), fixed("ANYTHING", indicator="/"), fixed("STOP RUN."))
        self.assertTrue(result.success)
        self.assertEqual([t.lexeme for t in result.tokens], ["STOP", "RUN", "."])

    def test_debug_lines_configurable(self):
        source = fixed("DISPLAY 'DEBUG'.", indicator="D")
        self.assertEqual(self.scan(source).tokens, [])
        self.assertEqual(len(self.scan(source, debug_lines=True).tokens), 3)

    def test_continuation_of_literal(self):
        result = self.scan(fixed('DISPLAY "OLA', area="B"), fixed('" MUNDO".', indicator="-", area="B"))
        self.assertTrue(result.success)
        self.assertEqual([t.value for t in result.tokens], ["DISPLAY", "OLA MUNDO", "."])
        self.assertEqual((result.tokens[1].line, result.tokens[1].column, result.tokens[1].end_line), (1, 20, 2))

    def test_continuation_without_repeated_quote(self):
        result = self.scan(fixed("DISPLAY 'AB"), fixed("CD'.", indicator="-"))
        self.assertTrue(result.success)
        self.assertEqual(result.tokens[1].value, "ABCD")

    def test_max_identifier_length(self):
        valid = "X" * 30
        invalid = "X" * 31
        self.assertTrue(self.scan(fixed(valid)).success)
        result = self.scan(fixed(invalid))
        self.assertEqual([e.code for e in result.diagnostics], ["IDENTIFIER_TOO_LONG"])
        self.assertEqual(result.tokens, [])

    def test_invalid_identifier_trailing_hyphen(self):
        result = self.scan(fixed("ABC-"))
        self.assertEqual([e.code for e in result.diagnostics], ["INVALID_IDENTIFIER"])

    def test_invalid_identifier_leading_hyphen(self):
        result = self.scan(fixed("-ABC"))
        self.assertEqual(result.diagnostics[0].code, "INVALID_CHARACTER")

    def test_invalid_unexpected_character(self):
        result = self.scan(fixed("DISPLAY @."))
        self.assertEqual([(e.code, e.column) for e in result.diagnostics], [("INVALID_CHARACTER", 20)])
        self.assertEqual([t.lexeme for t in result.tokens], ["DISPLAY", "."])

    def test_invalid_indicator(self):
        result = self.scan(fixed("DISPLAY 1.", indicator="?"))
        self.assertEqual(result.diagnostics[0].code, "INVALID_INDICATOR")
        self.assertEqual(result.diagnostics[0].column, 7)

    def test_continuation_without_previous_literal(self):
        result = self.scan(fixed('"TESTE"', indicator="-"))
        self.assertEqual(result.diagnostics[0].code, "UNEXPECTED_CONTINUATION")

    def test_unterminated_string_no_continuation(self):
        result = self.scan(fixed('DISPLAY "OLA'), fixed("STOP RUN."))
        self.assertEqual(result.diagnostics[0].code, "UNTERMINATED_STRING")
        self.assertEqual([t.lexeme for t in result.tokens if t.kind == "KEYWORD"], ["DISPLAY", "STOP", "RUN"])

    def test_unterminated_string_eof(self):
        result = self.scan(fixed("DISPLAY 'ABC"))
        self.assertEqual(result.diagnostics[0].code, "UNTERMINATED_STRING")

    def test_tab_in_code(self):
        result = self.scan(fixed("DISPLAY\t'ABC'"))
        self.assertEqual(result.diagnostics[0].code, "TAB_IN_SOURCE")

    def test_tab_in_sequence_columns(self):
        result = self.scan("\t00010 DISPLAY 1.")
        self.assertEqual(result.diagnostics[0].code, "TAB_IN_SOURCE")
        self.assertEqual(result.diagnostics[0].column, 1)

    def test_nonfixed_line(self):
        result = self.scan("MOVE")
        self.assertEqual(result.diagnostics[0].code, "INVALID_LINE")

    def test_empty_source(self):
        result = self.scan("", "", "      ")
        self.assertTrue(result.success)
        self.assertEqual(result.tokens, [])

    def test_long_word_not_fragmented(self):
        result = self.scan(fixed("A" * 31 + "."))
        self.assertEqual(result.diagnostics[0].code, "IDENTIFIER_TOO_LONG")
        self.assertEqual([t.kind for t in result.tokens], ["PERIOD"])


if __name__ == "__main__":
    unittest.main()
