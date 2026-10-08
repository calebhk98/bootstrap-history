"""Complaints/136: a foreign economy's mined capacity follows the tiles it holds, not its region labels."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.foreign_capacity import held_mineral_share
from sim.geography import api
from sim.geography.regions import region_records

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _civilisation(civilisation_id):
    with open(os.path.join(_ROOT, "data", "civilizations", civilisation_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class HeldMineralShareTests(unittest.TestCase):

    def test_tiles_only_civilisation_matches_its_labelled_twin(self):
        regions = region_records(api.load_geography())
        labelled = _civilisation("han_china_100ad")
        tiles_only = {"home_tiles": api.tiles_held(labelled)}
        for commodity in ("iron", "copper", "silver"):
            self.assertAlmostEqual(held_mineral_share(tiles_only, regions, commodity),
                                   held_mineral_share(labelled, regions, commodity), places=9)
        self.assertGreater(held_mineral_share(tiles_only, regions, "iron"), 0.0)

    def test_fewer_tiles_hold_less_of_a_regions_share(self):
        regions = region_records(api.load_geography())
        region = next(region_id for region_id, record in regions.items()
                      if any(share > 0.0 for share in (record.get("minerals") or {}).values()) and len(api.tiles_of_regions([region_id])) > 1)
        tiles = api.tiles_of_regions([region])
        commodity = next(name for name, share in sorted(regions[region]["minerals"].items()) if share > 0.0)
        part = held_mineral_share({"home_tiles": tiles[:1]}, regions, commodity)
        whole = held_mineral_share({"home_tiles": tiles}, regions, commodity)
        self.assertGreater(whole, part)
        self.assertGreater(part, 0.0)


if __name__ == "__main__":
    unittest.main()
