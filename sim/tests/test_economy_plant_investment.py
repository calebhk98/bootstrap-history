"""Plant is invested in to close the gap between the runs next year plans and the capacity left after wear, no more
than a set multiple of the year's wear (Eurace@Unibi Cons_Goods/Firm_Producer_Functions.c, Firm_calc_input_demands).
Wear that is replaced comes first and is paid from earnings; what is added beyond it is asked of the credit market."""

QUICK_TOPIC = True

import unittest

from sim.economy import plant_investment, producers_close
from sim.tests.test_economy_producers import SMELT, View, farmer


class InvestmentRunsTests(unittest.TestCase):
    def test_a_gap_within_the_cap_is_closed_whole(self):
        self.assertEqual(plant_investment.investment_runs(9.5, 9.0, 1.0, 2.0), 0.5)

    def test_a_gap_beyond_the_cap_is_closed_as_far_as_the_cap(self):
        self.assertEqual(plant_investment.investment_runs(20.0, 9.0, 1.0, 2.0), 2.0)

    def test_no_gap_means_no_investment_and_idle_plant_is_left_to_wear(self):
        self.assertEqual(plant_investment.investment_runs(8.0, 9.0, 1.0, 2.0), 0.0)

    def test_no_wear_leaves_no_room_to_invest(self):
        self.assertEqual(plant_investment.investment_runs(20.0, 9.0, 0.0, 2.0), 0.0)


class SplitTests(unittest.TestCase):
    def test_wear_is_replaced_before_anything_is_added(self):
        self.assertEqual(plant_investment.split(1.5, 1.0), (1.0, 0.5))

    def test_an_investment_below_the_wear_only_replaces(self):
        self.assertEqual(plant_investment.split(0.5, 1.0), (0.5, 0.0))


class CloseYearTests(unittest.TestCase):
    def close(self, **changes):
        view = View({"metal": 20.0, "silver": 5.0, "ore": 1.0, "stone": 1.0}, {"smith": 1.0})
        producer = farmer(recipe_id="smelt", last_runs=10.0, **changes)
        return producers_close.close_year(producer, SMELT, 500.0, 50.0, view, 10.0)

    def test_a_producer_expecting_to_sell_half_its_capacity_adds_no_plant(self):
        result = self.close(expected_sales=5.0)
        self.assertEqual(result.expansion_runs, 0.0)
        self.assertEqual(result.replacement_runs, 0.0)

    def test_a_producer_selling_all_its_capacity_replaces_its_wear_and_adds_within_the_cap(self):
        result = self.close(expected_sales=10.0)
        self.assertEqual(result.replacement_runs, 1.0)      # a tenth of ten runs wears in a ten-year life
        self.assertGreater(result.expansion_runs, 0.0)
        self.assertLessEqual(result.replacement_runs + result.expansion_runs, plant_investment.INVESTMENT_INERTIA * 1.0)


if __name__ == "__main__":
    unittest.main()
