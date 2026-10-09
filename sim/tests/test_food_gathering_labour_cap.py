"""Fishers and hunters feed a bounded number of people: food from the water and from game is held to the hours
of the gatherers the labour model has (Complaint 411). Small fixtures only, no game is built.
"""

QUICK_TOPIC = True

import types
import unittest

from sim.engine import data
from sim.engine.food_supply import FoodSupplyMixin
from sim.engine.state import EconomyState
from sim.labour import api as labour_api
from sim.tests.test_geography_food_gaps import STEPPE, mini_map

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
    world_map = mini_map({"a": (STEPPE, {}, [])})
    economy = EconomyState(society_labour_hours=dict(hours), wild_stock=dict(stock or {}))
    return types.SimpleNamespace(state=types.SimpleNamespace(economy=economy), civ={"home_tiles": ["a"]},
                                 world_map=world_map)


class Society(FoodSupplyMixin):
    def __init__(self, hours, stock=None):
        self.__dict__.update(vars(society(hours, stock)))


class SocietyFoodTests(unittest.TestCase):
    def test_a_society_with_no_hunters_takes_no_game_and_loses_none(self):
        game = Society({"labourer": 1.0e6})
        game.step_wild_stock()
        self.assertEqual(game.state.economy.wild_stock, {})
        self.assertEqual(game.society_food_potential().get("hunting", -1.0), 0.0)

    def test_a_few_hunters_bring_in_only_what_their_hours_allow(self):
        game = Society({"hunter": 1000.0})
        self.assertAlmostEqual(game.society_food_potential()["hunting"], 1000.0 * 1115.0)
        self.assertGreater(game.society_food_potential()["crops"], 0.0)

    def test_hunters_thin_the_game_and_the_game_recovers_when_they_stop(self):
        game = Society({"hunter": 1.0e9})
        for _year in range(5):
            game.step_wild_stock()
        thinned = dict(game.state.economy.wild_stock["a"])
        self.assertTrue(all(fraction < 1.0 for fraction in thinned.values()))
        game.state.economy.society_labour_hours = {}
        for _year in range(300):
            game.step_wild_stock()
        self.assertEqual(game.state.economy.wild_stock, {})

    def test_hunting_less_than_the_surplus_does_not_deplete_the_game(self):
        game = Society({"hunter": 10.0})
        for _year in range(100):
            game.step_wild_stock()
        self.assertTrue(all(fraction > 0.99 for fraction in game.state.economy.wild_stock.get("a", {}).values()))


if __name__ == "__main__":
    unittest.main()
