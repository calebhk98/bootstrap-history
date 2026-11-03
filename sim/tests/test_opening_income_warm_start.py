"""settled_income_per_head (sim/economy/opening_income.py): a start taken from a nearby root finds the same root in fewer asks."""

QUICK_TOPIC = True

import unittest

from sim.economy.opening_income import OPENING_INCOME_TOLERANCE, settled_income_per_head

CEILING = 1000.0
PEOPLE = 1.0


def asks_of(buys):
    """(demand_at, asked): `demand_at` gives `buys(income)` with a labour share of one half, and `asked` lists the incomes asked."""
    asked = []

    def demand_at(income):
        asked.append(income)
        return buys(income), 0.5
    return demand_at, asked


def jump_at_kink(income):
    """Households spend all of an income up to 100 and a fifth less of it above: unspent income jumps at 100."""
    return income if income <= 100.0 else 0.8 * income


def saves_twice(income):
    """Households save between 100 and 150 and again from 900, and spend all of any other income."""
    return 0.8 * income if 100.0 < income < 150.0 or income >= 900.0 else income


class WarmStart(unittest.TestCase):
    def test_a_start_near_the_root_finds_the_cold_root_in_fewer_asks(self):
        cold_demand, cold_asked = asks_of(jump_at_kink)
        cold = settled_income_per_head(CEILING, PEOPLE, cold_demand)
        for start in (99.0, 99.7, 100.0, 100.3, 101.0):
            warm_demand, warm_asked = asks_of(jump_at_kink)
            warm = settled_income_per_head(CEILING, PEOPLE, warm_demand, start)
            self.assertAlmostEqual(warm[0], cold[0], delta=2.0 * OPENING_INCOME_TOLERANCE * cold[0])
            self.assertLess(len(warm_asked), len(cold_asked))

    def test_the_root_is_within_the_tolerance_of_the_jump(self):
        demand, _asked = asks_of(jump_at_kink)
        income, _share = settled_income_per_head(CEILING, PEOPLE, demand, 98.0)
        self.assertLessEqual(income, 100.0)
        self.assertGreaterEqual(income, 100.0 * (1.0 - OPENING_INCOME_TOLERANCE))

    def test_a_start_too_far_to_bracket_falls_back_to_the_search_from_the_ceiling(self):
        cold_demand, _cold_asked = asks_of(jump_at_kink)
        cold = settled_income_per_head(CEILING, PEOPLE, cold_demand)
        for start in (0.001, 600.0):
            demand, _asked = asks_of(jump_at_kink)
            found = settled_income_per_head(CEILING, PEOPLE, demand, start)
            self.assertAlmostEqual(found[0], cold[0], delta=2.0 * OPENING_INCOME_TOLERANCE * cold[0])

    def test_a_start_under_a_lower_root_does_not_hide_the_largest_one(self):
        cold_demand, _asked = asks_of(saves_twice)
        cold = settled_income_per_head(CEILING, PEOPLE, cold_demand)
        warm_demand, _warm_asked = asks_of(saves_twice)
        warm = settled_income_per_head(CEILING, PEOPLE, warm_demand, 101.0)
        self.assertGreater(cold[0], 800.0)
        self.assertAlmostEqual(warm[0], cold[0], delta=2.0 * OPENING_INCOME_TOLERANCE * cold[0])

    def test_a_start_at_or_above_the_ceiling_is_ignored(self):
        demand, asked = asks_of(lambda income: income)
        self.assertEqual(settled_income_per_head(CEILING, PEOPLE, demand, CEILING)[0], CEILING)
        self.assertEqual(asked, [CEILING])


if __name__ == "__main__":
    unittest.main()
