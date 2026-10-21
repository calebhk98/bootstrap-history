"""Complaint 473: idle plantless capacity wears with its tools' service life, and a producer sheds workplaces only when
its expected sales do not cover their running cost, however many years it has lost."""

QUICK_TOPIC = True

import unittest

from sim.economy import idle_capacity, producers, producers_close
from sim.economy.types import Recipe, ToolFallback
from sim.tests.test_economy_producers import FARM, View, farm_view, farmer

TOOLED = Recipe("farm", {"grain": 10.0}, {"seed": 2.0, "iron": 0.5}, {"hand": 5.0}, tool_wear={"iron": 0.5},
                tool_fallbacks={"iron": (ToolFallback("", 0.0, 2.5, ("hand",)),)})


class IdleWearTests(unittest.TestCase):
    def test_idle_capacity_wears_at_one_over_its_tools_service_life(self):
        self.assertAlmostEqual(idle_capacity.wear_share_per_year(TOOLED, {"iron": 20.0}), 1.0 / 20.0)
        self.assertAlmostEqual(idle_capacity.wear_share_per_year(TOOLED, {"iron": 5.0}), 1.0 / 5.0)

    def test_tools_wear_as_each_is_used_up_per_run(self):
        two_tools = Recipe("farm", {"grain": 1.0}, {"iron": 1.0, "rope": 3.0}, {"hand": 1.0}, tool_wear={"iron": 1.0, "rope": 3.0})
        share = idle_capacity.wear_share_per_year(two_tools, {"iron": 10.0, "rope": 2.0})
        self.assertAlmostEqual(share, (1.0 / 10.0 + 3.0 / 2.0) / 4.0)

    def test_a_recipe_with_no_tools_or_tools_of_no_life_has_nothing_to_wear(self):
        self.assertEqual(idle_capacity.wear_share_per_year(FARM, {"iron": 20.0}), 0.0)
        self.assertEqual(idle_capacity.wear_share_per_year(TOOLED, {}), 0.0)
        self.assertEqual(idle_capacity.wear_share_per_year(TOOLED, {"iron": 0.0}), 0.0)

    def test_a_shorter_tool_life_leaves_less_idle_capacity(self):
        view = View({"grain": 0.5, "seed": 1.0, "iron": 1.0}, {"hand": 1.0})     # a run costs 7.5 against 5: some workplaces still pay
        short = producers_close.close_year(farmer(capacity_runs=10.0), TOOLED, 100.0, 50.0, view, 4.0, None, (), {"iron": 1.0})
        long = producers_close.close_year(farmer(capacity_runs=10.0), TOOLED, 100.0, 50.0, view, 4.0, None, (), {"iron": 200.0})
        self.assertLess(short.producer.capacity_runs, long.producer.capacity_runs)


class ShedOnCostNotYearsTests(unittest.TestCase):
    def test_a_producer_whose_sales_do_not_cover_cost_sheds_in_its_first_losing_year(self):
        result = producers_close.close_year(farmer(capacity_runs=10.0, years_of_loss=0), FARM, 3.0, 70.0, farm_view(0.001), 1.0)
        self.assertEqual(result.producer.years_of_loss, 1)
        self.assertTrue(result.exited)

    def test_a_producer_the_market_still_buys_from_does_not_exit_while_its_price_is_below_cost(self):
        # the price it expects is a fraction of cost, but it still expects to sell: buyers with nobody else to
        # buy from lift the price, so the maker waits (its sales' expectation fades by itself while nothing sells)
        selling = farmer(capacity_runs=10.0, expected_sales=8.0, last_runs=0.0)
        result = producers_close.close_year(selling, FARM, 0.0, 0.0, farm_view(0.001), 0.0)
        self.assertFalse(result.exited)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_a_producer_whose_sales_cover_cost_is_never_shed_whatever_its_years_of_loss(self):
        producer = farmer(capacity_runs=10.0, years_of_loss=50)
        result = producers_close.close_year(producer, FARM, 10.0, 100.0, farm_view(2.0), 5.0)
        self.assertFalse(result.exited)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_workplaces_its_expected_sales_still_need_are_not_shed_while_some_pay(self):
        # the workplaces that pay (about a third at this price) would make less than the producer expects to sell
        view = farm_view(0.5)
        needed = farmer(capacity_runs=10.0, expected_sales=9.0, last_runs=9.0)
        idle = farmer(capacity_runs=10.0, expected_sales=0.0, last_runs=1.0)
        kept = producers_close.close_year(needed, FARM, 3.0, 70.0, view, 9.0).producer.capacity_runs
        shed = producers_close.close_year(idle, FARM, 3.0, 70.0, view, 1.0).producer.capacity_runs
        self.assertAlmostEqual(kept, 10.0)
        self.assertLess(shed, kept)

    def test_the_shed_share_is_bounded_by_the_pace_workplaces_change(self):
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 3.0, 70.0, farm_view(0.5), 1.0)
        self.assertGreaterEqual(result.producer.capacity_runs, (1.0 - producers.OUTPUT_CHANGE_SHARE_PER_YEAR) * 10.0 - 1e-9)


if __name__ == "__main__":
    unittest.main()
