"""One money per labour hour: the figure an hour of work is counted at, and what the economy's opening reprices."""

QUICK_TOPIC = True

import contextlib
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.markets.api import MarkMoneyPricedAtEconomy
from sim.engine import data, money_units, opening_money
from sim.engine.wage_schedule import build_schedule
from sim.labour.labour import Labour
from sim.tests.labour_stand_in import stand_in_world


def _labour(paid, price_level=1.0):
    world = stand_in_world()
    world.society.wage_tightness_factors = {}
    world.build_wage_schedule = lambda civ, tightness_factors=None: build_schedule(
        data.TRADE_REGISTRY, civ, tightness_factors=tightness_factors)
    world.economy_unskilled_wage = lambda: paid
    world.home_price_level = lambda: price_level
    return Labour(world)


class FigureInUse(unittest.TestCase):

    def test_the_economy_wage_is_the_figure_once_it_is_paid(self):
        self.assertEqual(_labour(paid=7.25).money_per_labour_hour(), 7.25)

    def test_before_the_economy_pays_the_opening_figure_follows_the_price_level(self):
        opening = _labour(paid=None).money_per_labour_hour()
        self.assertGreater(opening, 0.0)
        self.assertAlmostEqual(_labour(paid=None, price_level=2.0).money_per_labour_hour(), 2.0 * opening)

    def test_the_economy_wage_replaces_the_opening_figure_whatever_the_price_level(self):
        self.assertEqual(_labour(paid=7.25, price_level=3.0).money_per_labour_hour(), 7.25)


class RepriceAtOpening(unittest.TestCase):

    @staticmethod
    def _game(before, after):
        purse = SimpleNamespace(capital=100.0, cash_mark=40.0)
        unmarked = SimpleNamespace(capital=10.0, cash_mark=None)
        households = {"first": purse, "second": unmarked}
        game = SimpleNamespace(state=SimpleNamespace(seats=households), sent=[],
                               labour=SimpleNamespace(money_per_labour_hour=lambda: after))

        @contextlib.contextmanager
        def act_as(seat_id):
            game.state.household = households[seat_id]
            yield
        game.act_as = act_as
        game.send = game.sent.append
        return game, purse, unmarked

    def test_every_purse_moves_by_the_ratio_of_the_figures_so_it_buys_the_same_hours(self):
        game, purse, unmarked = self._game(before=2.0, after=3.0)
        with mock.patch.object(opening_money, "reprice_tree"):
            opening_money.reprice_opening_money(game, 2.0)
        self.assertEqual(game.sent, [MarkMoneyPricedAtEconomy()])
        self.assertAlmostEqual(purse.capital / 3.0, 100.0 / 2.0)
        self.assertAlmostEqual(purse.cash_mark, 60.0)
        self.assertAlmostEqual(unmarked.capital, 15.0)
        self.assertIsNone(unmarked.cash_mark)


class TreeInTheCoin(unittest.TestCase):

    @staticmethod
    def _tree():
        return {"node": {"rev_hours": 1.0, "up_hours": 2.0, "cap_hours": 5.0, "lab": {"farmer": 3.0}, "_material_hours": 4.0}}

    def test_money_fields_are_hours_times_the_figure(self):
        tree = money_units.rebased_nodes(self._tree(), {"farmer": 0.5}, 2.0)
        node = tree["node"]
        self.assertEqual((node["rev"], node["up"], node["cap"]), (2.0, 4.0, 10.0))
        self.assertEqual(node["_material_cost"], 8.0)
        self.assertEqual(node["_labour_cost"], 1.5)
        self.assertEqual(node["_money_per_labour_hour"], 2.0)

    def test_a_tree_already_in_that_coin_is_returned_unchanged(self):
        tree = money_units.rebased_nodes(self._tree(), {"farmer": 0.5}, 2.0)
        self.assertIs(money_units.rebased_nodes(tree, {"farmer": 0.5}, 2.0), tree)

    def test_rebasing_never_mutates_the_shared_tree(self):
        shared = self._tree()
        money_units.rebased_nodes(shared, {"farmer": 0.5}, 2.0)
        self.assertNotIn("cap", shared["node"])


if __name__ == "__main__":
    unittest.main()
