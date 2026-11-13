"""The opening places people by the hours a person of their area sells, seeds only trades some hirer asks, and holds
contracts to the hours the placed people sell. Plain functions on written-out inputs."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import opening_placement, workforce_settle
from sim.labour.market import aptitude, opening, records, trades

REGISTRY = {
    "labourer": {"family": "toil", "training_years": 0, "fallback": True},
    "farmer": {"family": "toil", "training_years": 1},
    "smith": {"family": "craft", "training_years": 3},
}


class SoldHoursByAreaTests(unittest.TestCase):
    def test_an_area_sells_its_cohorts_hours_over_its_working_people(self):
        rows = {"a1": ("hill", 10.0), "a2": ("hill", 30.0), "b1": ("vale", 20.0)}
        found = opening_placement.sold_hours_per_worker_by_area({"a1": 4000.0, "a2": 8000.0, "b1": 20000.0}, rows, 500.0)
        self.assertEqual(found, {"hill": 300.0, "vale": 1000.0})

    def test_an_area_that_sells_nothing_takes_the_default(self):
        found = opening_placement.sold_hours_per_worker_by_area({"a1": 0.0}, {"a1": ("hill", 10.0)}, 500.0)
        self.assertEqual(found, {"hill": 500.0})

    def test_a_number_is_every_areas_and_a_mapping_is_per_area(self):
        self.assertEqual(opening_placement.hours_per_worker_in("hill", 700.0, 2000.0), 700.0)
        self.assertEqual(opening_placement.hours_per_worker_in("hill", {"hill": 300.0}, 2000.0), 300.0)
        self.assertEqual(opening_placement.hours_per_worker_in("vale", {"hill": 300.0}, 2000.0), 2000.0)


class PlacementByAreaHoursTests(unittest.TestCase):
    def test_each_areas_people_are_its_hours_over_what_a_person_there_sells(self):
        specs = trades.trade_specs(REGISTRY)
        state = opening.opening_state(specs, {"hill": 1000.0, "vale": 1000.0},
                                      {"hill": {"smith": 30000.0}, "vale": {"smith": 30000.0}},
                                      {"hill": 300.0, "vale": 600.0}, "farmer")
        self.assertAlmostEqual(aptitude.band_total(state.workers["hill"]["smith"]), 100.0)
        self.assertAlmostEqual(aptitude.band_total(state.workers["vale"]["smith"]), 50.0)

    def test_a_single_figure_still_serves_every_area(self):
        specs = trades.trade_specs(REGISTRY)
        state = opening.opening_state(specs, {"hill": 1000.0}, {"hill": {"smith": 30000.0}}, 300.0, "farmer")
        self.assertAlmostEqual(aptitude.band_total(state.workers["hill"]["smith"]), 100.0)
        self.assertAlmostEqual(records.people_in(state), 1000.0)

    def test_the_fallback_trade_is_placed_by_the_areas_hours_too(self):
        specs = trades.trade_specs(REGISTRY)
        state = opening.opening_state(specs, {"hill": 1000.0}, {"hill": {"labourer": 30000.0}}, {"hill": 300.0}, "farmer")
        self.assertAlmostEqual(aptitude.band_total(state.workers["hill"]["labourer"]), 100.0)
        self.assertAlmostEqual(aptitude.band_total(state.workers["hill"]["farmer"]), 900.0)


class SeedsWhereHiredTests(unittest.TestCase):
    def test_a_seed_is_cut_to_the_hours_the_areas_carriage_crews_ask_and_one_nobody_asks_is_dropped(self):
        seeds = {"port": {"sailor": 1000.0, "charcoal_burner": 450.0}, "inland": {"charcoal_burner": 50.0, "carter": 300.0}}
        hirers = {"port": {"sailor": 400.0}, "inland": {"carter": 900.0}}
        self.assertEqual(opening_placement.seeds_where_hired(seeds, hirers), {"port": {"sailor": 400.0}, "inland": {"carter": 300.0}})

    def test_no_hirer_keeps_nothing(self):
        self.assertEqual(opening_placement.seeds_where_hired({"port": {"sailor": 1000.0}}, {}), {})


class CappedContractsTests(unittest.TestCase):
    def test_contracts_wider_than_the_people_placed_sell_are_cut_in_proportion(self):
        held = {"vale": {"labourer": {"farm_a": 600.0, "farm_b": 400.0}}}
        found = opening_placement.capped_contracts(held, {"vale": {"labourer": 10.0}}, {"vale": 50.0}, 2000.0)
        self.assertEqual(found, {"vale": {"labourer": {"farm_a": 300.0, "farm_b": 200.0}}})

    def test_contracts_the_people_can_work_are_unchanged(self):
        held = {"vale": {"smith": {"farm_a": 500.0}}}
        self.assertEqual(opening_placement.capped_contracts(held, {"vale": {"smith": 10.0}}, 50.0, 2000.0), held)

    def test_a_trade_with_no_people_holds_no_contract(self):
        held = {"vale": {"smith": {"farm_a": 500.0}}}
        self.assertEqual(opening_placement.capped_contracts(held, {}, 50.0, 2000.0), {})


class TrimByAreaHoursTests(unittest.TestCase):
    def test_the_trim_keeps_the_people_an_areas_hours_need(self):
        specs = trades.trade_specs(REGISTRY)
        state = opening.opening_state(specs, {"hill": 1000.0}, {"hill": {"smith": 30000.0}}, {"hill": 300.0}, "farmer")
        workforce_settle.trim_people(state, {("hill", "smith"): 30000.0}, "labourer", {"hill": 300.0})
        self.assertAlmostEqual(aptitude.band_total(state.workers["hill"]["smith"]), 100.0)


if __name__ == "__main__":
    unittest.main()
