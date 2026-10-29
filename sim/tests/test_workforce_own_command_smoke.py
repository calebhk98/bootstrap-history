"""SMOKE: the workforce module sends two commands to other owners or to itself from inside a built game: the housing it builds
(its own `BuildHousing`) and the wages a household's move costs (`NoteSpend`, the ledger's). Both were refused in any built game
because the module's spec did not declare them in `sends`. Built over a purse that covers it, the housing is bought and the room
grows by the places built."""
import unittest

from sim.tests import harness

PLACES = 2.0
RICH = 1.0e7


class WorkforceSendsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = harness.unopened_sim(capital=RICH)

    def test_the_module_builds_housing_through_its_own_command(self):
        room = self.game.view("household_room")()
        built = self.game.labour._world.build_worker_housing(PLACES)
        self.assertEqual(built, PLACES)
        self.assertEqual(self.game.view("household_room")(), room + PLACES)

    def test_a_move_of_the_base_pays_its_wages_and_notes_the_spend(self):
        base = self.game.view("base_tile")()
        tile = next(tile for tile, people in sorted(self.game.view("settlement_tiles")().items())
                    if tile != base and people >= 1.0 and self.game.view("relocation_quote")[tile] is not None)
        moved, message = self.game.labour.move_base(tile)
        self.assertTrue(moved, message)
        self.assertEqual(self.game.view("base_tile")(), tile)


if __name__ == "__main__":
    unittest.main()
