"""The agent economy's money: more of it against the same goods raises prices, and every coin is accounted
for (Complaint 389). Built on the engine-free fixture; each test states a direction, not a figure."""

QUICK_TOPIC = True

import unittest

from sim.economy.economy import Economy
from sim.economy.types import EDGE_ISSUE, CurrencySpec, Transfer
from sim.tests import economy_fixture as fixture

COIN = "coin"
YEARS = 4


def fiat_setup():
    return fixture.small_setup(currency=CurrencySpec(COIN, "fiat", None, 0.0, "state:fixture", 0.0))


def with_windfall(factor: float):
    """A fiat economy whose households hold `factor` times the opening's cash, over the same goods."""
    setup = fiat_setup()
    economy = Economy(setup)
    for cohort_id in sorted(economy.record.cohorts):
        extra = economy.record.book.balance(cohort_id, COIN) * (factor - 1.0)
        if extra > 0.0:
            economy.record.book.transfer(Transfer(EDGE_ISSUE, cohort_id, COIN, extra, "windfall"))
    outcomes = [economy.step(fixture.quiet_year(setup)) for _ in range(YEARS)]
    return economy, outcomes


def mean_price_level(outcomes):
    return sum(outcome.basket_price_level for outcome in outcomes) / len(outcomes)


class MoreMoneyTests(unittest.TestCase):
    def test_more_money_with_the_same_goods_raises_the_price_level(self):
        _economy, control = with_windfall(1.0)
        _economy, doubled = with_windfall(2.0)
        _economy, tripled = with_windfall(3.0)
        self.assertGreater(mean_price_level(doubled), mean_price_level(control))
        self.assertGreater(mean_price_level(tripled), mean_price_level(doubled))

    def test_the_windfall_is_in_the_supply_the_outcome_reports(self):
        _economy, control = with_windfall(1.0)
        _economy, doubled = with_windfall(2.0)
        self.assertGreater(doubled[0].money_supply, control[0].money_supply)

    def test_more_money_does_not_make_goods(self):
        _economy, control = with_windfall(1.0)
        _economy, doubled = with_windfall(2.0)
        grain_control = sum(outcome.output.get(fixture.GRAIN, 0.0) for outcome in control)
        grain_doubled = sum(outcome.output.get(fixture.GRAIN, 0.0) for outcome in doubled)
        self.assertLess(grain_doubled, grain_control * 1.5)


class ConservationTests(unittest.TestCase):
    def test_money_is_conserved_year_after_year(self):
        economy, outcomes = fixture.run(years=YEARS)
        for outcome in outcomes:
            self.assertAlmostEqual(outcome.conservation_residual, 0.0, places=6)
            self.assertTrue(outcome.money_audit.ok, outcome.money_audit.unexpected)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())

    def test_the_supply_change_is_what_the_edge_accounts_paid_in(self):
        _economy, outcomes = fixture.run(years=YEARS)
        for outcome in outcomes:
            audit = outcome.money_audit
            edges = sum(nets.get(COIN, 0.0) for nets in audit.edge_net.values())
            self.assertAlmostEqual(audit.supply_change[COIN], edges, delta=1e-6 * audit.supply_at_end[COIN])

    def test_no_money_moves_through_an_unnamed_edge(self):
        _economy, outcomes = fixture.run(years=YEARS)
        for outcome in outcomes:
            self.assertEqual(outcome.money_audit.unexpected, ())

    def test_a_windfall_stays_conserved_and_audited(self):
        economy, outcomes = with_windfall(2.0)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())
        for outcome in outcomes:
            self.assertAlmostEqual(outcome.conservation_residual, 0.0, places=6)

    def test_struck_coin_stays_backed_by_the_mints_metal(self):
        _economy, outcomes = fixture.run(years=YEARS)
        for outcome in outcomes:
            backing = fixture.small_setup().currency.backing_per_unit
            self.assertLess(abs(outcome.money_audit.metal_gap[COIN]), 1e-3 * outcome.money_supply * backing + 1e-6)


if __name__ == "__main__":
    unittest.main()
