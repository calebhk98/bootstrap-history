"""Time the economy's market clearing and settlement at several market shapes.

    python3 sim/economy_timing.py [--repeat N] [--shapes 5x3,50x20,...]

Prints milliseconds per call for clear() and settle_goods() at each (bids x offers) shape.
Timings depend on the machine; nothing here asserts a speed.
"""
import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim.economy.accounts import Book  # noqa: E402
from sim.economy.goods_market import clear  # noqa: E402
from sim.economy.settlement import settle_goods  # noqa: E402
from sim.economy.types import EDGE_MINT, EDGE_PRODUCTION, Bid, GoodsMove, Offer, Transfer  # noqa: E402

DEFAULT_SHAPES = "5x3,50x20,300x5,1000x10"


def make_market(bid_count, offer_count, seed=7):
    """A market whose demand crosses supply inside the offers' price range."""
    rng = random.Random(seed)
    classes = [(1.0, 0.8), (1.5, 1.2), (2.5, 0.6)]
    bids = []
    for number in range(bid_count):
        reference, elasticity = classes[number % len(classes)]
        bids.append(Bid("buyer%d" % number, "grain", "area", "tile%d" % (number % 90), rng.uniform(0.5, 2.0),
                        rng.uniform(1.0, 6.0), reference, elasticity, rng.uniform(50.0, 400.0), number % 2))
    offers = [Offer("seller%d" % number, "grain", "area", "farm%d" % number,
                    rng.uniform(0.3, 1.0) * 3.5 * bid_count / offer_count, rng.uniform(0.4, 2.0))
              for number in range(offer_count)]
    return bids, offers


def funded_book(bids, offers, result):
    book = Book()
    for bid in bids:
        book.transfer(Transfer(EDGE_MINT, bid.buyer, "coin", 1e6, "opening"))
    for offer in offers:
        book.move(GoodsMove(EDGE_PRODUCTION, offer.seller, "grain", offer.tile, offer.quantity, "harvest"))
    return book


def best_of(function, repeat):
    best = float("inf")
    for _ in range(repeat):
        start = time.perf_counter()
        function()
        best = min(best, time.perf_counter() - start)
    return best * 1000.0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repeat", type=int, default=20, help="calls per shape; the fastest is reported")
    parser.add_argument("--shapes", default=DEFAULT_SHAPES, help="comma list of BIDSxOFFERS")
    args = parser.parse_args(argv)
    print("%-12s %12s %16s" % ("bids x offers", "clear ms", "settle_goods ms"))
    for shape in args.shapes.split(","):
        bid_count, offer_count = (int(part) for part in shape.split("x"))
        bids, offers = make_market(bid_count, offer_count)
        result = clear(bids, offers, "grain", "area", "coin", None)
        clear_ms = best_of(lambda: clear(bids, offers, "grain", "area", "coin", None), args.repeat)
        settle_times = []
        for _ in range(args.repeat):
            book = funded_book(bids, offers, result)
            start = time.perf_counter()
            settle_goods(book, result)
            settle_times.append(time.perf_counter() - start)
        print("%-12s %12.3f %16.3f" % (shape, clear_ms, min(settle_times) * 1000.0))


if __name__ == "__main__":
    main()
