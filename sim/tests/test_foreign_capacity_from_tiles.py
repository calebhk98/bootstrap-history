"""Complaints/136: a foreign economy's mined capacity follows the tiles it holds, not its region labels."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.foreign_capacity import held_mineral_share
from sim.geography import api
from sim.geography.regions import region_records
from sim.world import mineral_shares

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _civilisation(civilisation_id):
    with open(os.path.join(_ROOT, "data", "civilizations", civilisation_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class HeldMineralShareTests(unittest.TestCase):

    def test_holding_every_tile_of_a_region_holds_its_whole_regional_share(self):
        geography = api.load_geography()
        regions = region_records(geography)
        han = _civilisation("han_china_100ad")
        for commodity in ("iron", "copper", "silver"):
            self.assertAlmostEqual(held_mineral_share(han, geography, commodity),
                                   regions["china"]["minerals"][commodity], places=9)
        self.assertGreater(held_mineral_share(han, geography, "iron"), 0.0)

    def test_a_deposit_counts_only_on_the_tile_it_sits_on(self):
        geography = api.load_geography()
        on_tile = mineral_shares.deposit_shares_by_tile(geography)["iron"]
        tile_id, share = sorted(on_tile.items())[0]
        region_tiles = api.tiles_of_regions([api.layer_value(tile_id, "region")])
        other = next(tile for tile in region_tiles if tile not in on_tile)
        with_deposit = held_mineral_share({"home_tiles": [tile_id]}, geography, "iron")
        without = held_mineral_share({"home_tiles": [other]}, geography, "iron")
        self.assertGreaterEqual(with_deposit, share)
        self.assertLess(without, share)
        self.assertGreater(held_mineral_share({"home_tiles": region_tiles}, geography, "iron"), with_deposit - 1e-12)


if __name__ == "__main__":
    unittest.main()
