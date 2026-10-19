"""Complaint 545: the opening sizes producers for what households do not grow themselves.

A year lets the hours nobody hires grow the household's floors on its own plot, and those floors are not bought.
The opening applies the same rule (opening_own.py), so the market demand and the producers' capacity for a food
floor the households grow do not collapse between the opening and the first year.
"""
import math
import unittest

from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture

QUICK_TOPIC = False
TOLERANCE = 0.1       # share of the floor: the opening's idle hours are an average over the nation, a year's are cohort by cohort


def _grain_capacity(economy):
    return math.fsum(p.capacity_runs for p in economy.record.producers.values() if p.recipe_id == fixture.FARM)


def _first_year(setup):
    """(economy before the year, grown need units by cohort in the year, outcome)."""
    economy = Economy(setup)
    seen = {}
    original = Economy._grow_own

    def spy(self, offers, ledger, *args, **kwargs):
        original(self, offers, ledger, *args, **kwargs)
        seen["units"] = {cohort: dict(units) for cohort, units in ledger.grown_units.items()}
    Economy._grow_own = spy
    try:
        capacity_before = _grain_capacity(economy)
        outcome = economy.step(fixture.quiet_year(setup))
    finally:
        Economy._grow_own = original
    return economy, capacity_before, seen.get("units", {}), outcome


class OpeningOwnPlots(unittest.TestCase):
    def setUp(self):
        fixture.households_with_a_surplus(self)
        self.plots = fixture.small_setup(land_per_run={fixture.FARM: 1.0})
        self.no_plots = fixture.small_setup()

    def test_opening_demand_is_what_first_year_leaves_to_buy(self):
        economy, _capacity, grown_units, _outcome = _first_year(self.plots)
        bare = Economy(self.no_plots)
        floor = math.fsum(c.people for c in bare.record.cohorts.values()) * 250.0
        opening_grown = bare.record.opening_basket.get(fixture.GRAIN, 0.0) - Economy(self.plots).record.opening_basket.get(fixture.GRAIN, 0.0)
        year_grown = math.fsum(units.get(fixture.FOOD, 0.0) for units in grown_units.values())
        self.assertGreater(year_grown, 0.0)
        self.assertLessEqual(abs(opening_grown - year_grown) / floor, TOLERANCE)

    def test_producers_capacity_does_not_collapse_in_the_first_year(self):
        def first_year_use(setup):
            opened = Economy(setup)
            capacity = _grain_capacity(opened)
            self.assertGreater(capacity, 0.0)
            return opened.step(fixture.quiet_year(setup)).output.get(fixture.GRAIN, 0.0) / (capacity * 1000.0)
        # plots that households work take no more of the farms' sales in year one than the opening sized for
        self.assertGreaterEqual(first_year_use(self.plots), first_year_use(self.no_plots) * (1.0 - TOLERANCE))

    def test_plots_cut_the_opening_demand_for_the_floor(self):
        with_plots = Economy(self.plots).record.opening_basket.get(fixture.GRAIN, 0.0)
        without = Economy(self.no_plots).record.opening_basket.get(fixture.GRAIN, 0.0)
        self.assertLess(with_plots, without)


if __name__ == "__main__":
    unittest.main()
