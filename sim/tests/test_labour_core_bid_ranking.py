"""Employers are ranked by the most an hour is worth to them (Complaint 667): an entrant whose maximum bid beats an
incumbent's takes hours from it even though the wage paid stays under the ceiling. Plain records, no game."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing
from sim.tests.test_labour_core_clearing import bid, make_state, run


def held_market():
    state = make_state(people=10.0, wage=1.0)
    state.hired_hours = {"vale": {"digger": {"farm": 1000.0}}}
    return state


class HigherMaximumBidWins(unittest.TestCase):
    def test_an_entrant_with_a_far_higher_maximum_takes_hours_from_the_incumbent(self):
        result = run(held_market(), [bid("farm", 2000.0, maximum=3.0), bid("merchant", 50.0, maximum=300.0)])
        self.assertGreater(result.hired_by_employer.get("merchant", 0.0), 0.0)
        self.assertLess(result.hired_by_employer["farm"], 1000.0)

    def test_an_entrant_with_a_lower_maximum_takes_nothing(self):
        result = run(held_market(), [bid("farm", 2000.0, maximum=300.0), bid("merchant", 50.0, maximum=3.0)])
        self.assertEqual(result.hired_by_employer.get("merchant", 0.0), 0.0)

    def test_the_wage_paid_still_follows_the_clearing_rule_not_the_maximum(self):
        bids = [bid("farm", 2000.0, maximum=3.0), bid("merchant", 50.0, maximum=300.0)]
        result = run(held_market(), bids)
        self.assertLessEqual(result.paid_by_employer["merchant"], result.wage * (1.0 + 1e-9))
        self.assertLess(result.wage, 300.0)

    def test_standing_orders_by_maximum_then_premium(self):
        self.assertGreater(clearing.standing(5.0, 0.0), clearing.standing(3.0, 0.5))
        self.assertGreater(clearing.standing(3.0, 0.5), clearing.standing(3.0, 0.0))


if __name__ == "__main__":
    unittest.main()
