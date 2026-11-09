"""Numba port, the year's cohort orders for a basket with share limits: `households_orders_pack.kernel_orders` makes the orders of a basket
whose goods declare `max_share_of_need` (the quality re-mix searches the limits, `households_orders_kernel._remix`), agreeing with the old
per-cohort path (`households.goods_orders`) on random cohorts. The baskets of `test_opening_demand_kernel` with limits on the goods of
light and food; no game."""

QUICK_TOPIC = True

import copy
import dataclasses
import random
import unittest
from unittest import mock

from sim.economy import households, households_orders_pack
from sim.tests import test_opening_demand_kernel as opening_tests
from sim.tests import test_year_speed_cohort_orders as year_tests

LIMITED_DATA = copy.deepcopy(opening_tests.NEED_DATA)
LIMITED_DATA["goods"]["tallow"]["max_share_of_need"] = {"light": 0.3}
LIMITED_DATA["goods"]["oil"]["max_share_of_need"] = {"light": 0.45}
LIMITED_DATA["goods"]["millet"]["max_share_of_need"] = {"food": 0.25}


class LimitedBasketTests(unittest.TestCase):
    def test_kernel_and_old_path_agree_on_baskets_with_limits(self):
        rng = random.Random(8)
        compared = skipped = binding = 0
        for _case in range(60):
            with mock.patch.object(opening_tests, "NEED_DATA", LIMITED_DATA):
                basket, view, cohorts = year_tests.year_world(rng)
            year_tests.stores.clear()
            units = year_tests.random_units(rng, cohorts, basket)
            priceds = [households.need_prices(basket, view, cohort.tile) for cohort in cohorts]
            cashes = [cohort.last_year_income * rng.uniform(0.3, 2.5) for cohort in cohorts]
            incomes = [cohort.last_year_income * rng.uniform(0.5, 1.5) for cohort in cohorts]
            cohorts = [dataclasses.replace(cohort, last_year_income=cohort.last_year_income * rng.choice([0.0, 1.0])) for cohort in cohorts]
            got, _planned = year_tests.kernel(cohorts, [basket] * len(cohorts), priceds, view, cashes, incomes,
                                              [units[cohort.agent_id] for cohort in cohorts], True)
            for cohort, priced, cash, income in zip(cohorts, priceds, cashes, incomes):
                grown = units[cohort.agent_id]
                expected = year_tests.reference(cohort, basket, priced, view, cash, income, grown, True)
                if not year_tests.is_stable(cohort, basket, priced, view, cash, income, grown, True, expected):
                    skipped += 1
                    continue
                year_tests.same_orders(self, got[cohort.agent_id], expected)
                compared += 1
                binding += any(need.spec.share_limits and any(good in dict(need.spec.share_limits) for good, *_rest in need.goods)
                               for need in priced)
        self.assertGreaterEqual(compared, 0.8 * (compared + skipped), "most cases are compared (%d skipped)" % skipped)
        self.assertGreater(binding, 20, "baskets with limits are exercised")


if __name__ == "__main__":
    unittest.main()
