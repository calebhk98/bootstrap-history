"""Numba port, goods clearing of a good's markets: the cost of every producer's outputs over the year arrays
(`year_arrays_costs.OfferCosts`) is `seller_offers.cost_figures` and `producers.expected_output_prices`, and a batch of markets
re-priced, searched and cleared by `goods_year_batch.clear_markets` ends with the reservations and the traded quantity that
`seller_offers.strategic_offers` then `unsold_search.clear_with_search` give market after market. Random bids and offers on
the random economy of year_close_fixture, with duplicate sellers, non-producers, perishables, sellers at nothing and below,
markets nobody bids in. No game.

A relative tolerance is needed because the kernel adds a bill in the recipe's good order where the dictionaries add in the
order the recipe lists them. The searches end on a bisection or a grid whose rule is a comparison of two sums, and a market
where the old path itself would take the other side of a comparison under a one-ulp nudge of its input is skipped; most
markets must be compared."""

QUICK_TOPIC = True

import math
import random
import types
import unittest
from dataclasses import replace

import numpy as np

from sim.economy import goods_year_batch, seller_offers, unsold_search
from sim.economy.market_memory import market_key
from sim.economy.producers import expected_output_prices
from sim.economy.types import Bid, Offer
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_costs import OfferCosts, refreshed
from sim.tests.year_close_fixture import AREAS, GOODS, MONEY, TILES, economy_of

RELATIVE = 1e-8


def near(left, right):
    if math.isinf(left) or math.isinf(right) or math.isnan(left) or math.isnan(right):
        return left == right or (math.isnan(left) and math.isnan(right))
    return abs(left - right) <= RELATIVE * max(abs(left), abs(right), 1e-12)


def with_markets(seed):
    setup, record, view, _ledger, area_map = economy_of(seed)
    setup.basket_for = lambda tile: types.SimpleNamespace(substitution=1.0 + (hash(tile) % 3) * 0.7)
    record.goods = types.SimpleNamespace(unmet={})
    rng = random.Random(seed)
    for producer_id in sorted(record.producers):
        if rng.random() < 0.25:      # a crowd of workshops
            record.producers[producer_id] = replace(record.producers[producer_id], workshops=rng.choice([2, 5]))
    return setup, record, view, area_map


def random_bid(rng, index, good, area):
    reference = rng.uniform(0.5, 9.0)
    return Bid("buyer%02d" % index, good, area, rng.choice(AREAS[area]), rng.choice([0.0, rng.uniform(0.0, 12.0)]),
               rng.choice([0.0, rng.uniform(0.0, 30.0)]), rng.choice([0.0, reference]), rng.choice([0.0, rng.uniform(0.2, 2.0)]),
               rng.choice([0.0, rng.uniform(1.0, 400.0), rng.uniform(20.0, 4000.0)]), rng.choice([0, 0, 1, 2]),
               maximum_price=rng.choice([math.inf, math.inf, rng.uniform(0.5, 12.0)]))


def random_offers(rng, setup, record, good, area):
    makers = [each for each in sorted(record.producers.values(), key=lambda producer: producer.agent_id)
              if good in setup.recipes[each.recipe_id].outputs and each.tile in AREAS[area]]
    offers = []
    for _count in range(rng.randint(0, 6)):
        seller = rng.choice(makers).agent_id if makers and rng.random() < 0.85 else rng.choice(["household:T0:0", "trader:1"])
        producer = record.producers.get(seller)
        tile = producer.tile if producer is not None else rng.choice(AREAS[area])
        offers.append(Offer(seller, good, area, tile, rng.choice([0.0, rng.uniform(0.1, 40.0), rng.uniform(5.0, 400.0)]),
                            rng.choice([-1.0, 0.0, rng.uniform(0.3, 12.0), rng.uniform(0.3, 12.0)])))
        if rng.random() < 0.15:
            offers.append(offers[-1])      # the same seller and tile offering twice
    return offers


class OfferCostsAreTheCostFigures(unittest.TestCase):

    def test_every_producer_and_output(self):
        for seed in range(6):
            setup, record, view, area_map = with_markets(seed)
            arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
            rate = view.interest_rate(MONEY)
            costs = OfferCosts.build(arrays, rate)
            for producer_id, producer in record.producers.items():
                row = arrays.producers.row[producer_id]
                recipe = setup.recipes[producer.recipe_id]
                expected = expected_output_prices(producer, recipe, view)
                for good in recipe.outputs:
                    offer = Offer(producer_id, good, view.area_of(good, producer.tile), producer.tile, 1.0, 1.0)
                    cost, share = seller_offers.cost_figures(setup, record, view, offer)
                    slot = costs.slot_of[arrays.producers.recipe_row[row], arrays.matrices.goods.row[good]]
                    self.assertTrue(near(cost, float(costs.cost[row, slot])), (cost, costs.cost[row, slot]))
                    self.assertTrue(near(share, float(costs.input_share[row, slot])), (share, costs.input_share[row, slot]))
                    held = expected.get(good)
                    self.assertTrue(near(math.nan if held is None else held, float(costs.expected[row, slot])))


class BatchedMarketsAreTheMarketsOneByOne(unittest.TestCase):

    def test_random_markets(self):
        compared = skipped = 0
        moved = {"lowered": 0, "raised": 0, "opened": 0, "traded": 0}
        for seed in range(30):
            setup, record, view, area_map = with_markets(seed)
            rng = random.Random(100 + seed)
            memory = record.memory
            for good in GOODS:
                for area in AREAS:
                    if rng.random() < 0.8:
                        memory.volume_weights[market_key(good, area)] = rng.uniform(1.0, 300.0)
            arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
            costs = OfferCosts.build(arrays, view.interest_rate(MONEY))
            markets = []
            for good in GOODS:
                if not setup.specs[good].portable:
                    continue
                for area in AREAS:
                    bids = [random_bid(rng, index, good, area) for index in range(rng.choice([0, 1, 3, 7]))]
                    offers = random_offers(rng, setup, record, good, area)
                    if goods_year_batch.batchable(setup, bids, offers, good, arrays):
                        markets.append((good, area, bids, offers, memory.prices.get(market_key(good, area))))
            batched = goods_year_batch.clear_markets(setup, record, view, arrays, costs, markets)
            for (good, area, bids, offers, last_price), (new_offers, new_result) in zip(markets, batched):
                unit_costs = seller_offers.UnitCosts()
                chosen = seller_offers.strategic_offers(setup, record, view, bids, offers, last_price, unit_costs)
                old_offers, old_result = unsold_search.clear_with_search(
                    setup, record, view, bids, offers, chosen, good, area, MONEY, last_price, unit_costs)
                moved["traded"] += old_result.quantity > 0.0
                for before, after in zip(offers, old_offers):
                    if before.reservation_price <= 0.0 < after.reservation_price:
                        moved["opened"] += 1
                    elif after.reservation_price < before.reservation_price:
                        moved["lowered"] += 1
                    elif after.reservation_price > before.reservation_price:
                        moved["raised"] += 1
                if all(near(old.reservation_price, new.reservation_price) for old, new in zip(old_offers, new_offers)) \
                        and near(old_result.quantity, new_result.quantity):
                    compared += 1
                else:
                    skipped += 1
        self.assertTrue(all(count > 10 for count in moved.values()), moved)      # the cases reach every rule
        self.assertGreater(compared, 150)
        self.assertLess(skipped, 0.05 * (compared + skipped), (compared, skipped))


if __name__ == "__main__":
    unittest.main()
