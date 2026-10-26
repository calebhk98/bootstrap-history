"""Complaint 609: the farm trade and the unskilled fallback trade are different trades, so unskilled work
that is not farming (quarrying, burning, hauling) shows in the non-farm need shares."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.labour import legacy_trade_defaults, workforce_spinup
from sim.labour.market import trades as market_trades
from sim.engine.catalog import load_production_catalog
from sim.prices.solve_prices_core import techniques_available_to
from sim.labour import workforce_carriage

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _registry():
    with open(os.path.join(_ROOT, "data", "world", "trades.json"), encoding="utf-8") as handle:
        return json.load(handle)["trades"]


def _fallback(registry):
    return market_trades.fallback_trade(market_trades.trade_specs(registry))


def _rome_shares():
    with open(os.path.join(_ROOT, "data", "civilizations", "rome_100ad.json"), encoding="utf-8") as handle:
        civ = json.load(handle)
    reached = set(civ["starting_techs"])
    return workforce_spinup.need_shares_by_trade(
        load_production_catalog(_ROOT), reached, techniques_available_to,
        workforce_carriage.carriage_for(reached), civ)


class FarmTradeIsNotTheFallbackTests(unittest.TestCase):

    def test_the_farm_trade_is_a_registered_trade_other_than_the_fallback(self):
        registry = _registry()
        fallback = _fallback(registry)
        self.assertIn(legacy_trade_defaults.FARM_TRADE, registry)
        self.assertNotEqual(legacy_trade_defaults.FARM_TRADE, fallback)

    def test_unskilled_work_that_is_not_farming_has_a_non_farm_share_and_the_farm_has_none(self):
        shares = _rome_shares()
        fallback = _fallback(_registry())
        self.assertGreater(shares.get(fallback, 0.0), 0.0)
        self.assertNotIn(legacy_trade_defaults.FARM_TRADE, shares)

    def test_crop_recipes_book_the_farm_trade_not_the_fallback(self):
        production = load_production_catalog(_ROOT)
        fallback = _fallback(_registry())
        for recipe_id in ("wheat_kg", "millet_kg", "maize_kg"):
            hours = production[recipe_id]["labour_hours"]
            self.assertIn(legacy_trade_defaults.FARM_TRADE, hours, recipe_id)
            self.assertNotIn(fallback, hours, recipe_id)


if __name__ == "__main__":
    unittest.main()
