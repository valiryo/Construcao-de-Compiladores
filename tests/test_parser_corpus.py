"""Toda a coorte da etapa léxica é exercitada; negativos não são excluídos."""

import json
from pathlib import Path
import unittest

from cobol_compiler import parse_file, parse_source
from cobol_compiler import ast as A
from cobol_compiler.validation import validate_ast
from tools.auditar_parser import audit_corpus, markdown
from test_parser import program


ROOT = Path(__file__).resolve().parents[1]
OFFICIALS = {
    "CALCMD01": (285, 52, 8), "CAIXAREG": (390, 71, 10),
    "CAD0004A": (133, 16, 8), "BUSCA01A": (208, 23, 9),
    "CAD0005A": (516, 87, 15), "PROG024A": (1463, 194, 65),
    "CAD0002A": (954, 153, 47),
}


class ParserCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit_corpus()

    def official(self, name):
        path = ROOT / "examples" / ("corrigidos" if name == "CAD0005A" else "oficiais") / (name + ".cbl")
        result = parse_file(path, include_dirs=[ROOT / "examples/dependencias"])
        self.assertTrue(result.success, result.diagnostics)
        return result

    def nodes(self, result, cls):
        return [n for n in A.walk(result.ast) if isinstance(n, cls)]

    def test_all_previous_lexer_successes_are_really_parsed(self):
        summary = self.report["summary"]
        self.assertEqual(summary["total_files"], 86)
        self.assertEqual(summary["previously_accepted_by_lexer"], 77)
        self.assertEqual(summary["previously_accepted_submitted_to_parser"], 77)
        self.assertEqual(summary["unexpected_failures"], [])
        old = json.loads((ROOT / "docs/auditoria-lexer-depois.json").read_text())["files"]
        self.assertEqual(set(old), set(self.report["files"]))
        for path, item in self.report["files"].items():
            with self.subTest(path=path):
                if not old[path]["diagnostics"]:
                    self.assertNotEqual(item["parsing"], "not_run")

    def test_known_failures_are_individual_and_explicit(self):
        failures = {path: item["classification"] for path, item in self.report["files"].items()
                    if item["previously_accepted_by_lexer"] and not item["success"]}
        self.assertEqual(failures, {
            "examples/complementares/CLIESQL01.cbl": "syntax_error",
            "examples/complementares/PROG006A.cbl": "unsupported_extension",
            "examples/complementares/clientes-sql.cbl": "unsupported_extension",
        })
        for path in failures:
            self.assertGreater(self.report["files"][path]["error_count"], 0)
        self.assertEqual(self.report["summary"]["successful_programs"], 72)
        self.assertEqual(self.report["summary"]["successful_data_fragments"], 2)

    def test_every_success_has_complete_tokens_and_validated_ast(self):
        for path, item in self.report["files"].items():
            if not item["success"]:
                continue
            with self.subTest(path=path):
                self.assertEqual(item["error_count"], 0)
                self.assertEqual(item["consumed_tokens"], item["expanded_token_count"])
                self.assertEqual(item["skipped_tokens"], 0)
                self.assertEqual(item["structural_validation"]["errors"], [])
                self.assertEqual(item["structural_validation"]["expected_statements"], item["structural_validation"]["represented_statements"])

    def test_official_statement_data_and_token_counts(self):
        for name, (tokens, commands, data_items) in OFFICIALS.items():
            with self.subTest(program=name):
                result = self.official(name)
                validation = validate_ast(result.ast, result.preprocessed.tokens)
                self.assertTrue(validation.success, validation.errors)
                self.assertEqual(result.parsed.consumed_tokens, tokens)
                self.assertEqual(validation.represented_statements, commands)
                self.assertEqual(validation.node_counts["DataItem"], data_items)
                self.assertEqual(result.ast.identification.program_id, name)

    def test_official_calculation_and_fixed_decimal_structure(self):
        result = self.official("CALCMD01")
        operations = self.nodes(result, A.Arithmetic)
        self.assertEqual(operations[-1].sources[0].operator, "/")
        self.assertEqual(len(self.nodes(result, A.Perform)), 11)
        result = self.official("CAIXAREG")
        self.assertIn("ZZZ.ZZZ.ZZZ,ZZ", [p.mask for p in self.nodes(result, A.PictureClause)])
        self.assertEqual(self.nodes(result, A.SpecialName)[0].value.value, "COMMA")

    def test_cadastro_simple_paragraphs_and_search_file_handlers(self):
        result = self.official("CAD0004A")
        self.assertEqual(self.nodes(result, A.ProcedureSection), [])
        self.assertEqual([p.name for p in self.nodes(result, A.Paragraph)], ["0001-PROCESSAR", "0001-END", "0002-CADASTRAR-REG", "0002-END"])
        self.assertEqual(len(self.nodes(result, A.Write)), 1)
        result = self.official("BUSCA01A")
        read = self.nodes(result, A.Read)[0]
        self.assertEqual(read.into.name, "REGISTRO-ENTRADA")
        self.assertEqual([(h.event, h.negated) for h in read.handlers], [("END", False), ("END", True)])
        self.assertTrue(read.explicit_end)

    def test_agenda_control_and_real_table_size(self):
        result = self.official("CAD0005A")
        self.assertEqual(self.nodes(result, A.OccursClause)[0].minimum.value, "10")
        self.assertEqual(len(self.nodes(result, A.Evaluate)[0].cases), 4)
        self.assertGreater(len(self.nodes(result, A.Continue)), 0)
        self.assertEqual(len(self.nodes(result, A.Write)), 2)

    def test_library_copy_call_file_layout_and_duplicate_names(self):
        result = self.official("PROG024A")
        self.assertEqual(len(self.nodes(result, A.FileDescriptor)), 2)
        self.assertEqual(len([n for n in self.nodes(result, A.DataItem) if n.name == "TAB-ENT-LINHA"]), 2)
        call = self.nodes(result, A.Call)[0]
        self.assertEqual(call.program.value, "PROGDATA")
        self.assertEqual(call.parameters[0].value.name, "COD001A-REGISTRO")
        copied = [n for n in self.nodes(result, A.DataItem) if Path(n.span.start.file).name == "COD001A.cpy"]
        self.assertEqual(len(copied), 15)
        self.assertTrue(all(n.span.start.inclusion_stack for n in copied))

    def test_linkage_copy_table_refs_class_conditions_and_evaluate(self):
        result = self.official("CAD0002A")
        self.assertEqual(result.ast.procedure.parameters[0].value.name, "COPY002A-REGISTRO")
        linkage = next(s for s in result.ast.data.sections if s.name == "LINKAGE")
        self.assertEqual([n.name for n in linkage.entries], ["COPY002A-HEADER", "COPY002A-REGISTRO"])
        self.assertEqual(self.nodes(result, A.OccursClause)[0].minimum.value, "50")
        self.assertEqual(len(self.nodes(result, A.ReferenceModification)), 4)
        self.assertEqual(len(self.nodes(result, A.Inspect)), 5)
        self.assertTrue(any(n.name == "REVERSE" for n in self.nodes(result, A.FunctionCall)))
        tests = [selection.value for e in self.nodes(result, A.Evaluate) for case in e.cases
                 for alt in case.alternatives for selection in alt]
        self.assertTrue(any(isinstance(n, A.ClassCondition) and n.operand is None for n in tests))
        self.assertTrue(any(isinstance(n, A.AbbreviatedCondition) for n in tests))

    def test_additional_families_have_specific_nodes(self):
        examples = {
            "PROG003A": (A.Arithmetic, A.Move),
            "PROG017A": (A.Set, A.OccursClause),
            "PROG018A": (A.Alter, A.GoTo),
            "PROG020A": (A.Search, A.KeyClause),
            "PROG025A": (A.Unstring, A.FunctionCall),
            "PROGTEST": (A.ScreenBlank, A.ScreenPosition, A.ScreenUsing),
            "PROGTEST4": (A.UsageClause, A.Search),
            "PROGVSAM": (A.KeyClause, A.RedefinesClause, A.Write),
            "NCURSESDEMO": (A.Call, A.CallParameter),
        }
        for name, classes in examples.items():
            with self.subTest(name=name):
                result = parse_file(ROOT / "examples/complementares" / (name + ".cbl"), include_dirs=[ROOT / "examples/dependencias"])
                self.assertTrue(result.success, result.diagnostics)
                for cls in classes:
                    self.assertTrue(self.nodes(result, cls), cls.__name__)
                if name == "PROG003A":
                    self.assertTrue(any(n.corresponding for n in self.nodes(result, A.Move)))

    def test_validator_detects_removed_statement_and_wrong_span(self):
        result = parse_source(program("DISPLAY 'A'."))
        sentence = result.ast.procedure.body[0]
        display = sentence.statements.pop()
        validation = validate_ast(result.ast, result.preprocessed.tokens)
        self.assertTrue(any("sem nó AST" in e for e in validation.errors))
        sentence.statements.append(display)
        display.span = result.ast.span
        self.assertTrue(any("SourceSpan" in e for e in validate_ast(result.ast, result.preprocessed.tokens).errors))

    def test_generated_reports_are_current(self):
        saved = json.loads((ROOT / "docs/auditoria-parser.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, self.report)
        self.assertEqual((ROOT / "docs/auditoria-parser.md").read_text(encoding="utf-8"), markdown(self.report))


if __name__ == "__main__":
    unittest.main()
