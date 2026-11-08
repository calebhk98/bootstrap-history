"""`bid_columns`: the entry rules' sums over a market's bids as columns against the sums over `Bid` objects they replace, bit for bit on
random bids (under numba and ROME_NO_JIT=1): `demand_at` against `entry_trial.demand_at`, `sum_taken_at` against the `math.fsum` of
`goods_market.quantity_at`, and the columns of a `MarketBids` against those of its objects."""
QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import bid_columns, entry_trial
from sim.economy.goods_market import quantity_at
from sim.economy.types import Bid


def random_bids(rng, count):
    return [Bid("b%d" % each, "bread", "north", "t0", rng.choice([0.0, rng.uniform(0.0, 20.0)]), rng.choice([0.0, rng.uniform(0.0, 40.0)]),
                rng.choice([0.0, rng.uniform(0.1, 5.0)]), rng.choice([0.5, 1.0, 2.0, 0.0]),
                rng.choice([0.0, rng.uniform(1.0, 80.0), rng.uniform(80.0, 900.0), math.inf]), 0,
                maximum_price=rng.choice([math.inf, math.inf, rng.uniform(0.5, 6.0)])) for each in range(count)]


class SumsOverColumnsAreSumsOverBids(unittest.TestCase):

    def test_demand_at_is_the_entry_trial_sum(self):
        for seed in range(60):
            rng = random.Random(seed)
            bids = random_bids(rng, rng.randint(0, 9))
            price, now = rng.uniform(0.05, 8.0), rng.choice([0.0, rng.uniform(0.05, 8.0)])
            columns = bid_columns.columns_of_bids(bids)
            self.assertEqual(bid_columns.demand_at(columns, price, now), entry_trial.demand_at(bids, price, now), seed)

    def test_sum_taken_at_is_the_fsum_of_quantity_at(self):
        for seed in range(60):
            rng = random.Random(seed)
            bids = random_bids(rng, rng.randint(0, 9))
            price = rng.choice([rng.uniform(0.05, 8.0), 0.0])
            columns = bid_columns.columns_of_bids(bids)
            self.assertEqual(bid_columns.sum_taken_at(columns, price), math.fsum(quantity_at(bid, price) for bid in bids), seed)

    def test_no_bids_take_nothing(self):
        columns = bid_columns.columns_of_bids([])
        self.assertEqual((bid_columns.demand_at(columns, 2.0, 2.0), bid_columns.sum_taken_at(columns, 2.0)), (0.0, 0.0))


class ColumnsOfAMarketsBids(unittest.TestCase):

    def test_joined_columns_follow_the_first_then_the_second(self):
        rng = random.Random(3)
        one, other = random_bids(rng, 3), random_bids(rng, 2)
        joined = bid_columns.joined(bid_columns.columns_of_bids(one), bid_columns.columns_of_bids(other))
        self.assertEqual([column.tolist() for column in joined], [column.tolist() for column in bid_columns.columns_of_bids(one + other)])

    def test_a_market_bids_gives_columns_and_objects_and_a_plain_list_gives_columns(self):
        bids = random_bids(random.Random(5), 4)
        market = bid_columns.MarketBids(lambda: bid_columns.columns_of_bids(bids), lambda: list(bids), len(bids))
        self.assertEqual((len(market), bool(market), list(market)), (4, True, bids))
        self.assertEqual([column.tolist() for column in bid_columns.columns_of(market)],
                         [column.tolist() for column in bid_columns.columns_of(bids)])


if __name__ == "__main__":
    unittest.main()
