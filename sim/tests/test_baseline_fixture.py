"""Complaint 554, classified under Complaint 640. Baseline validations (CLAUDE.md 4.2): `BaselineValidationFixtureRunTests` runs the small three-tile fixture economy
(fixed people, no shocks, no engine orders) and asserts relationships a quiet economy must show: every year's accounts
are physically feasible, stocks are not eaten through, food is eaten in every tile, and the price level, wage, money
supply and rate settle. They read the whole economy, so they are slow-only; a failure names the series, not a rule.
The Rome run is in test_baseline_rome; the statistic's rules are in test_series_settling_rule."""
import math
import unittest

from sim.economy import api as economy_api
from sim.economy.baseline_checks import feasibility, food_eaten_over_need, stock_depletion
from sim.economy.economy import Economy
from sim.economy.settling import SETTLING_WINDOW_YEARS, format_report, series_settling, settling_report
from sim.tests import economy_fixture as fixture

YEARS = 60


def controlled_run(years=YEARS):
    """(economy, outcomes, rows) for `years` quiet years; rows hold what settling_report reads."""
    setup = fixture.small_setup()
    economy = Economy(setup)
    economy_api.begin_spin_up(economy)
    outcomes, rows = [], []
    for _year in range(years):
        outcome = economy.step(fixture.quiet_year(setup))
        outcomes.append(outcome)
        row = {"price_level": outcome.basket_price_level, "money_supply": outcome.money_supply, "rate": outcome.rate,
               "wage": outcome.wages.get(setup.unskilled_trade, 0.0)}
        row.update(economy_api.money_year_figures(economy, outcome))
        rows.append(row)
    return economy, outcomes, rows


class BaselineValidationFixtureRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.economy, cls.outcomes, cls.rows = controlled_run()
        cls.accounts = [outcome.accounts for outcome in cls.outcomes]

    def test_the_run_is_physically_feasible(self):
        self.assertEqual(feasibility(self.accounts), [])

    def test_stocks_are_not_eaten_through(self):
        late = self.accounts[-SETTLING_WINDOW_YEARS:]
        depletion = stock_depletion(late)
        self.assertTrue(depletion)
        for good, share in depletion.items():
            self.assertLessEqual(share, 0.5, good)

    def test_the_report_names_the_four_series_with_finite_statistics(self):
        report = settling_report(self.rows)
        self.assertEqual([item.name for item in report], ["price_level", "wage", "money_supply", "rate"])
        for item in report:
            self.assertTrue(math.isfinite(item.largest_step) and math.isfinite(item.trend_per_year), item.name)

    def test_validation_the_quiet_fixture_settles(self):
        # Validation, not a rule. The bounds are the declared temporary heuristics of settling.py. It fails while the
        # economy does not settle (Complaint 473: the fixture cycles and drifts as the Rome spin-up does); that is an
        # honest result, so do not loosen it.
        report = settling_report(self.rows)
        self.assertEqual([item.name for item in report if not item.settled], [],
                         "the economy does not settle (Complaint 473)\n" + format_report(report))

    def test_food_is_eaten_in_every_tile_in_the_last_year(self):
        eaten = food_eaten_over_need(self.accounts)
        self.assertTrue(eaten)
        for tile, ratio in eaten.items():
            self.assertTrue(ratio > 0.0, tile)


if __name__ == "__main__":
    unittest.main()
