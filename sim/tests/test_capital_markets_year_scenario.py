"""SCENARIO (Complaint 640): the capital markets in the economy's year (Complaint 106): the hazard's record is kept whatever the
society holds; with the institutions the society holds, households insure against a poor harvest, found a fund with their idle
savings, and sell claims, and the year's money is conserved throughout. Rules are in test_insurance.py, test_funds.py,
test_secondary_trade.py and test_bank_runs.py."""

QUICK_TOPIC = False

import contextlib
import unittest
from unittest import mock

from sim.economy import banks, funds, insurance, secondary_trade
from sim.tests import economy_fixture as fixture

WEATHER = (1.0, 1.0, 0.6, 1.0, 0.7, 1.0)


def run_years(institutions, weather=WEATHER, cannot_bear_a_poor_year=False):
    """The stationary economy over the weather. The fixture's households hold more cash than a poor harvest costs them, so
    they would not buy cover; `cannot_bear_a_poor_year` has every exposed household want it (the buying rule is
    tested in test_insurance.py), to follow the cover through the year."""
    setup = fixture.stationary_setup()
    patch = mock.patch.object(insurance, "wants_cover", lambda *_args: True) if cannot_bear_a_poor_year else contextlib.nullcontext()
    with patch:
        return _run(setup, institutions, weather)


def _run(setup, institutions, weather):
    def inputs(economy, year):
        return fixture.quiet_year(setup, year=year, harvest_factor=weather[year], institutions=tuple(institutions))

    return fixture.run(setup, years=len(weather), inputs_for_year=inputs)


class TheYear(unittest.TestCase):
    def test_the_hazard_is_watched_each_year_whatever_the_society_holds(self):
        economy, _outcomes = run_years(())
        hazard = economy.record.capital.hazards[insurance.HARVEST]
        self.assertEqual(hazard.years, len(WEATHER))
        self.assertAlmostEqual(hazard.worst, 0.4)
        self.assertEqual(economy.record.capital.policies, [])

    def test_a_society_with_no_institution_founds_no_insurer_fund_or_trade(self):
        economy, _outcomes = run_years(())
        self.assertEqual((economy.record.capital.insurers, economy.record.capital.funds), ({}, {}))

    def test_a_society_that_knows_a_mutual_has_its_households_insure_one_another_and_the_book_holds(self):
        economy, _outcomes = run_years((insurance.RISK_POOLING,), cannot_bear_a_poor_year=True)
        state = economy.record.capital
        self.assertTrue(state.insurers)
        self.assertTrue(all(insurer.mutual for insurer in state.insurers.values()))
        self.assertTrue(state.policies)

    def test_a_society_that_knows_the_company_has_a_household_found_one_that_prices_from_the_record(self):
        economy, _outcomes = run_years((insurance.INSURANCE_UNDERWRITING,), cannot_bear_a_poor_year=True)
        state = economy.record.capital
        self.assertTrue(state.insurers)
        self.assertTrue(any(not insurer.mutual for insurer in state.insurers.values()))

    def test_a_society_that_knows_funds_has_the_richest_household_found_one(self):
        economy, _outcomes = run_years((funds.POOLED_FUNDS, secondary_trade.SHARE_TRADING, secondary_trade.BOND_MARKET))
        self.assertEqual(len(economy.record.capital.funds), 1)
        fund = next(iter(economy.record.capital.funds.values()))
        self.assertTrue(fund.units)                         # the idle savings of the household that founded it went in
        self.assertGreater(economy.record.book.balance(fund.agent_id, economy.setup.currency_id), 0.0)

    def test_every_institution_together_runs_the_years_and_the_book_is_conserved(self):
        every = (banks.DEPOSIT_BANKING, funds.POOLED_FUNDS, secondary_trade.SHARE_TRADING, secondary_trade.BOND_MARKET,
                 insurance.INSURANCE_UNDERWRITING, insurance.RISK_POOLING)
        economy, outcomes = run_years(every)
        self.assertEqual(len(outcomes), len(WEATHER))


if __name__ == "__main__":
    unittest.main()
