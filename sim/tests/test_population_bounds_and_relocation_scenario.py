"""Scenarios (Complaints/56, 68, 116) on a built game: the reachable tradesmen of a shrinking nation never exceed the people in the trade,
the household's base can move (what it costs and what it changes), and hiring more people than exist is refused. The town and
invariant bounds and the staffing shortfall are in test_population_bounds_and_relocation."""
import random
import unittest

from sim import simulator
from sim.engine.core import Sim
from sim.tests.harness import build_unopened
from sim.ui.proto.dispatch import _agent_dispatch

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim(civ="rome_100ad"):
    return build_unopened(lambda: Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ(civ)))


def _shrink_nation(sim, total):
    """Scale every age cohort so the nation holds `total` people."""
    factor = total / sim.population.total
    sim.population.children *= factor
    sim.population.working_age *= factor
    sim.population.elderly *= factor


class ReachableTradesmenTests(unittest.TestCase):

    def test_reachable_tradesmen_never_exceed_people_in_trade(self):
        sim = _fresh_sim("norse_900ad")
        for total in (None, 5000, 200, 30):
            if total is not None:
                _shrink_nation(sim, total)
            for trade in sorted(_WAGES):
                if not sim.labour.trade_available(trade):
                    continue
                reach = sim.labour.reachable_trade_population(trade)
                limit = max(sim.labour.national_trade_population(trade), sim.state.household.employees.get(trade, 0.0))
                self.assertLessEqual(reach, limit + 1e-6, "%s at %s" % (trade, total))
                self.assertLessEqual(reach, sim.population.total)

    def test_hiring_more_than_exist_is_refused(self):
        sim = _fresh_sim()
        _shrink_nation(sim, 200)
        sim.state.household.capital = 1e9
        ok, message = sim.labour.hire("smith", 5)
        self.assertFalse(ok)
        self.assertIn("exist", message)


class MoveBaseTests(unittest.TestCase):

    def test_move_changes_town_and_trades(self):
        sim = _fresh_sim()
        home = sim.labour.base_tile()
        town_before = sim.labour.home_town_population_estimate()
        supply_before = sim.labour.market_supply("smith")
        people = sim.labour.settlement_tiles()
        others = [tile for tile in people if tile != home and people[tile] >= 1.0]
        sim.state.household.capital = 1e9
        # A poorer tile hosts a smaller town, and so fewer reachable smiths.
        poorest = min(others, key=lambda tile: people[tile])
        ok, message = sim.labour.move_base(poorest)
        self.assertTrue(ok, message)
        self.assertEqual(sim.labour.base_tile(), poorest)
        self.assertEqual(sim.state.household.base_tile, poorest)
        self.assertLess(sim.labour.home_town_population_estimate(), town_before)
        self.assertLess(sim.labour.market_supply("smith"), supply_before)

    def test_move_costs_hours_money_and_local_contracts(self):
        sim = _fresh_sim()
        household = sim.state.household
        household.employees["smith"] = 2.0
        household.commissioned["smith"] = 400.0
        household.familiarity = 0.5
        capital = household.capital
        far = max((tile for tile in sim.labour.settlement_tiles() if tile != sim.labour.base_tile()),
                  key=lambda tile: sim.labour.distance_to_tile_km(tile))
        ok, message = sim.labour.move_base(far)
        self.assertTrue(ok, message)
        self.assertLess(household.capital, capital)
        self.assertLess(household.familiarity, 0.5)
        self.assertFalse(household.commissioned.get("smith"))
        self.assertGreater(household.relocation_hours_this_year, 0.0)

    def test_move_refuses_unknown_and_same_tile(self):
        sim = _fresh_sim()
        self.assertFalse(sim.labour.move_base("atlantis_01")[0])
        self.assertFalse(sim.labour.move_base(sim.labour.base_tile())[0])

    def test_the_move_command_lists_the_tiles(self):
        sim = _fresh_sim()
        listing = _agent_dispatch(sim, _NODES, {"cmd": "move_base"})
        self.assertTrue(listing["ok"])
        self.assertIn("tiles", listing)


if __name__ == "__main__":
    unittest.main()
