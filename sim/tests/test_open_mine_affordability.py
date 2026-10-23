"""Complaint 640 (a Mexica break test): a mine you typed is not a standing order to spend everything. `open_mine` with
`partial=False` refuses a mine its purse cannot pay for and spends nothing; with `partial=True` (the automatic policy) it
sinks the most the purse buys. Called on the stand-in host of test_mine_names_a_deposit with the budget set here."""
QUICK_TOPIC = True

import unittest

from .test_mine_names_a_deposit import _Host

MATERIAL = "aluminium_kg"      # no deposit data: bounded by the ceiling alone, so only the purse limits it
COST_PER_TONNE_A_YEAR = 10.0   # the host's capex, at its price level of one


class Budgeted(_Host):
    def __init__(self, budget):
        super().__init__()
        self.budget = budget

    def spending_power(self, kind):
        return self.budget


class OpenMineAffordability(unittest.TestCase):
    def test_a_mine_the_purse_cannot_pay_for_is_refused_when_it_was_typed_and_nothing_is_spent(self):
        host = Budgeted(30.0)
        self.assertEqual(host.open_mine(MATERIAL, 5.0, partial=False), 0.0)
        self.assertEqual((host.paid, host.holdings.mine_tranches), ([], None))

    def test_the_automatic_policy_sinks_the_most_the_purse_buys(self):
        host = Budgeted(30.0)
        opened = host.open_mine(MATERIAL, 5.0, partial=True)
        self.assertAlmostEqual(opened, 30.0 / COST_PER_TONNE_A_YEAR)
        self.assertAlmostEqual(host.paid[0], 30.0)

    def test_a_mine_the_purse_covers_is_sunk_whole_either_way(self):
        for partial in (False, True):
            host = Budgeted(1000.0)
            self.assertEqual(host.open_mine(MATERIAL, 5.0, partial=partial), 5.0)
            self.assertAlmostEqual(host.paid[0], 5.0 * COST_PER_TONNE_A_YEAR)

    def test_a_purse_that_buys_nothing_sinks_nothing(self):
        host = Budgeted(0.0)
        self.assertEqual(host.open_mine(MATERIAL, 5.0, partial=True), 0.0)
        self.assertEqual(host.paid, [])


if __name__ == "__main__":
    unittest.main()
