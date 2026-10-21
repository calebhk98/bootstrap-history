"""SCENARIO (Complaint 514): the default Rome founder runs a concern whose goods the economy trades; its ledger is paid what
the year's clearing paid for them, not the engine's estimate, and the estimate leaves that concern out."""
import unittest

from .harness import sim
from .income_probe import open_book_concerns, tally_credits


class FounderPaidFromTheClearing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = sim(capital=1e9, manual=True)
        cls.concerns = open_book_concerns(cls.game, 1)
        cls.forecast = cls.game.revenue()
        cls.estimate = cls.game.estimated_revenue()
        cls.credits = tally_credits(cls.game)
        cls.game.step()
        cls.stored = cls.game.economy.agent.stored

    def test_a_concern_was_opened_that_sells_in_the_book(self):
        self.assertTrue(self.concerns)
        self.assertTrue(all(self.game.concern_sells_on_book(node_id) for node_id in self.concerns))

    def test_the_estimate_leaves_the_book_concern_out_of_the_forecast(self):
        self.assertLess(self.estimate, self.forecast)

    def test_the_ledger_credit_is_the_clearings_proceeds(self):
        self.assertAlmostEqual(self.credits["concern sales"], self.stored["seat_takings"][self.game.state.acting_seat])
        self.assertGreater(self.credits["concern sales"], 0.0)

    def test_the_estimate_credit_has_no_book_concern_in_it(self):
        self.assertAlmostEqual(self.credits["venture revenue"], self.estimate)

    def test_the_inputs_the_concern_bought_are_charged(self):
        self.assertLess(self.credits["inputs of concerns sold in the book"], 0.0)


if __name__ == "__main__":
    unittest.main()
