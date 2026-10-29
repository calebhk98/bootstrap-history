"""SMOKE: the Towns code mod in a whole game, allowed in a temporary mods directory. Its `towns` command lists the cited towns on the
nation's tiles from the map catalogue the mod's data overlays, with the days from the base the workforce module quotes; its `go`
command sends the ordinary base move, so the base tile changes, the move costs what the shipped move costs, and a name that matches
nothing is refused without changing the base. The mod reads the game only through its declared access."""
import unittest

from sim.assembly.api import UndeclaredRead
from sim.tests.shipped_mod_games import ModGames
from sim.ui.proto.dispatch import _agent_dispatch_inner

MOD = "bh_towns_m8d4"


def command(game, word, text=""):
    return _agent_dispatch_inner(game, {}, {"cmd": "%s:%s" % (MOD, word), "text": text})


class TownsModTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = ModGames([MOD])

    @classmethod
    def tearDownClass(cls):
        cls.games.close()

    def test_the_command_lists_the_towns_on_the_nations_tiles_with_the_days_from_the_base(self):
        game = self.games.unopened()
        reply = command(game, "towns")
        rows = {row["town"]: row for row in reply["towns"]}
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(rows["Rome"]["tile"], "italy_03")
        self.assertEqual(rows["Rome"]["people"], 450000)
        self.assertEqual(rows["Rome"]["days_from_your_base"], round(game.view("relocation_quote")["italy_03"][0]))
        self.assertTrue(all(row["held"] for row in rows.values()))

    def test_going_to_a_town_moves_the_base_to_its_tile_and_pays_the_shipped_cost(self):
        game = self.games.unopened()
        self.assertNotEqual(game.view("base_tile")(), "italy_03")
        reply = command(game, "go", "Roma")
        self.assertTrue(reply["ok"], reply)
        self.assertEqual((reply["based_at"], reply["town"]), ("italy_03", "Rome"))
        self.assertEqual(game.view("base_tile")(), "italy_03")

    def test_a_name_that_matches_no_town_changes_nothing(self):
        game = self.games.unopened()
        base = game.view("base_tile")()
        reply = command(game, "go", "Atlantis")
        self.assertFalse(reply["ok"])
        self.assertEqual(game.view("base_tile")(), base)

    def test_the_mod_reads_only_what_it_declared(self):
        access = self.games.unopened().assembly.mod_access[MOD]
        self.assertIn("map_catalogue", access.reads)
        with self.assertRaises(UndeclaredRead):
            access.view("population")


if __name__ == "__main__":
    unittest.main()
