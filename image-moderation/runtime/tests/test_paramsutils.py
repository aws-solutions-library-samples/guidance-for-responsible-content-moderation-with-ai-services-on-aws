from unittest import TestCase

from chalicelib.paramsutils import Strings


class TestStrings(TestCase):
    def test_get_list_from_str(self):
        """
        Unit tests
        """
        string = " Military , Military Base ,Military Officer , Military Uniform,,,"
        list_tokens = Strings.get_list_from_string(string, ['Military'])
        list_tokens_with_empty = Strings.get_list_from_string('', ['Military'])
        list_tokens_with_None = Strings.get_list_from_string(None, ['Military'])

        self.assertEqual(list_tokens, ['Military', 'Military Base', 'Military Officer', 'Military Uniform'])
        self.assertEqual(list_tokens_with_empty, ['Military'])
        self.assertEqual(list_tokens_with_None, ['Military'])

    def test_get_int_from_string(self):
        """
        Unit tests
        """
        ten = Strings.get_int_from_string('10')
        empty_default = Strings.get_int_from_string('', 1)
        none_default = Strings.get_int_from_string(None, 9)
        none_default2 = Strings.get_int_from_string(None)

        self.assertEqual(ten, 10)
        self.assertEqual(empty_default, 1)
        self.assertEqual(none_default, 9)
        self.assertEqual(none_default2, 0)

    def test_get_bool_from_string(self):
        """
        Unit tests
        """
        true_val = Strings.get_bool_from_string('True')
        false_val = Strings.get_bool_from_string('False')
        empty_default = Strings.get_bool_from_string('', True)
        none_default = Strings.get_bool_from_string(None, True)
        none_default2 = Strings.get_bool_from_string(None)

        self.assertTrue(true_val)
        self.assertFalse(false_val)
        self.assertTrue(empty_default)
        self.assertTrue(none_default)
        self.assertFalse(none_default2)

    def test_get_float_from_string(self):
        """
        Unit tests
        """
        eighty_five = Strings.get_float_from_string('85.1')
        eighty = Strings.get_float_from_string('80')
        empty_default = Strings.get_float_from_string('', 10)
        none_default = Strings.get_float_from_string(None, 9)
        none_default2 = Strings.get_float_from_string(None)

        self.assertAlmostEqual(eighty_five, 85.1, 6)
        self.assertAlmostEqual(eighty, 80, 6)
        self.assertAlmostEqual(empty_default, 10, 6)
        self.assertAlmostEqual(none_default, 9, 6)
        self.assertAlmostEqual(none_default2, 0, 6)