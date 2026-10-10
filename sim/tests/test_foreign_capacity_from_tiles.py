"""Complaints/136: a foreign economy's mined capacity follows the deposits on the tiles it holds, not its region labels."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.geography import api
from sim.geography.api import mineral_shares

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _civilisation(civilisation_id):
    with open(os.path.join(_ROOT, "data", "civilizations", civilisation_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class HeldMineralShareTests(unittest.TestCase):

    def test_a_civilisation_draws_on_the_deposits_standing_on_its_tiles(self):
        geography = api.load_geography()
        han = api.tiles_held(_civilisation("han_china_100ad"))
        by_tile = mineral_shares.deposit_shares_by_tile(geography)
        for commodity in ("iron", "copper", "silver"):
            expected = sum(share for tile_id, share in by_tile[commodity].items() if tile_id in han)
            self.assertAlmostEqual(mineral_shares.held_share(han, commodity, geography), expected, places=9)
        self.assertGreater(mineral_shares.held_share(han, "iron", geography), 0.0)

    def test_a_deposit_counts_only_on_the_tile_it_sits_on(self):
        geography = api.load_geography()
        on_tile = mineral_shares.deposit_shares_by_tile(geography)["iron"]
        tile_id, share = sorted(on_tile.items())[0]
        other = next(tile for tile in geography["land_tiles"]["tiles"] if tile not in on_tile)
        self.assertGreaterEqual(mineral_shares.held_share([tile_id], "iron", geography), share)
        self.assertEqual(mineral_shares.held_share([other], "iron", geography), 0.0)


if __name__ == "__main__":
    unittest.main()
