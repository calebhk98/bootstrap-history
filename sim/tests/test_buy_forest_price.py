"""Complaint 640 (a break test: a forest bought with no price shown): `quote forest` and `buy_forest` read one price,
`forest_price_per_hectare`, so the quoted price is the charge. `buy_forest` is called on a stand-in `self` with the ceiling, the
purse and the price level written out; a purchase the purse cannot cover buys nothing and a ceiling cuts what is bought."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.economy_mining import MiningMixin
from sim.refusal import cause_of
from sim.tests import event_stand_in


class Woodland(MiningMixin):
    send = event_stand_in.send
    FOREST_COST_PER_HA = 4.0
    price_index = 1.5

    def __init__(self, budget=1.0e9, ceiling=1000.0, held=0.0):
        self.budget, self.ceiling, self.paid, self.log = budget, ceiling, [], []
        self.holdings = types.SimpleNamespace(forest_ha=held)
        self.state = types.SimpleNamespace(holdings=self.holdings, household=types.SimpleNamespace(log=self.log),
                                           scenario=types.SimpleNamespace(year=100))

    def forest_land_ceiling(self):
        return self.ceiling

    def spending_power(self, kind):
        return self.budget

    def pay_edge(self, edge, money, text):
        self.paid.append(money)


class BuyForest(unittest.TestCase):
    def test_the_price_quoted_per_hectare_is_the_price_level_times_the_base_cost(self):
        self.assertEqual(Woodland().forest_price_per_hectare(), 4.0 * 1.5)

    def test_the_charge_is_the_hectares_times_the_quoted_price(self):
        game = Woodland()
        self.assertEqual(game.buy_forest(100), 100)
        self.assertEqual(game.paid, [100 * game.forest_price_per_hectare()])
        self.assertEqual(game.holdings.forest_ha, 100)

    def test_a_purchase_the_purse_cannot_cover_buys_nothing(self):
        game = Woodland(budget=100.0)
        self.assertEqual(game.buy_forest(100), 0.0)
        self.assertEqual((game.paid, game.holdings.forest_ha), ([], 0.0))

    def test_a_purchase_beyond_the_ceiling_is_cut_to_the_room_and_the_cut_is_logged(self):
        game = Woodland(ceiling=150.0, held=100.0)
        self.assertEqual(game.buy_forest(100), 50.0)
        self.assertEqual(cause_of(game.log[0][1]), "coppice_limit")

    def test_no_room_buys_nothing_and_charges_nothing(self):
        game = Woodland(ceiling=100.0, held=100.0)
        self.assertEqual(game.buy_forest(10), 0.0)
        self.assertEqual(game.paid, [])


if __name__ == "__main__":
    unittest.main()
