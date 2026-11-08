"""IdTable: dense, history-independent numbering of names."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.compiled_tables.ids import DROPPED, IdTable


class AdmitTests(unittest.TestCase):
    def test_new_names_are_numbered_in_sorted_order_whatever_order_they_arrive(self):
        ids = IdTable("agent")
        numbers = ids.admit(["rome", "alba", "cumae"])
        self.assertEqual(numbers.tolist(), [2, 0, 1])
        self.assertEqual(ids.names, ("alba", "cumae", "rome"))

    def test_a_later_batch_continues_the_numbering_and_keeps_old_numbers(self):
        ids = IdTable("good", ["wheat", "iron"])
        numbers = ids.admit(["zinc", "iron", "brass"])
        self.assertEqual(numbers.tolist(), [3, 0, 2])
        self.assertEqual(ids.names, ("iron", "wheat", "brass", "zinc"))


class LookupTests(unittest.TestCase):
    def test_the_hot_read_views_follow_the_table(self):
        ids = IdTable("good", ["wheat", "iron"])
        ids.admit(["brass"])
        self.assertEqual((ids.numbers.get("brass"), ids.numbers.get("gold"), ids.name_list), (2, None, ["iron", "wheat", "brass"]))

    def test_find_answers_none_for_an_unknown_name(self):
        self.assertIsNone(IdTable("good", ["iron"]).find("gold"))

    def test_number_refuses_an_unknown_name(self):
        with self.assertRaises(KeyError):
            IdTable("good", ["iron"]).number("gold")

    def test_describe_shows_the_name_and_number(self):
        self.assertEqual(IdTable("good", ["iron", "wheat"]).describe(1), "wheat#1")

    def test_describe_shows_a_number_that_is_not_known_instead_of_raising(self):
        self.assertIn("#7", IdTable("good", ["iron"]).describe(7))


class StateTests(unittest.TestCase):
    def test_from_state_restores_the_live_numbering_not_a_sorted_one(self):
        live = ["wheat", "iron"]       # admitted in two batches, so not in sorted order
        restored = IdTable.from_state("good", live)
        self.assertEqual(restored.number("wheat"), 0)
        self.assertEqual(restored.state(), live)

    def test_from_state_refuses_a_repeated_name(self):
        with self.assertRaises(ValueError):
            IdTable.from_state("good", ["iron", "iron"])


class CompactTests(unittest.TestCase):
    def test_compacted_drops_the_dead_and_maps_old_numbers_to_new(self):
        ids = IdTable("agent", ["a", "b", "c", "d"])
        smaller, old_to_new = ids.compacted(numpy.array([True, False, True, False]))
        self.assertEqual(smaller.names, ("a", "c"))
        self.assertEqual(old_to_new.tolist(), [0, DROPPED, 1, DROPPED])


if __name__ == "__main__":
    unittest.main()
