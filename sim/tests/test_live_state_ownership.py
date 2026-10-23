"""The household's own mutation methods (Complaint 640 audit: a HouseholdState built here, no game;
the facade is test_live_state_facade).

cost_capital, costCapital, add_capital, add_reputation, deduct_reputation and add_scandal update the household's
state, and the edge cases (zero, a refund, a negative delta) do the plain arithmetic."""
import unittest

from sim.engine.state import HouseholdState

QUICK_TOPIC = True


def _household():
    household = HouseholdState(capital=1000.0)
    household.total_spend = 0.0
    return household


class HouseholdMutation(unittest.TestCase):

    def test_cost_capital_takes_the_capital_and_counts_the_spend(self):
        household = _household()
        household.cost_capital(250.0)
        self.assertEqual((household.capital, household.total_spend), (750.0, 250.0))

    def test_the_camel_case_alias_does_the_same(self):
        household = _household()
        household.costCapital(150.0)
        self.assertEqual((household.capital, household.total_spend), (850.0, 150.0))

    def test_add_capital_increases_capital_only(self):
        household = _household()
        household.add_capital(500.0)
        self.assertEqual((household.capital, household.total_spend), (1500.0, 0.0))

    def test_reputation_and_scandal_move_by_their_deltas(self):
        household = _household()
        start_reputation, start_scandal = household.reputation, household.scandal
        household.add_reputation(2.5)
        household.deduct_reputation(1.0)
        household.add_scandal(3.0)
        self.assertEqual(household.reputation, start_reputation + 1.5)
        self.assertEqual(household.scandal, start_scandal + 3.0)

    def test_zero_amounts_change_nothing(self):
        household = _household()
        household.cost_capital(0.0)
        household.add_capital(0.0)
        self.assertEqual((household.capital, household.total_spend), (1000.0, 0.0))

    def test_a_negative_cost_is_a_refund(self):
        household = _household()
        household.cost_capital(100.0)
        household.cost_capital(-50.0)
        self.assertEqual((household.capital, household.total_spend), (950.0, 50.0))

    def test_a_negative_reputation_deduction_adds(self):
        household = _household()
        start = household.reputation
        household.deduct_reputation(-2.0)
        self.assertEqual(household.reputation, start + 2.0)


if __name__ == "__main__":
    unittest.main()
