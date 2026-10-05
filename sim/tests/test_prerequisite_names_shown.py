"""Complaints/227: a prerequisite is shown with its name, so a player in a civilisation whose
words differ can tell what an id such as patron_senatorial is."""
import json
import unittest

from sim.tests.harness import proto


class PrerequisiteNamesTests(unittest.TestCase):

    def setUp(self):
        replies, _, _ = proto([{"cmd": "why", "id": "semaphore_telegraph"}], civ="han_china_100ad")
        self.reply = replies[0]

    def test_why_names_each_prerequisite_in_the_civilisations_words(self):
        names = self.reply["prerequisite_names"]
        self.assertEqual(set(names), set(self.reply["direct_prerequisites"]))
        self.assertIn("Grand Administrator", names["patron_senatorial"])
        self.assertNotIn("Senatorial", json.dumps(names))

    def test_the_blocked_sentence_names_the_prerequisite_beside_its_id(self):
        self.assertIn("patron_senatorial (Patronage of a commandery Grand Administrator)",
                      self.reply["start_blocked_reason"])


if __name__ == "__main__":
    unittest.main()
