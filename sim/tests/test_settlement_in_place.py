"""`settlement_batch_kernel.settle_markets` (markets settled in place on shared scratch) against `settlement_kernel.settle_pairs` run market
after market with the purses and stocks carried between them, on random batches with short stocks, short purses, edge, mint and
external agents, negative asks and tied quantities; and `settlement_number_kernel.market_keys` on markets wide enough to take the
sorting path."""
QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import settlement_batch_kernel as batch
from sim.economy import settlement_kernel as single
from sim.economy import settlement_number_kernel as number_kernel
from sim.tests.test_settlement_number_kernel import random_batch


def reference(pair_offset, agent_offset, key_offset, buyer_key, seller_key, quantity, ask, key_agent, key_global, agent_global, stock_state,
              cash_state, flags, delivers, sale):
    """Per market: `settle_pairs` on copies of what the market's keys and agents hold, the carried state updated after each market."""
    stock_state, cash_state = stock_state.copy(), cash_state.copy()
    answers = []
    for market in range(len(pair_offset) - 1):
        pairs = slice(pair_offset[market], pair_offset[market + 1])
        agents_here = agent_global[agent_offset[market]:agent_offset[market + 1]]
        keys_here = key_global[key_offset[market]:key_offset[market + 1]]
        if pairs.stop == pairs.start:
            answers.append(None)
            continue
        answer = single.settle_pairs(buyer_key[pairs], seller_key[pairs], quantity[pairs], ask[pairs], delivers, sale,
                                     key_agent[key_offset[market]:key_offset[market + 1]], stock_state[keys_here], cash_state[agents_here],
                                     *[flag[agents_here] for flag in flags])
        answers.append(answer)
        cash_state[agents_here] = cash_state[agents_here] - answer[3] + answer[4]
        if delivers:
            stock_state[keys_here] = stock_state[keys_here] - answer[12] + answer[13]
    return answers, stock_state, cash_state


class SettleMarkets(unittest.TestCase):

    def test_the_batch_kernel_gives_the_per_market_kernels_bits(self):
        for seed in range(150):
            rng = random.Random(seed)
            pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bids, offers = random_batch(seed)
            (positions, pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent, holder, tile,
             agents, sold_from) = number_kernel.number_good(pair_ptr, slots, pair_bid, pair_offer, bid_rows, offer_rows, bids.buyer,
                                                            bids.tile, offers.seller, offers.tile, 4, 3)
            pairs, keys, batch_agents = len(positions), len(holder), len(agents)
            quantity = numpy.array([rng.choice((0.0, 1.0, 1.0, 2.5, 7.0)) for _ in range(pairs)])
            ask = numpy.array([rng.choice((1.0, 1.0, 2.0, -1.5)) for _ in range(pairs)])
            stock_state = numpy.array([rng.choice((0.0, 1.0, 3.0, 50.0)) for _ in range(keys)])
            cash_state = numpy.array([rng.choice((0.0, 2.0, 9.0, 500.0)) for _ in range(batch_agents)])
            flags = [numpy.array([rng.random() < share for _ in range(batch_agents)]) for share in (0.2, 0.2, 0.2, 0.2, 0.2)]
            for delivers, sale in ((True, True), (True, False), (False, True)):
                wanted, wanted_stock, wanted_cash = reference(pair_offset, agent_offset, key_offset, buyer_key, seller_key, quantity, ask,
                                                              key_agent, key_global, agent_global, stock_state, cash_state, flags, delivers,
                                                              sale)
                stock, cash = stock_state.copy(), cash_state.copy()
                answer = batch.settle_markets(pair_offset, agent_offset, key_offset, buyer_key, seller_key, quantity, ask, key_agent,
                                              key_global, agent_global, stock, cash, *flags, delivers, sale)
                self.assertEqual(stock.tolist(), wanted_stock.tolist(), seed)
                self.assertEqual(cash.tolist(), wanted_cash.tolist(), seed)
                per_pair = (0, 1, 2)
                per_agent = tuple(range(3, 12))
                per_key = (12, 13, 14)
                for market, expected in enumerate(wanted):
                    if expected is None:
                        continue
                    for outputs, offsets in ((per_pair, pair_offset), (per_agent, agent_offset), (per_key, key_offset)):
                        for index in outputs:
                            self.assertEqual(answer[index][offsets[market]:offsets[market + 1]].tolist(), expected[index].tolist(),
                                             (seed, market, index))


class MarketKeys(unittest.TestCase):

    def test_wide_markets_list_their_keys_and_agents_ascending(self):
        rng = random.Random(5)
        key_total, agent_total = 120, 40
        key_agent = numpy.array(sorted(rng.randrange(agent_total) for _ in range(key_total)), dtype=numpy.int64)
        sizes = numpy.array([90, 3, 60], dtype=numpy.int64)
        receipt = numpy.array([rng.randrange(key_total) for _ in range(sizes.sum())], dtype=numpy.int64)
        seller = numpy.array([rng.randrange(key_total) for _ in range(sizes.sum())], dtype=numpy.int64)
        (pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global,
         key_agent_local) = number_kernel.market_keys(sizes, receipt, seller, key_agent, agent_total)
        for market in range(3):
            pairs = slice(pair_offset[market], pair_offset[market + 1])
            keys = sorted(set(receipt[pairs].tolist()) | set(seller[pairs].tolist()))
            here = key_global[key_offset[market]:key_offset[market + 1]].tolist()
            self.assertEqual(here, keys)
            self.assertEqual(agent_global[agent_offset[market]:agent_offset[market + 1]].tolist(), sorted({int(key_agent[key]) for key in keys}))
            self.assertEqual([here[key] for key in buyer_key[pairs]], receipt[pairs].tolist())
            self.assertEqual([here[key] for key in seller_key[pairs]], seller[pairs].tolist())


if __name__ == "__main__":
    unittest.main()
