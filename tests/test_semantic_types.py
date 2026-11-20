"""Contratos de tipo independentes da resolução de programas."""

from dataclasses import asdict
import unittest

from cobol_compiler.types import parse_picture, PictureError, numeric_type, arithmetic_type


class PictureTests(unittest.TestCase):
    def test_text_categories(self):
        self.assertEqual((parse_picture('A(5)').category,parse_picture('X9X').length),('alphabetic',3))
        self.assertEqual(parse_picture('X(30)').category,'alphanumeric')

    def test_implicit_decimal_and_sign_have_no_bytes(self):
        typ=parse_picture('S9(5)V99')
        self.assertEqual((typ.length,typ.precision,typ.scale,typ.signed),(7,7,2,True))
        self.assertEqual(typ.representation,'display-overpunch')

    def test_fraction_without_integer_part(self):
        typ=parse_picture('V999')
        self.assertEqual((typ.length,typ.precision,typ.scale),(3,3,3))

    def test_edited_decimal_comma(self):
        typ=parse_picture('-ZZ.ZZZ.ZZZ,999999',decimal_comma=True)
        self.assertEqual((typ.category,typ.length,typ.precision,typ.scale),('numeric-edited',18,14,6))
        self.assertEqual(typ.decimal_point,',')
        self.assertFalse(typ.numeric)

    def test_separator_depends_on_program_convention(self):
        self.assertEqual(parse_picture('ZZZ,ZZZ').scale,0)
        self.assertEqual(parse_picture('ZZZ,ZZZ',decimal_comma=True).scale,3)

    def test_binary_abi_is_explicit(self):
        for digits,size in [(4,2),(5,4),(9,4),(10,8),(18,8),(28,12)]:
            with self.subTest(digits=digits):
                typ=parse_picture(f'S9({digits})','COMP')
                self.assertEqual((typ.length,typ.representation),(size,'binary-le'))

    def test_usage_aliases(self):
        for usage in ('COMP','COMP-4','COMPUTATIONAL','BINARY'):
            self.assertEqual(parse_picture('9(6)',usage).usage,'COMP')

    def test_packed_decimal(self):
        self.assertEqual(parse_picture('S9(5)V99','COMP-3').length,4)
        self.assertEqual(parse_picture('9(6)','PACKED-DECIMAL').length,4)

    def test_twenty_eight_digits_are_not_restricted_to_int64(self):
        typ=parse_picture('9(28)')
        self.assertEqual((typ.precision,typ.length),(28,28))
        self.assertEqual(asdict(typ)['representation'],'display-digits')

    def test_invalid_masks(self):
        for mask in ('','9(0)','9(-1)','X(100001)','9Q9','99S','SS99','9V9V9','9.9.9','A9','X9Z','SZZ9'):
            with self.subTest(mask=mask),self.assertRaises(PictureError): parse_picture(mask)

    def test_invalid_usage_combinations(self):
        for mask,usage in [('X(8)','COMP'),('ZZ9','COMP-3'),('9(8)','COMP-1')]:
            with self.subTest(mask=mask,usage=usage),self.assertRaises(PictureError):parse_picture(mask,usage)

    def test_addition_and_product_precision(self):
        left,right=numeric_type(7,2),numeric_type(6,3)
        summed=arithmetic_type('+',left,right)
        product=arithmetic_type('*',left,right)
        self.assertEqual((summed.precision,summed.scale),(9,3))
        self.assertEqual((product.precision,product.scale),(13,5))

    def test_division_retains_exact_rational_until_receiver(self):
        typ=arithmetic_type('/',numeric_type(28,0),numeric_type(2,0))
        self.assertIsNone(typ.scale)
        self.assertEqual(typ.representation,'exact-rational')

    def test_dynamic_power_does_not_invent_precision(self):
        self.assertIsNone(arithmetic_type('**',numeric_type(2),numeric_type(2)).precision)
