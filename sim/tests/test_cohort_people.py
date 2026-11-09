"""The cohorts' people as columns: totals by tile, following demography's count, the hunger by tile and the stored work plans."""
import unittest

import numpy as np

from sim.economy import cohort_close_write, cohort_people
from sim.economy.cohort_store import CohortStore
from sim.economy.households_cohort import Cohort

QUICK_TOPIC = True


def _store():
    return CohortStore({each.agent_id: each for each in (
        Cohort("household:t1:0", "t1", 0, 10.0, 4.0, 0.4, unmet_floor_by_need={"hunger": 1.5}),
        Cohort("household:t1:1", "t1", 1, 30.0, 12.0, 0.6),
        Cohort("household:t2:0", "t2", 0, 8.0, 0.0, 1.0, unmet_floor_by_need={"hunger": 2.0, "warmth": 1.0}))})


class TotalsByTile(unittest.TestCase):
    def test_a_column_is_added_by_tile_in_table_order(self):
        store = _store()
        numbers = store.names["tiles"].numbers
        totals = cohort_people.total_by_tile(store, "people")
        self.assertEqual(totals[numbers["t1"]], 40.0)
        self.assertEqual(totals[numbers["t2"]], 8.0)

    def test_cohorts_left_out_by_the_flag_add_nothing(self):
        store = _store()
        totals = cohort_people.total_by_tile(store, "people", np.array([True, False, True]))
        self.assertEqual(totals[store.names["tiles"].numbers["t1"]], 10.0)

    def test_hunger_is_the_need_short_added_by_tile_for_the_tiles_short(self):
        self.assertEqual(cohort_people.hunger_by_tile(_store(), "hunger"), {"t1": 1.5, "t2": 2.0})
        self.assertEqual(cohort_people.hunger_by_tile(_store(), "warmth"), {"t2": 1.0})
        self.assertEqual(cohort_people.hunger_by_tile(_store(), "nothing"), {})


class FollowingPopulation(unittest.TestCase):
    def test_each_tiles_cohorts_are_scaled_to_the_tiles_people_and_working_people(self):
        store = _store()
        cohort_people.follow_population(store, {"t1": 80.0}, {"t1": 8.0})
        self.assertEqual(store["household:t1:0"].people, 20.0)
        self.assertEqual(store["household:t1:1"].people, 60.0)
        self.assertEqual(store["household:t1:0"].working_people, 2.0)
        self.assertEqual(store["household:t1:1"].working_people, 6.0)

    def test_a_tile_not_named_is_left_as_it_was(self):
        store = _store()
        cohort_people.follow_population(store, {"t1": 80.0}, {"t1": 8.0})
        self.assertEqual(store["household:t2:0"].people, 8.0)
        self.assertEqual(store["household:t2:0"].working_people, 0.0)

    def test_working_people_follow_the_people_when_the_tile_has_no_working_age_count(self):
        store = _store()
        cohort_people.follow_population(store, {"t1": 80.0}, {})
        self.assertEqual(store["household:t1:1"].working_people, 24.0)

    def test_a_tile_with_no_working_people_shares_the_working_age_count_by_people(self):
        store = _store()
        cohort_people.follow_population(store, {"t2": 16.0}, {"t2": 4.0})
        self.assertEqual(store["household:t2:0"].people, 16.0)
        self.assertEqual(store["household:t2:0"].working_people, 4.0)

    def test_working_people_never_exceed_the_people(self):
        store = _store()
        cohort_people.follow_population(store, {"t1": 4.0}, {"t1": 40.0})
        for each in ("household:t1:0", "household:t1:1"):
            self.assertLessEqual(store[each].working_people, store[each].people)

    def test_a_numpy_count_makes_numpy_figures(self):
        store = _store()
        cohort_people.follow_population(store, {"t1": np.float64(80.0)}, {"t1": 8.0})
        self.assertIsInstance(store["household:t1:0"].people, np.floating)
        self.assertIs(type(store["household:t2:0"].people), float)


class WorkPlans(unittest.TestCase):
    def test_a_plan_that_differs_is_stored_and_one_that_does_not_is_not(self):
        store = _store()
        cohort_people.apply_work_plans(store, {"household:t1:0": (2.0, 5.0, ("wheat",)), "household:t1:1": (0.0, 1.0, ()),
                                               "household:t2:0": (0.0, 0.0, ())})
        self.assertEqual(store["household:t1:0"].hired_work_per_person, 2.0)
        self.assertEqual(store["household:t1:0"].milled_grains, ("wheat",))
        self.assertEqual(store["household:t1:1"].hired_work_per_person, 0.0)

    def test_a_plan_that_only_changes_the_grains_is_stored(self):
        store = _store()
        cohort_people.apply_work_plans(store, {"household:t2:0": (0.0, 0.0, ("rye",))})
        self.assertEqual(store["household:t2:0"].milled_grains, ("rye",))


class CloseWrite(unittest.TestCase):
    def test_the_figures_of_a_close_land_in_the_rows_named(self):
        store = _store()
        cohort_close_write.write_close(
            store, np.array([2, 0]), {"cash_target": [9.0, 3.0], "share_wealth": [None, 6.0], "planned_spending": [0.0, 0.0]},
            [{"hunger": 0.25}, {}], [{}, {"hunger": 7.0}])
        self.assertEqual(store["household:t2:0"].cash_target, 9.0)
        self.assertIsNone(store["household:t2:0"].share_wealth)
        self.assertEqual(store["household:t2:0"].unmet_floor_by_need, {"hunger": 0.25})
        self.assertEqual(store["household:t1:0"].cash_target, 3.0)
        self.assertEqual(store["household:t1:0"].share_wealth, 6.0)
        self.assertEqual(store["household:t1:0"].own_plan_by_need, {"hunger": 7.0})
        self.assertEqual(store["household:t1:1"].cash_target, 0.0)


if __name__ == "__main__":
    unittest.main()
