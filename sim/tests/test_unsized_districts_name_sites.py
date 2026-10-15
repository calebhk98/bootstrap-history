"""Complaint 520: every named ore district on a civilisation's tiles names a site, and a deposit worked for ages
is drawn down by its rate and size, not closed by a fixed horizon."""

QUICK_TOPIC = True

import json
import os
import types
import unittest

from sim.engine.mine_deposits import MineDepositsMixin
from sim.engine.state_holdings import HoldingsState
from sim.geography import api as geography

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CIVILISATIONS = ("rome_100ad", "han_china_100ad", "norse_900ad", "england_1300", "mexica_1500")


class _Host(MineDepositsMixin):
    def __init__(self, name):
        self.world_map = geography.open_map()
        with open(os.path.join(ROOT, "data", "civilizations", name + ".json"), encoding="utf-8") as handle:
            self.civ = json.load(handle)
        self.holdings = HoldingsState()
        year = int(self.civ["year"])
        self.state = types.SimpleNamespace(holdings=self.holdings, scenario=types.SimpleNamespace(year=year))
        self.cfg = {"start_year": year}

    def _capacity_naming(self, deposit_id):
        return 0.0


class UnsizedDistrictTests(unittest.TestCase):
    def test_every_worked_district_on_the_tiles_has_a_size_unless_the_output_model_sizes_it(self):
        records = {row["id"]: row for row in geography.deposit_records()}
        for name in CIVILISATIONS:
            host = _Host(name)
            tiles = geography.tiles_held(host.civ, host.world_map)
            for resource_id in sorted(geography.ore_goods(host.world_map)):
                for row in geography.worked_deposits(tiles, resource_id, host.cfg["start_year"], (), host.world_map):
                    if "share_of_empire_output" not in records[row["id"]]:
                        self.assertIsNotNone(row["size_tonnes"], (name, row["id"]))

    def test_a_civilisation_with_only_unsized_districts_gets_sites_from_them(self):
        for name, resource_id in (("han_china_100ad", "iron"), ("mexica_1500", "copper"), ("norse_900ad", "iron")):
            rows = _Host(name).found_deposits(resource_id)
            self.assertTrue(rows, name)
            self.assertTrue(all(row["room_tonnes_per_year"] > 0.0 for row in rows), name)

    def test_a_deposit_first_worked_after_the_start_is_not_named(self):
        self.assertEqual([row["id"] for row in _Host("norse_900ad").found_deposits("lead")], [])
        self.assertNotIn("taxco_silver", [row["id"] for row in _Host("mexica_1500").found_deposits("silver")])

    def test_a_large_deposit_worked_for_millennia_keeps_what_its_rate_leaves(self):
        rows = {row["id"]: row for row in _Host("rome_100ad").found_deposits("copper")}
        self.assertGreater(rows["rio_tinto_copper"]["remaining_tonnes"], 0.0)
        self.assertLess(rows["rio_tinto_copper"]["remaining_tonnes"], rows["rio_tinto_copper"]["size_tonnes"])
        # Cyprus is small beside the rate it was worked at: the data close it, not a horizon
        self.assertAlmostEqual(rows["cyprus_copper"]["remaining_tonnes"], 0.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
