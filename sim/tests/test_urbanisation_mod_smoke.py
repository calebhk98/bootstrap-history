"""SMOKE: the Urbanisation code mod in a whole game with the agent economy open, allowed in a temporary mods directory. After a year
its phase has stored each held tile's derived town and mortality premium in the mod's two stores; the town size the labour market
reads for the base tile is that stored town (bounded by the tile's people), and the premium the population step reads for the
tile is the stored premium scaled by the share of the tile's people who live in the town. The non-farm people the mod derives
start from the civilisation's urban fraction. The mod reads the game only through its declared access."""
import unittest

from sim.assembly.api import UndeclaredRead
from sim.tests.shipped_mod_games import ModGames
from sim.ui.proto.dispatch import _agent_dispatch_inner

MOD = "bh_urbanisation_w2n6"


class UrbanisationModTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = ModGames([MOD])
        cls.game = cls.games.opened()
        cls.games.step(cls.game)
        cls.base = cls.game.view("base_tile")()
        cls.towns = cls.game.view("store")[MOD + ":town_people"]["values"]
        cls.premiums = cls.game.view("store")[MOD + ":urban_mortality_premium"]["values"]

    @classmethod
    def tearDownClass(cls):
        cls.games.close()

    def test_the_phase_stored_a_town_and_a_premium_for_the_held_tiles(self):
        self.assertIn(self.base, self.towns)
        self.assertEqual(set(self.premiums), set(self.towns))
        self.assertGreater(max(self.towns.values()), 0.0)
        self.assertTrue(all(0.0 <= premium for premium in self.premiums.values()))

    def test_the_town_the_labour_market_reads_is_the_stored_town_bounded_by_the_tiles_people(self):
        people = self.game.view("settlement_tiles")()[self.base]
        self.assertEqual(self.game.view("home_town_population_estimate")(), min(self.towns[self.base], people))

    def test_the_premium_the_population_step_reads_is_the_stored_premium_scaled_by_the_towns_share_of_the_tile(self):
        people = self.game.view("settlement_tiles")()[self.base]
        town = self.game.view("home_town_population_estimate")()
        found = self.game.view("town_mortality_premium_by_tile")()
        self.assertAlmostEqual(found[self.base], self.premiums[self.base] * min(1.0, town / people), places=12)

    def test_the_non_farm_people_start_from_the_civilisations_urban_fraction(self):
        report = _agent_dispatch_inner(self.game, {}, {"cmd": MOD + ":towns"})
        population = self.game.view("population")().total
        fraction = self.game.view("civilisation")()["urban_fraction"]
        self.assertGreater(fraction, 0.0)
        self.assertGreaterEqual(report["nonfarm_people"], round(population * fraction))

    def test_the_mod_reads_only_what_it_declared(self):
        access = self.game.assembly.mod_access[MOD]
        self.assertIn("disease_burden", access.reads)
        with self.assertRaises(UndeclaredRead):
            access.view("cast")


if __name__ == "__main__":
    unittest.main()
