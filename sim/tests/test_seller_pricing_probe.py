"""The seller's reservation search clears its market many times against the same buyers; the shortcut it
uses (buyers sorted once, no fills built) gives exactly the price and quantity a full `goods_market.clear` gives."""

QUICK_TOPIC = True

import math
import random
import unittest
from dataclasses import replace

from sim.economy import goods_market, seller_pricing
from sim.economy.types import Bid, Offer

GOOD, AREA = "cloth", "area"
SELLER = "producer:own"


def random_market(seed):
    """Buyers with floors, tiers and ceilings, several rivals (some sharing a reservation), and the seller's offer."""
    generator = random.Random(seed)
    bids = [Bid("household:%d" % index, GOOD, AREA, "tile%d" % (index % 3),
                generator.choice([0.0, generator.uniform(0.0, 5.0)]), generator.uniform(0.0, 50.0),
                generator.uniform(0.5, 2.0), generator.choice([0.5, 1.0, 1.5]), generator.uniform(0.0, 80.0),
                generator.choice([0, 0, 1]), generator.choice([math.inf, generator.uniform(0.8, 3.0)]))
            for index in range(generator.randint(0, 40))]
    asks = [generator.uniform(0.2, 2.5) for _ in range(4)]
    rivals = [Offer("producer:%d" % index, GOOD, AREA, "tile%d" % (index % 3),
                    generator.choice([0.0, generator.uniform(0.1, 40.0)]), generator.choice(asks + [-0.5]))
              for index in range(generator.randint(0, 8))]
    rivals.append(Offer(SELLER, GOOD, AREA, "tile9", generator.uniform(0.0, 5.0), generator.choice(asks)))
    offer = Offer(SELLER, GOOD, AREA, "tile0", generator.uniform(0.1, 60.0), generator.choice(asks))
    last_price = generator.choice([None, generator.uniform(0.3, 2.0)])
    return bids, rivals, offer, last_price


def by_full_clear(bids, rivals, offer, reservation, last_price):
    offers = list(rivals) + ([] if reservation is None else [replace(offer, reservation_price=reservation)])
    result = goods_market.clear(bids, offers, GOOD, AREA, "", last_price)
    sold = math.fsum(fill.quantity for fill in result.fills if fill.agent == offer.seller and fill.side == "sell")
    return result.price, sold


class ShortcutMatchesFullClear(unittest.TestCase):
    def test_price_and_sold_equal_a_full_clear_for_every_reservation(self):
        for seed in range(150):
            bids, rivals, offer, last_price = random_market(seed)
            buyers = goods_market.Buyers(bids, last_price)
            ordered = goods_market.in_clearing_order(rivals)
            for reservation in (None, 0.0, 0.4, 1.0, 1.7, 5.0):
                offers = ordered if reservation is None else goods_market.with_offer(
                    ordered, replace(offer, reservation_price=reservation))
                self.assertEqual(goods_market.price_and_sold(buyers, offers, SELLER),
                                 by_full_clear(bids, rivals, offer, reservation, last_price), (seed, reservation))

    def test_best_reservation_equals_the_search_by_full_clears(self):
        for seed in range(150):
            bids, rivals, offer, last_price = random_market(seed)
            expected = _best_by_full_clears(bids, rivals, offer, 0.3, last_price, offer.reservation_price * 1.1,
                                            offer.reservation_price * 0.9, offer.reservation_price)
            self.assertEqual(seller_pricing.best_reservation(bids, rivals, offer, 0.3, last_price,
                                                             ceiling=offer.reservation_price * 1.1,
                                                             floor=offer.reservation_price * 0.9,
                                                             current=offer.reservation_price), expected, seed)


def _best_by_full_clears(bids, rivals, offer, unit_value, last_price, ceiling, floor, current):
    """The reservation search written against `goods_market.clear` alone, as the reference."""
    without = by_full_clear(bids, rivals, offer, None, last_price)[0]
    at_zero = by_full_clear(bids, rivals, offer, 0.0, last_price)[0]
    if abs(at_zero - without) <= seller_pricing.ROUNDING_SHARE * max(abs(at_zero), abs(without)):
        return None

    def profit(reservation):
        price, sold = by_full_clear(bids, rivals, offer, reservation, last_price)
        return (price - unit_value) * sold

    best, best_profit = None, profit(current)
    for reservation in sorted({floor, ceiling, *seller_pricing._candidates(rivals, last_price, unit_value)}):
        if reservation > ceiling or reservation < floor or reservation == current:
            continue
        candidate_profit = profit(reservation)
        if candidate_profit > best_profit + seller_pricing.ROUNDING_SHARE * max(abs(best_profit), 1e-300):
            best, best_profit = reservation, candidate_profit
    return best
