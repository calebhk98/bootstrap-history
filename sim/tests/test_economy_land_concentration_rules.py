"""Channels that move land concentration, each a rule called on built inputs (Bekar and Reed 2009, Oxford Economic
and Social History 79: distress sales after harvest shocks concentrate land, partible inheritance spreads it):
a failed run of harvests, a lender that takes the pledged plot, an estate that divides among heirs."""

QUICK_TOPIC = True

import unittest

from sim.economy import titles, titles_concentration, titles_inheritance
from sim.tests import land_fixture as fixture

HOUSEHOLDS = 10
DEARTH_YEARS = 4


def dearth(*sufferers, years=DEARTH_YEARS):
    """Harvest input: the named households (by index) harvest almost nothing for `years` years, the rest normally."""
    def income(household, year):
        failed = int(household.rsplit(":", 1)[1]) in sufferers and year < years
        return fixture.FAILED_INCOME if failed else fixture.NORMAL_INCOME
    return income


def gini_after(sufferers, years=8, inheritance=False, partible_share=1.0, household_lender=False):
    """The village after `years`; with `household_lender` the lender is the richest household (so its estate can divide)."""
    setup, record = fixture.village(HOUSEHOLDS, lender_is_a_household=household_lender)
    lender = fixture.household_ids(record)[-1] if household_lender else None
    fixture.run(setup, record, years, dearth(*sufferers), inheritance=inheritance, partible_share=partible_share,
                lender=lender)
    return setup, record, titles_concentration.summary(setup.tiles, record)


class HarvestShockTests(unittest.TestCase):
    def test_good_harvests_leave_titles_equal(self):
        setup, record, measured = gini_after(())
        self.assertAlmostEqual(measured["gini"], 0.0)
        self.assertEqual(record.tenancies, {})

    def test_a_run_of_failed_harvests_passes_the_borrowers_plot_to_the_lender_and_raises_the_gini(self):
        setup, record, measured = gini_after((0,))
        self.assertGreater(measured["gini"], 0.0)
        self.assertGreater(titles.holding(record, fixture.TILE, fixture.LENDER), 0.0)
        self.assertAlmostEqual(titles.tenant_share(record, fixture.TILE, "household:village:0"),
                               titles.holding(record, fixture.TILE, fixture.LENDER))

    def test_more_households_hit_means_more_land_concentrated(self):
        ginis = [gini_after(sufferers)[2]["gini"] for sufferers in ((), (0,), (0, 1, 2), (0, 1, 2, 3, 4, 5))]
        self.assertEqual(ginis, sorted(ginis))
        self.assertLess(ginis[0], ginis[-1])

    def test_a_single_failed_year_is_carried_by_borrowing_and_moves_no_title(self):
        setup, record = fixture.village(HOUSEHOLDS)
        fixture.run(setup, record, 8, dearth(0, 1, 2, years=1))
        self.assertEqual(record.tenancies, {})

    def test_the_landless_are_in_the_gini_only_in_the_wider_denominator(self):
        _setup, _record, measured = gini_after((0, 1, 2))
        self.assertGreater(measured["landless_share"], 0.0)
        self.assertGreater(measured["gini"], measured["gini_landholders_only"])


class PartibleInheritanceTests(unittest.TestCase):
    def test_estates_that_divide_hold_the_gini_below_estates_that_stay_whole(self):
        whole = gini_after((0, 1, 2, 3), years=40, inheritance=False, household_lender=True)[2]["gini"]
        divided = gini_after((0, 1, 2, 3), years=40, inheritance=True, household_lender=True)[2]["gini"]
        self.assertLess(divided, whole)

    def test_a_larger_partible_share_means_a_lower_gini(self):
        ginis = [gini_after((0, 1, 2, 3), years=40, inheritance=True, partible_share=share, household_lender=True)[2]["gini"]
                 for share in (0.0, 0.25, 1.0)]
        self.assertEqual(ginis, sorted(ginis, reverse=True))
        self.assertLess(ginis[-1], ginis[0])

    def test_with_a_household_lender_the_gathered_estate_passes_back_to_the_households_that_lost_land(self):
        setup, record = fixture.village(HOUSEHOLDS, lender_is_a_household=True)
        lender = fixture.household_ids(record)[-1]
        fixture.run(setup, record, 8, dearth(0, 1), lender=lender)
        gathered = titles.holding(record, fixture.TILE, lender) - record.cohorts[lender].ownership_share
        self.assertGreater(gathered, 0.0)
        before = titles_concentration.summary(setup.tiles, record)["gini"]
        titles_inheritance.divide_estates(record, generation_years=5.0, partible_share=1.0)
        self.assertLess(titles_concentration.summary(setup.tiles, record)["gini"], before)


if __name__ == "__main__":
    unittest.main()
