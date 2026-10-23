"""The labour market's quote reaches bondage repayment and the workshop's output. Called on stand-in games that carry
only the market's quote, so a change in the quote shows in both."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine.bondage_workshop_rules import bondage_repayment, serve_bondage_year, workshop_craft_wages
from sim.engine.core_step_phases import StepPhasesMixin
from sim.engine.economy_production import ProductionMixin


class BondageGame(StepPhasesMixin):
    BONDAGE_LABOUR_SHARE = 0.5
    BONDAGE_WAGE_MARKUP = 1.2

    def __init__(self, labourer_quote):
        self.cfg = {"founder_hours_per_year": 2000.0}
        self.labour = types.SimpleNamespace(market=types.SimpleNamespace(quote=lambda trade: labourer_quote[trade]))
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(bondage_years_left=5, bondage_debt=1.0e9, log=[]),
            scenario=types.SimpleNamespace(year=100))


class WorkshopGame(ProductionMixin):
    WORKSHOP_WAGE_MARKUP_BASE = 1.5

    def __init__(self, annual_quote):
        self.state = types.SimpleNamespace(household=types.SimpleNamespace(
            employees={"smith": 2.0}, freedmen=0.0, slaves=0.0))
        self.labour = types.SimpleNamespace(market=types.SimpleNamespace(quote_annual=annual_quote))

    def running_with_mechanic(self, mechanic):
        return True

    def effect_sum(self, name, base):
        return base

    def capability_factor(self):
        return 1.0


class BondageYear(unittest.TestCase):

    def test_a_year_of_bondage_repays_the_markets_labourer_hour(self):
        game = BondageGame({"labourer": 3.0})
        game._step_bondage()
        household = game.state.household
        self.assertAlmostEqual(1.0e9 - household.bondage_debt, 2000.0 * 0.5 * 1.2 * 3.0)
        self.assertEqual(household.bondage_years_left, 4)

    def test_a_dearer_labourer_hour_repays_more(self):
        cheap, dear = BondageGame({"labourer": 3.0}), BondageGame({"labourer": 4.0})
        cheap._step_bondage()
        dear._step_bondage()
        self.assertGreater(1.0e9 - dear.state.household.bondage_debt, 1.0e9 - cheap.state.household.bondage_debt)

    def test_a_repayment_is_hours_times_share_times_markup_times_the_quote(self):
        self.assertEqual(bondage_repayment(2000.0, 0.5, 1.2, 3.0), 3600.0)

    def test_a_term_that_runs_out_discharges_what_is_left(self):
        years_left, debt, served = serve_bondage_year(1, 100.0, 10.0)
        self.assertEqual((years_left, debt, served), (0, 0.0, True))


class WorkshopOutput(unittest.TestCase):

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
