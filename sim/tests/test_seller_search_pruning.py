"""The pruned reservation search finds a reservation as profitable as trying every candidate in the band."""

QUICK_TOPIC = True

import unittest

from sim.economy import seller_pricing
from sim.economy.accounts import ROUNDING_SHARE
from sim.tests.test_seller_pricing_probe import SELLER, random_market


class SellerSearchPruning(unittest.TestCase):
    def test_pruned_search_matches_trying_every_candidate(self):
        compared = 0
        for seed in range(300):
            bids, rivals, offer, last_price = random_market(seed)
            rivals = [rival for rival in rivals if rival.seller != SELLER]
            if not seller_pricing.moves_the_price(bids, rivals, offer, last_price):
                continue
            current = max(offer.reservation_price, 0.0)
            value = 0.5 * current
            floor, ceiling = current * 0.9, current * 1.1 + 1e-9
            choice = seller_pricing.best_reservation(bids, rivals, offer, value, last_price, ceiling=ceiling,
                                                     floor=floor, current=current)
            candidates = [reservation for reservation in seller_pricing._candidates(rivals, last_price, value)
                          if floor <= reservation <= ceiling] + [floor, ceiling, current]
            profits = [seller_pricing.profit_at(bids, rivals, offer, reservation, value, last_price)
                       for reservation in candidates]
            baseline = seller_pricing.profit_at(bids, rivals, offer, current, value, last_price)
            chosen = baseline if choice is None else seller_pricing.profit_at(bids, rivals, offer, choice, value,
                                                                              last_price)
            self.assertGreaterEqual(chosen + ROUNDING_SHARE * max(abs(max(profits)), 1.0), max(profits))
            compared += 1
        self.assertGreater(compared, 30)


if __name__ == "__main__":
    unittest.main()
