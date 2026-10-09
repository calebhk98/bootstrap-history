"""Complaints/136: the share of a metal a holder can draw on counts the deposits on its tiles, plus the
region-table remainder (shares with no deposit behind them) by the fraction of that region's tiles held."""

QUICK_TOPIC = True

import unittest

from sim.world import mineral_shares


def _tile(latitude, longitude):
    return {"lat": latitude, "lon": longitude}


GEOGRAPHY = {
    "regions": {"north": {"name": "North", "minerals": {"iron": 0.1, "coal": 0.5}},
                "south": {"name": "South", "minerals": {"iron": 0.4}}},
    "land_tiles": {
        "tiles": {"n1": _tile(50.0, 0.0), "n2": _tile(50.0, 10.0), "n3": _tile(50.0, 20.0),
                  "n4": _tile(50.0, 30.0), "s1": _tile(-40.0, 0.0)},
        "region_to_tiles": {"north": ["n1", "n2", "n3", "n4"], "south": ["s1"]}},
}
DEPOSITS = {"deposits": {"iron": [
    {"lat": 50.0, "lon": 0.5, "share_of_empire_output": 0.3},
    {"lat": 50.0, "lon": 19.0, "share_of_empire_output": 0.2}],
    "gold": [{"lat": 50.0, "lon": 0.0, "share_of_empire_output": 1.0}]}}


def held(tiles, metal):
    return mineral_shares.held_share(tiles, metal, GEOGRAPHY, DEPOSITS)


class HeldShareTests(unittest.TestCase):

    def test_a_deposit_counts_on_the_tile_that_holds_it(self):
        self.assertAlmostEqual(held(["n1"], "iron"), 0.3 + 0.1 / 4)

    def test_a_deposit_on_a_tile_not_held_does_not_count(self):
        self.assertAlmostEqual(held(["n2"], "iron"), 0.1 / 4)

    def test_the_table_remainder_follows_the_fraction_of_the_regions_tiles_held(self):
        self.assertAlmostEqual(held(["s1"], "iron"), 0.4)
        self.assertAlmostEqual(held(["n1", "n2", "n3", "n4"], "iron"), 0.3 + 0.2 + 0.1)

    def test_a_metal_the_tables_never_list_stays_untracked(self):
        self.assertEqual(held(["n1"], "gold"), 0.0)

    def test_holding_nothing_holds_no_share(self):
        self.assertEqual(held([], "iron"), 0.0)
        self.assertEqual(held(["n1", "nowhere"], "coal"), 0.5 / 4)

    def test_the_regional_view_is_the_sum_of_what_each_tile_holds(self):
        regional = mineral_shares.regional_mineral_shares(GEOGRAPHY, DEPOSITS)
        self.assertAlmostEqual(regional["north"]["iron"], held(["n1", "n2", "n3", "n4"], "iron"))


if __name__ == "__main__":
    unittest.main()
