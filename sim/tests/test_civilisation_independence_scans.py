"""Complaints/131 and 132: whether an institution is foreign follows the society tag. A pure function, no game. The game
starting with a civilisation file absent is in test_civilisation_independence."""
QUICK_TOPIC = True

import unittest


class ForeignInstitutionsFollowData(unittest.TestCase):
    """Whether an institution is foreign comes from the civilisation's society
    tag and the marker table, not from which civilisation it is."""

    def test_foreignness_follows_the_society_tag(self):
        from sim.diffusion import institution_societies as societies
        text = "annona_grain_dole"
        owner = societies._table()["markers"]["annona"]
        self.assertFalse(societies.belongs_to_other_society(text, {"id": owner}, "markers"))
        self.assertTrue(societies.belongs_to_other_society(text, {"id": "invented"}, "markers"))
        self.assertFalse(societies.belongs_to_other_society(
            text, {"id": "invented", "society": owner}, "markers"))
        self.assertTrue(societies.belongs_to_other_society(
            text, {"id": owner, "society": "invented"}, "markers"))


if __name__ == "__main__":
    unittest.main()
