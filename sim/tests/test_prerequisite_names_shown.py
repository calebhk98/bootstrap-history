"""Complaints/227: a prerequisite is shown with its name, so a player in a civilisation whose words differ can tell what an
id such as patron_senatorial is. The label and the names map are called on nodes the test builds, and the Han words are applied by
`_localise_words` to a names map built from the tree's own (Roman) name."""
import json
import unittest

from sim.engine.data import load_civ
from sim.engine.fog import prerequisite_label, prerequisite_names
from sim.ui.proto.util import _localise_words

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

    def test_a_civilisation_whose_words_differ_sees_its_own_name_for_a_prerequisite(self):
        tree_names = {"patron_senatorial": {"name": "Senatorial patronage"}}
        reply = {"prerequisite_names": prerequisite_names(tree_names, ["patron_senatorial"])}
        local = _localise_words(reply, load_civ("han_china_100ad")["local_words"]["pairs"])
        self.assertIn("Grand Administrator", local["prerequisite_names"]["patron_senatorial"])
        self.assertNotIn("Senatorial", json.dumps(local))
        self.assertEqual(_localise_words(reply, load_civ("rome_100ad").get("local_words", {}).get("pairs")), reply)


if __name__ == "__main__":
    unittest.main()
