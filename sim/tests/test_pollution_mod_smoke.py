"""SMOKE: the Pollution code mod in a whole game, allowed in a temporary mods directory. A second small mod adds a coal-burning producer
to the markets module's answer about last year's runs (through the supported view adjuster), so the shipped mod has something to
turn into harm: its externality provider's deaths reach the demography module's year (`externality_deaths`), its yield factor
reaches the agriculture module's harvest (`externality_yield_factors`), and its command reports the emissions. In a game with the
economy open, after a year, the markets view the mod reads answers the producers that really ran. The mod reads the game only
through its declared access."""
import unittest

from sim.assembly.api import UndeclaredRead
from sim.tests.shipped_mod_games import ModGames
from sim.ui.proto.dispatch import _agent_dispatch_inner

MOD = "bh_pollution_t9c3"
FEEDER = "test_feeder_s7q2"
RUNS = 1.0e11
FEEDER_SOURCE = '''
def register(api):
    def burn(needs, value, *arguments):
        tile = needs.base_tile()
        return list(value or []) + [{"tile": tile, "runs": %r, "inputs": {"coal_kg": 1.0}, "outputs": {}}]
    api.adjust_view("agent_producer_runs", burn, reads=("base_tile",))
''' % RUNS
NO_DEATHS = {"children": 0.0, "working_age": 0.0, "elderly": 0.0}


class PollutionModTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = ModGames([MOD], {FEEDER: FEEDER_SOURCE})
        cls.game = cls.games.unopened()
        cls.plain_games = ModGames([MOD])
        cls.plain = cls.plain_games.unopened()
        cls.base = cls.game.view("base_tile")()
        cls.year = cls.game.view("year")()

    @classmethod
    def tearDownClass(cls):
        cls.plain_games.close()
        cls.games.close()

    def test_the_harm_reaches_the_demography_modules_deaths(self):
        fed = self.game.view("externality_deaths")(dict(NO_DEATHS), self.year)
        plain = self.plain.view("externality_deaths")(dict(NO_DEATHS), self.year)
        self.assertEqual(plain, NO_DEATHS)
        self.assertGreater(sum(fed.values()), 0.0)

    def test_the_harm_reaches_the_agriculture_modules_yield_factor_of_the_tile(self):
        fed = self.game.view("externality_yield_factors")(self.year)
        self.assertLess(fed[self.base], 1.0)
        self.assertEqual(self.plain.view("externality_yield_factors")(self.year), {})

    def test_the_command_reports_the_emissions_of_the_tile_it_was_fed(self):
        reply = _agent_dispatch_inner(self.game, {}, {"cmd": MOD + ":pollution"})
        self.assertTrue(reply["ok"], reply)
        self.assertEqual([row["tile"] for row in reply["tiles"]], [self.base])
        self.assertGreater(reply["totals_emitted_kg"]["sulphur_dioxide"], 0.0)
        self.assertTrue(reply["applied_to_the_game"])
        self.assertEqual(self.game.state.interface["mod_state"][MOD]["history"][str(self.year)]["tiles_emitting"], 1)

    def test_a_game_without_the_feeder_emits_nothing(self):
        reply = _agent_dispatch_inner(self.plain, {}, {"cmd": MOD + ":pollution"})
        self.assertEqual(reply["tiles"], [])

    def test_the_mod_reads_only_what_it_declared(self):
        access = self.game.assembly.mod_access[MOD]
        self.assertIn("agent_producer_runs", access.reads)
        with self.assertRaises(UndeclaredRead):
            access.view("cast")


class ProducerRunsTests(unittest.TestCase):
    def test_after_a_year_the_view_the_mod_reads_answers_the_producers_that_ran(self):
        games = ModGames([MOD])
        self.addCleanup(games.close)
        game = games.opened()
        games.step(game)
        rows = game.view("agent_producer_runs")()
        self.assertTrue(rows)
        self.assertTrue(all(row["runs"] > 0.0 and row["tile"] and isinstance(row["inputs"], dict) for row in rows))


if __name__ == "__main__":
    unittest.main()
