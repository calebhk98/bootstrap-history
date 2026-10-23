"""A tile's yield factor from an externality provider takes its share of the pooled national harvest (Complaint 635).

The real method is called on a stand-in holding a civilisation's cells and their tile shares, with a provider registered
through the mod door."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim import simulator
from sim.engine import externalities, mod_code
from sim.engine.core import Sim
from sim.tests import harness  # noqa: F401  (isolates the home directory)
from sim.world import agriculture
from sim.world.weather_pooling import correlation_cholesky, harm_multiplier, tile_shares

ROME = simulator.load_civ("rome_100ad")


def stand_in():
    stub = SimpleNamespace(civ=ROME, world_map=None, rng=random.Random(1), _agriculture=agriculture,
                           state=SimpleNamespace(scenario=SimpleNamespace(weather_salt=7)))
    stub._cap_pooled_farm_weather_cells = lambda cells: Sim._cap_pooled_farm_weather_cells(stub, cells)
    stub._raw_farm_weather_cells = lambda: Sim._raw_farm_weather_cells(stub)
    stub._farm_weather_cells = Sim._compute_farm_weather_cells(stub)
    stub._farm_weather_correlation_cholesky = correlation_cholesky(stub._farm_weather_cells, 800.0)
    stub._farm_tile_arable_share = Sim._compute_farm_tile_arable_share(stub)
    stub._farm_year_weather_seed = lambda year, region=None: Sim._farm_year_weather_seed(stub, year, region=region)
    return stub


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
        cells = stand_in()._raw_farm_weather_cells()
        self.assertAlmostEqual(sum(tile_shares(cells).values()), 1.0)


class PooledHarvest(unittest.TestCase):
    def setUp(self):
        self.sim = stand_in()
        self.addCleanup(externalities.clear)

    def harvest(self, **options):
        return Sim._pooled_farm_weather_multiplier(self.sim, 150, **options)

    def test_with_no_provider_the_harvest_is_the_weather(self):
        self.assertEqual(self.harvest(), self.harvest(harmed=False))

    def test_a_half_ruined_tile_cuts_the_harvest_by_its_share_of_the_land(self):
        tile, share = max(self.sim._farm_tile_arable_share.items(), key=lambda item: item[1])
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
