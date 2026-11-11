"""A need at its satiation limit asks for no more as the price falls, so a glut clears at a lower price."""
QUICK_TOPIC = True

import math
import unittest

from sim.economy import inventory
from sim.economy.goods_market import clear_at_one_price as clear
from sim.economy.satiated_demand import bid_elasticity, is_satiated
from sim.economy.types import Bid, GoodSpec, Offer


def grain_bid(elasticity):
    return Bid("household", "grain", "area", "tile", 100.0, 100.0, 2.0, elasticity, 1e9)


def grain_offer(quantity, reservation):
    return Offer("farm", "grain", "area", "tile", quantity, reservation)


class SatiatedNeedRule(unittest.TestCase):
    def test_units_at_or_over_the_limit_are_satiated_and_under_it_are_not(self):
        self.assertTrue(is_satiated(1000.0, 100.0, 10.0))
        self.assertFalse(is_satiated(999.0, 100.0, 10.0))

    def test_a_need_with_no_limit_is_never_satiated(self):
        self.assertFalse(is_satiated(1e12, math.nan, 10.0))

    def test_a_satiated_bid_has_no_price_response_and_another_keeps_the_substitution(self):
        self.assertEqual(bid_elasticity(2.0, True), 0.0)
        self.assertEqual(bid_elasticity(2.0, False), 2.0)


class AGlutLowersTheClearingPrice(unittest.TestCase):
    def test_a_satiated_buyer_clears_a_glut_below_the_price_an_uncapped_one_holds_up(self):
        offers = [grain_offer(150.0, 0.5), grain_offer(150.0, 1.0)]
        uncapped = clear([grain_bid(2.0)], offers, "grain", "area", "coin", 2.0)
        satiated = clear([grain_bid(bid_elasticity(2.0, True))], offers, "grain", "area", "coin", 2.0)
        self.assertLess(satiated.price, uncapped.price)

    def test_a_satiated_buyer_never_takes_more_than_its_capped_units(self):
        offers = [grain_offer(500.0, 0.1)]
        result = clear([grain_bid(bid_elasticity(2.0, True))], offers, "grain", "area", "coin", 2.0)
        self.assertLessEqual(result.quantity, 200.0 + 1e-9)


class ASurplusIsCarriedNotDestroyed(unittest.TestCase):
    def test_unsold_grain_loses_only_its_spoilage_share_and_the_rest_stays_with_the_holder(self):
        specs = {"grain": GoodSpec("grain", 1.0, 0.2, 0.0, "food")}
        moves = inventory.spoilage_moves({("farm", "grain", "tile"): 1000.0}, specs)
        self.assertEqual(sum(move.quantity for move in moves), 200.0)

    def test_a_holder_with_no_buyer_this_year_still_values_a_unit_at_what_it_nets_next_year(self):
        reservation = inventory.holding_reservation(10.0, 0.05, 0.2, 0.0)
        self.assertAlmostEqual(reservation, 10.0 * 0.8 / 1.05)
        self.assertGreater(reservation, 0.0)
