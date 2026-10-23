"""The urbanisation mod's registration declares two tile stores, a world-scope yearly phase and a town provider with a
mortality premium. The hooks are registered against the mod code api; no game."""

QUICK_TOPIC = True

from sim.engine import mod_code, mod_stores
from sim.engine.year_phases import MOD_PHASES
from sim.labour import town_providers
from sim.tests.mod_files import load_mod_file
from sim.tests.test_mod_stores import StoreTestBase

MOD = "bh_urbanisation_w2n6"


class UrbanisationRegistrationTests(StoreTestBase):
    def clean(self):
        super().clean()
        town_providers.PROVIDERS.clear()
        town_providers.PREMIUMS.clear()

    def test_registration_declares_two_tile_stores_a_phase_and_a_provider(self):
        load_mod_file(MOD, "hooks.py").register(mod_code.ModCodeApi(MOD))
        phase = next(phase for phase in MOD_PHASES if phase.name == MOD + ":derive_towns")
        self.assertEqual(mod_stores.DECLARED[MOD + ":town_people"].keyed_by, "tile")
        self.assertEqual(mod_stores.DECLARED[MOD + ":urban_mortality_premium"].keyed_by, "tile")
        self.assertEqual(phase.scope, "world")
        self.assertIn(MOD + ":towns", town_providers.PROVIDERS)
        self.assertIn(MOD + ":towns", town_providers.PREMIUMS)
