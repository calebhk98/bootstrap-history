"""Complaint 640 (a break test: a forest bought with no price shown): `quote forest` and `buy_forest` read one price,
`forest_price_per_hectare`, so the quoted price is the charge. `buy_forest` is called on the resources module with the ceiling,
the purse and the price level written out; a purchase the purse cannot cover buys nothing and a ceiling cuts what is bought."""
QUICK_TOPIC = True

import unittest

from sim.refusal import Refusal
from sim.reporting.api import RecordEvent
from sim.resources.api import BuyForest
from sim.resources.constants import FOREST_LABOUR_HOURS_PER_HA
from sim.resources.state import ResourcesSeat
from sim.tests import module_harness, resources_stand_in

PRICE_INDEX = 1.5
BASE_COST = 4.0


def woodland(budget=1.0e9, ceiling=1000.0, held=0.0):
    """The resources module with a purse, a price level, a base cost of four a hectare and a ceiling written out."""
    module = resources_stand_in.build(budget=budget, seat=ResourcesSeat(forest_ha=held), views={
        "price_index": PRICE_INDEX, "money_per_labour_hour": BASE_COST / FOREST_LABOUR_HOURS_PER_HA})
    module.forest_land_ceiling = lambda: ceiling
    return module


def buy(module, hectares):
    answer = module.buy_forest(BuyForest(hectares))
    return 0.0 if isinstance(answer, Refusal) else answer


class BuyingForest(unittest.TestCase):
    def test_the_price_quoted_per_hectare_is_the_price_level_times_the_base_cost(self):
        self.assertEqual(woodland().forest_price_per_hectare(), BASE_COST * PRICE_INDEX)

    def test_the_charge_is_the_hectares_times_the_quoted_price(self):
        game = woodland()
        self.assertEqual(buy(game, 100), 100)
        self.assertEqual(resources_stand_in.paid(game), [100 * game.forest_price_per_hectare()])
        self.assertEqual(game.seat.forest_ha, 100)

    def test_a_purchase_the_purse_cannot_cover_buys_nothing(self):
        game = woodland(budget=100.0)
        answer = game.buy_forest(BuyForest(100))
        self.assertEqual(answer.cause, "cannot_afford")
        self.assertEqual((resources_stand_in.paid(game), game.seat.forest_ha), ([], 0.0))

    def test_a_purchase_beyond_the_ceiling_is_cut_to_the_room_and_the_cut_is_logged(self):
        game = woodland(ceiling=150.0, held=100.0)
        self.assertEqual(buy(game, 100), 50.0)
        (line,) = [command for command in module_harness.sent(game) if isinstance(command, RecordEvent)]
        self.assertEqual(line.kind, "coppice_limit")

    def test_no_room_buys_nothing_and_charges_nothing(self):
        game = woodland(ceiling=100.0, held=100.0)
        self.assertEqual(game.buy_forest(BuyForest(10)).cause, "no_room")
        self.assertEqual(resources_stand_in.paid(game), [])


if __name__ == "__main__":
    unittest.main()
