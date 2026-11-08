"""A purpose text as a template and a reference (sim/book_purposes.py), and back."""
QUICK_TOPIC = True

import unittest

from sim.book_purposes import NO_REFERENCE, Purposes


class EncodeTests(unittest.TestCase):
    def test_a_sale_splits_into_its_template_and_the_good(self):
        purposes = Purposes()
        template, reference = purposes.encode("sale of wheat_kg")
        self.assertEqual((purposes.templates.name(template), purposes.references.name(reference)), ("sale of ", "wheat_kg"))

    def test_a_plain_text_is_a_template_with_no_reference(self):
        purposes = Purposes()
        template, reference = purposes.encode("consumption")
        self.assertEqual((purposes.templates.name(template), reference), ("consumption", NO_REFERENCE))

    def test_two_sales_share_a_template_and_differ_in_reference(self):
        purposes = Purposes()
        (first, wheat), (second, iron) = purposes.encode("sale of wheat"), purposes.encode("sale of iron")
        self.assertEqual((first == second, wheat != iron), (True, True))

    def test_the_same_text_is_always_the_same_pair(self):
        purposes = Purposes()
        self.assertEqual(purposes.encode("wages for smith"), purposes.encode("wages for smith"))

    def test_the_text_of_a_tax_splits_after_its_prefix(self):
        purposes = Purposes()
        template, reference = purposes.encode("tax:land_tax")
        self.assertEqual((purposes.templates.name(template), purposes.references.name(reference)), ("tax:", "land_tax"))


class DecodeTests(unittest.TestCase):
    def test_decode_gives_the_exact_text_back(self):
        purposes = Purposes()
        for text in ("sale of wheat_kg", "consumption", "state stores used", "tax:land_tax", "", "sale of ", "odd text of 7"):
            self.assertEqual(purposes.decode(*purposes.encode(text)), text)


class StateTests(unittest.TestCase):
    def test_a_restored_table_numbers_as_the_saved_one_did(self):
        purposes = Purposes()
        pairs = [purposes.encode(text) for text in ("sale of zinc", "sale of apples", "input", "output")]
        restored = Purposes.from_state(purposes.state())
        self.assertEqual([restored.encode(text) for text in ("sale of zinc", "sale of apples", "input", "output")], pairs)


if __name__ == "__main__":
    unittest.main()
