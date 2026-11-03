"""`ScenarioReads.held_civ` is the civilisation's record with the tiles the country holds now as its home tiles."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.markets.port_world_reads import ScenarioReads


class HeldCiv(unittest.TestCase):
	def test_the_home_tiles_are_the_ones_held_now(self):
		needs = SimpleNamespace(civilisation=lambda: {"id": "land", "home_tiles": ["opening_tile"]},
		                        home_tiles_held=lambda: ("held_a", "held_b"))
		held = ScenarioReads(needs).held_civ
		self.assertEqual(held["home_tiles"], ["held_a", "held_b"])
		self.assertEqual(held["id"], "land")

	def test_the_openings_record_is_not_changed(self):
		record = {"id": "land", "home_tiles": ["opening_tile"]}
		ScenarioReads(SimpleNamespace(civilisation=lambda: record, home_tiles_held=lambda: ("x",))).held_civ
		self.assertEqual(record["home_tiles"], ["opening_tile"])


if __name__ == "__main__":
	unittest.main()
