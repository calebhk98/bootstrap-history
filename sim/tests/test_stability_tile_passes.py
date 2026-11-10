"""The stability phase reads a state's tiles in kernel passes: a quiet year is one pass and one `SetTileReadings`; a rising ends a pass, is
settled, and the next pass starts at the following tile and reads the garrison afresh."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.campaigns.module import Campaigns
from sim.polity.api import SetTileReadings
from sim.tests import module_harness
from sim.tests.agents_fake_world import flat_namespace
from sim.tests.test_campaigns_module import build
from sim.world.army_record import Army

OWNER = "rome"
TILES = ["france_05", "spain_03"]


class RecordingRisings(Campaigns):
    """The module with each rising only noted, and what it does to the garrison done by `after_rising`."""

    def _rising(self, owner, world, record, tile, soldiers, strength, garrison, garrison_strength, on_seat, year, cause):
        self.risen.append((tile, round(soldiers, 6), garrison is None))
        self.after_rising()
        return "put_down"


def read(force, equipment=12.5, after_rising=lambda held: None):
    """The readings and risings of the two tiles for a state whose army is `force` soldiers (a dict is read each pass)."""
    held = {"force": force}
    module, _ = build(RecordingRisings, owners={tile: OWNER for tile in TILES}, extra={
        "tile_facts": lambda tile: {"food_kcal_per_year": 0.0, "working_age_endemic_loss": 0.0, "ruggedness": 0.0},
        "food_eaten": lambda: {},
        "country_world": lambda owner: flat_namespace(
            equipment_kg_per_soldier=lambda: equipment, soldiers_under_arms=lambda: held["force"])})
    module.risen = []
    module.after_rising = lambda: after_rising(held)
    world = flat_namespace(equipment_kg_per_soldier=lambda: equipment, soldiers_under_arms=lambda: held["force"])
    world.army = SimpleNamespace(equipment_kg_per_soldier=lambda: equipment, soldiers_under_arms=lambda: held["force"])
    record = SimpleNamespace(land_taken_by_tile={})
    module._read_tiles(OWNER, world, record, {tile: 5000.0 for tile in TILES}, {tile: 5000.0 for tile in TILES}, 5.0, "individual",
                       0.2, 31.0, None, 100, 1.0)
    return module, [command for command in module_harness.sent(module) if isinstance(command, SetTileReadings)]


class ReadTilesPasses(unittest.TestCase):
    def test_a_quiet_year_is_one_pass_with_every_tile_in_order(self):
        module, readings = read(force=1.0e9)
        self.assertEqual(module.risen, [])
        self.assertEqual([command.tiles for command in readings], [tuple(TILES)])
        self.assertTrue(all(0.0 < value <= 1.0 for value in readings[0].unrest + readings[0].hold))

    def test_a_rising_ends_a_pass_and_the_next_pass_starts_at_the_following_tile(self):
        module, readings = read(force=0.0)
        self.assertEqual([tile for tile, _, _ in module.risen], TILES)
        self.assertEqual([command.tiles for command in readings], [(TILES[0],), (TILES[1],)])


if __name__ == "__main__":
    unittest.main()
