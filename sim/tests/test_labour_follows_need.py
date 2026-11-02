"""The training premium grows with the interest rate (Complaint 640: the schedule built from a game's own rate is in
test_labour_follows_need_scenario)."""
QUICK_TOPIC = True

import unittest

from sim.tests import harness  # noqa: F401  (the suite's shared setup)
from sim.labour import wages


class TrainingPremiumTests(unittest.TestCase):

    def test_higher_interest_rate_gives_a_larger_premium(self):
        self.assertGreater(wages.training_premium(5.0, 0.30), wages.training_premium(5.0, 0.05))

    def test_the_default_constant_is_gone(self):
        self.assertFalse(hasattr(wages, "DEFAULT_DISCOUNT_RATE"))


if __name__ == "__main__":
    unittest.main()
