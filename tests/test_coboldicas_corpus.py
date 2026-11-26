"""Regressões do corpus fixado, sem acesso à rede ou compiladores externos."""

import hashlib
import json
from pathlib import Path
import unittest

from cobol_lexer import CobolLexer
from test_extended_lexer import run_cli
from test_lexer import fixed
from regression_corpus import audit_file, dependencies, OFFICIAL_NAMES
from tools.corpus_contracts import corpus_contracts, fingerprint


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_COUNTS = {
    "BUSCA01A.cbl": 208, "CAD0002A.cbl": 868, "CAD0004A.cbl": 133,
    "CAD0005A.cbl": 516, "CAIXAREG.cbl": 390, "CALCMD01.cbl": 285,
    "PROG024A.cbl": 1397,
}
NEGATIVES = {
    "CBREAKEX.cbl": ("INVALID_INDICATOR", 38),
    "PROG002A.cbl": ("MERGE_CONFLICT", 3),
    "PROG010A.cbl": ("MERGE_CONFLICT", 30),
    "PROG023C.cbl": ("MERGE_CONFLICT", 3),
    "PROG042A.cbl": ("IDENTIFIER_TOO_LONG", 2),
    "SORT001A.cbl": ("MERGE_CONFLICT", 3),
    "TELABMS.cbl": ("INVALID_CHARACTER", 2),
    "VALIDA1B.cbl": ("MERGE_CONFLICT", 27),
}


class CorpusTests(unittest.TestCase):
    def test_official_programs_and_cli(self):
        self.assertEqual(set(OFFICIAL_COUNTS), set(OFFICIAL_NAMES))
        for name, count in OFFICIAL_COUNTS.items():
            with self.subTest(name=name):
                folder = "corrigidos" if name == "CAD0005A.cbl" else "oficiais"
                path = ROOT / "examples" / folder / name
                result = CobolLexer().tokenize(path.read_text(encoding="utf-8-sig"))
                self.assertEqual(result.diagnostics, [])
                self.assertEqual(len(result.tokens), count)
                self.assertEqual(result.tokens[0].value, "IDENTIFICATION")
                process = run_cli(str(path), "--json")
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(len(json.loads(process.stdout)["tokens"]), count)

    def test_imported_bytes_match_manifest(self):
        manifest = json.loads((ROOT / "examples/manifesto-coboldicas.json").read_text())
        self.assertEqual(manifest["commit"], "1ffb3bf279bbb1e596b1091f1dda1cf7ddf51295")
        sources = 0
        for entry in manifest["files"]:
            with self.subTest(path=entry["path"]):
                self.assertEqual(hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest(), entry["sha256"])
                sources += entry["category"] != "referencia"
        self.assertEqual(sources, 85)

    def test_correction_changes_only_conflict_block(self):
        original = (ROOT / "examples/oficiais/CAD0005A.cbl").read_bytes()
        lines = original.splitlines(keepends=True)
        start = lines.index(b"<<<<<<< HEAD\n")
        self.assertEqual(lines[start + 1].rstrip(), lines[start + 3].rstrip())
        expected = b"".join(lines[:start] + [lines[start + 1]] + lines[start + 5:])
        actual = (ROOT / "examples/corrigidos/CAD0005A.cbl").read_bytes()
        self.assertEqual(actual, expected)
        self.assertEqual(hashlib.sha256(actual).hexdigest(), "19b1d31741229462db14bae6b83c4e014bb20a8902d8b023b7dcdecb3ddf009e")

    def test_original_conflict_is_negative(self):
        path = ROOT / "examples/oficiais/CAD0005A.cbl"
        result = CobolLexer().tokenize(path.read_text())
        self.assertEqual([(d.code, d.line, d.column) for d in result.diagnostics], [
            ("MERGE_CONFLICT", 97, 1), ("MERGE_CONFLICT", 99, 1), ("MERGE_CONFLICT", 101, 1),
        ])
        process = run_cli(str(path), "--json")
        self.assertEqual(process.returncode, 1)

    def test_complementary_corpus_positive_and_negative(self):
        paths = sorted((ROOT / "examples/complementares").glob("*"))
        self.assertEqual(len(paths), 75)
        for path in paths:
            with self.subTest(name=path.name):
                result = CobolLexer().tokenize(path.read_text(encoding="utf-8-sig"))
                if path.name in NEGATIVES:
                    code, count = NEGATIVES[path.name]
                    self.assertEqual([d.code for d in result.diagnostics], [code] * count)
                else:
                    self.assertEqual(result.diagnostics, [])

    def test_known_dependencies(self):
        for path in sorted((ROOT / "examples/dependencias").glob("*")):
            with self.subTest(name=path.name):
                self.assertTrue(CobolLexer().tokenize(path.read_text()).success)
        cases = {"CAD0002A.cbl": {("COPY", "COPY002A")},
                 "PROG024A.cbl": {("COPY", "COD001A"), ("CALL", "PROGDATA")}}
        for name, expected in cases.items():
            result = CobolLexer().tokenize((ROOT / "examples/oficiais" / name).read_text())
            deps = dependencies(result.tokens, {})
            self.assertEqual({(d["kind"], d["target"]) for d in deps if d["kind"] != "ASSIGN"}, expected)

    def test_physical_positions_and_original_lexemes(self):
        for folder in ("oficiais", "corrigidos", "dependencias", "complementares"):
            for path in sorted((ROOT / "examples" / folder).glob("*")):
                source = path.read_text(encoding="utf-8-sig")
                lines = source.splitlines()
                for t in CobolLexer().tokenize(source).tokens:
                    with self.subTest(path=path.name, line=t.line, col=t.column):
                        self.assertGreaterEqual(t.column, 8)
                        self.assertLessEqual(t.end_column, 72)
                        self.assertEqual(t.area, "A" if t.column <= 11 else "B")
                        if t.line == t.end_line:
                            self.assertEqual(lines[t.line - 1][t.column - 1:t.end_column], t.lexeme)

    def test_generated_audit_is_current(self):
        files = corpus_contracts()["files"]
        sources = {Path(p).name.upper(): p for p in files if "corrigidos" not in p}
        for path, item in files.items():
            with self.subTest(path=path):
                contract = item["lexer"]
                result = audit_file(ROOT / path, sources, contract["baseline"])
                self.assertEqual(fingerprint(result), contract["sha256"])


class CorpusFeatureTests(unittest.TestCase):
    def scan(self, *lines):
        return CobolLexer().tokenize("\n".join(lines))

    def test_corpus_keywords_and_nearby_identifiers(self):
        words = """EXIT GO END-PERFORM SPECIAL-NAMES DECIMAL-POINT CONTINUE
            NUMERIC END-READ VARYING REDEFINES LINKAGE USING CALL GOBACK
            INITIALIZE FILLER ALPHANUMERIC GREATER LESS LENGTH COMMA LINE
            SEQUENTIAL COMP EXTEND RETURN-CODE DATE DAY DAY-OF-WEEK
            YYYYMMDD YYYYDDD TIME CORR CORRESPONDING ROUNDED THEN ALTER
            PROCEED ASCENDING SD SORT UNSTRING DELIMITED BLANK SCREEN
            COLUMN REFERENCE DUPLICATES CRT NORMAL EXEC END-EXEC RETURN
            TRUE FALSE""".split()
        for word in words:
            with self.subTest(word=word):
                result = self.scan(fixed(f"{word.lower()} {word}-FIELD"))
                self.assertTrue(result.success, result.diagnostics)
                self.assertEqual([(t.kind, t.value) for t in result.tokens],
                                 [("KEYWORD", word), ("IDENTIFIER", word + "-FIELD")])

    def test_intrinsic_function_names_remain_contextual(self):
        for name in ("REVERSE", "MOD", "ORD", "RANDOM", "INTEGER", "INTEGER-OF-DATE"):
            result = self.scan(fixed(f"FUNCTION {name.lower()}(FIELD)"))
            self.assertTrue(result.success)
            self.assertEqual((result.tokens[1].kind, result.tokens[1].value), ("IDENTIFIER", name))

    def test_reference_modification(self):
        result = self.scan(fixed("MOVE CAMPO(INICIO:TAMANHO) TO OUT-FIELD."))
        self.assertTrue(result.success)
        colon = next(t for t in result.tokens if t.kind == "COLON")
        self.assertEqual((colon.lexeme, colon.line, colon.column, colon.end_column), (":", 1, 29, 29))
        # Parênteses ou índices inválidos pertencem ao parser, não ao lexer.
        self.assertTrue(self.scan(fixed("CAMPO(:) CAMPO(1:0) CAMPO(1:2")).success)

    def test_inline_comment_and_string_escape(self):
        result = self.scan(fixed('DISPLAY "A""*>B". *> @ \' lixo\t'))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([t.value for t in result.tokens], ["DISPLAY", 'A"*>B', "."])
        self.assertEqual(result.tokens[-1].column, 28)

    def test_inline_comment_without_space_after_picture(self):
        result = self.scan(fixed("01 FIELD PIC Z.ZZZ,ZZ.*> @"))
        self.assertTrue(result.success)
        self.assertEqual([t.kind for t in result.tokens], ["NUMBER", "IDENTIFIER", "KEYWORD", "PICTURE", "PERIOD"])
        self.assertEqual(result.tokens[-2].lexeme, "Z.ZZZ,ZZ")

    def test_inline_comments_between_continuations(self):
        result = self.scan(fixed("MOVE TAB- *> anotação"), fixed("*> comentário"),
                           fixed("FIELD TO TARGET.", indicator="-"))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual(result.tokens[1].value, "TAB-FIELD")
        self.assertEqual((result.tokens[1].line, result.tokens[1].column,
                          result.tokens[1].end_line, result.tokens[1].end_column), (1, 17, 3, 16))

    def test_comment_marker_in_continued_string(self):
        result = self.scan(fixed('DISPLAY "AB'), fixed('"*>CD". *> ignorado', indicator="-"))
        self.assertTrue(result.success)
        self.assertEqual(result.tokens[1].value, "AB*>CD")

    def test_inline_comment_does_not_hide_open_string_or_tab(self):
        self.assertEqual([d.code for d in self.scan(fixed('DISPLAY "AB *> comment')).diagnostics], ["UNTERMINATED_STRING"])
        self.assertEqual([d.code for d in self.scan(fixed("DISPLAY\t1 *> comment")).diagnostics], ["TAB_IN_SOURCE"])
        self.assertEqual([d.code for d in self.scan(fixed("DISPLAY @ *> ignored")).diagnostics], ["INVALID_CHARACTER"])

    def test_conflict_markers_and_safe_occurrences(self):
        for marker in ("<<<<<<< HEAD", "=======", ">>>>>>> branch", "||||||| base"):
            for source, column in ((marker, 1), (fixed(marker), 12)):
                result = self.scan(source, fixed("STOP RUN."))
                self.assertEqual([(d.code, d.line, d.column) for d in result.diagnostics], [("MERGE_CONFLICT", 1, column)])
                self.assertEqual([t.value for t in result.tokens], ["STOP", "RUN", "."])
            self.assertTrue(self.scan(fixed(marker, indicator="*")).success)
            self.assertTrue(self.scan(fixed(f'DISPLAY "{marker}".')).success)
            self.assertTrue(self.scan(fixed("STOP RUN.", tail=marker)).success)
        result = self.scan(fixed('DISPLAY "AB'), fixed('<<<<<<< HEAD".', indicator="-"))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual(result.tokens[1].value, "AB<<<<<<< HEAD")

    def test_decimal_comma_configuration_and_original_lexemes(self):
        result = self.scan(fixed("SPECIAL-NAMES."), fixed("decimal-point IS"),
                           fixed("comma."), fixed("MOVE -12,50 TO FIELD. DISPLAY 1,25, +2,00."))
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual([(t.lexeme, t.value) for t in result.tokens if t.kind == "NUMBER"],
                         [("-12,50", "-12.50"), ("1,25", "1.25"), ("+2,00", "+2.00")])
        self.assertEqual([t.kind for t in result.tokens[-4:]], ["NUMBER", "COMMA", "NUMBER", "PERIOD"])
        number = next(t for t in result.tokens if t.lexeme == "-12,50")
        self.assertEqual((number.line, number.column, number.end_column), (4, 17, 22))

    def test_decimal_configuration_ignores_strings_and_comments(self):
        result = self.scan(fixed('DISPLAY "DECIMAL-POINT IS COMMA".'),
                           fixed("*> DECIMAL-POINT IS COMMA."), fixed("MOVE 1,25 TO FIELD."))
        self.assertTrue(result.success)
        self.assertEqual([(t.kind, t.value) for t in result.tokens[3:6]],
                         [("KEYWORD", "MOVE"), ("NUMBER", "1"), ("COMMA", ",")])

    def test_decimal_state_resets_between_calls_and_programs(self):
        lexer = CobolLexer()
        lexer.tokenize(fixed("DECIMAL-POINT IS COMMA."))
        result = lexer.tokenize(fixed("DISPLAY 1.25."))
        self.assertEqual(result.tokens[1].value, "1.25")
        result = self.scan(fixed("DECIMAL-POINT IS COMMA."), fixed("PROGRAM-ID. SECOND."), fixed("DISPLAY 1.25."))
        self.assertEqual(result.tokens[-2].lexeme, "1.25")

    def test_decimal_invalid_words_recover_in_both_modes(self):
        for clause, number in (("", "12.5"), ("DECIMAL-POINT IS COMMA.", "12,5")):
            for sign in ("", "+", "-"):
                with self.subTest(clause=clause, sign=sign):
                    result = self.scan(fixed(clause), fixed(f"MOVE {sign}{number}BAD TO FIELD."))
                    self.assertEqual([(d.code, d.line, d.column) for d in result.diagnostics], [("INVALID_WORD", 2, 17)])
                    self.assertEqual([t.value for t in result.tokens[-4:]], ["MOVE", "TO", "FIELD", "."])

    def test_corpus_masks_and_negative_masks(self):
        for mask in ("ZZZ.ZZZ.ZZZ,ZZ", "Z.ZZZ.ZZZ,ZZ", "---,---,--9.99", "S9(11)V9(6)", "V999"):
            result = self.scan(fixed(f"PIC {mask}."))
            self.assertTrue(result.success, result.diagnostics)
            self.assertEqual((result.tokens[1].kind, result.tokens[1].lexeme), ("PICTURE", mask))
        for mask in ("Z.ZZZ,ZZ@", "S9(0)V99", "X(2):", "ZZZ(ABC)"):
            self.assertEqual([d.code for d in self.scan(fixed(f"PIC {mask} VALUE 0.")).diagnostics], ["INVALID_PICTURE"])


if __name__ == "__main__":
    unittest.main()
