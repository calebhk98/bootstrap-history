"""Hunting depletes a game stock that the game keeps between years, and the stock regrows (Complaint 411).

Tiles are copies of real map tiles, so every case runs without a game.
"""

QUICK_TOPIC = True

import unittest

from sim.geography import api
from sim.tests.test_geography_food_gaps import STEPPE, mini_map

FOREST = "france_05"


def hunted_total(world_map, wild_stock=None):
    return sum(api.hunted_kcal("a", wild_stock, world_map).values())


class WildStockTests(unittest.TestCase):
    def setUp(self):
        self.world_map = mini_map({"a": (STEPPE, {}, [])})

    def test_an_untouched_map_needs_no_stock(self):
        self.assertEqual(api.regrow_wild_stock({}, self.world_map), {})
        self.assertEqual(api.food_potential("a", None, self.world_map, {})["kcal_per_year"],
                         api.food_potential("a", None, self.world_map)["kcal_per_year"])

    def test_hunting_takes_stock_and_a_depleted_stock_yields_less(self):
        full = api.hunted_kcal("a", {}, self.world_map)
        self.assertTrue(full)
        stock = api.draw_wild_stock({}, "a", {species: 20.0 * kcal for species, kcal in full.items()}, self.world_map)
        self.assertTrue(stock["a"])
        self.assertTrue(all(0.0 <= fraction < 1.0 for fraction in stock["a"].values()))
        self.assertLess(hunted_total(self.world_map, stock), hunted_total(self.world_map))
        potential = api.food_potential("a", None, self.world_map, stock)["kcal_per_year"]
        self.assertLess(potential.get("hunting", 0.0), api.food_potential("a", None, self.world_map)["kcal_per_year"]["hunting"])

    def test_the_draw_is_not_applied_in_place(self):
        before = {"a": {"steppe_grazers": 0.9}}
        api.draw_wild_stock(before, "a", {"steppe_grazers": 1.0e9}, self.world_map)
        self.assertEqual(before, {"a": {"steppe_grazers": 0.9}})

    def test_a_stock_hunted_to_nothing_regrows_over_years_and_ends_full(self):
        stock = {"a": {"steppe_grazers": 0.0}}
        previous = 0.0
        for _year in range(200):
            stock = api.regrow_wild_stock(stock, self.world_map)
            current = stock.get("a", {}).get("steppe_grazers", 1.0)
            self.assertGreaterEqual(current, previous)
            previous = current
        self.assertEqual(stock, {})

    def test_hunting_the_yearly_surplus_leaves_a_steady_stock(self):
        full = api.hunted_kcal("a", {}, self.world_map)
        stock = api.draw_wild_stock({}, "a", {species: 0.5 * kcal for species, kcal in full.items()}, self.world_map)
        for _year in range(50):
            stock = api.regrow_wild_stock(stock, self.world_map)
            stock = api.draw_wild_stock(stock, "a", {species: 0.5 * kcal for species, kcal in full.items()}, self.world_map)
        self.assertTrue(all(fraction > 0.3 for fraction in stock["a"].values()))

    def test_hunting_out_the_wild_grazers_leaves_more_grass_for_herds(self):
        grazers = {"a": {"steppe_grazers": 0.1, "savanna_ungulates": 0.1}}
        herds = api.food_potential("a", None, self.world_map)["kcal_per_year"].get("pastoral", 0.0)
        thinned = api.food_potential("a", None, self.world_map, grazers)["kcal_per_year"].get("pastoral", 0.0)
        self.assertGreater(thinned, herds)


if __name__ == "__main__":
    unittest.main()
