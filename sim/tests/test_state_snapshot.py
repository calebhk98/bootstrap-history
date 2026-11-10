"""`saveload.snapshot_text`: a game held as pickled serialized state gives back exactly the text `state_json` gives the
same state, including the values JSON changes on the way (tuples, integer keys, objects written with `str`)."""
QUICK_TOPIC = True

import pickle
import unittest

from sim.engine import saveload


class Named:
    """An object the JSON encoder writes with `str`, as `state_json`'s `default=str` does."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "named:" + self.name

    def __eq__(self, other):
        return isinstance(other, Named) and other.name == self.name


class SnapshotTextTest(unittest.TestCase):
    def serialized(self):
        return {"year": 104, "pair": (1, 2.5), "by_number": {3: "three", 1: "one"}, "kept": [Named("x"), 0.1 + 0.2],
                "nested": {"floats": [1e-300, -0.0, 12345.678901234567], "flag": True, "none": None}}

    def test_pickled_state_gives_the_text_of_the_state(self):
        serialized = self.serialized()
        held = ("pickle", pickle.dumps(serialized, protocol=pickle.HIGHEST_PROTOCOL))
        self.assertEqual(saveload.snapshot_text(held), saveload.state_json(serialized))

    def test_a_state_held_as_text_is_given_back_as_it_was(self):
        text = saveload.state_json(self.serialized())
        self.assertEqual(saveload.snapshot_text(("text", text)), text)

    def test_the_pickle_does_not_follow_later_changes(self):
        serialized = self.serialized()
        held = ("pickle", pickle.dumps(serialized, protocol=pickle.HIGHEST_PROTOCOL))
        before = saveload.state_json(serialized)
        serialized["nested"]["floats"].append(7.0)
        self.assertEqual(saveload.snapshot_text(held), before)


if __name__ == "__main__":
    unittest.main()
