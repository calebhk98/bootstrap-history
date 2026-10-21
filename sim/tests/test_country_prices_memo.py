"""`country_figures.prices` reuses its answer only while the prices and weights it read compare equal to the live
ones: over random markets and random changes between calls it equals the scan made afresh every time."""

QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.economy import country_figures

GOODS = ["grain", "iron", "salt", "wool"]
AREAS = ["north", "south", "east"]
TILES = {"a": {"t1", "t2"}, "b": {"t3"}}


def economy_of(generator):
    areas = {good: [SimpleNamespace(area_id=area, tiles=generator.sample(["t1", "t2", "t3"], generator.randint(1, 3)))
                    for area in AREAS] for good in GOODS[:3]}
    area_map = SimpleNamespace(areas=lambda good: areas[good], goods=lambda: list(areas))
    setup = SimpleNamespace(tiles=["t1", "t2", "t3"], tiles_of=lambda country: TILES[country])
    memory = SimpleNamespace(prices={}, volume_weights={})
    record = SimpleNamespace(memory=memory, volumes={})
    return SimpleNamespace(setup=setup, area_map=area_map, record=record)


def change(generator, economy):
    memory = economy.record.memory
    for good in GOODS:
        for area in AREAS:
            key = good + "|" + area
            if generator.random() < 0.3:
                memory.prices[key] = generator.uniform(0.1, 9.0)
            if generator.random() < 0.3:
                target = memory.volume_weights if generator.random() < 0.7 else economy.record.volumes
                target[key] = generator.uniform(0.0, 50.0)
    if generator.random() < 0.2:
        memory.volume_weights.clear()


class CountryPricesMemoTests(unittest.TestCase):
    def test_equals_a_fresh_scan_through_changes(self):
        generator = random.Random(11)
        for _case in range(60):
            economy = economy_of(generator)
            for _call in range(12):
                if generator.random() < 0.5:
                    change(generator, economy)
                country = generator.choice([None, "a", "b"])
                fresh = country_figures.scan_prices(economy, country)
                got = country_figures.prices(economy, country)
                self.assertEqual(list(fresh.items()), list(got.items()))
                got["grain"] = -1.0
                self.assertEqual(list(fresh.items()), list(country_figures.prices(economy, country).items()))

    def test_traded_volumes_equal_a_fresh_scan_through_changes(self):
        generator = random.Random(12)
        for _case in range(60):
            economy = economy_of(generator)
            for _call in range(12):
                if generator.random() < 0.5:
                    change(generator, economy)
                country = generator.choice([None, "a", "b"])
                fresh = country_figures.scan_volumes(economy, country)
                got = country_figures.traded_volumes(economy, country)
                self.assertEqual(list(fresh.items()), list(got.items()))
                got["grain"] = -1.0
                self.assertEqual(list(fresh.items()), list(country_figures.traded_volumes(economy, country).items()))


if __name__ == "__main__":
    unittest.main()
