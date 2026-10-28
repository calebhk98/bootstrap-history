"""A view another module reads cannot be changed through its answer (sim/assembly/read_guard.py `guarded`)."""
import json
import unittest

from sim.assembly.api import ViewWrite
from sim.assembly.read_guard import guarded

QUICK_TOPIC = True


class GuardedAnswers(unittest.TestCase):

    def test_a_dict_answer_reads_as_the_dict_it_was(self):
        answer = guarded({"grain": 2.0, "salt": 1.0}, "held_goods", "materials")
        self.assertIsInstance(answer, dict)
        self.assertEqual(answer, {"grain": 2.0, "salt": 1.0})
        self.assertEqual(json.loads(json.dumps(answer)), {"grain": 2.0, "salt": 1.0})

    def test_writing_a_dict_answer_raises_naming_the_view_and_the_reader(self):
        owner_state = {"grain": 2.0}
        answer = guarded(owner_state, "held_goods", "materials")
        for write in (lambda: answer.__setitem__("probe", 123.0), lambda: answer.update(probe=1.0), lambda: answer.pop("grain"),
                      lambda: answer.setdefault("probe", 0.0), answer.clear):
            with self.assertRaises(ViewWrite) as caught:
                write()
            self.assertIn("held_goods", str(caught.exception))   # presentation: the error names the view and the reader
            self.assertIn("materials", str(caught.exception))
        self.assertEqual(owner_state, {"grain": 2.0})

    def test_a_nested_value_read_from_the_answer_is_guarded_too(self):
        answer = guarded({"tile": {"grain": [1.0, 2.0]}}, "stock_by_tile", "markets")
        with self.assertRaises(ViewWrite):
            answer["tile"]["grain"].append(3.0)
        with self.assertRaises(ViewWrite):
            answer.get("tile")["salt"] = 1.0
        with self.assertRaises(ViewWrite):
            dict(answer.items())["tile"]["salt"] = 1.0

    def test_list_and_set_answers_cannot_be_changed(self):
        listed = guarded([3.0, 1.0], "prices", "coin")
        with self.assertRaises(ViewWrite):
            listed.sort()
        with self.assertRaises(ViewWrite):
            listed.append(2.0)
        held = guarded({"smithing"}, "techniques_held", "polity")
        with self.assertRaises(ViewWrite):
            held.add("writing")
        self.assertEqual((listed, held), ([3.0, 1.0], {"smithing"}))

    def test_a_readers_own_copy_can_change(self):
        answer = guarded({"grain": 2.0}, "held_goods", "materials")
        mine = dict(answer)
        mine["grain"] = 5.0
        self.assertEqual((mine["grain"], answer["grain"]), (5.0, 2.0))

    def test_a_dict_subclass_keeps_its_class_and_its_reads(self):
        from collections import Counter, defaultdict
        counted = guarded(Counter({"grain": 2.0}), "held_goods", "materials")
        self.assertIsInstance(counted, Counter)
        self.assertEqual((counted["grain"], counted["salt"]), (2.0, 0))
        with self.assertRaises(ViewWrite):
            counted["salt"] += 1.0
        with self.assertRaises(ViewWrite):
            counted.update({"salt": 1.0})
        listed = guarded(defaultdict(list, {"tile": [1.0]}), "people_by_tile", "disease")
        self.assertEqual(listed.default_factory, list)
        with self.assertRaises(ViewWrite):
            listed["tile"].append(2.0)

    def test_numbers_strings_and_tuples_pass_as_they_are(self):
        self.assertEqual([guarded(value, "view", "reader") for value in (2.5, "rome", (1, 2), None)], [2.5, "rome", (1, 2), None])


if __name__ == "__main__":
    unittest.main()
