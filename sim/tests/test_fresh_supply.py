"""fresh_supply: the supply curve over the price of a producer's good that cannot be kept a year."""

QUICK_TOPIC = True

import unittest

from sim.economy.fresh_supply import FreshCurve
from sim.economy.producers import share_working
from sim.economy.types import Offer

MADE = 1000.0
EXPECTED = 4.0


def make_curve(made=MADE, expected=EXPECTED):
    return FreshCurve(Offer("producer:baker", "bread_kg", "area", "tile", made, 0.0), expected)


class FreshCurveSupply(unittest.TestCase):
    def test_at_the_expected_price_everything_made_is_let_go(self):
        self.assertAlmostEqual(make_curve().supply_at(EXPECTED), MADE)

    def test_above_the_expected_price_everything_made_is_let_go_and_no_more(self):
        self.assertEqual(make_curve().supply_at(EXPECTED * 10.0), MADE)

    def test_under_the_expected_price_the_share_let_go_is_the_working_share_at_it_over_that_at_the_expected_price(self):
        price = EXPECTED * 0.9
        self.assertAlmostEqual(make_curve().supply_at(price), MADE * share_working(price, EXPECTED) / share_working(EXPECTED, EXPECTED))

    def test_a_tenth_off_the_expected_price_holds_back_between_a_tenth_and_a_half(self):
        let_go = make_curve().supply_at(EXPECTED * 0.9) / MADE
        self.assertLess(let_go, 0.9)
        self.assertGreater(let_go, 0.5)

    def test_supply_rises_with_the_price_up_to_the_expected_price(self):
        curve = make_curve()
        supplies = [curve.supply_at(EXPECTED * share) for share in (0.2, 0.5, 0.8, 0.95, 1.0)]
        self.assertEqual(supplies, sorted(supplies))
        self.assertLess(supplies[0], supplies[-1])

    def test_no_price_lets_nothing_go(self):
        self.assertEqual(make_curve().supply_at(0.0), 0.0)

    def test_the_highest_price_is_the_expected_price_and_the_lowest_is_nothing(self):
        curve = make_curve()
        self.assertEqual(curve.highest_price, EXPECTED)
        self.assertEqual(curve.lowest_price, 0.0)


class FreshCurveOffer(unittest.TestCase):
    def test_the_offer_carries_the_units_let_go_at_the_price_as_its_reservation(self):
        curve = make_curve()
        price = EXPECTED * 0.8
        offer = curve.offer_at(price)
        self.assertAlmostEqual(offer.quantity, curve.supply_at(price))
        self.assertAlmostEqual(offer.reservation_price, price)
        self.assertEqual((offer.seller, offer.good, offer.area, offer.tile), ("producer:baker", "bread_kg", "area", "tile"))

    def test_above_the_expected_price_the_reservation_is_the_expected_price(self):
        offer = make_curve().offer_at(EXPECTED * 3.0)
        self.assertAlmostEqual(offer.reservation_price, EXPECTED)
        self.assertAlmostEqual(offer.quantity, MADE)


if __name__ == "__main__":
    unittest.main()
