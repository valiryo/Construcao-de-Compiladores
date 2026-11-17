"""Invariantes e exemplos pequenos independentes dos snapshots de cobertura."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from cobol_compiler import parse_source, parse_file
from cobol_compiler import ast as A
from test_lexer import fixed


ROOT = Path(__file__).resolve().parents[1]


def program(*body, data=(), environment=()):
    lines = [fixed("IDENTIFICATION DIVISION.", area="A"), fixed("PROGRAM-ID. TEST-PROGRAM.", area="A")]
    if environment:
        lines += [fixed("ENVIRONMENT DIVISION.", area="A"), *environment]
    if data:
        lines += [fixed("DATA DIVISION.", area="A"), fixed("WORKING-STORAGE SECTION.", area="A")]
        lines += [fixed(line) for line in data]
    lines += [fixed("PROCEDURE DIVISION.", area="A")]
    lines += [fixed(line) for line in body]
    return "\n".join(lines)


class ParserTests(unittest.TestCase):
    def good(self, *body, **kwargs):
        result = parse_source(program(*body, **kwargs))
        self.assertTrue(result.success, "\n".join(d.format() for d in result.diagnostics) + repr(result.parsed.structural_errors if result.parsed else None))
        self.assertEqual(result.parsed.skipped_tokens, 0)
        self.assertEqual(result.parsed.consumed_tokens, len(result.preprocessed.tokens))
        self.assertEqual(A.validate_structure(result.ast, len(result.preprocessed.tokens)), [])
        return result

    def nodes(self, result, cls):
        return [n for n in A.walk(result.ast) if isinstance(n, cls)]

    def bad(self, *body, **kwargs):
        result = parse_source(program(*body, **kwargs))
        self.assertFalse(result.success)
        self.assertIsNone(result.ast)
        self.assertTrue(result.diagnostics)
        return result

    def test_minimal_program_and_metadata(self):
        result = self.good("STOP RUN.")
        self.assertIsNone(result.ast.environment)
        self.assertIsNone(result.ast.data)
        self.assertEqual(result.ast.identification.program_id, "TEST-PROGRAM")
        self.assertEqual(len(self.nodes(result, A.StopRun)), 1)

    def test_data_hierarchy_redefines_and_conditions(self):
        result = self.good("STOP RUN.", data=(
            "01 GRP.", "05 FIELD PIC X(10) VALUE SPACES.",
            "05 VIEW-FIELD REDEFINES FIELD PIC 9(10).",
            "88 VALID-FIELD VALUE 1 THRU 5, 9.", "77 SINGLE-FIELD PIC 9.",
        ))
        entries = result.ast.data.sections[0].entries
        self.assertEqual([n.name for n in entries], ["GRP", "SINGLE-FIELD"])
        self.assertEqual([n.name for n in entries[0].children], ["FIELD", "VIEW-FIELD"])
        condition = entries[0].children[1].children[0]
        self.assertEqual((condition.name, condition.level), ("VALID-FIELD", 88))
        values = condition.clauses[0].values
        self.assertEqual((values[0].lower.value, values[0].upper.value), ("1", "5"))
        self.assertEqual(len(values), 2)

    def test_occurs_variable_size_keys_usage_and_original_pic(self):
        result = self.good("STOP RUN.", data=(
            "01 TABLE-FIELD OCCURS 1 TO 10 TIMES DEPENDING ON N",
            "ASCENDING KEY IS CODE INDEXED BY IDX.",
            "05 CODE PIC 9(3) USAGE IS COMP-3 VALUE ZERO.",
        ))
        item = result.ast.data.sections[0].entries[0]
        occurs = item.clauses[0]
        self.assertEqual((occurs.minimum.value, occurs.maximum.value, occurs.depending.name), ("1", "10", "N"))
        self.assertEqual(occurs.keys[0].keys[0].name, "CODE")
        self.assertEqual(occurs.indexes[0].name, "IDX")
        self.assertEqual(self.nodes(result, A.UsageClause)[0].usage, "COMP-3")

    def test_reference_qualification_subscripts_and_modification(self):
        result = self.good("MOVE SRC OF PARENT-FIELD IN ROOT-FIELD(I, J)(2:3)", "TO DEST.")
        source = self.nodes(result, A.Move)[0].source
        self.assertEqual(source.qualifiers, ["PARENT-FIELD", "ROOT-FIELD"])
        self.assertEqual([x.name for x in source.subscripts], ["I", "J"])
        self.assertEqual((source.modification.start.value, source.modification.length.value), ("2", "3"))
        result = self.good("MOVE SRC(2:) TO DEST.")
        self.assertIsNone(self.nodes(result, A.Move)[0].source.modification.length)

    def test_arithmetic_precedence_and_right_associative_power(self):
        result = self.good("COMPUTE TARGET = 1 + 2 * 3 ** 2 ** 4.")
        expr = self.nodes(result, A.Arithmetic)[0].sources[0]
        self.assertEqual(expr.operator, "+")
        self.assertEqual(expr.right.operator, "*")
        self.assertEqual(expr.right.right.operator, "**")
        self.assertEqual(expr.right.right.right.operator, "**")

    def test_identifier_count_remains_usable_in_expressions(self):
        result = self.good("COMPUTE TOTAL = (COUNT+1) ** -2 / +3.",
                           "MOVE TOTAL TO COUNT.")
        self.assertEqual(self.nodes(result, A.Move)[0].targets[0].name, "COUNT")

    def test_unary_sign_and_power(self):
        for sign in ("-", "- "):
            result = self.good(f"COMPUTE TARGET = {sign}2 ** 2.")
            expr = self.nodes(result, A.Arithmetic)[0].sources[0]
            self.assertIsInstance(expr, A.Unary)
            self.assertEqual(expr.operator, "-")
            self.assertEqual(expr.operand.operator, "**")
        result = self.good("COMPUTE TARGET = 4 -2 ** 2.")
        expr = self.nodes(result, A.Arithmetic)[0].sources[0]
        self.assertEqual((expr.operator, expr.right.operator), ("-", "**"))

    def test_display_signed_literals_are_separate_operands(self):
        result = self.good("DISPLAY 1 -2 +3.")
        operands = self.nodes(result, A.Display)[0].operands
        self.assertEqual([n.value for n in operands], ["1", "-2", "+3"])

    def test_boolean_precedence_and_abbreviated_conditions(self):
        result = self.good("IF FIELD = 1 OR 2 AND < 4 DISPLAY 'YES' END-IF.")
        condition = self.nodes(result, A.If)[0].condition
        self.assertEqual(condition.operator, "OR")
        self.assertIsInstance(condition.left, A.Comparison)
        self.assertEqual(condition.right.operator, "AND")
        self.assertIsInstance(condition.right.left, A.AbbreviatedCondition)
        self.assertEqual(condition.right.left.operator, "=")
        self.assertEqual(condition.right.right.operator, "<")
        self.assertEqual(condition.right.left.inherited_subject, condition.left.left.span)

    def test_abbreviation_uses_latest_explicit_subject(self):
        result = self.good("IF A = 1 OR B > 2 OR 3 CONTINUE END-IF.")
        comparisons = self.nodes(result, A.Comparison)
        abbreviated = self.nodes(result, A.AbbreviatedCondition)[0]
        self.assertEqual(comparisons[1].left.name, "B")
        self.assertEqual(abbreviated.operator, ">")
        self.assertEqual(abbreviated.inherited_subject, comparisons[1].left.span)

    def test_not_and_class_conditions(self):
        result = self.good("IF NOT (FIELD IS NOT NUMERIC) CONTINUE END-IF.")
        cond = self.nodes(result, A.If)[0].condition
        self.assertEqual(cond.operator, "NOT")
        cls = self.nodes(result, A.ClassCondition)[0]
        self.assertEqual((cls.operand.name, cls.category, cls.negated), ("FIELD", "NUMERIC", True))

    def test_word_comparison_and_negation(self):
        result = self.good("IF FIELD IS NOT GREATER THAN OR EQUAL TO 10",
                           "CONTINUE END-IF.")
        self.assertEqual(self.nodes(result, A.Comparison)[0].operator, "<")

    def test_nested_if_dangling_else_and_period_closure(self):
        result = self.good("IF A = 1 IF B = 2 DISPLAY 'INNER'",
                           "ELSE DISPLAY 'OTHER'.", "DISPLAY 'AFTER'.")
        outer, inner = self.nodes(result, A.If)
        self.assertEqual(outer.else_body, [])
        self.assertEqual(len(inner.else_body), 1)
        self.assertFalse(outer.explicit_end)
        self.assertFalse(inner.explicit_end)
        self.assertEqual(len(result.ast.procedure.body), 2)

    def test_explicit_end_closes_only_current_scope(self):
        result = self.good("IF A = 1 IF B = 2 CONTINUE END-IF",
                           "DISPLAY 'OUTER' ELSE CONTINUE END-IF.")
        outer = self.nodes(result, A.If)[0]
        self.assertEqual([type(n).__name__ for n in outer.then_body], ["If", "Display"])
        self.assertTrue(all(n.explicit_end for n in self.nodes(result, A.If)))

    def test_evaluate_subjects_ranges_and_relative_tests(self):
        result = self.good("EVALUATE FIELD ALSO SECOND-FIELD",
                           "WHEN 1 THRU 5 ALSO ANY DISPLAY 'RANGE'",
                           "WHEN LESS 0 ALSO IS NOT NUMERIC CONTINUE",
                           "WHEN OTHER CONTINUE END-EVALUATE.")
        node = self.nodes(result, A.Evaluate)[0]
        self.assertEqual(len(node.subjects), 2)
        first = node.cases[0].alternatives[0]
        self.assertEqual((first[0].kind, first[0].upper.value, first[1].kind), ("range", "5", "any"))
        second = node.cases[1].alternatives[0]
        self.assertIsInstance(second[0].value, A.AbbreviatedCondition)
        self.assertIsNone(second[1].value.operand)
        self.assertTrue(node.cases[-1].other)

    def test_evaluate_consecutive_when_share_body(self):
        result = self.good("EVALUATE FIELD WHEN 1 WHEN 2 DISPLAY 'SAME'",
                           "WHEN OTHER CONTINUE END-EVALUATE.")
        case = self.nodes(result, A.Evaluate)[0].cases[0]
        self.assertEqual(len(case.alternatives), 2)
        self.assertEqual(len(case.body), 1)

    def test_perform_variants(self):
        result = self.good("PERFORM PARA THRU LAST-PARA 3 TIMES",
                           "PERFORM PARA WITH TEST AFTER UNTIL A = 5",
                           "PERFORM WITH TEST BEFORE VARYING I FROM 1 BY 1",
                           "UNTIL I > 5 AFTER J FROM 1 BY 2 UNTIL J > 8",
                           "CONTINUE END-PERFORM",
                           "PERFORM N TIMES CONTINUE END-PERFORM.")
        nodes = self.nodes(result, A.Perform)
        self.assertEqual(nodes[0].through.name, "LAST-PARA")
        self.assertEqual(nodes[0].times.value, "3")
        self.assertEqual(nodes[1].test, "AFTER")
        self.assertEqual([v.target.name for v in nodes[2].varying], ["I", "J"])
        self.assertEqual(nodes[3].times.name, "N")
        self.assertTrue(nodes[2].explicit_end)

    def test_initialize_replacements_and_multiple_move_targets(self):
        result = self.good("INITIALIZE FIRST-FIELD SECOND-FIELD",
                           "REPLACING ALPHANUMERIC BY SPACES NUMERIC BY ZERO",
                           "MOVE ALL 'A' TO FIRST-FIELD SECOND-FIELD.")
        initialize = self.nodes(result, A.Initialize)[0]
        self.assertEqual(len(initialize.targets), 2)
        self.assertEqual([r.category for r in initialize.replacements], ["ALPHANUMERIC", "NUMERIC"])
        move = self.nodes(result, A.Move)[0]
        self.assertTrue(move.source.all)
        self.assertEqual(len(move.targets), 2)

    def test_arithmetic_verbs_giving_rounded_and_handlers(self):
        result = self.good("ADD 1 2 TO FIELD ROUNDED GIVING RESULT-FIELD",
                           "ON SIZE ERROR DISPLAY 'ERROR'",
                           "NOT ON SIZE ERROR CONTINUE END-ADD",
                           "SUBTRACT 2 FROM FIELD",
                           "MULTIPLY 2 BY 3 GIVING PRODUCT-FIELD",
                           "DIVIDE 9 BY 2 GIVING QUOTIENT REMAINDER REST.")
        nodes = self.nodes(result, A.Arithmetic)
        self.assertTrue(nodes[0].targets[0].rounded)
        self.assertEqual([h.negated for h in nodes[0].handlers], [False, True])
        self.assertTrue(nodes[0].explicit_end)
        self.assertEqual(nodes[2].sources[1].value, "3")
        self.assertEqual(nodes[3].remainder.name, "REST")

    def test_file_control_descriptors_and_operations(self):
        source = "\n".join([
            fixed("IDENTIFICATION DIVISION.", area="A"), fixed("PROGRAM-ID. FILE-TEST.", area="A"),
            fixed("ENVIRONMENT DIVISION.", area="A"), fixed("INPUT-OUTPUT SECTION.", area="A"), fixed("FILE-CONTROL.", area="A"),
            fixed("SELECT FILE-NAME ASSIGN TO 'x.dat'"), fixed("ORGANIZATION IS INDEXED ACCESS MODE IS DYNAMIC"),
            fixed("RECORD KEY IS CODE ALTERNATE RECORD KEY IS ALT-CODE"), fixed("WITH DUPLICATES FILE STATUS IS FS."),
            fixed("DATA DIVISION.", area="A"), fixed("FILE SECTION.", area="A"), fixed("FD FILE-NAME.", area="A"),
            fixed("01 REC.", area="A"), fixed("05 CODE PIC 9."), fixed("PROCEDURE DIVISION.", area="A"),
            fixed("OPEN I-O FILE-NAME"), fixed("READ FILE-NAME INTO REC AT END CONTINUE"), fixed("NOT AT END DISPLAY REC END-READ"),
            fixed("WRITE REC FROM SRC INVALID KEY CONTINUE"), fixed("NOT INVALID KEY CONTINUE END-WRITE"), fixed("CLOSE FILE-NAME STOP RUN."),
        ])
        result = parse_source(source)
        self.assertTrue(result.success, result.diagnostics)
        self.assertEqual(len(self.nodes(result, A.KeyClause)), 2)
        self.assertEqual(self.nodes(result, A.FileDescriptor)[0].records[0].children[0].name, "CODE")
        self.assertEqual(len(self.nodes(result, A.Read)[0].handlers), 2)
        self.assertEqual(len(self.nodes(result, A.Write)[0].handlers), 2)

    def test_outer_handler_boundary_is_visible_in_nested_if(self):
        result = self.good("READ F AT END IF A = 1 CONTINUE",
                           "NOT AT END DISPLAY 'ROW' END-READ.")
        node = self.nodes(result, A.Read)[0]
        self.assertEqual(len(node.handlers), 2)
        self.assertIsInstance(node.handlers[0].body[0], A.If)
        self.assertFalse(node.handlers[0].body[0].explicit_end)

    def test_accept_sources_and_display_positions(self):
        result = self.good("ACCEPT FIELD FROM DATE YYYYMMDD",
                           "ACCEPT OTHER-FIELD FROM DAY YYYYDDD",
                           "DISPLAY 'TEXT' AT LINE 2 COLUMN COL FIELD",
                           "WITH NO ADVANCING.")
        self.assertEqual([n.date_format for n in self.nodes(result, A.Accept)], ["YYYYMMDD", "YYYYDDD"])
        display = self.nodes(result, A.Display)[0]
        self.assertEqual([n.axis for n in display.operands if isinstance(n, A.ScreenPosition)], ["LINE", "COLUMN"])
        self.assertIsInstance(display.operands[-1], A.Reference)
        self.assertTrue(display.no_advancing)

    def test_call_parameters_modes_and_functions(self):
        result = self.good("CALL 'SUBPROGRAM' USING A B BY VALUE 1 2",
                           "BY REFERENCE C RETURNING RESULT-FIELD END-CALL",
                           "COMPUTE FIELD = FUNCTION MOD(FUNCTION ORD(C), 11).")
        call = self.nodes(result, A.Call)[0]
        self.assertEqual([p.mode for p in call.parameters], ["REFERENCE", "REFERENCE", "VALUE", "VALUE", "REFERENCE"])
        self.assertEqual(call.returning.name, "RESULT-FIELD")
        self.assertTrue(call.explicit_end)
        self.assertEqual([f.name for f in self.nodes(result, A.FunctionCall)], ["MOD", "ORD"])

    def test_inspect_tally_replace_and_converting(self):
        result = self.good("INSPECT FUNCTION REVERSE(FIELD) TALLYING N",
                           "FOR LEADING SPACES",
                           "INSPECT FIELD REPLACING ALL '.' BY ','",
                           "INSPECT FIELD CONVERTING 'ABC' TO 'abc'.")
        nodes = self.nodes(result, A.Inspect)
        self.assertEqual(nodes[0].tallies[0].patterns[0].mode, "LEADING")
        self.assertEqual(nodes[1].replacements[0].replacement.value, ",")
        self.assertEqual(nodes[2].converting[1].value, "abc")

    def test_string_and_unstring_attributes(self):
        result = self.good("STRING 'A' FIELD DELIMITED BY SIZE",
                           "INTO TARGET WITH POINTER PTR END-STRING",
                           "UNSTRING TARGET DELIMITED BY ALL ',' OR ';'",
                           "INTO A DELIMITER IN D COUNT IN N B",
                           "WITH POINTER PTR TALLYING IN CNT END-UNSTRING.")
        string = self.nodes(result, A.String)[0]
        self.assertTrue(string.parts[0].delimiter.size)
        self.assertEqual(string.pointer.name, "PTR")
        unstring = self.nodes(result, A.Unstring)[0]
        self.assertTrue(unstring.delimiters[0].all)
        self.assertEqual(unstring.targets[0].count_in.name, "N")
        self.assertEqual(unstring.tallying.name, "CNT")

    def test_search_set_alter_and_exits(self):
        result = self.good("SET IDX TO 1 SEARCH ALL TABLE-FIELD",
                           "AT END CONTINUE WHEN CODE(IDX) = 2",
                           "EXIT PERFORM END-SEARCH",
                           "ALTER PARA TO PROCEED TO OTHER-PARA",
                           "EXIT PARAGRAPH GOBACK.")
        search = self.nodes(result, A.Search)[0]
        self.assertTrue(search.all)
        self.assertEqual(search.cases[0].condition.operator, "=")
        self.assertEqual(self.nodes(result, A.Alter)[0].pairs[0].target.name, "OTHER-PARA")
        self.assertEqual([n.scope for n in self.nodes(result, A.Exit)], ["PERFORM", "PARAGRAPH"])

    def test_paragraph_section_and_sentence_order(self):
        source = program("DISPLAY 'ENTRY'.") + "\n" + "\n".join([
            fixed("FIRST-SECTION SECTION.", area="A"), fixed("DISPLAY 'SECTION'."),
            fixed("FIRST-PARA.", area="A"), fixed("CONTINUE. CONTINUE."),
            fixed("SECOND-PARA.", area="A"), fixed("EXIT."),
            fixed("LAST-SECTION SECTION.", area="A"), fixed("STOP RUN."),
        ])
        result = parse_source(source)
        self.assertTrue(result.success, result.diagnostics)
        body = result.ast.procedure.body
        self.assertEqual([type(n).__name__ for n in body], ["Sentence", "ProcedureSection", "ProcedureSection"])
        self.assertEqual([type(n).__name__ for n in body[1].body], ["Sentence", "Paragraph", "Paragraph"])
        self.assertEqual(len(body[1].body[1].sentences), 2)

    def test_source_spans_json_and_ast_invariants(self):
        result = self.good('DISPLAY "a"', 'CONTINUE.', data=("01 FIELD PIC X(2).",))
        display = self.nodes(result, A.Display)[0]
        self.assertEqual((display.span.start.line, display.span.start.column, display.span.end.line), (7, 12, 7))
        payload = json.loads(json.dumps(A.to_dict(result.ast)))
        self.assertEqual(payload["node"], "Program")
        self.assertEqual(payload["procedure"]["body"][0]["node"], "Sentence")

    def test_copybook_fragments_have_data_ast(self):
        result = parse_source(fixed("05 FIELD PIC X."), copybook=True)
        self.assertTrue(result.success)
        self.assertIsInstance(result.ast, A.DataFragment)
        self.assertEqual(result.ast.entries[0].level, 5)
        self.assertFalse(parse_source(fixed("05 FIELD PIC X.")).success)

    def test_unknown_verbs_and_trailing_garbage_are_errors(self):
        self.bad("BOGUS FIELD.")
        self.bad("STOP RUN. @")
        self.bad("DISPLAY 'A' END-IF.")
        self.bad("MOVE A B TO C.")

    def test_malformed_compound_statements_are_errors(self):
        for lines in (("IF A = CONTINUE END-IF.",), ("IF > 1 CONTINUE END-IF.",),
                      ("PERFORM UNTIL A = 2 CONTINUE.",), ("EVALUATE A WHEN 1 END-EVALUATE.",),
                      ("EVALUATE A WHEN OTHER CONTINUE", "WHEN 1 CONTINUE END-EVALUATE."),
                      ("READ F AT END END-READ.",), ("CALL 'P' USING.",),
                      ("UNSTRING FIELD INTO END-UNSTRING.",),
                      ("COMPUTE X = (1 + 2.",), ("MULTIPLY 2 BY 3.",),
                      ("SUBTRACT 2 GIVING X.",)):
            with self.subTest(lines=lines):
                self.bad(*lines)

    def test_empty_source_division_order_and_missing_period(self):
        result = parse_source("")
        self.assertFalse(result.success)
        self.assertEqual(result.diagnostics[0].span.start.line, 1)
        self.bad("STOP RUN")
        result = parse_source(program("STOP RUN.").replace("IDENTIFICATION DIVISION.", "DATA DIVISION."))
        self.assertFalse(result.success)

    def test_headers_outside_area_a_are_diagnosed(self):
        source = program("STOP RUN.").replace("000100 PROCEDURE", "000100     PROCEDURE")
        result = parse_source(source)
        self.assertEqual(result.diagnostics[0].code, "INVALID_HEADER_AREA")

    def test_recovery_reports_two_errors_and_retains_later_paragraph(self):
        source = program("MOVE TO X.", "COMPUTE X = .") + "\n" + fixed("LAST-PARA.", area="A") + "\n" + fixed("DISPLAY 'RECOVERED'.")
        result = parse_source(source)
        self.assertFalse(result.success)
        self.assertEqual(len(result.diagnostics), 2)
        self.assertIsNone(result.parsed.ast)
        partial = result.parsed.partial_ast
        self.assertEqual(partial.procedure.body[-1].name, "LAST-PARA")
        self.assertEqual(partial.procedure.body[-1].sentences[0].statements[0].operands[0].value, "RECOVERED")
        self.assertGreater(result.parsed.skipped_tokens, 0)

    def test_syntax_diagnostic_in_copy_has_original_position(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "p.cbl").write_text(program("COPY BAD.", "STOP RUN."))
            (root / "BAD.cpy").write_text(fixed("MOVE TO X."))
            result = parse_file(root / "p.cbl")
            diagnostic = result.diagnostics[0]
            self.assertEqual((Path(diagnostic.span.start.file).name, diagnostic.span.start.line, diagnostic.span.start.column), ("BAD.cpy", 1, 17))
            self.assertEqual(diagnostic.expected, "identificador")
            self.assertEqual(len(diagnostic.span.start.inclusion_stack), 1)

    def test_sql_extension_is_explicitly_unsupported(self):
        result = self.bad("EXEC SQL CONNECT END-EXEC.")
        self.assertEqual(result.diagnostics[0].code, "UNSUPPORTED_EXEC")

    def test_computer_and_special_names_clauses(self):
        result = self.good("STOP RUN.", environment=(
            fixed("CONFIGURATION SECTION.", area="A"),
            fixed("SOURCE-COMPUTER. PC WITH DEBUGGING MODE.", area="A"),
            fixed("OBJECT-COMPUTER. PC.", area="A"),
            fixed("SPECIAL-NAMES.", area="A"), fixed("CURSOR IS CURSOR-FIELD CRT STATUS IS KEY-FIELD."),
        ))
        self.assertEqual([n.debugging for n in self.nodes(result, A.ComputerClause)], [True, False])
        self.assertEqual([n.setting for n in self.nodes(result, A.SpecialName)], ["CURSOR", "CRT STATUS"])

    def test_sort_has_typed_keys_and_file_operands(self):
        result = self.good("SORT SORT-FILE ON ASCENDING KEY FIELD",
                           "USING INPUT-FILE GIVING OUTPUT-FILE.")
        node = self.nodes(result, A.Sort)[0]
        self.assertEqual(node.keys[0].role, "ASCENDING")
        self.assertEqual(node.using[0].name, "INPUT-FILE")
        self.assertEqual(node.giving[0].name, "OUTPUT-FILE")

    def test_go_depending_next_sentence_and_scope_exits(self):
        result = self.good("GO TO FIRST-PARA SECOND-PARA DEPENDING ON CHOICE",
                           "NEXT SENTENCE EXIT SECTION EXIT PROGRAM.")
        node = self.nodes(result, A.GoTo)[0]
        self.assertEqual(len(node.targets), 2)
        self.assertEqual(node.depending.name, "CHOICE")
        self.assertTrue(self.nodes(result, A.NextSentence))
        self.assertEqual([n.scope for n in self.nodes(result, A.Exit)], ["SECTION", "PROGRAM"])

    def test_start_write_advancing_and_call_exception_handlers(self):
        result = self.good("START FILE-NAME KEY IS NOT LESS THAN CODE",
                           "INVALID KEY CONTINUE END-START",
                           "WRITE REC AFTER ADVANCING 2 LINES",
                           "CALL 'P' ON EXCEPTION CONTINUE",
                           "NOT ON EXCEPTION CONTINUE END-CALL.")
        self.assertEqual(self.nodes(result, A.Start)[0].condition.operator, ">=")
        self.assertEqual(self.nodes(result, A.Write)[0].timing, "AFTER")
        self.assertEqual(len(self.nodes(result, A.Call)[0].handlers), 2)

    def test_non_integer_occurs_and_invalid_verb_clauses(self):
        invalid_level = self.bad("STOP RUN.", data=("99 FIELD PIC X.",))
        self.assertEqual(invalid_level.diagnostics[0].unexpected, "'99'")
        self.assertEqual(invalid_level.diagnostics[0].span.start.column, 12)
        self.bad("STOP RUN.", data=("01 TABLE-FIELD OCCURS 'X' TIMES PIC X.",))
        self.bad("STOP RUN.", data=("01 TABLE-FIELD OCCURS 1.5 TIMES PIC X.",))
        for statement in ("COMPUTE X = 1 GIVING Y.", "ADD 1 TO X REMAINDER Y.",
                          "DIVIDE 1 INTO X REMAINDER Y.", "GO TO PARA OTHER-PARA.",
                          "STRING INTO FIELD END-STRING.",
                          "DISPLAY 'X' WITH NO ADVANCING WITH NO ADVANCING.",
                          "DISPLAY 'X' UPON CONSOLE UPON CONSOLE."):
            with self.subTest(statement=statement):
                self.bad(statement)

    def test_fd_is_rejected_outside_file_section(self):
        self.bad("STOP RUN.", data=("FD FILE-NAME.", "01 REC PIC X.",))

    def test_known_unimplemented_statement_has_specific_code(self):
        result = self.bad("REWRITE REC.")
        self.assertEqual(result.diagnostics[0].code, "UNSUPPORTED_STATEMENT")

    def test_deleting_tokens_never_crashes_recovery(self):
        # Mutações determinísticas de entrada localizada, sem supor que excluir
        # um token opcional deva tornar a sentença inválida.
        from cobol_compiler import Parser
        result = self.good("IF A > 1 DISPLAY 'YES' ELSE CONTINUE END-IF.")
        tokens = result.preprocessed.tokens
        for i in range(len(tokens)):
            with self.subTest(index=i):
                parsed = Parser(tokens[:i] + tokens[i + 1:]).parse()
                if parsed.diagnostics:
                    self.assertFalse(parsed.success)
                    self.assertIsNone(parsed.ast)

    def test_cli_check_dump_and_failure_codes(self):
        good = subprocess.run([sys.executable, "-m", "cobol_compiler", "examples/oficiais/CALCMD01.cbl", "--check-syntax"],
                              cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(good.returncode, 0, good.stderr)
        dump = subprocess.run([sys.executable, "-m", "cobol_compiler", "examples/dependencias/COD001A.cpy", "--dump-ast"],
                              cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(json.loads(dump.stdout)["node"], "DataFragment")
        bad = subprocess.run([sys.executable, "-m", "cobol_compiler", "examples/complementares/CLIESQL01.cbl", "--dump-ast"],
                             cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(bad.stdout, "")
        self.assertIn(":1:1:", bad.stderr)
        missing = subprocess.run([sys.executable, "-m", "cobol_compiler", "absent.cbl"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
