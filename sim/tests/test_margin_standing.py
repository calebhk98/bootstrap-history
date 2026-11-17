"""The margin's standing moves continuously with the expected price and entry is in proportion to it (Complaint 473)."""
QUICK_TOPIC = True

import unittest

from sim.economy import entry_margin
from sim.economy.entry_margin_kernel import margin_draw_of, margin_share_of, standing_after
from sim.economy.entry_trial import ENTRY_PRICE_MARGIN_SHARE
from sim.economy.producers_close import LOSS_YEARS_BEFORE_EXIT

ENTRY_PRICE = 12.5
COST = ENTRY_PRICE / (1.0 + ENTRY_PRICE_MARGIN_SHARE)
HAIR = 1e-9


def price_a_margin_above_entry():
    return ENTRY_PRICE + (ENTRY_PRICE - COST)


class MarginStandingTests(unittest.TestCase):
    def test_a_hair_above_and_a_hair_below_the_entry_price_give_standings_a_hair_apart(self):
        above = entry_margin.margin_standing(2.0, ENTRY_PRICE + HAIR, ENTRY_PRICE)
        below = entry_margin.margin_standing(2.0, ENTRY_PRICE - HAIR, ENTRY_PRICE)
        self.assertAlmostEqual(above, below, delta=1e-6)

    def test_a_price_at_the_entry_price_leaves_the_standing_where_it_was(self):
        self.assertAlmostEqual(entry_margin.margin_standing(1.5, ENTRY_PRICE, ENTRY_PRICE), 1.5)

    def test_a_price_a_whole_margin_above_the_entry_price_adds_a_year(self):
        self.assertAlmostEqual(entry_margin.margin_standing(1.0, price_a_margin_above_entry(), ENTRY_PRICE), 2.0)

    def test_a_price_at_cost_takes_a_year_off(self):
        self.assertAlmostEqual(entry_margin.margin_standing(2.0, COST, ENTRY_PRICE), 1.0)

    def test_the_standing_stays_between_nothing_and_the_wait(self):
        self.assertEqual(entry_margin.margin_standing(0.5, 0.0, ENTRY_PRICE), 0.0)
        self.assertEqual(entry_margin.margin_standing(LOSS_YEARS_BEFORE_EXIT, 1e9, ENTRY_PRICE), LOSS_YEARS_BEFORE_EXIT)

    def test_a_clear_margin_held_for_the_wait_reaches_the_wait(self):
        standing = 0.0
        for _year in range(LOSS_YEARS_BEFORE_EXIT):
            standing = entry_margin.margin_standing(standing, 2.0 * ENTRY_PRICE, ENTRY_PRICE)
        self.assertEqual(standing, LOSS_YEARS_BEFORE_EXIT)

    def test_an_entry_price_that_is_not_positive_leaves_nothing(self):
        self.assertEqual(entry_margin.margin_standing(2.0, 5.0, 0.0), 0.0)


class MarginShareTests(unittest.TestCase):
    def test_nothing_below_the_wait_less_a_year(self):
        self.assertEqual(entry_margin.margin_share(LOSS_YEARS_BEFORE_EXIT - 1.0), 0.0)
        self.assertEqual(entry_margin.margin_share(0.0), 0.0)

    def test_all_at_the_wait(self):
        self.assertEqual(entry_margin.margin_share(float(LOSS_YEARS_BEFORE_EXIT)), 1.0)

    def test_half_midway(self):
        self.assertAlmostEqual(entry_margin.margin_share(LOSS_YEARS_BEFORE_EXIT - 0.5), 0.5)

    def test_never_outside_nought_to_one(self):
        self.assertEqual(entry_margin.margin_share(-3.0), 0.0)
        self.assertEqual(entry_margin.margin_share(LOSS_YEARS_BEFORE_EXIT + 4.0), 1.0)


class KernelTwinTests(unittest.TestCase):
    def test_the_standing_is_the_plain_standing(self):
        for standing in (0.0, 0.7, 2.0, float(LOSS_YEARS_BEFORE_EXIT)):
            for expected_price in (0.0, COST, ENTRY_PRICE - HAIR, ENTRY_PRICE, 13.0, price_a_margin_above_entry(), 99.0):
                self.assertEqual(standing_after(standing, expected_price, ENTRY_PRICE), entry_margin.margin_standing(standing, expected_price, ENTRY_PRICE))
        self.assertEqual(standing_after(2.0, 5.0, 0.0), entry_margin.margin_standing(2.0, 5.0, 0.0))

    def test_the_share_is_the_plain_share(self):
        for standing in (-1.0, 0.0, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
            self.assertEqual(margin_share_of(standing), entry_margin.margin_share(standing))


class MarginDrawTests(unittest.TestCase):
    def test_a_price_at_the_entry_price_draws_nothing(self):
        self.assertEqual(entry_margin.margin_draw(ENTRY_PRICE, ENTRY_PRICE), 0.0)
        self.assertEqual(entry_margin.margin_draw(COST, ENTRY_PRICE), 0.0)

    def test_a_price_a_whole_margin_above_draws_all_and_no_more(self):
        self.assertAlmostEqual(entry_margin.margin_draw(price_a_margin_above_entry(), ENTRY_PRICE), 1.0)
        self.assertEqual(entry_margin.margin_draw(100.0 * ENTRY_PRICE, ENTRY_PRICE), 1.0)

    def test_half_a_margin_above_draws_half(self):
        self.assertAlmostEqual(entry_margin.margin_draw(ENTRY_PRICE + 0.5 * (ENTRY_PRICE - COST), ENTRY_PRICE), 0.5)

    def test_a_hair_above_the_entry_price_draws_a_hair(self):
        self.assertLess(entry_margin.margin_draw(ENTRY_PRICE * (1.0 + HAIR), ENTRY_PRICE), 1e-6)

    def test_an_entry_price_that_is_not_positive_draws_nothing(self):
        self.assertEqual(entry_margin.margin_draw(5.0, 0.0), 0.0)

    def test_the_kernel_gives_the_same_draw(self):
        for price in (COST, ENTRY_PRICE, ENTRY_PRICE * 1.01, ENTRY_PRICE * 1.1, price_a_margin_above_entry(), 40.0):
            self.assertEqual(margin_draw_of(price, ENTRY_PRICE), entry_margin.margin_draw(price, ENTRY_PRICE))


if __name__ == "__main__":
    unittest.main()
