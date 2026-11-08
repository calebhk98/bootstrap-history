"""`market_curves_rows.summarize_columns` against `market_curves.summarize`: the summary of a market's own book from columns is the one
the objects give, on written-out and random books (shared keys, no ceiling, unfunded bids, the external edge's orders, sold-out offers)."""
QUICK_TOPIC = True

import math
import random
import unittest

import numpy

from sim.economy import market_curves, market_curves_rows
from sim.economy.types import EDGE_EXTERNAL, Bid, Offer


def columns_of(bids, offers):
    return market_curves_rows.summarize_columns(
        numpy.array([bid.floor_quantity for bid in bids]), numpy.array([bid.flexible_quantity for bid in bids]),
        numpy.array([bid.reference_price for bid in bids]), numpy.array([bid.elasticity for bid in bids]),
        numpy.array([bid.budget for bid in bids]), numpy.array([bid.maximum_price for bid in bids]),
        numpy.array([bid.buyer == EDGE_EXTERNAL for bid in bids], dtype=bool), numpy.array([offer.reservation_price for offer in offers]),
        numpy.array([offer.quantity for offer in offers]), numpy.array([offer.seller == EDGE_EXTERNAL for offer in offers], dtype=bool))


class SummaryFromColumnsIsSummaryFromObjects(unittest.TestCase):

    def test_a_written_out_book(self):
        bids = [Bid("a", "g", "x", "t", 2.0, 0.0, 5.0, 0.0, 10.0, 0, math.inf), Bid("b", "g", "x", "t", 1.0, 3.0, 4.0, 1.0, 9.0, 0, 8.0),
                Bid("c", "g", "x", "t", 4.0, 0.0, 7.0, 0.0, 12.0, 0, math.inf), Bid(EDGE_EXTERNAL, "g", "x", "t", 9.0, 0.0, 1.0, 0.0, 9.0, 0, 3.0),
                Bid("d", "g", "x", "t", 1.0, 0.0, 1.0, 0.0, 0.0, 0, 3.0)]
        offers = [Offer("s", "g", "x", "t", 5.0, 3.0), Offer("u", "g", "x", "t", 2.0, 3.0), Offer(EDGE_EXTERNAL, "g", "x", "t", 4.0, 1.0),
                  Offer("v", "g", "x", "t", 0.0, 2.0), Offer("w", "g", "x", "t", 1.5, 2.5)]
        self.assertEqual(columns_of(bids, offers), market_curves.summarize(bids, offers))

    def test_random_books(self):
        for seed in range(60):
            rng = random.Random(seed)
            bids = [Bid(rng.choice(("a", "b", EDGE_EXTERNAL)), "g", "x", "t", rng.choice((0.0, 1.0, 2.5)), rng.choice((0.0, 0.0, 3.0, 4.0)),
                        rng.choice((1.0, 2.0, 2.0)), rng.choice((0.0, 0.5, 1.0)), rng.choice((0.0, 5.0, 7.5, 11.0)), 0,
                        rng.choice((math.inf, math.inf, 4.0, 9.0))) for _ in range(rng.randint(0, 25))]
            offers = [Offer(rng.choice(("s", "u", EDGE_EXTERNAL)), "g", "x", "t", rng.choice((0.0, 0.1, 2.0, 7.3)), rng.choice((0.0, 1.5, 1.5, 3.0)))
                      for _ in range(rng.randint(0, 25))]
            self.assertEqual(columns_of(bids, offers), market_curves.summarize(bids, offers), seed)


if __name__ == "__main__":
    unittest.main()
