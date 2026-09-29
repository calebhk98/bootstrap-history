"""The engine steps sim/world/labour_market.py every simulated year, so the
share of working hours on the farm responds to food scarcity."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.engine import labour_allocation


def _rome_sim():
    return sim(civ="rome_100ad", events=False)


def _farm_hours(test_sim):
    return test_sim.state.economy.society_labour_hours[labour_allocation.FARM_TRADE]


class WorkforceAllocationWiringTests(unittest.TestCase):

    def test_engine_imports_the_labour_market(self):
        import sim.engine.labour_allocation as module
        self.assertTrue(hasattr(module, "labour_market"))

    def test_unshocked_first_year_keeps_the_baseline_farm_workforce(self):
        test_sim = _rome_sim()
        baseline_fte = labour_allocation.agriculture.farm_workers_fte_for_population(
            test_sim._adult_equivalent_population(test_sim.population))
        test_sim._demographic_recovery(101)
        fte = _farm_hours(test_sim) / labour_allocation.HOURS_PER_FARM_WORKER_YEAR
        self.assertAlmostEqual(fte / baseline_fte, 1.0, places=6)

    def test_a_short_harvest_pulls_hours_onto_the_farm(self):
        # Half the farm hands leave: food runs short, and workers move back.
        test_sim = _rome_sim()
        test_sim._demographic_recovery(101)
        hours = test_sim.state.economy.society_labour_hours
        removed = hours[labour_allocation.FARM_TRADE] * 0.5
        hours[labour_allocation.FARM_TRADE] -= removed
        # The farm hands become craft workers in proportion to each trade's size.
        rest_total = sum(value for trade, value in hours.items()
                         if trade != labour_allocation.FARM_TRADE)
        for trade in list(hours):
            if trade != labour_allocation.FARM_TRADE:
                hours[trade] += removed * hours[trade] / rest_total
        depleted = _farm_hours(test_sim)
        test_sim._demographic_recovery(102)
        after_one_year = _farm_hours(test_sim)
        test_sim._demographic_recovery(103)
        after_two_years = _farm_hours(test_sim)
        self.assertGreater(after_one_year, depleted)
        self.assertGreater(after_two_years, after_one_year)

    def test_workforce_hours_are_conserved_by_reallocation(self):
        hours = {labour_allocation.FARM_TRADE: 40.0, "smith": 20.0, "potter": 40.0}
        moved = labour_allocation.reallocate(hours, 100.0, 70.0)
        self.assertAlmostEqual(sum(moved.values()), 100.0)
        self.assertGreater(moved[labour_allocation.FARM_TRADE], 40.0)

    def test_land_saturation_caps_the_farm_need(self):
        # Workers beyond what the land can employ produce nothing more.
        need = labour_allocation.farm_workers_needed(
            baseline_fte=100.0, current_fte=100.0, shortfall_kg=1e12,
            marginal_product_kg_per_hour=0.001, land_hectares=210.0)
        self.assertLessEqual(need, 210.0 / labour_allocation.agriculture.hectares_cropped_per_farm_worker() + 1e-9)

    def test_workforce_round_trips_through_save_and_load(self):
        import os
        import tempfile
        from sim.engine.proto import saveload
        test_sim = _rome_sim()
        for year in range(101, 106):
            test_sim._demographic_recovery(year)
        before = dict(test_sim.state.economy.society_labour_hours)
        path = tempfile.mktemp(suffix=".json")
        try:
            saveload.save_state(test_sim, path)
            fresh = _rome_sim()
            saveload.load_state(fresh, path)
            self.assertEqual(dict(fresh.state.economy.society_labour_hours), before)
        finally:
            if os.path.exists(path):
                os.remove(path)
