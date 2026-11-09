"""`settlement_number_kernel` and `settlement_note_kernel` against the plain numpy rules they replaced (`settlement_ids_plain.py`) on random
inputs, and `numpy_sum` against `ndarray.sum` at lengths either side of the 8, 128 and recursion boundaries."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

import numpy

from sim.economy import settlement_note_kernel as note_kernel
from sim.economy import settlement_number_kernel as number_kernel
from sim.tests import settlement_ids_plain as plain


def random_batch(seed):
    """(pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bids, offers) of up to four markets on random agents and tiles."""
    rng = random.Random(seed)
    bid_rows, offer_rows, pair_bid, pair_offer, pair_ptr = [], [], [], [], [0]
    buyer, bid_tile, seller, offer_tile = [], [], [], []
    for _ in range(rng.randrange(1, 5)):
        first_bid, first_offer = len(bid_rows), len(offer_rows)
        for _ in range(rng.randrange(1, 6)):
            bid_rows.append(len(buyer))
            buyer.append(rng.randrange(8))
            bid_tile.append(rng.choice((0, 1, 2, 3)))        # tile 3 is the empty tile
        for _ in range(rng.randrange(1, 4)):
            offer_rows.append(len(seller))
            seller.append(rng.randrange(4, 12))
            offer_tile.append(rng.choice((0, 1, 2)))
        for _ in range(rng.randrange(1, 7)):
            pair_bid.append(first_bid + rng.randrange(len(bid_rows) - first_bid))
            pair_offer.append(first_offer + rng.randrange(len(offer_rows) - first_offer))
        pair_ptr.append(len(pair_bid))
    bids = SimpleNamespace(buyer=numpy.array(buyer, dtype=numpy.int64), tile=numpy.array(bid_tile, dtype=numpy.int64))
    offers = SimpleNamespace(seller=numpy.array(seller, dtype=numpy.int64), tile=numpy.array(offer_tile, dtype=numpy.int64))
    markets = len(pair_ptr) - 1
    slots = numpy.array(sorted(rng.sample(range(markets), rng.randrange(1, markets + 1))), dtype=numpy.int64)
    return (numpy.array(pair_ptr, dtype=numpy.int64), slots, numpy.array(pair_bid, dtype=numpy.int64),
            numpy.array(pair_offer, dtype=numpy.int64), numpy.array(bid_rows, dtype=numpy.int64),
            numpy.array(offer_rows, dtype=numpy.int64), bids, offers)


class NumberGood(unittest.TestCase):

    def test_the_kernel_numbers_keys_and_agents_as_the_numpy_rules_do(self):
        for seed in range(300):
            pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bids, offers = random_batch(seed)
            answer = number_kernel.number_good(pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bids.buyer, bids.tile,
                                               offers.seller, offers.tile, 4, 3)
            wanted = plain.number_good(pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bids, offers, 4, 3)
            self.assertEqual(len(answer), len(wanted))
            for index, (got, expected) in enumerate(zip(answer, wanted)):
                self.assertEqual(numpy.asarray(got).tolist(), numpy.asarray(expected).tolist(), (seed, index))

    def test_first_use_numbers_values_by_first_appearance(self):
        numbers, distinct = number_kernel.first_use(numpy.array([9, 4, 9, 7, 4], dtype=numpy.int64))
        self.assertEqual((numbers.tolist(), distinct.tolist()), ([0, 1, 0, 2, 1], [9, 4, 7]))

    def test_pair_positions_list_the_pairs_of_the_chosen_markets_one_after_another(self):
        sizes, positions = number_kernel.pair_positions(numpy.array([0, 2, 2, 5, 6]), numpy.array([3, 0, 2]))
        self.assertEqual((sizes.tolist(), positions.tolist()), ([1, 2, 3], [5, 0, 1, 2, 3, 4]))


class NumpySum(unittest.TestCase):

    def test_the_kernel_sum_is_the_bits_numpy_gives_at_every_length(self):
        rng = numpy.random.default_rng(5)
        for count in list(range(0, 300)) + [511, 512, 513, 1000, 4097]:
            values = rng.uniform(-1e3, 1e3, count + 3) * rng.choice([1.0, 1e-7, 1e9], count + 3)
            first = 2
            self.assertEqual(number_kernel.numpy_sum(values, first, first + count), values[first:first + count].sum(), count)

    def test_delivered_by_market_sums_each_market_on_its_own(self):
        goods = numpy.array([0.1, 0.2, 0.3, 1.0, 2.0])
        self.assertEqual(number_kernel.delivered_by_market(goods, numpy.array([0, 3, 3, 5])).tolist(),
                         [goods[:3].sum(), 0.0, goods[3:].sum()])


class NoteColumns(unittest.TestCase):

    def test_the_kernel_makes_the_ledger_columns_the_numpy_code_made(self):
        for seed in range(200):
            rng = numpy.random.default_rng(seed)
            counts = rng.integers(1, 5, rng.integers(1, 4))
            agent_offset = numpy.concatenate(([0], numpy.cumsum(counts))).astype(numpy.int64)
            rows = int(agent_offset[-1])
            slots = numpy.sort(rng.choice(8, len(counts), replace=False)).astype(numpy.int64)
            agent = rng.integers(0, 12, rows).astype(numpy.int64)
            paid = rng.choice([0.0, 2.5], rows)
            got, was_buyer = rng.random(rows) < 0.5, rng.random(rows) < 0.5
            net, units = rng.uniform(0, 5, rows), rng.uniform(0, 5, rows)
            imports, exports = rng.choice([0.0, 0.0, 1.5], rows), rng.choice([0.0, 0.0, 0.0, 2.5], rows)
            makers = numpy.sort(rng.choice(12, 3, replace=False)).astype(numpy.int64)
            args = (agent_offset, slots, agent, paid, got, was_buyer, net, units, imports, exports, makers, 2, 5)
            answer = note_kernel.note_columns(*args)
            wanted = plain.note_columns(*args, code=(note_kernel.FOREIGN_MARKET, note_kernel.FOREIGN_MARKET))
            for index, (got_column, expected) in enumerate(zip(answer, wanted)):
                self.assertEqual(numpy.asarray(got_column).tolist(), numpy.asarray(expected).tolist(), (seed, index))


if __name__ == "__main__":
    unittest.main()
