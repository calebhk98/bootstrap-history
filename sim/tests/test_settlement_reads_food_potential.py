"""Complaints/416 (414): a nation's people settle by what each tile's food can feed, not by arable land alone."""
QUICK_TOPIC = True

import unittest

from sim.geography import api, settlement


class SettlementTests(unittest.TestCase):

    def test_a_tile_with_no_arable_land_but_game_and_fish_holds_people(self):
        held = ["greenland_16", "greenland_17"]
        self.assertGreater(settlement.population_share(held, "greenland_16"), 0.0)

    def test_shares_follow_the_total_food_potential_of_the_tiles(self):
        held = ["italy_01", "greenland_16", "egypt_01"]
        energy = {tile: api.food_potential(tile)["total_kcal_per_year"] for tile in held}
        total = sum(energy.values())
        for tile in held:
            self.assertAlmostEqual(settlement.population_share(held, tile), energy[tile] / total)
        self.assertAlmostEqual(sum(settlement.population_share(held, tile) for tile in held), 1.0)

    def test_the_best_fed_tile_is_the_default_base(self):
        held = ["italy_01", "greenland_16"]
        energy = {tile: api.food_potential(tile)["total_kcal_per_year"] for tile in held}
        self.assertEqual(settlement.default_base_tile(held), max(held, key=lambda tile: energy[tile]))


if __name__ == "__main__":
    unittest.main()
