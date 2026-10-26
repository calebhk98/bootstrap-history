"""A tile's yield factor from an externality provider takes its share of the pooled national harvest (Complaint 635).

The module's `harvest_weather` is called over a civilisation's real tiles, reading the yield factors a provider registered
through the mod door answers."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim import simulator
from sim.engine import externalities, mod_code
from sim.tests import agriculture_stand_in, harness, land_host  # noqa: F401  (harness isolates the home directory)
from sim.world.weather_pooling import harm_multiplier, tile_shares

ROME = simulator.load_civ("rome_100ad")


def rome_rows():
    return land_host.build(ROME).held_tile_geometry()


def farm_over_rome():
    return agriculture_stand_in.build(
        rome_rows(), salt=7, views={"externality_yield_factors": lambda year: externalities.yield_factors(None, year)})


class HarmRule(unittest.TestCase):
    SHARES = {"a": 0.5, "b": 0.3, "c": 0.2}

    def test_no_harm_leaves_the_whole_harvest(self):
        self.assertEqual(harm_multiplier(self.SHARES, {}), 1.0)

    def test_a_tile_loses_its_share_of_the_land_times_its_loss(self):
        self.assertAlmostEqual(harm_multiplier(self.SHARES, {"a": 0.5}), 0.75)
        self.assertAlmostEqual(harm_multiplier(self.SHARES, {"a": 0.0, "b": 0.0, "c": 0.0}), 0.0)

    def test_a_tile_with_no_land_share_and_a_factor_over_one_change_nothing(self):
        self.assertEqual(harm_multiplier(self.SHARES, {"elsewhere": 0.0, "b": 3.0}), 1.0)

    def test_shares_sum_to_one(self):
        from sim.agriculture import rules
        self.assertAlmostEqual(sum(tile_shares(rules.raw_cells(rome_rows())).values()), 1.0)


class PooledHarvest(unittest.TestCase):
    def setUp(self):
        self.farm = farm_over_rome()
        self.addCleanup(externalities.clear)

    def harvest(self, **options):
        return self.farm.harvest_weather(150, **options)

    def test_with_no_provider_the_harvest_is_the_weather(self):
        self.assertEqual(self.harvest(), self.harvest(harmed=False))

    def test_a_half_ruined_tile_cuts_the_harvest_by_its_share_of_the_land(self):
        self.farm.weather_cells()
        tile, share = max(self.farm._tile_share.items(), key=lambda item: item[1])
        weather = self.harvest(harmed=False)
        mod_code.ModCodeApi("test_smoke_k3f9").externality(lambda sim, year: {"yield_factor_by_tile": {tile: 0.5}})
        self.assertAlmostEqual(self.harvest(), weather * (1.0 - 0.5 * share))
        self.assertEqual(self.harvest(harmed=False), weather)

    def test_a_tile_the_civilisation_does_not_farm_changes_nothing(self):
        weather = self.harvest(harmed=False)
        mod_code.ModCodeApi("test_smoke_k3f9").externality(lambda sim, year: {"yield_factor_by_tile": {"nowhere_00": 0.0}})
        self.assertEqual(self.harvest(), weather)


if __name__ == "__main__":
    unittest.main()
