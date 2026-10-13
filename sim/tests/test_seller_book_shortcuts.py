"""Two shortcuts in goods clearing give the answers of the plain search to within rounding: a seller whose only
offer is the one priced (sales read from the supply below it), and a crossing that sits on a buyer's price
ceiling (found by bisecting the ceilings instead of the whole price range)."""

QUICK_TOPIC = True

import math
import random
import unittest
from dataclasses import replace

from sim.economy import goods_market, goods_market_solve, seller_book
from sim.economy.types import Bid, Offer

from .test_seller_pricing_probe import AREA, GOOD, SELLER, random_market

RELATIVE = 1e-9


def alone(seed):
    """A random market where the seller has no offer but the one being priced."""
    bids, rivals, offer, last_price = random_market(seed)
    return bids, [rival for rival in rivals if rival.seller != SELLER], offer, last_price


class SoleOfferBook(unittest.TestCase):
    def test_sales_and_price_match_the_clearing_for_every_reservation(self):
        for seed in range(300):
            bids, rivals, offer, last_price = alone(seed)
            buyers = goods_market.Buyers(bids, last_price)
            ordered = goods_market.in_clearing_order(rivals)
            book = seller_book.SellerBook(buyers, ordered, offer)
            asks = sorted({rival.reservation_price for rival in rivals})
            for reservation in (None, 0.0, -1.0, 1e-9, 0.4, 1.0, 1.7, 5.0, *asks, *(ask * 0.999 for ask in asks)):
                offers = ordered if reservation is None else goods_market.with_offer(
                    ordered, replace(offer, reservation_price=reservation))
                price, sold = goods_market.price_and_sold(buyers, offers, SELLER)
                got_sold, got_price = book.sold_and_price(reservation)
                self.assertAlmostEqual(got_price, price, delta=RELATIVE * max(abs(price), 1e-12), msg=(seed, reservation))
                self.assertAlmostEqual(got_sold, sold, delta=RELATIVE * max(abs(sold), 1.0), msg=(seed, reservation))

    def test_reading_whether_the_offer_moves_the_price_agrees_with_solving_it(self):
        checked = 0
        for seed in range(400):
            bids, rivals, offer, last_price = alone(seed)
            buyers = goods_market.Buyers(bids, last_price)
            book = seller_book.SellerBook(buyers, goods_market.in_clearing_order(rivals), offer)
            without, with_it = book.sold_and_price(None)[1], book.sold_and_price(0.0)[1]
            read = book.moves_the_price(without)
            if read is None:
                continue
            gap = abs(with_it - without) / max(abs(with_it), abs(without), 1e-300)
            if 0.2 * goods_market.ROUNDING_SHARE < gap < 5.0 * goods_market.ROUNDING_SHARE:
                continue    # too close to the threshold for two ways of rounding to be told apart
            checked += 1
            self.assertEqual(read, gap > goods_market.ROUNDING_SHARE, seed)
        self.assertGreater(checked, 50)


class CrossingOnACeiling(unittest.TestCase):
    def test_bisecting_the_ceilings_finds_the_price_the_plain_search_does(self):
        jumps_used = 0
        for seed in range(300):
            bids, rivals, _offer, last_price = random_market(seed)
            buyers = goods_market.Buyers(bids, last_price)
            ordered = goods_market.in_clearing_order(rivals)
            if not ordered:
                continue
            schedule = buyers.schedule
            levels, running = [], 0.0
            for rival in ordered:
                running += rival.quantity
                levels.append((max(rival.reservation_price, buyers.minimum_price), running))
            levels = sorted(levels)
            demand_at_first = schedule.total_at(levels[0][0])
            if demand_at_first <= 0.0:
                continue
            plain = goods_market_solve.solve_price(levels, schedule.total_at, demand_at_first)
            with_jumps = goods_market_solve.solve_price(levels, schedule.total_at, demand_at_first,
                                                        jumps=schedule.ceilings_ascending())
            jumps_used += bool(schedule.ceilings_ascending())
            self.assertAlmostEqual(with_jumps, plain, delta=1e-8 * plain, msg=seed)
        self.assertGreater(jumps_used, 50)


if __name__ == "__main__":
    unittest.main()
