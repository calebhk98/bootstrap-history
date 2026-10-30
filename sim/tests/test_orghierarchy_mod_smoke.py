"""SMOKE: the Organisational Hierarchy code mod in a whole game, allowed in a temporary mods directory. Its directed-hours overhead is
charged against the workforce module's pool once the founder has staff (and not before), by the mod's own rule over the staff,
the technologies held and the game's directed hours per manager; its `hierarchy` command reads the same figures. The mod reads
the game only through its declared access."""
import unittest

from sim.assembly.api import UndeclaredRead
from sim.tests.mod_files import load_mod_file
from sim.tests.shipped_mod_games import ModGames
from sim.ui.proto.dispatch import _agent_dispatch_inner
from sim.workforce.api import HireStaff

MOD = "bh_orghierarchy_r4k8"
HIERARCHY = load_mod_file(MOD, "hierarchy_commands.py")
STAFF = 5


class OrgHierarchyModTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = ModGames([MOD])
        cls.game = cls.games.unopened()
        cls.charged_before = cls.game.labour._world.director_overhead_hours()
        cls.hired = cls.game.send(HireStaff("scribe", STAFF))

    @classmethod
    def tearDownClass(cls):
        cls.games.close()

    def staff(self):
        """The people hired (the market may give fewer than asked)."""
        return float(sum(self.game.view("staff")()["employees"].values()))

    def test_nothing_is_charged_while_the_founder_has_no_staff(self):
        self.assertEqual(self.charged_before, 0.0)

    def test_the_overhead_charged_is_the_mods_rule_over_the_staff_hired(self):
        self.assertEqual(self.hired[0], True, self.hired)
        parameters = HIERARCHY.load_parameters()
        manager_hours = float(self.game.view("game_config")()["director_hours_per_year"])
        expected = HIERARCHY.apex_overhead_hours(self.staff(), manager_hours, parameters, set(self.game.view("techniques_held")()), 0)
        self.assertGreater(expected, 0.0)
        self.assertEqual(self.game.labour._world.director_overhead_hours(), expected)

    def test_the_hierarchy_command_reads_the_same_staff(self):
        reply = _agent_dispatch_inner(self.game, {}, {"cmd": MOD + ":hierarchy"})
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(reply["workers"], self.staff())

    def test_the_mod_reads_only_what_it_declared(self):
        access = self.game.assembly.mod_access[MOD]
        self.assertIn("hours_available", access.reads)
        with self.assertRaises(UndeclaredRead):
            access.view("population")


if __name__ == "__main__":
    unittest.main()
