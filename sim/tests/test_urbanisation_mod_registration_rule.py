"""The urbanisation mod's registration declares two tile stores, a world-scope yearly phase and a town provider with a
mortality premium. The hooks are recorded by the mod code api as operations on the assembly; no game."""

QUICK_TOPIC = True

from sim.engine import mod_code
from sim.tests.mod_files import load_mod_file
from sim.tests.test_mod_stores import StoreTestBase

MOD = "bh_urbanisation_w2n6"


class UrbanisationRegistrationTests(StoreTestBase):
    def test_registration_declares_two_tile_stores_a_phase_and_a_provider(self):
        api = mod_code.ModCodeApi(MOD)
        load_mod_file(MOD, "hooks.py").register(api)
        operations = api.operations
        phase = next(phase for phase in operations.phases if phase.name == MOD + ":derive_towns")
        declared = {spec.name: spec for answer in operations.provided["store_declarations"] for spec in answer()}
        self.assertEqual(declared[MOD + ":town_people"].keyed_by, "tile")
        self.assertEqual(declared[MOD + ":urban_mortality_premium"].keyed_by, "tile")
        self.assertEqual(phase.scope, "world")
        self.assertEqual(len(operations.provided["town_population"]), 1)
        self.assertEqual(len(operations.provided["town_mortality_premium"]), 1)
