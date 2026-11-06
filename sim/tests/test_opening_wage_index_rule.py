"""`opening_wage_index` (sim/workforce/rules.py): the index a civilisation opens on, from its file."""
import unittest

from sim.workforce.rules import opening_wage_index

QUICK_TOPIC = True


class OpeningWageIndex(unittest.TestCase):

    def test_the_file_names_the_index(self):
        self.assertEqual(opening_wage_index({"wage_index": 1.25}), 1.25)

    def test_a_file_that_names_none_is_an_error_not_an_index_of_one(self):
        with self.assertRaises(KeyError):
            opening_wage_index({"id": "rome"})

    def test_an_integer_is_read_as_a_float(self):
        self.assertIsInstance(opening_wage_index({"wage_index": 2}), float)
