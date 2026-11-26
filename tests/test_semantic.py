"""Resolução, layout e vínculos observáveis; nenhum teste executa COBOL/C."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from cobol_compiler import parse_source, parse_file, analyze, check_source, check_file
from cobol_compiler import ast as A
from test_parser import program
from test_lexer import fixed


ROOT=Path(__file__).resolve().parents[1]


def unit(*, name='TEST-PROGRAM', data=(), linkage=(), files=(), environment=(), body=('STOP RUN.',), using=''):
    lines=['IDENTIFICATION DIVISION.', f'PROGRAM-ID. {name}.']
    if environment: lines+=['ENVIRONMENT DIVISION.',*environment]
    lines+=['DATA DIVISION.']
    if files: lines+=['FILE SECTION.',*files]
    if data: lines+=['WORKING-STORAGE SECTION.',*data]
    if linkage: lines+=['LINKAGE SECTION.',*linkage]
    lines+=[f'PROCEDURE DIVISION{using}.',*body]
    return '\n'.join(fixed(s,area='A') for s in lines)


class SemanticTests(unittest.TestCase):
    def check(self,*body,data=(),**kwargs):
        frontend=parse_source(program(*body,data=data))
        self.assertTrue(frontend.success,'\n'.join(d.format() for d in frontend.diagnostics))
        return analyze(frontend,**kwargs)

    def good(self,*args,**kwargs):
        r=self.check(*args,**kwargs)
        self.assertTrue(r.success,'\n'.join(d.format() for d in r.diagnostics))
        self.assertIsNotNone(r.ast)
        return r

    def bad(self,code,*args,**kwargs):
        r=self.check(*args,**kwargs)
        self.assertFalse(r.success)
        self.assertIsNone(r.ast)
        self.assertIn(code,[d.code for d in r.diagnostics])
        return r

    def symbol(self,r,name,namespace='data'):
        values=r.table.candidates(name,[namespace])
        self.assertEqual(len(values),1)
        return values[0]

    def nodes(self,r,cls): return [n for n in A.walk(r.frontend.ast) if isinstance(n,cls)]

    def test_qualified_hierarchy_and_original_case(self):
        r=self.good('MOVE field-a OF left-group TO field-a IN right-group.',data=(
            '01 left-group.','05 field-a PIC X(3).','01 right-group.','05 field-a PIC X(3).'))
        move=self.nodes(r,A.Move)[0]
        left=r.table.symbols[r.annotation(move.source).symbol_id]
        right=r.table.symbols[r.annotation(move.targets[0]).symbol_id]
        self.assertNotEqual(left.id,right.id)
        self.assertEqual(left.original_name,'field-a')
        self.assertEqual(r.table.symbols[left.parent].name,'LEFT-GROUP')
        r=check_source(unit(name='mixed-Name'))
        self.assertEqual(r.table.candidates('MIXED-NAME',['program'])[0].original_name,'mixed-Name')

    def test_ambiguous_reference_has_related_declarations(self):
        r=self.bad('AMBIGUOUS_REFERENCE','DISPLAY FIELD-A.',data=(
            '01 LEFT-GROUP.','05 FIELD-A PIC X.','01 RIGHT-GROUP.','05 FIELD-A PIC X.'))
        d=next(d for d in r.diagnostics if d.code=='AMBIGUOUS_REFERENCE')
        self.assertEqual(len(d.related),2)
        self.assertIn('Declaração relacionada',d.format())

    def test_duplicate_siblings_and_roots(self):
        for data in [('01 FIELD-A PIC X.','01 FIELD-A PIC 9.'),('01 GRP.','05 FIELD-A PIC X.','05 FIELD-A PIC X.')]:
            with self.subTest(data=data):self.bad('DUPLICATE_SYMBOL','STOP RUN.',data=data)

    def test_same_name_parent_and_child_not_duplicate(self):
        r=self.good('DISPLAY FIELD-A OF FIELD-A.',data=('01 FIELD-A.','05 FIELD-A PIC X.'))
        self.assertEqual(len(r.table.candidates('FIELD-A',['data'])),2)

    def test_undefined_reference_and_filler_not_usable(self):
        self.bad('UNDEFINED_SYMBOL','MOVE MISSING TO FIELD-A.',data=('01 FIELD-A PIC X.',))
        r=self.good('STOP RUN.',data=('01 GRP.','05 FILLER PIC X.','05 FILLER PIC 9.'))
        self.assertEqual(len([s for s in r.table.symbols.values() if s.namespace=='filler']),2)

    def test_layout_nested_offsets_and_occurs(self):
        r=self.good('MOVE 2 TO N.', 'DISPLAY CODE(N).',data=(
            '01 N PIC 9.','01 RECORD-A.','05 HEADER-A PIC X(2).','05 ROW-A OCCURS 3 TIMES.',
            '10 CODE PIC 9(2).','10 TEXT-A PIC X(4).','05 TAIL-A PIC X.'))
        record,row,code,tail=(r.layout.for_symbol(self.symbol(r,n)) for n in ('RECORD-A','ROW-A','CODE','TAIL-A'))
        self.assertEqual((record.offset,record.size,record.total_size),(1,21,21))
        self.assertEqual((row.offset,row.size,row.total_size),(3,6,18))
        self.assertEqual((code.offset,code.size,tail.offset),(3,2,21))
        self.assertEqual((code.dimensions[0].base,code.dimensions[0].stride,code.dimensions[0].maximum),(1,6,3))
        access=next(n for n in self.nodes(r,A.Reference) if n.name=='CODE')
        self.assertEqual(r.annotation(access).checks[0]['kind'],'subscript')

    def test_nested_table_dimensions(self):
        r=self.good('DISPLAY FIELD-A(2,3).',data=('01 ROW-A OCCURS 2.','05 COL-A OCCURS 3.','10 FIELD-A PIC X(4).'))
        layout=r.layout.for_symbol(self.symbol(r,'FIELD-A'))
        self.assertEqual([d.stride for d in layout.dimensions],[12,4])
        self.assertEqual(r.layout.areas['WORKING-STORAGE'],24)

    def test_redefines_alias_and_reserves_larger_region(self):
        r=self.good('MOVE 1 TO VIEW-A.',data=('01 GRP.','05 ORIGINAL-A PIC X(2).',
            '05 VIEW-A REDEFINES ORIGINAL-A PIC 9(4).','05 TAIL-A PIC X.'))
        left,right=(r.layout.for_symbol(self.symbol(r,n)) for n in ('ORIGINAL-A','VIEW-A'))
        self.assertEqual(left.offset,right.offset)
        self.assertEqual(right.redefines,left.symbol_id)
        self.assertEqual(right.initial['policy'],'alias')
        self.assertEqual(r.layout.for_symbol(self.symbol(r,'TAIL-A')).offset,4)
        self.assertEqual(r.layout.areas['WORKING-STORAGE'],5)

    def test_redefines_forward_or_different_parent_is_invalid(self):
        self.bad('INVALID_REDEFINES','STOP RUN.',data=('01 VIEW-A REDEFINES ORIGINAL-A PIC X.','01 ORIGINAL-A PIC X.'))
        self.bad('INVALID_REDEFINES','STOP RUN.',data=('01 GROUP-A.','05 FIELD-A PIC X.','01 VIEW-A REDEFINES FIELD-A PIC X.'))

    def test_level_77_and_88_storage(self):
        r=self.good('SET YES-A TO TRUE.','IF YES-A DISPLAY SINGLE-A END-IF.',data=(
            '77 SINGLE-A PIC X(2).','01 STATUS-A PIC X.','88 YES-A VALUE "Y".'))
        condition=self.symbol(r,'YES-A','condition')
        self.assertNotIn(condition.id,r.layout.items)
        self.assertEqual(r.layout.areas['WORKING-STORAGE'],3)
        self.assertEqual(condition.type.category,'boolean')

    def test_condition_without_value_and_group_pic(self):
        self.bad('CONDITION_WITHOUT_VALUE','STOP RUN.',data=('01 STATUS-A PIC X.','88 YES-A.'))
        self.bad('GROUP_WITH_PICTURE','STOP RUN.',data=('01 GRP PIC X.','05 FIELD-A PIC X.'))
        self.bad('INVALID_LEVEL_77','STOP RUN.',data=('77 FIELD-A PIC X OCCURS 2.',))

    def test_invalid_top_level_and_missing_pic(self):
        self.bad('INVALID_DATA_LEVEL','STOP RUN.',data=('05 FIELD-A PIC X.',))
        self.bad('MISSING_PICTURE','STOP RUN.',data=('01 FIELD-A.',))

    def test_linkage_has_external_storage_and_formal_binding(self):
        r=check_source(unit(linkage=('01 ARG-A.','05 FIELD-A PIC X(4).',),using=' USING ARG-A',body=('GOBACK.',)))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        arg=self.symbol(r,'ARG-A');layout=r.layout.for_symbol(arg)
        self.assertFalse(layout.local)
        self.assertTrue(layout.area.startswith('LINKAGE:'))
        self.assertEqual(layout.initial['policy'],'external')
        self.assertEqual(r.parameters[0]['symbol_id'],arg.id)

    def test_formal_must_be_linkage_root(self):
        r=check_source(unit(data=('01 ARG-A PIC X.',),using=' USING ARG-A'))
        self.assertIn('FORMAL_NOT_LINKAGE',[d.code for d in r.diagnostics])

    def test_initialization_default_and_strict_mode(self):
        r=self.good('STOP RUN.',data=('01 NUM-A PIC 9(3).','01 TEXT-A PIC X(3).'))
        self.assertEqual(r.layout.for_symbol(self.symbol(r,'NUM-A')).initial['policy'],'zero')
        self.assertEqual(r.layout.for_symbol(self.symbol(r,'TEXT-A')).initial['policy'],'spaces')
        self.bad('MISSING_VALUE','STOP RUN.',data=('01 NUM-A PIC 9.',),strict=True)

    def test_invalid_initial_values_and_ranges(self):
        for data,code in [('01 NUM-A PIC 9 VALUE 10.','VALUE_OUT_OF_RANGE'),
            ('01 NUM-A PIC 9 VALUE -1.','VALUE_OUT_OF_RANGE'),
            ('01 NUM-A PIC 9 VALUE "A".','INVALID_NUMERIC_VALUE'),
            ('01 TEXT-A PIC X VALUE "AB".','VALUE_TOO_LONG'),
            ('01 NUM-A PIC 9 VALUE 0.5.','VALUE_SCALE_LOSS')]:
            with self.subTest(data=data):self.bad(code,'STOP RUN.',data=(data,))
        self.bad('REVERSED_VALUE_RANGE','STOP RUN.',data=('01 NUM-A PIC 9.','88 RANGE-A VALUE 5 THRU 1.'))

    def test_move_alphabetic_to_numeric_rejected_but_x_conversion_recorded(self):
        self.bad('MOVE_ALPHABETIC_TO_NUMERIC','MOVE ALPHA-A TO NUM-A.',data=('01 ALPHA-A PIC A(2).','01 NUM-A PIC 9(2).'))
        r=self.good('MOVE TEXT-A TO NUM-A.',data=('01 TEXT-A PIC X(2).','01 NUM-A PIC 9(2).'))
        conversion=r.annotation(self.nodes(r,A.Move)[0]).conversions[0]
        self.assertEqual(conversion['operation'],'numeric')
        self.assertEqual(conversion['target_id'],self.symbol(r,'NUM-A').id)

    def test_group_and_multiple_moves(self):
        r=self.good('MOVE LEFT-GROUP TO RIGHT-GROUP THIRD-A.',data=('01 LEFT-GROUP.','05 FIELD-A PIC X(3).',
            '01 RIGHT-GROUP.','05 FIELD-A PIC X(4).','01 THIRD-A PIC X(5).'))
        conversions=r.annotation(self.nodes(r,A.Move)[0]).conversions
        self.assertEqual(len(conversions),2)
        self.assertEqual({c['operation'] for c in conversions},{'group-bytes'})

    def test_move_corresponding_pairs_resolved(self):
        r=self.good('MOVE CORR LEFT-GROUP TO RIGHT-GROUP.',data=('01 LEFT-GROUP.','05 FIELD-A PIC 9.',
            '05 LEFT-ONLY PIC X.','01 RIGHT-GROUP.','05 FIELD-A PIC 9(2).','05 RIGHT-ONLY PIC X.'))
        pairs=r.annotation(self.nodes(r,A.Move)[0]).details['corresponding']
        self.assertEqual(len(pairs),1)
        self.assertEqual(r.table.symbols[pairs[0]['target']].name,'FIELD-A')

    def test_initialize_replacing_receivers_exclude_filler_and_aliases(self):
        r=self.good('INITIALIZE GRP REPLACING NUMERIC BY 2.',data=('01 GRP.','05 NUM-A PIC 9.',
            '05 FILLER PIC X.','05 VIEW-A REDEFINES NUM-A PIC X.'))
        init=self.nodes(r,A.Initialize)[0]
        self.assertEqual(r.annotation(init).details['initialize_receivers'],[self.symbol(r,'NUM-A').id])
        self.assertEqual(r.annotation(init.replacements[0]).conversions[0]['target_type']['category'],'numeric')

    def test_arithmetic_requires_numeric_receivers(self):
        self.bad('NUMERIC_REQUIRED','ADD 1 TO TEXT-A.',data=('01 TEXT-A PIC X.',))
        self.bad('NUMERIC_REQUIRED','COMPUTE NUM-A = TEXT-A + 1.',data=('01 NUM-A PIC 9.','01 TEXT-A PIC X.',))

    def test_compute_precision_and_receiver_scale_annotation(self):
        r=self.good('COMPUTE DEST-A ROUNDED = LEFT-A * RIGHT-A.',data=('01 LEFT-A PIC 9(3)V99.',
            '01 RIGHT-A PIC 9V9.','01 DEST-A PIC 9(6)V9.'))
        node=self.nodes(r,A.Arithmetic)[0]
        typ=r.annotation(node).type
        self.assertEqual((typ.precision,typ.scale),(7,3))
        target=r.annotation(node.targets[0])
        self.assertTrue(target.details['rounded'])
        self.assertEqual(target.details['receiving_scale'],1)

    def test_divide_giving_remainder_and_runtime_checks(self):
        r=self.good('DIVIDE 10 BY 3 GIVING DEST-A REMAINDER REM-A.',data=('01 DEST-A PIC 9(2).','01 REM-A PIC 9.'))
        node=self.nodes(r,A.Arithmetic)[0]
        self.assertEqual(r.annotation(node).type.representation,'exact-rational')
        self.assertIn('division-by-zero',[c['kind'] for c in r.annotation(node).checks])

    def test_conditions_and_abbreviated_subject_bindings(self):
        r=self.good('IF NUM-A = 1 OR 2 DISPLAY NUM-A END-IF.',data=('01 NUM-A PIC 9.',))
        abbrev=self.nodes(r,A.AbbreviatedCondition)[0]
        subject=r.annotation(abbrev).details['subject']
        self.assertEqual(r.annotations[subject].symbol_id,self.symbol(r,'NUM-A').id)
        self.bad('CONDITION_REQUIRED','IF NUM-A DISPLAY NUM-A END-IF.',data=('01 NUM-A PIC 9.',))

    def test_evaluate_relative_class_and_comparison(self):
        r=self.good('EVALUATE NUM-A WHEN LESS 2 CONTINUE',
            'WHEN IS NOT NUMERIC CONTINUE', 'WHEN OTHER CONTINUE END-EVALUATE.',data=('01 NUM-A PIC 9.',))
        subject=self.nodes(r,A.Evaluate)[0].subjects[0]
        for cls in (A.AbbreviatedCondition,A.ClassCondition):
            self.assertEqual(r.annotation(self.nodes(r,cls)[0]).details['subject'],r.node_ids[id(subject)])

    def test_subscript_count_bounds_type(self):
        data=('01 TAB-A OCCURS 3.','05 FIELD-A PIC X.','01 DEC-A PIC 9V9.')
        self.bad('SUBSCRIPT_COUNT','DISPLAY FIELD-A.',data=data)
        self.bad('SUBSCRIPT_BOUNDS','DISPLAY FIELD-A(0).',data=data)
        self.bad('SUBSCRIPT_BOUNDS','DISPLAY FIELD-A(4).',data=data)
        self.bad('INTEGER_REQUIRED','DISPLAY FIELD-A(DEC-A).',data=data)
        self.bad('NUMERIC_REQUIRED','DISPLAY FIELD-A("A").',data=data)

    def test_reference_modification_result_and_dynamic_checks(self):
        r=self.good('DISPLAY TEXT-A(2:3) TEXT-A(N:).',data=('01 TEXT-A PIC X(8).','01 N PIC 9.',))
        refs=[n for n in self.nodes(r,A.Reference) if n.name=='TEXT-A']
        self.assertEqual(r.annotation(refs[0]).type.length,3)
        self.assertIsNone(r.annotation(refs[1]).type.length)
        self.assertEqual(r.annotation(refs[1]).checks[0]['kind'],'refmod')
        self.bad('REFMOD_BOUNDS','DISPLAY TEXT-A(7:3).',data=('01 TEXT-A PIC X(8).',))
        self.bad('REFMOD_CATEGORY','DISPLAY NUM-A(1:2).',data=('01 NUM-A PIC 9(4) COMP.',))

    def test_variable_occurs_depending_and_bounds_metadata(self):
        r=self.good('DISPLAY FIELD-A(2).',data=('01 N PIC 9.','01 TAB-A OCCURS 1 TO 5 DEPENDING ON N.','05 FIELD-A PIC X.'))
        layout=r.layout.for_symbol(self.symbol(r,'FIELD-A'))
        self.assertEqual(layout.dimensions[0].depending_id,self.symbol(r,'N').id)
        self.assertEqual(r.layout.areas['WORKING-STORAGE'],6)
        ref=next(n for n in self.nodes(r,A.Reference) if n.name=='FIELD-A')
        self.assertEqual(r.annotation(ref).checks[0]['depending_id'],self.symbol(r,'N').id)

    def test_intrinsic_signatures_and_lengths(self):
        r=self.good('DISPLAY FUNCTION REVERSE(TEXT-A) LENGTH OF TEXT-A.',data=('01 TEXT-A PIC X(8).',))
        self.assertEqual(r.annotation(self.nodes(r,A.FunctionCall)[0]).type.length,8)
        self.assertEqual(r.annotation(self.nodes(r,A.LengthOf)[0]).details['constant_length'],8)
        self.bad('FUNCTION_ARITY','DISPLAY FUNCTION MOD(1).')
        self.bad('FUNCTION_ARGUMENT_TYPE','DISPLAY FUNCTION INTEGER("A").')
        self.bad('UNSUPPORTED_FUNCTION_UNKNOWN','DISPLAY FUNCTION UNKNOWN(1).')

    def test_forward_procedures_and_perform_range(self):
        r=check_source(unit(body=('PERFORM START-A THRU END-A.','STOP RUN.',
            'START-A.','DISPLAY "A".','END-A.','EXIT.')))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        perform=self.nodes(r,A.Perform)[0]
        binding=r.annotation(perform).details['perform']
        self.assertEqual(r.table.symbols[binding['entry_symbol']].name,'START-A')
        self.assertEqual(r.table.symbols[binding['limit_symbol']].name,'END-A')
        self.assertEqual(binding['stack'],'explicit-perform')
        self.assertEqual(r.annotation(self.nodes(r,A.Exit)[0]).details['exit']['effect'],'noop')

    def test_undefined_and_reversed_control_targets(self):
        self.bad('UNDEFINED_SYMBOL','PERFORM MISSING.')
        self.bad('UNDEFINED_SYMBOL','GO TO MISSING.')
        r=check_source(unit(body=('PERFORM END-A THRU START-A.','START-A.','EXIT.','END-A.','EXIT.')))
        self.assertIn('REVERSED_PERFORM_RANGE',[d.code for d in r.diagnostics])

    def test_exit_context_and_boolean_loop_control(self):
        self.bad('EXIT_CONTEXT','EXIT PERFORM.')
        self.bad('EXIT_CONTEXT','EXIT SECTION.')
        self.bad('CONDITION_REQUIRED','PERFORM UNTIL 1 CONTINUE END-PERFORM.')
        self.good('PERFORM 2 TIMES EXIT PERFORM END-PERFORM.')

    def test_index_varying_and_set(self):
        self.good('PERFORM VARYING IDX FROM 1 BY 1 UNTIL IDX > 3',
            'DISPLAY FIELD-A(IDX) END-PERFORM SET IDX TO 1.',data=('01 TAB-A OCCURS 3 INDEXED BY IDX.','05 FIELD-A PIC X.'))
        self.bad('INVALID_SET_TARGET','SET NUM-A TO 1.',data=('01 NUM-A PIC 9.',))

    def test_search_all_keys_and_index_bindings(self):
        r=self.good('SEARCH ALL TAB-A WHEN CODE(IDX) = 1 DISPLAY CODE(IDX)',
            'END-SEARCH.',data=('01 TAB-A OCCURS 3 ASCENDING KEY CODE INDEXED BY IDX.','05 CODE PIC 9.'))
        search=self.nodes(r,A.Search)[0]
        binding=r.annotation(search).details['search_all']
        self.assertEqual(binding['keys'][0]['symbols'],[self.symbol(r,'CODE').id])
        self.assertEqual(r.annotation(search).details['indexes'],[self.symbol(r,'IDX','index').id])
        r=self.good('SET IDX OF TAB-A TO 1.',data=(
            '01 TAB-A OCCURS 3 ASCENDING KEY CODE INDEXED BY IDX.',
            '05 CODE PIC 9.','01 TAB-B OCCURS 3',
            'ASCENDING KEY CODE INDEXED BY IDX.','05 CODE PIC 9.'))
        self.assertEqual(len(r.table.candidates('IDX',['index'])),2)
        self.assertEqual(len(r.table.candidates('CODE',['data'])),2)

    def test_string_unstring_inspect_validate_destinations(self):
        self.good('STRING "AB" DELIMITED BY SIZE INTO TEXT-A END-STRING',
            'UNSTRING TEXT-A DELIMITED BY SPACE INTO FIELD-A END-UNSTRING',
            'INSPECT TEXT-A TALLYING NUM-A FOR ALL "A".',data=('01 TEXT-A PIC X(8).','01 FIELD-A PIC X(4).','01 NUM-A PIC 9(2).'))
        self.bad('TEXT_TARGET_REQUIRED','STRING "A" DELIMITED BY SIZE INTO NUM-A.',data=('01 NUM-A PIC 9.',))
        self.bad('INSPECT_REPLACEMENT_LENGTH','INSPECT TEXT-A REPLACING ALL "AB" BY "X".',data=('01 TEXT-A PIC X(8).',))

    def test_no_op_return_and_stop_are_distinct(self):
        r=self.good('EXIT CONTINUE GOBACK STOP RUN.')
        self.assertEqual(r.annotation(self.nodes(r,A.Exit)[0]).details['exit']['effect'],'noop')
        self.assertEqual(r.annotation(self.nodes(r,A.Goback)[0]).details['effect'],'return-caller-or-host')
        self.assertEqual(r.annotation(self.nodes(r,A.StopRun)[0]).details['effect'],'terminate-run-unit')

    def test_annotations_have_stable_ids_and_are_serializable(self):
        text=program('MOVE 1 TO NUM-A.',data=('01 NUM-A PIC 9.',))
        left,right=check_source(text),check_source(text)
        self.assertEqual(left.dump_symbols(),right.dump_symbols())
        json.dumps(left.dump_symbols())
        self.assertEqual(left.frontend.ast.data.sections[0].entries[0].name,'NUM-A')

    def test_invalid_frontend_and_copybook_not_validated_as_program(self):
        r=check_source('')
        self.assertFalse(r.success)
        fragment=parse_source(fixed('01 FIELD-A PIC X.',area='A'),copybook=True)
        r=analyze(fragment)
        self.assertFalse(r.success)
        self.assertIn('COPYBOOK_CONTEXT_REQUIRED',[d.code for d in r.diagnostics])

    def test_value_precision_uses_no_decimal_context_rounding(self):
        value='9999999999999999999999999999'
        r=self.good('STOP RUN.',data=(f'01 BIG-A PIC 9(28) VALUE {value}.',))
        self.assertEqual(self.symbol(r,'BIG-A').type.precision,28)
        self.good('STOP RUN.',data=('01 NUM-A PIC 9 VALUE 1.00.',))

    def test_index_cannot_address_a_different_table(self):
        self.bad('INDEX_TABLE_MISMATCH','DISPLAY FIELD-B(IDX-A).',data=(
            '01 TAB-A OCCURS 3 INDEXED BY IDX-A.','05 FIELD-A PIC X.',
            '01 TAB-B OCCURS 3 INDEXED BY IDX-B.','05 FIELD-B PIC X(2).'))

    def test_initialize_replacement_rejects_text_for_numeric_category(self):
        self.bad('INVALID_INITIALIZE_REPLACEMENT','INITIALIZE NUM-A REPLACING NUMERIC BY "A".',data=('01 NUM-A PIC 9.',))

    def test_intrinsic_ord_requires_one_byte(self):
        self.bad('FUNCTION_ARGUMENT_LENGTH','DISPLAY FUNCTION ORD("AB").')

    def test_linkage_redefines_preserves_same_external_area(self):
        r=check_source(unit(linkage=('01 ARG-A PIC X(4).','01 VIEW-A REDEFINES ARG-A PIC 9(4).'),using=' USING ARG-A'))
        self.assertTrue(r.success,[d.format() for d in r.diagnostics])
        original=r.layout.for_symbol(self.symbol(r,'ARG-A'))
        alias=r.layout.for_symbol(self.symbol(r,'VIEW-A'))
        self.assertEqual(alias.area,original.area)
        self.assertEqual(alias.offset,original.offset)
        self.assertEqual(alias.redefines,original.symbol_id)
        self.assertFalse(alias.local)

    def test_set_condition_is_not_writable_move_receiver(self):
        self.bad('NOT_WRITABLE','MOVE "Y" TO YES-A.',data=('01 STATUS-A PIC X.','88 YES-A VALUE "Y".',))

    def test_unanalyzed_nodes_cannot_pass_silently(self):
        frontend=parse_source(program('CONTINUE.'))
        old=frontend.ast.procedure.body[0].statements[0]
        frontend.ast.procedure.body[0].statements[0]=A.Statement(span=old.span,token_start=old.token_start,token_end=old.token_end)
        r=analyze(frontend)
        self.assertFalse(r.success)
        self.assertIn('UNSUPPORTED_STATEMENT',[d.code for d in r.diagnostics])

    def test_length_of_table_is_one_occurrence(self):
        r=self.good('DISPLAY LENGTH OF ROW-A.',data=('01 GRP.','05 ROW-A OCCURS 3.','10 FIELD-A PIC X(4).'))
        length=self.nodes(r,A.LengthOf)[0]
        self.assertEqual(r.annotation(length).details['constant_length'],4)
        self.assertEqual(r.layout.for_symbol(self.symbol(r,'ROW-A')).total_size,12)

    def test_length_of_variable_group_is_deferred(self):
        r=self.good('DISPLAY LENGTH OF GRP.',data=('01 N PIC 9.','01 GRP.',
            '05 ROW-A OCCURS 1 TO 3 DEPENDING ON N.','10 FIELD-A PIC X(4).'))
        length=self.nodes(r,A.LengthOf)[0]
        self.assertIsNone(r.annotation(length).details['constant_length'])
        self.assertEqual(r.annotation(length).details['maximum_length'],12)
        self.assertEqual(r.annotation(length).details['dynamic_dimensions'][0]['depending_id'],self.symbol(r,'N').id)
