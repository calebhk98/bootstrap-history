"""Complaints/58, 70, 120: the local labour market cannot outlive the nation,
tradesmen cannot outnumber the people who exist, the base can move, and a
nation too small for a project simply cannot staff it.

unittest.TestCase style, like the other focused complaint suites.
"""
import os
import random
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)
from sim import simulator
from sim.engine.core import Sim
from sim.engine.invariants import check_labour_market_invariants
from sim.engine.proto.dispatch import _agent_dispatch
from sim.engine.proto.typed import parse_typed

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim(civ="rome_100ad"):
    return Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ(civ))


def _shrink_nation(sim, total):
    """Scale every age cohort so the nation holds `total` people."""
    factor = total / sim.population.total
    sim.population.children *= factor
    sim.population.working_age *= factor
    sim.population.elderly *= factor


class TownShrinksWithNationTests(unittest.TestCase):

    def test_town_falls_below_the_old_floor_after_collapse(self):
        sim = _fresh_sim()
        before = sim.home_town_population_estimate()
        _shrink_nation(sim, 5000)
        after = sim.home_town_population_estimate()
        self.assertLess(after, before * 0.25 * 0.5)
        self.assertLessEqual(after, sim.population.total)

    def test_town_never_exceeds_nation_at_any_size(self):
        for total in (5000000, 50000, 500, 30, 3):
            sim = _fresh_sim()
            _shrink_nation(sim, total)
            self.assertLessEqual(sim.home_town_population_estimate(), total)

    def test_reachable_tradesmen_never_exceed_people_in_trade(self):
        for civ in ("rome_100ad", "norse_900ad"):
            for total in (None, 5000, 200, 30):
                sim = _fresh_sim(civ)
                if total is not None:
                    _shrink_nation(sim, total)
                for trade in sorted(_WAGES):
                    if not sim.trade_available(trade):
                        continue
                    reach = sim.reachable_trade_population(trade)
                    limit = max(sim.national_trade_population(trade),
                                sim.state.household.employees.get(trade, 0.0))
                    self.assertLessEqual(reach, limit + 1e-6,
                                         "%s %s at %s" % (civ, trade, total))
                    self.assertLessEqual(reach, sim.population.total)

    def test_invariant_checker_flags_a_town_larger_than_the_nation(self):
        sim = _fresh_sim()
        self.assertTrue(check_labour_market_invariants(sim))
        sim.home_town_population_estimate = lambda: sim.population.total * 2
        with self.assertRaises(AssertionError):
            check_labour_market_invariants(sim)

    def test_invariant_checker_flags_more_staff_than_working_people(self):
        sim = _fresh_sim()
        sim.state.household.employees["smith"] = sim.population.working_age + 10.0
        with self.assertRaises(AssertionError):
            check_labour_market_invariants(sim)


class MoveBaseTests(unittest.TestCase):

    def test_move_changes_town_and_trades(self):
        sim = _fresh_sim()
        home = sim.base_tile()
        town_before = sim.home_town_population_estimate()
        supply_before = sim.market_supply("smith")
        people = sim.settlement_tiles()
        others = [tile for tile in people if tile != home and people[tile] >= 1.0]
        sim.state.household.capital = 1e9
        # A poorer tile hosts a smaller town, and so fewer reachable smiths.
        poorest = min(others, key=lambda tile: people[tile])
        ok, message = sim.move_base(poorest)
        self.assertTrue(ok, message)
        self.assertEqual(sim.base_tile(), poorest)
        self.assertLess(sim.home_town_population_estimate(), town_before)
        self.assertLess(sim.market_supply("smith"), supply_before)

    def test_move_costs_hours_money_and_local_contracts(self):
        sim = _fresh_sim()
        household = sim.state.household
        household.employees["smith"] = 2.0
        household.commissioned["smith"] = 400.0
        household.familiarity = 0.5
        capital = household.capital
        far = max((tile for tile in sim.settlement_tiles() if tile != sim.base_tile()),
                  key=lambda tile: sim.distance_to_tile_km(tile))
        ok, message = sim.move_base(far)
        self.assertTrue(ok, message)
        self.assertLess(household.capital, capital)
        self.assertLess(household.familiarity, 0.5)
        self.assertFalse(household.commissioned.get("smith"))
        self.assertGreater(household.relocation_hours_this_year, 0.0)

    def test_move_refuses_unknown_and_same_tile(self):
        sim = _fresh_sim()
        self.assertFalse(sim.move_base("atlantis_01")[0])
        self.assertFalse(sim.move_base(sim.base_tile())[0])

    def test_move_command_and_typed_parser(self):
        command, error = parse_typed("move italia_01")
        self.assertIsNone(error)
        self.assertEqual(command["cmd"], "move_base")
        self.assertEqual(command["to"], "italia_01")
        sim = _fresh_sim()
        listing = _agent_dispatch(sim, _NODES, {"cmd": "move_base"})
        self.assertTrue(listing["ok"])
        self.assertIn("tiles", listing)

    def test_base_is_stored_on_the_household(self):
        sim = _fresh_sim()
        target = next(tile for tile in sim.settlement_tiles() if tile != sim.base_tile())
        sim.state.household.capital = 1e9
        sim.move_base(target)
        self.assertEqual(sim.state.household.base_tile, target)


class TooSmallToStaffTests(unittest.TestCase):

    def test_tiny_nation_cannot_staff_a_factory(self):
        sim = _fresh_sim()
        _shrink_nation(sim, 200)
        ok, reason = sim.start_reason("fin_factory")
        self.assertFalse(ok)
        self.assertIn("exist", reason)
        self.assertIn("country", reason)

    def test_same_project_is_not_refused_for_people_in_a_full_nation(self):
        sim = _fresh_sim()
        ok, reason = sim.start_reason("fin_factory")
        self.assertNotIn("people who could do the work", reason or "")

    def test_hiring_more_than_exist_is_refused(self):
        sim = _fresh_sim()
        _shrink_nation(sim, 200)
        sim.state.household.capital = 1e9
        ok, message = sim.hire("smith", 5)
        self.assertFalse(ok)
        self.assertIn("exist", message)


if __name__ == "__main__":
    unittest.main()
