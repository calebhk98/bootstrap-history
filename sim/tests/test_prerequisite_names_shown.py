"""Complaints/227: a prerequisite is shown with its name, so a player in a civilisation whose words differ can tell what an
id such as patron_senatorial is. The label and the names map are called on nodes the test builds."""
import unittest

from sim.engine.fog import prerequisite_label, prerequisite_names

QUICK_TOPIC = True

NODES = {"patron": {"name": "Patronage of a Grand Administrator"}, "plain": {"name": "plain"}, "nameless": {}}


class PrerequisiteNamesTests(unittest.TestCase):

    def test_a_label_puts_the_name_beside_the_id(self):
        self.assertEqual(prerequisite_label(NODES, "patron"), "patron (Patronage of a Grand Administrator)")

    def test_a_label_is_the_bare_id_when_the_name_adds_nothing(self):
        self.assertEqual(prerequisite_label(NODES, "plain"), "plain")
        self.assertEqual(prerequisite_label(NODES, "nameless"), "nameless")
        self.assertEqual(prerequisite_label(NODES, "unknown"), "unknown")

    def test_names_cover_each_known_prerequisite_in_the_nodes_words(self):
        self.assertEqual(prerequisite_names(NODES, ["patron", "unknown"]), {"patron": "Patronage of a Grand Administrator"})


if __name__ == "__main__":
    unittest.main()
