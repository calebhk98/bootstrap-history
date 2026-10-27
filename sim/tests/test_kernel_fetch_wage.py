"""The kernel `markets.fetch_wage` (sim/labour/market/fetch_wage.py) called on its own samples: the same calls a mod's replacement is checked on."""

QUICK_TOPIC = True

import unittest

from sim.labour.market.fetch_wage import fetch_wage
from sim.labour.market.fetch_wage_samples import CASES, call_of, samples
from sim.markets.kernels import FETCH_WAGE, KERNELS


def answer(name):
    arguments, keywords = call_of(CASES[name])
    return fetch_wage(*arguments, **keywords)


def hours_filled(name, wage, sources):
    """Hours sold here plus those fetched from `sources` at `wage`, as the case's lookups give them."""
    arguments, _keywords = call_of(CASES[name])
    area, _wanted, _going, _top, _offers, hours_at, wanted_at, _spare_of = arguments
    return hours_at(area, wage) + sum(max(0.0, hours_at(other, wage) - wanted_at(other)) for other in sources)


class FetchWageKernelTest(unittest.TestCase):
    def test_the_workers_on_the_spot_selling_enough_need_no_fetching(self):
        self.assertIsNone(answer("enough_at_home"))

    def test_the_wage_is_the_cost_of_the_first_source_that_fills_the_shortage(self):
        self.assertEqual(answer("first_source_fills"), 1.5)

    def test_hours_rising_with_the_wage_put_the_cap_between_two_ways_in(self):
        wage = answer("bisected_between_sources")
        self.assertTrue(1.5 < wage < 4.0)
        wanted = CASES["bisected_between_sources"]["wanted"]
        self.assertGreaterEqual(hours_filled("bisected_between_sources", wage, ["b"]), wanted)
        self.assertLess(hours_filled("bisected_between_sources", wage - 1e-6, ["b"]), wanted)

    def test_a_shortage_only_a_higher_wage_fills_is_priced_up_to_the_most_a_bid_pays(self):
        wage = answer("filled_only_at_the_top")
        self.assertTrue(1.5 < wage <= CASES["filled_only_at_the_top"]["top"])
        self.assertGreaterEqual(hours_filled("filled_only_at_the_top", wage, ["b"]), CASES["filled_only_at_the_top"]["wanted"])

    def test_a_shortage_no_hands_in_reach_fill_has_no_cap(self):
        self.assertIsNone(answer("never_filled"))
        self.assertIsNone(answer("no_way_in"))

    def test_the_kernel_is_declared_with_samples_that_reach_every_branch(self):
        kernel = next(each for each in KERNELS if each.name == FETCH_WAGE)
        self.assertIs(kernel.reference, fetch_wage)
        found = [fetch_wage(*arguments, **keywords) for arguments, keywords in kernel.samples()]
        self.assertEqual(len(found), len(samples()))
        self.assertIn(None, found)
        self.assertIn(1.5, found)
        self.assertTrue(any(wage is not None and wage not in (1.5, 3.0) for wage in found))


if __name__ == "__main__":
    unittest.main()
