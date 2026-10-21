"""The unsold-stock search skips its bisection when every searched ask shares one floor and the buyers want, at
that floor's price, less than the searched offers hold: it returns what the bisection would (the asks at the
floor). Built books against a copy of the search without the shortcut."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import goods_market, unsold_search
from sim.economy.types import Bid, Offer

GOOD, AREA = "grain", "area"


def search_without_the_shortcut(bids, offers, floors, buyers, last_price):
    searched = list(floors)

    def trial(level):
        candidate = unsold_search._with_level(offers, {index: floors[index] for index in searched}, level)
        sold = goods_market.sold_by_seller(buyers, candidate)
        return candidate, [index for index in unsold_search._unsold(sold, candidate, searched)
                           if candidate[index].reservation_price > floors[index]]

    low = min(floors[index] for index in searched)
    best = trial(low)
    high = max(offers[index].reservation_price for index in searched)
    ceiling = high
    while high - low > unsold_search.SEARCH_PRECISION * (high if low > 0.0 else ceiling):
        middle = math.sqrt(low) * math.sqrt(high) if low > 0.0 else 0.5 * (low + high)
        attempt = trial(middle)
        if attempt[1]:
            high = middle
        else:
            low, best = middle, attempt
    return best[0], goods_market.clear(bids, best[0], GOOD, AREA, "coin", last_price, buyers)


def book(generator):
    bids = [Bid("buyer%d" % index, GOOD, AREA, "tile", generator.choice([0.0, 2.0]), generator.uniform(0.0, 30.0),
                generator.uniform(0.5, 3.0), generator.uniform(0.3, 2.0), generator.uniform(5.0, 400.0),
                generator.choice([0, 1]), generator.choice([4.0, 1e9]))
            for index in range(generator.randint(1, 6))]
    offers = [Offer("seller%d" % index, GOOD, AREA, generator.choice(["tile", "tile", "other"]),
                    generator.uniform(0.5, 40.0), generator.choice([0.0, 0.7, 1.0, 1.6, 2.5, 4.0, 8.0]))
              for index in range(generator.randint(1, 6))]
    return bids, offers


class FloorShortcutTests(unittest.TestCase):
    def test_equals_the_bisection(self):
        generator = random.Random(5)
        skipped = searched = 0
        for _case in range(1500):
            bids, offers = book(generator)
            last_price = generator.choice([None, 1.2])
            buyers = goods_market.Buyers(bids, last_price)
            shared = generator.choice([0.0, 0.3, 0.7, 1.0])
            floors = {index: (shared if generator.random() < 0.8 else generator.choice([0.2, 0.5]))
                      for index, offer in enumerate(offers) if offer.reservation_price > 0.7 and generator.random() < 0.8}
            floors = {index: floor for index, floor in floors.items() if offers[index].reservation_price > floor}
            if not floors:
                continue
            result = goods_market.clear(bids, offers, GOOD, AREA, "coin", last_price, buyers)
            if not unsold_search._unsold(unsold_search._sold_by_offer(result, offers), offers, list(floors)):
                continue
            searched += 1
            skipped += unsold_search.unsold_above_the_floor(buyers, offers, floors)
            expected = search_without_the_shortcut(bids, offers, floors, buyers, last_price)
            actual = unsold_search.search_asks(bids, offers, floors, buyers, GOOD, AREA, "coin", last_price)
            self.assertEqual(actual, expected)
        self.assertGreater(skipped, 20)
        self.assertGreater(searched, skipped)


if __name__ == "__main__":
    unittest.main()
