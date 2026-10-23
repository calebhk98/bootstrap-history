"""SCENARIO: the urbanisation mod's yearly phase stores each tile's derived town, the town provider it registers hands that
town and its mortality premium to the labour market, and the premium reaches the regions' deaths (Complaint 634)."""
import unittest

from sim.engine import mod_code, mod_stores
from sim.engine.year_phases import MOD_PHASES
from sim.labour import town_providers
from sim.tests.harness import unopened_sim
from sim.tests.mod_files import load_mod_file
from sim.tests.test_mod_stores import StoreTestBase

MOD = "bh_urbanisation_w2n6"


class UrbanisationModTests(StoreTestBase):
    def clean(self):
        super().clean()
        town_providers.PROVIDERS.clear()
        town_providers.PREMIUMS.clear()

    def installed(self):
        hooks = load_mod_file(MOD, "hooks.py")
        game = None
        hooks.register(mod_code.ModCodeApi(MOD))
        game = unopened_sim()
        phase = next(phase for phase in MOD_PHASES if phase.name == MOD + ":derive_towns")
        return hooks, game, phase

    def test_registration_declares_two_tile_stores_a_phase_and_a_provider(self):
        hooks, _game, phase = self.installed()
        self.assertEqual(mod_stores.DECLARED[MOD + ":town_people"].keyed_by, "tile")
        self.assertEqual(mod_stores.DECLARED[MOD + ":urban_mortality_premium"].keyed_by, "tile")
        self.assertEqual(phase.scope, "world")
        self.assertIn(MOD + ":towns", town_providers.PROVIDERS)
        self.assertIn(MOD + ":towns", town_providers.PREMIUMS)

    def test_the_phase_stores_the_derived_town_and_the_labour_market_reads_it(self):
        hooks, game, phase = self.installed()
        phase.handler(game, [])
        rows = {row["tile"]: row for row in hooks.urban_report(game, limit=None)["towns"]}
        base = game.labour.base_tile()
        stored = game.stores.view(MOD + ":town_people").get(base)
        self.assertEqual(stored, rows[base]["town_people"])
        people = game.labour.settlement_tiles()[base]
        self.assertEqual(game.labour.home_town_population_estimate(), min(float(stored), people))

    def test_the_stored_premium_reaches_the_regions_premium_by_tile(self):
        hooks, game, phase = self.installed()
        phase.handler(game, [])
        found = game.labour.town_mortality_premium_by_tile()
        self.assertTrue(found)
        for tile, premium in found.items():
            self.assertGreater(premium, 0.0)
            self.assertLessEqual(premium, game.stores.view(MOD + ":urban_mortality_premium").get(tile))

    def test_before_the_first_year_the_provider_has_no_opinion(self):
        _hooks, game, _phase = self.installed()
        nominal = game.labour._nominal_town_population()
        self.assertIsNone(town_providers.provided_town_population(game.labour, game.labour.base_tile(), nominal))
        self.assertEqual(game.labour.town_mortality_premium_by_tile(), {})


if __name__ == "__main__":
    unittest.main()
