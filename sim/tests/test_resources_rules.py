"""The resources module's plain rules (sim/resources/rules.py and sizing.py): depletion, cost scale, capacity sums, the room a
deposit leaves and where new capacity goes. Each test calls one function on written-out values."""
QUICK_TOPIC = True
UNDER_TEST = {"depletion_factor", "average_depletion", "cost_scale", "capacity_by_material", "priced_row", "allocation_plan"}

import unittest

from sim.resources import rules


class Depletion(unittest.TestCase):
    def test_a_fresh_working_keeps_all_its_yield_and_a_worn_one_falls_to_the_floor(self):
        self.assertEqual(rules.depletion_factor(0.0, 0.5, 120.0), 1.0)
        self.assertEqual(rules.depletion_factor(60.0, 0.5, 120.0), 0.5)
        self.assertEqual(rules.depletion_factor(1e9, 0.5, 120.0), 0.5)

    def test_the_average_is_weighted_by_capacity_and_one_with_nothing_standing(self):
        self.assertAlmostEqual(rules.average_depletion([40.0, 20.0], [0.5, 1.0]), (0.5 * 40.0 + 20.0) / 60.0)
        self.assertEqual(rules.average_depletion([], []), 1.0)

    def test_the_cost_scale_is_depletion_inverted_and_bounded(self):
        self.assertEqual(rules.cost_scale(1.0, 0.4, 2.5), 1.0)
        self.assertEqual(rules.cost_scale(0.5, 0.4, 2.5), 2.0)
        self.assertEqual(rules.cost_scale(0.1, 0.4, 2.5), 2.5)
        self.assertEqual(rules.cost_scale(5.0, 0.4, 2.5), 0.4)

    def test_a_year_adds_the_capacity_over_the_ceiling_and_a_ceiling_under_one_counts_as_one(self):
        self.assertEqual(rules.next_intensity(1.0, 10.0, 100.0), 1.1)
        self.assertEqual(rules.next_intensity(0.0, 10.0, 0.0), 10.0)

    def test_a_working_yields_no_more_than_its_deposit_has_left(self):
        self.assertEqual(rules.working_yield(10.0, 0.5, None), 5.0)
        self.assertEqual(rules.working_yield(10.0, 0.5, 2.0), 2.0)

    def test_there_is_nothing_to_explain_for_a_working_that_has_lost_nothing(self):
        self.assertIsNone(rules.depletion_note(1.0))
        self.assertIn("50%", rules.depletion_note(0.5))   # presentation: the note states the share worked out


class Capacity(unittest.TestCase):
    def test_capacity_is_summed_by_material_in_the_order_the_materials_first_stand(self):
        workings = [{"material": "tin", "capacity": 1.0}, {"material": "coal", "capacity": 2.0},
                    {"material": "tin", "capacity": 3.0}]
        totals = rules.capacity_by_material(workings)
        self.assertEqual((list(totals), totals["tin"]), (["tin", "coal"], 4.0))

    def test_what_a_deposit_has_named_counts_standing_workings_and_shafts_being_sunk(self):
        workings = [{"capacity": 3.0, "deposit": "d"}, {"capacity": 5.0, "deposit": "e"}, {"capacity": 7.0}]
        tranches = [["coal", 2.0, 105, 0.0, "", "d"], ["coal", 11.0, 105]]
        self.assertEqual(rules.capacity_naming(workings, tranches, "d"), 5.0)


class Deposits(unittest.TestCase):
    ROW = {"id": "d", "tile_id": "t"}

    def test_the_room_is_the_larger_of_the_working_share_and_the_data_rate_less_what_is_named(self):
        priced = rules.priced_row(self.ROW, 1000.0, 0.0, 0.0, 4.0, 10.0, 3.0)
        self.assertEqual((priced["rate_tonnes_per_year"], priced["room_tonnes_per_year"]), (10.0, 7.0))

    def test_what_was_worked_before_the_start_and_drawn_since_is_not_left(self):
        priced = rules.priced_row(self.ROW, 1000.0, 0.25, 50.0, 1e9, 0.0, 0.0)
        self.assertEqual(priced["remaining_tonnes"], 700.0)
        self.assertEqual(priced["rate_tonnes_per_year"], 700.0)

    def test_new_capacity_goes_to_the_deposit_with_most_room_first(self):
        rows = [{"id": "a", "room_tonnes_per_year": 2.0}, {"id": "b", "room_tonnes_per_year": 5.0}]
        self.assertEqual(rules.allocation_plan(rows, 6.0), [("b", 5.0), ("a", 1.0)])
        self.assertEqual(rules.allocation_plan(rows, 6.0, "a"), [("a", 2.0)])
        self.assertEqual(rules.room_in_deposits(rows), 7.0)


if __name__ == "__main__":
    unittest.main()
