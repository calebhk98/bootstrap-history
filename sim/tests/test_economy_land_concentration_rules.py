"""Channels that move land concentration, each a rule called on a record written out in the test (Bekar and Reed 2009,
Oxford Economic and Social History 79: distress sales after harvest shocks concentrate land, partible inheritance spreads it):
the summary that measures it, a lender that takes the pledged plot, an estate that divides among heirs."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import titles, titles_concentration, titles_inheritance

TILE = "village"
TILES = {TILE: types.SimpleNamespace(cropland_hectares=100.0)}
HOUSEHOLDS = 10


def village(held=None):
    """A record of ten households that each opened holding a tenth of the tile; `held` replaces the titles."""
    cohorts = {"household:%d" % index: types.SimpleNamespace(agent_id="household:%d" % index, tile=TILE, ownership_share=0.1)
               for index in range(HOUSEHOLDS)}
    held = {holder: cohort.ownership_share for holder, cohort in cohorts.items()} if held is None else held
    return types.SimpleNamespace(cohorts=cohorts, titles={TILE: dict(held)}, tenancies={}, loans=[])


def gini_of(held):
    return titles_concentration.summary(TILES, village(held))["gini"]


def pledge(borrower="household:0", lender="lender:village", share=0.1):
    return types.SimpleNamespace(borrower=borrower, lender=lender, collateral_tile=TILE, collateral_share=share,
                                 collateral_value=50.0)


class ConcentrationSummaryTests(unittest.TestCase):
    def test_equal_titles_have_no_gini(self):
        self.assertAlmostEqual(titles_concentration.summary(TILES, village())["gini"], 0.0)

    def test_the_gini_rises_with_the_land_gathered_by_one_holder(self):
        def held(landless):
            share = 1.0 / (HOUSEHOLDS - landless)
            return {"household:%d" % index: share for index in range(landless, HOUSEHOLDS)}
        ginis = [gini_of(held(landless)) for landless in (0, 1, 3, 6)]
        self.assertEqual(ginis, sorted(ginis))
        self.assertLess(ginis[0], ginis[-1])

    def test_the_landless_are_in_the_gini_only_in_the_wider_denominator(self):
        measured = titles_concentration.summary(TILES, village({"household:%d" % index: 1.0 / 7 for index in range(3, HOUSEHOLDS)}))
        self.assertAlmostEqual(measured["landless_share"], 0.3)
        self.assertGreater(measured["gini"], measured["gini_landholders_only"])


class ForeclosureTests(unittest.TestCase):
    def test_a_defaulted_pledge_passes_the_borrowers_plot_to_the_lender_who_leaves_him_as_tenant(self):
        record = village()
        titles.foreclose(record, pledge())
        self.assertAlmostEqual(titles.holding(record, TILE, "lender:village"), 0.1)
        self.assertAlmostEqual(titles.holding(record, TILE, "household:0"), 0.0)
        self.assertAlmostEqual(titles.tenant_share(record, TILE, "household:0"), 0.1)


class PartibleInheritanceTests(unittest.TestCase):
    def gathered(self):
        """The last household has gathered the land of the first four, which opened with a tenth each."""
        held = {"household:%d" % index: 0.1 for index in range(4, HOUSEHOLDS - 1)}
        held["household:9"] = 0.5
        return village(held)

    def test_dividing_estates_gives_the_gathered_land_back_to_the_households_that_lost_it(self):
        record = self.gathered()
        before = titles_concentration.summary(TILES, record)["gini"]
        titles_inheritance.divide_estates(record, generation_years=5.0, partible_share=1.0)
        self.assertLess(titles_concentration.summary(TILES, record)["gini"], before)
        self.assertGreater(titles.holding(record, TILE, "household:0"), 0.0)
        self.assertLess(titles.holding(record, TILE, "household:9"), 0.5)

    def test_a_larger_partible_share_means_a_lower_gini(self):
        ginis = []
        for share in (0.0, 0.25, 1.0):
            record = self.gathered()
            titles_inheritance.divide_estates(record, generation_years=5.0, partible_share=share)
            ginis.append(titles_concentration.summary(TILES, record)["gini"])
        self.assertEqual(ginis, sorted(ginis, reverse=True))
        self.assertLess(ginis[-1], ginis[0])


if __name__ == "__main__":
    unittest.main()
