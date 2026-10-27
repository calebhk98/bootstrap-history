"""The labour market's quote reaches bondage repayment and the workshop's output. Called on stand-in games that carry
only the market's quote, so a change in the quote shows in both."""

QUICK_TOPIC = True

import types
import unittest

from sim.production.bondage_workshop_rules import workshop_craft_wages
from unittest import mock

from sim.production import revenue as production_revenue
from sim.tests import production_host
from sim.finance.constants import BONDAGE_LABOUR_SHARE, BONDAGE_WAGE_MARKUP
from sim.finance.rules import bondage_repayment, serve_bondage_year
from sim.finance.state import FinanceSeat
from sim.tests import finance_host


def bondage_module(labourer_quote):
    """The finance module of a household owing a debt in bondage, over a labour market quoting the labourer's hour."""
    return finance_host.build(seat=FinanceSeat(bondage_years_left=5, bondage_debt=1.0e9), game_config={"founder_hours_per_year": 2000.0},
                              labour_market=types.SimpleNamespace(quote=lambda trade: labourer_quote[trade]))


def WorkshopGame(annual_quote):
    """The production module over a workshop of two smiths and a labour market quoting `annual_quote`."""
    game = types.SimpleNamespace(
        labour=types.SimpleNamespace(market=types.SimpleNamespace(quote_annual=annual_quote)),
        running_with_mechanic=lambda mechanic: True, effect_sum=lambda name, base: base)
    module = production_host.build(game, staff={"employees": {"smith": 2.0}, "freedmen": 0.0, "slaves": 0.0})
    module.capability_factor = lambda: 1.0
    return module


class BondageYear(unittest.TestCase):

    def test_a_year_of_bondage_repays_the_markets_labourer_hour(self):
        module = bondage_module({"labourer": 3.0})
        module.serve_bondage_year()
        self.assertAlmostEqual(1.0e9 - module.seat.bondage_debt, 2000.0 * BONDAGE_LABOUR_SHARE * BONDAGE_WAGE_MARKUP * 3.0)
        self.assertEqual(module.seat.bondage_years_left, 4)

    def test_a_dearer_labourer_hour_repays_more(self):
        cheap, dear = bondage_module({"labourer": 3.0}), bondage_module({"labourer": 4.0})
        cheap.serve_bondage_year()
        dear.serve_bondage_year()
        self.assertGreater(1.0e9 - dear.seat.bondage_debt, 1.0e9 - cheap.seat.bondage_debt)

    def test_a_repayment_is_hours_times_share_times_markup_times_the_quote(self):
        self.assertEqual(bondage_repayment(2000.0, 0.5, 1.2, 3.0), 3600.0)

    def test_a_term_that_runs_out_discharges_what_is_left(self):
        years_left, debt, served = serve_bondage_year(1, 100.0, 10.0)
        self.assertEqual((years_left, debt, served), (0, 0.0, True))


class WorkshopOutput(unittest.TestCase):

    def setUp(self):
        patched = mock.patch.object(production_revenue, "WORKSHOP_WAGE_MARKUP_BASE", 1.5)
        patched.start()
        self.addCleanup(patched.stop)

    def test_craft_hands_are_valued_at_the_markets_annual_wage_whatever_the_wage_is(self):
        for wage in (100.0, 250.0):
            game = WorkshopGame(lambda trade, wage=wage: wage)
            self.assertAlmostEqual(game.workshop_output(), 2.0 * wage * 1.5)

    def test_the_output_per_wage_does_not_move_with_the_wage_level(self):
        low, high = WorkshopGame(lambda trade: 100.0), WorkshopGame(lambda trade: 300.0)
        self.assertAlmostEqual(low.workshop_output() / 100.0, high.workshop_output() / 300.0)

    def test_craft_wages_count_only_craft_trades_plus_the_unfree_at_the_artisan_quote(self):
        wages = workshop_craft_wages({"smith": 2.0, "scribe": 5.0}, lambda trade: trade == "smith",
                                     lambda trade: 100.0, 1.5, 80.0)
        self.assertEqual(wages, 2.0 * 100.0 + 1.5 * 80.0)


if __name__ == "__main__":
    unittest.main()
