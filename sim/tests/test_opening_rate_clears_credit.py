"""The opening starts at the rate where households' saving meets borrowers' requests (Complaint 526)."""

import math
import unittest
from unittest import mock

from sim.economy import opening, opening_rate
from sim.tests import economy_fixture as fixture


def income_over_ceiling(setup, record):
    people = math.fsum(cohort.people for cohort in record.cohorts.values())
    income = math.fsum(cohort.last_year_income for cohort in record.cohorts.values())
    return income / (opening._full_employment_income_per_head(setup) * people)


class ClearingRateSearchTests(unittest.TestCase):
    def test_finds_the_rate_where_saving_equals_requests(self):
        search = opening_rate.clearing_rate(lambda rate: 100.0 * rate, lambda rate: 40.0 - 100.0 * rate,
                                            lowest=0.0, guess=0.5)
        self.assertTrue(search.clears)
        self.assertAlmostEqual(search.rate, 0.2, places=2)
        self.assertAlmostEqual(search.saving, search.requests, delta=0.01 * 40.0)

    def test_nothing_to_borrow_means_no_clearing_rate(self):
        search = opening_rate.clearing_rate(lambda rate: 10.0 + rate, lambda rate: 0.0, lowest=0.05, guess=0.12)
        self.assertFalse(search.clears)
        self.assertEqual(search.rate, 0.05)

    def test_requests_beyond_any_saving_open_at_the_guess(self):
        search = opening_rate.clearing_rate(lambda rate: 1.0, lambda rate: 50.0, lowest=0.05, guess=0.12)
        self.assertFalse(search.clears)
        self.assertEqual(search.rate, 0.12)


class OpeningRateTests(unittest.TestCase):
    def test_a_society_nobody_borrows_in_reports_no_clearing_rate(self):
        setup = fixture.small_setup()
        with mock.patch.object(opening_rate, "borrowers_requests", lambda *arguments: 0.0):
            record, _areas, _carriage = opening.open_economy(setup)
        found = record.opening_credit
        self.assertEqual(found["requests"], 0.0)
        self.assertFalse(found["clears"])
        self.assertGreater(found["saving"], 0.0)
        self.assertEqual(found["rate"], found["lowest"])

    def test_the_opening_rate_is_found_not_taken_from_the_data(self):
        setup = fixture.small_setup()
        record, _areas, _carriage = opening.open_economy(setup)
        self.assertLess(record.opening_credit["rate"], setup.opening_rate)
        self.assertEqual(record.memory.rates[setup.currency_id], record.opening_credit["rate"])

    def test_settled_income_rises_over_the_data_rate_opening(self):
        setup = fixture.small_setup()
        at_data_rate, _areas, _carriage = opening._open(setup, 0.0)
        found, _areas, _carriage = opening.open_economy(setup)
        self.assertGreater(income_over_ceiling(setup, found), income_over_ceiling(setup, at_data_rate))

    def test_where_saving_clears_it_equals_requests_within_tolerance(self):
        setup = fixture.small_setup()
        record, areas, carriage = opening._open(setup, 0.0)
        people = math.fsum(cohort.people for cohort in record.cohorts.values())
        search = opening_rate.find_rate(setup, record, areas, carriage,
                                        opening._full_employment_income_per_head(setup) * people)
        if search.clears:
            self.assertAlmostEqual(search.saving, search.requests,
                                   delta=opening_rate.CLEARING_TOLERANCE_SHARE * max(search.saving, search.requests))
        else:
            self.assertNotEqual(search.saving, search.requests)


if __name__ == "__main__":
    unittest.main()
