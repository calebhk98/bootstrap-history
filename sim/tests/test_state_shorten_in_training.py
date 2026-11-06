"""The short `state` reply counts the people in training, not the rows of the queue."""

QUICK_TOPIC = True

import unittest

from sim.ui.proto.state import _agent_state_shorten


class InTraining(unittest.TestCase):
    def test_in_training_sums_the_people_of_every_row(self):
        out = _agent_state_shorten({"training_pending": [{"trade": "smith", "people": 2.5}, {"trade": "carter", "people": 4.0}]}, False)
        self.assertEqual(out["in_training"], 6.5)


if __name__ == "__main__":
    unittest.main()
