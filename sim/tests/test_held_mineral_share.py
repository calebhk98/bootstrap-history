"""Complaints/136: the share of a resource a holder can draw on is the shares of the deposits on its tiles;
only resources some deposit lists on the reference-share field are tracked."""

QUICK_TOPIC = True

import unittest

from sim.geography.api import mineral_shares


def _tile(latitude, longitude):
    return {"lat": latitude, "lon": longitude}


GEOGRAPHY = {
    "land_tiles": {
        "tiles": {"n1": _tile(50.0, 0.0), "n2": _tile(50.0, 10.0), "n3": _tile(50.0, 20.0),
                  "n4": _tile(50.0, 30.0), "s1": _tile(-40.0, 0.0)}},
}


def _row(resource, latitude, longitude, key, share, ident=None):
    ident = ident or "%s_%s_%s" % (resource, latitude, longitude)
    return {"id": ident, "name": ident, "resource": resource, "lat": latitude, "lon": longitude, key: share}


ROWS = [
    _row("iron", 50.0, 0.5, "share_of_empire_output", 0.3),
    _row("iron", 50.0, 19.0, "share_of_reference_output", 0.2),
    _row("iron", -40.0, 0.0, "share_of_reference_output", 0.4),
    _row("coal", 50.0, 31.0, "share_of_reference_output", 0.5),
    _row("gold", 50.0, 0.0, "share_of_empire_output", 1.0),
]


def held(tiles, resource):
    return mineral_shares.held_share(tiles, resource, GEOGRAPHY, ROWS)


class HeldShareTests(unittest.TestCase):

    def test_a_deposit_counts_on_the_tile_that_holds_it(self):
        self.assertAlmostEqual(held(["n1"], "iron"), 0.3)
        self.assertAlmostEqual(held(["n3"], "iron"), 0.2)

    def test_a_deposit_on_a_tile_not_held_does_not_count(self):
        self.assertEqual(held(["n2"], "iron"), 0.0)

    def test_holding_every_tile_holds_every_share(self):
        self.assertAlmostEqual(held(list(GEOGRAPHY["land_tiles"]["tiles"]), "iron"), 0.9)

    def test_a_resource_with_no_reference_share_row_stays_untracked(self):
        self.assertEqual(mineral_shares.tracked_resources(ROWS), {"iron", "coal"})
        self.assertEqual(held(["n1"], "gold"), 0.0)

    def test_holding_nothing_holds_no_share(self):
        self.assertEqual(held([], "iron"), 0.0)
        self.assertEqual(held(["nowhere"], "coal"), 0.0)

    def test_two_deposits_on_one_tile_add(self):
        rows = ROWS + [_row("iron", 50.0, 1.0, "share_of_reference_output", 0.05, "iron_second")]
        self.assertAlmostEqual(mineral_shares.held_share(["n1"], "iron", GEOGRAPHY, rows), 0.35)

    def test_every_reference_share_is_declared_a_temporary_heuristic(self):
        from sim.constants import REGISTRY
        mineral_shares.share_rows(ROWS)
        declared = REGISTRY["DEPOSIT_REFERENCE_SHARE_IRON_50.0_19.0"]
        self.assertEqual(declared["kind"], "temporary_heuristic")
        self.assertEqual(declared["value"], 0.2)


if __name__ == "__main__":
    unittest.main()
