"""Complaints/56, 68, 116: the local labour market cannot outlive the nation, tradesmen cannot outnumber the people who exist, and a
nation too small for a project simply cannot staff it.

`Labour` runs on a small stand-in world (a real civilisation file and a real `Population`), and the invariant checker on a stub
labour; no game is built. Moving the base is test_labour_move_base_rule; the bounds on the people who exist and on
hiring are test_trade_supply_rules."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.invariants import check_labour_market_invariants
from sim.labour.labour import Labour
from sim.tests.harness import NODES
from sim.tests.labour_stand_in import shrink, stand_in_world
from sim.ui.proto.typed import parse_typed
from sim.tests.ui_stand_in import Game


class TownShrinksWithNationTests(unittest.TestCase):

    def test_town_shrinks_with_the_nation_and_never_exceeds_it(self):
        world = stand_in_world()
        labour = Labour(world)
        before = labour.home_town_population_estimate()
        shrink(world.population, 5000)
        after = labour.home_town_population_estimate()
        self.assertLess(after, before * 0.25 * 0.5)
        self.assertLessEqual(after, world.population.total)
        for total in (500, 30, 3):
            shrink(world.population, total)
            self.assertLessEqual(labour.home_town_population_estimate(), total)

    def test_the_town_never_exceeds_the_nation_in_any_civilisation(self):
        for civ_id in ("rome_100ad", "norse_900ad", "mexica_1500", "han_china_100ad"):
            for total in (None, 5000, 200, 30):
                world = stand_in_world(civ_id, total)
                self.assertLessEqual(Labour(world).home_town_population_estimate(), world.population.total + 1e-6, (civ_id, total))


class InvariantCheckerTests(unittest.TestCase):
    """`check_labour_market_invariants` flags a town larger than the nation, tradesmen beyond the people in the trade, and more
    staff than working people."""

    def _game(self, town=100.0, reachable=10.0, exist=50.0, staff=5.0, nation=1000.0, working_age=600.0):
        labour = SimpleNamespace(home_town_population_estimate=lambda: town, available_trades=lambda: ["smith"],
                                 reachable_trade_population=lambda trade: reachable, people_who_exist=lambda trade: exist)
        return Game(population=SimpleNamespace(total=nation, working_age=working_age), labour=labour,
                               view=lambda name: (lambda: {"employees": {"smith": staff}}))

    def test_a_consistent_labour_market_passes(self):
        self.assertTrue(check_labour_market_invariants(self._game()))

    def test_a_town_larger_than_the_nation_is_flagged(self):
        with self.assertRaises(AssertionError):
            check_labour_market_invariants(self._game(town=2000.0))

    def test_more_reachable_tradesmen_than_exist_is_flagged(self):
        with self.assertRaises(AssertionError):
            check_labour_market_invariants(self._game(reachable=60.0, exist=50.0))

    def test_more_reachable_tradesmen_than_the_nation_is_flagged(self):
        with self.assertRaises(AssertionError):
            check_labour_market_invariants(self._game(reachable=1500.0, exist=2000.0))

    def test_more_staff_than_working_people_is_flagged(self):
        with self.assertRaises(AssertionError):
            check_labour_market_invariants(self._game(staff=700.0, working_age=600.0))


class TooSmallToStaffTests(unittest.TestCase):
    """A project that needs more people than exist cannot be staffed; the same project in a full nation is not refused for people."""

    def test_tiny_nation_cannot_staff_a_factory(self):
        shortfall = Labour(stand_in_world(total=200)).project_staffing_shortfall(NODES["fin_factory"])
        self.assertIsNotNone(shortfall)
        # presentation: the refusal says people do not exist in the country
        self.assertIn("exist", shortfall)
        self.assertIn("country", shortfall)

    def test_the_same_project_is_not_refused_for_people_in_a_full_nation(self):
        self.assertIsNone(Labour(stand_in_world()).project_staffing_shortfall(NODES["fin_factory"]))


class MoveCommandParses(unittest.TestCase):
    def test_move_parses_to_a_move_base_command_naming_the_tile(self):
        command, error = parse_typed("move italia_01")
        self.assertIsNone(error)
        self.assertEqual(command["cmd"], "move_base")
        self.assertEqual(command["to"], "italia_01")


if __name__ == "__main__":
    unittest.main()
