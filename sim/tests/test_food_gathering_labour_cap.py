"""Fishers and hunters feed a bounded number of people: food from the water and from game is held to the hours
of the gatherers the labour model has (Complaint 411). Small fixtures only, no game is built.
"""

QUICK_TOPIC = True

import types
import unittest

from sim.agriculture.state import AgricultureWorld
from sim.engine import data
from sim.geography.api import Geography
from sim.labour import api as labour_api
from sim.tests import agriculture_stand_in
from sim.tests.test_geography_food_gaps import STEPPE, mini_map
from sim.world.farming_technique import DEFAULT_TECHNIQUE

REGISTRY = {
    "hunter": {"family": "labour", "gathers_food_sources": ["hunting"], "food_kcal_per_hour": 1000.0},
    "fisher": {"family": "labour", "gathers_food_sources": ["marine_fishing", "freshwater_fishing"],
               "food_kcal_per_hour": 500.0},
    "smith": {"family": "craft"},
}


class LabourCapTests(unittest.TestCase):
    def test_a_source_is_bounded_by_the_hours_of_the_trades_that_gather_it(self):
        caps = labour_api.hours_cap_kcal({"hunter": 2000.0, "fisher": 1000.0, "smith": 5000.0}, REGISTRY)
        self.assertEqual(caps, {"hunting": 2.0e6, "marine_fishing": 5.0e5, "freshwater_fishing": 5.0e5})

    def test_no_hours_means_no_food_from_that_source(self):
        self.assertEqual(labour_api.hours_cap_kcal({}, REGISTRY)["hunting"], 0.0)

    def test_food_output_scales_with_hours_up_to_the_ecological_ceiling(self):
        ceiling = {"hunting": 1.0e7, "crops": 5.0e7}
        taken = [labour_api.capped_kcal(ceiling, labour_api.hours_cap_kcal({"hunter": hours}, REGISTRY))["hunting"]
                 for hours in (1000.0, 2000.0, 4000.0, 1.0e6)]
        self.assertEqual(taken, [1.0e6, 2.0e6, 4.0e6, 1.0e7])

    def test_a_source_no_trade_gathers_is_not_bounded(self):
        self.assertEqual(labour_api.capped_kcal({"crops": 9.0}, labour_api.hours_cap_kcal({}, REGISTRY)), {"crops": 9.0})

    def test_the_shipped_trades_name_fishers_and_hunters_with_a_return(self):
        caps = labour_api.hours_cap_kcal({"hunter": 1.0, "fisher": 1.0}, {
            trade_id: {"family": trade.family, **trade.extra} for trade_id, trade in data.TRADE_REGISTRY.items()})
        for source in ("hunting", "marine_fishing", "freshwater_fishing"):
            self.assertGreater(caps[source], 0.0, source)


def society(hours, stock=None):
    """The agriculture module over a one-tile steppe map; `hours` is the society's labour hours, which a test may replace."""
    world_map = mini_map({"a": (STEPPE, {}, [])})
    civ = {"home_tiles": ["a"]}
    geography = Geography(types.SimpleNamespace(civ=civ, world_map=world_map))
    labour = {"hours": dict(hours)}
    farm = agriculture_stand_in.build(world=AgricultureWorld(wild_stock=dict(stock or {})), views={
        "society_labour_hours": lambda: labour["hours"], "trade_registry": {trade_id: {"family": trade.family, **trade.extra} for trade_id, trade in data.TRADE_REGISTRY.items()},
        "farming_technique": DEFAULT_TECHNIQUE, "society_herds": {},
        "crop_sites": geography.crop_sites, "food_kcal_by_source": geography.food_kcal_by_source,
        "game_food_sources": geography.game_food_sources, "huntable_kcal": geography.huntable_kcal,
        "take_hunt": geography.take_hunt, "regrow_wild_stock": geography.regrow_wild_stock,
        "tile_soil_nitrogen_factors": geography.soil_nitrogen_factors})
    farm.labour_hours = labour
    return farm


class SocietyFoodTests(unittest.TestCase):
    def test_a_society_with_no_hunters_takes_no_game_and_loses_none(self):
        game = society({"labourer": 1.0e6})
        game.step_wild_stock()
        self.assertEqual(game.world.wild_stock, {})
        self.assertEqual(game.food_potential().get("hunting", -1.0), 0.0)

    def test_a_few_hunters_bring_in_only_what_their_hours_allow(self):
        game = society({"hunter": 1000.0})
        self.assertAlmostEqual(game.food_potential()["hunting"], 1000.0 * 1115.0)
        self.assertIn("crops", game.food_potential())   # the steppe tile crops almost nothing, but the source is not capped away

    def test_hunters_thin_the_game_and_the_game_recovers_when_they_stop(self):
        game = society({"hunter": 1.0e9})
        for _year in range(5):
            game.step_wild_stock()
        thinned = dict(game.world.wild_stock["a"])
        self.assertTrue(all(fraction < 1.0 for fraction in thinned.values()))
        game.labour_hours["hours"] = {}
        for _year in range(300):
            game.step_wild_stock()
        self.assertEqual(game.world.wild_stock, {})

    def test_hunting_less_than_the_surplus_does_not_deplete_the_game(self):
        game = society({"hunter": 10.0})
        for _year in range(100):
            game.step_wild_stock()
        self.assertTrue(all(fraction > 0.99 for fraction in game.world.wild_stock.get("a", {}).values()))


if __name__ == "__main__":
    unittest.main()
