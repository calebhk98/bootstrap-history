"""stock_supply: a producer's supply curve over the price out of its stock, and the content price it is centred on."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy.stock_supply import STOCK_PRICE_SLOPE, StockCurve, content_price
from sim.economy.types import Offer

HELD = 10.0
TARGET = 4.0
CONTENT = 2.0


def make_curve(held=HELD, target=TARGET, content=CONTENT):
    return StockCurve(Offer("producer:a", "grain_kg", "area", "tile", held, 1.0), target, content)


class StockCurveLevels(unittest.TestCase):
    def test_at_the_content_price_the_level_kept_is_the_target(self):
        self.assertAlmostEqual(make_curve().level_at(CONTENT), TARGET)

    def test_at_the_content_price_the_supply_is_held_less_target(self):
        self.assertAlmostEqual(make_curve().supply_at(CONTENT), HELD - TARGET)

    def test_no_price_keeps_an_unbounded_stock_and_supplies_nothing(self):
        curve = make_curve()
        self.assertEqual(curve.level_at(0.0), math.inf)
        self.assertEqual(curve.supply_at(0.0), 0.0)

    def test_supply_is_zero_at_the_lowest_price_and_all_of_the_offer_at_the_highest(self):
        curve = make_curve()
        self.assertAlmostEqual(curve.lowest_price, CONTENT * math.exp(STOCK_PRICE_SLOPE * (1.0 - HELD / TARGET)))
        self.assertAlmostEqual(curve.highest_price, CONTENT * math.exp(STOCK_PRICE_SLOPE))
        self.assertAlmostEqual(curve.supply_at(curve.lowest_price), 0.0)
        self.assertAlmostEqual(curve.supply_at(curve.highest_price), HELD)

    def test_supply_is_flat_outside_the_two_prices(self):
        curve = make_curve()
        self.assertEqual(curve.supply_at(curve.lowest_price * 0.5), 0.0)
        self.assertEqual(curve.supply_at(curve.highest_price * 2.0), HELD)

    def test_supply_rises_with_the_price(self):
        curve = make_curve()
        low, middle, high = [curve.lowest_price + share * (curve.highest_price - curve.lowest_price) for share in (0.25, 0.5, 0.75)]
        self.assertLess(curve.supply_at(low), curve.supply_at(middle))
        self.assertLess(curve.supply_at(middle), curve.supply_at(high))


class StockCurveFloor(unittest.TestCase):
    """A pile many times the target: the curve alone would let units go for next to nothing; the floor price stops it."""

    def setUp(self):
        self.floor = CONTENT * 0.8
        self.curve = StockCurve(Offer("producer:a", "grain_kg", "area", "tile", 100.0 * TARGET, 1.0), TARGET, CONTENT, self.floor)

    def test_without_a_floor_the_lowest_price_of_a_large_pile_is_far_under_the_content_price(self):
        bare = StockCurve(self.curve.offer, TARGET, CONTENT)
        self.assertLess(bare.lowest_price, CONTENT * 1e-6)

    def test_the_lowest_price_is_the_floor_price(self):
        self.assertAlmostEqual(self.curve.lowest_price, self.floor)

    def test_under_the_floor_price_nothing_is_let_go(self):
        self.assertEqual(self.curve.supply_at(self.floor * 0.99), 0.0)
        self.assertEqual(self.curve.level_at(self.floor * 0.99), math.inf)

    def test_at_the_floor_price_the_curves_own_units_are_let_go(self):
        kept = TARGET * (1.0 - math.log(self.floor / CONTENT) / STOCK_PRICE_SLOPE)
        self.assertAlmostEqual(self.curve.supply_at(self.floor), 100.0 * TARGET - kept)

    def test_a_floor_under_the_curves_own_lowest_price_changes_nothing(self):
        small = StockCurve(Offer("producer:a", "grain_kg", "area", "tile", HELD, 1.0), TARGET, CONTENT, CONTENT * 0.01)
        self.assertAlmostEqual(small.lowest_price, make_curve().lowest_price)
        self.assertAlmostEqual(small.supply_at(CONTENT), make_curve().supply_at(CONTENT))

    def test_the_highest_price_is_never_under_the_floor_price(self):
        high = StockCurve(Offer("producer:a", "grain_kg", "area", "tile", HELD, 1.0), TARGET, CONTENT, CONTENT * 5.0)
        self.assertAlmostEqual(high.highest_price, CONTENT * 5.0)
        self.assertAlmostEqual(high.supply_at(high.highest_price), HELD)


class StockCurveOffer(unittest.TestCase):
    def test_the_offer_carries_the_units_let_go_at_the_price_as_its_reservation(self):
        curve = make_curve()
        price = 2.1
        offer = curve.offer_at(price)
        self.assertAlmostEqual(offer.quantity, curve.supply_at(price))
        self.assertAlmostEqual(offer.reservation_price, price)
        self.assertEqual((offer.seller, offer.good, offer.area, offer.tile), ("producer:a", "grain_kg", "area", "tile"))

    def test_above_the_highest_price_the_reservation_is_the_highest_price(self):
        curve = make_curve()
        offer = curve.offer_at(curve.highest_price * 3.0)
        self.assertAlmostEqual(offer.reservation_price, curve.highest_price)
        self.assertAlmostEqual(offer.quantity, HELD)


class ContentPrice(unittest.TestCase):
    def test_a_posted_reservation_at_or_above_the_carrying_value_leaves_the_expected_price(self):
        self.assertEqual(content_price(5.0, 6.0, 6.0), 5.0)
        self.assertEqual(content_price(5.0, 9.0, 6.0), 5.0)

    def test_a_posted_reservation_under_the_carrying_value_scales_the_price_down(self):
        self.assertAlmostEqual(content_price(5.0, 3.0, 6.0), 5.0 * 3.0 / 6.0)

    def test_a_negative_posted_reservation_gives_nothing(self):
        self.assertEqual(content_price(5.0, -1.0, 6.0), 0.0)

    def test_a_carrying_value_not_positive_leaves_the_expected_price(self):
        self.assertEqual(content_price(5.0, 3.0, 0.0), 5.0)
        self.assertEqual(content_price(5.0, 3.0, -2.0), 5.0)


if __name__ == "__main__":
    unittest.main()
