"""Complaint 637: a map overlay's `places` catalogue names the places on a tile, and `map` and `move` carry them."""
import unittest

from sim.geography import map_source, tile_names
from sim.tests.test_missing_screens import _ask, _fresh_sim


def with_places(sim, places):
    """The sim's merged map plus a `places` catalogue, as a mod overlay would add."""
    base = sim.world_map
    catalogues = dict(base.catalogues, places={entry["id"]: entry for entry in places})
    sim.__dict__["_world_map"] = map_source.WorldMap(
        base.map_id, base.tiles, base.layers, catalogues, base.folders, base.properties)
    return sim


class PlaceNameTests(unittest.TestCase):

    def test_places_on_a_tile_come_highest_rank_first(self):
        sim = _fresh_sim()
        tile = sim.labour.base_tile()
        with_places(sim, [{"id": "a", "name": "Small", "tile": tile, "rank": 1},
                          {"id": "b", "name": "Great", "tile": tile, "rank": 9},
                          {"id": "c", "name": "Elsewhere", "tile": "nowhere_01"}])
        self.assertEqual(tile_names.places_on(sim.world_map, tile), ["Great", "Small"])

    def test_a_map_without_places_changes_no_row(self):
        reply = _ask(_fresh_sim(), "map")
        self.assertNotIn("places", reply["you_are_based_at"])

    def test_map_and_move_carry_the_places(self):
        sim = _fresh_sim()
        tile = sim.labour.base_tile()
        people = sim.labour.settlement_tiles()
        other = next(name for name in people
                     if name != tile and people[name] >= 1.0 and sim.labour.relocation_quote(name) is not None)
        with_places(sim, [{"id": "a", "name": "Here", "tile": tile}, {"id": "b", "name": "There", "tile": other}])
        self.assertEqual(_ask(sim, "map")["you_are_based_at"]["places"], ["Here"])
        rows = {row["tile"]: row for row in _ask(sim, "move_base")["tiles"]}
        self.assertEqual(rows[other]["places"], ["There"])


if __name__ == "__main__":
    unittest.main()
