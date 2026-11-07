"""Numba port item 0b: the equity built for the households (`equity.producer_worths`, `equity.holdings`) reads each plant cost and
each price once per (recipe, tile) and (good, tile) and splits a worth over a tile's cohorts from shares summed once. The old
per-producer functions are the reference, copied here, run beside the new ones on random built economies.

Tolerance: a relative 1e-9. The new inventory sum is exact (math.fsum over the terms) where the old one added in the order of the
book's sorted tiles, so the last digits differ."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import credit_claims, equity, producers, unit_cost
from sim.economy.credit_view import CreditView
from sim.economy.setup import labour_area
from sim.economy.households_cohort import distribute_property_income
from sim.tests.year_close_fixture import economy_of


def old_inventory_value(record, producer, view):
    total = 0.0
    for good, tiles in record.book.holdings(producer.agent_id)["goods"].items():
        price = view.price(good, view.area_of(good, producer.tile))
        if price is not None and price > 0.0:
            total += price * sum(quantity for quantity in tiles.values() if quantity > 0.0)
    return total


def old_plant_value(producer, recipe, view):
    if recipe.plant_life_years <= 0.0:
        return 0.0
    return producer.capacity_runs * unit_cost.plant_value_per_run(
        recipe, producers.live_input_prices(producer, recipe, view), producers.live_wages(producer, recipe, view))


def old_producer_worths(setup, record, view):
    debts = credit_claims.debts_by_borrower(record.credit.loans, setup.currency_id)
    worths = {}
    for producer_id, producer in sorted(record.producers.items()):
        if record.cohorts.get(producer.owner) is None or producer.capacity_runs <= 0.0:
            continue
        assets = (record.book.balance(producer_id, setup.currency_id) + old_plant_value(producer, setup.recipes[producer.recipe_id], view)
                  + old_inventory_value(record, producer, view))
        worths[producer_id] = max(0.0, assets - debts.get(producer_id, 0.0))
    return worths


def old_holdings(setup, record, view):
    cohorts_of_tile = {}
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        cohorts_of_tile.setdefault(cohort.tile, []).append(cohort)
    factor = record.capital_markets.capital.share_price_factor
    held = {}
    for producer_id, worth in old_producer_worths(setup, record, view).items():
        owner = record.cohorts[record.producers[producer_id].owner]
        outside = record.capital_markets.shares.get(producer_id)
        if outside:
            for holder, part in outside.items():
                held[holder] = held.get(holder, 0.0) + part * worth * factor
            worth *= max(0.0, 1.0 - sum(outside.values()))
        for agent, amount in distribute_property_income(cohorts_of_tile[owner.tile], worth).items():
            held[agent] = held.get(agent, 0.0) + amount
    return held


def close(a, b):
    return a == b or abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def economy(seed):
    setup, record, view, _ledger, _area_map = economy_of(seed, producer_count=60)
    for index, cohort in enumerate(record.cohorts.values()):
        cohort.ownership_share = 0.0 if index == 2 else 0.2 + index
    record.capital_markets = types.SimpleNamespace(
        capital=types.SimpleNamespace(share_price_factor=0.8),
        shares={"producer:003": {"household:T1:0": 0.25, "outsider": 0.5}, "producer:010": {"household:T2:0": 0.1}})
    return setup, record, view


class EquityBuiltOnce(unittest.TestCase):
    def test_producer_worths_equal_the_per_producer_reads(self):
        compared = 0
        for seed in range(10):
            setup, record, view = economy(seed)
            new, old = equity.producer_worths(setup, record, view), old_producer_worths(setup, record, view)
            self.assertEqual(sorted(new), sorted(old))
            for producer_id, worth in old.items():
                self.assertTrue(close(new[producer_id], worth), (producer_id, new[producer_id], worth))
                compared += 1
        self.assertGreater(compared, 300)

    def test_holdings_equal_the_per_producer_reads(self):
        for seed in range(10):
            setup, record, view = economy(seed)
            new, old = equity.holdings(setup, record, view), old_holdings(setup, record, view)
            self.assertEqual(sorted(new), sorted(old))
            for agent, value in old.items():
                self.assertTrue(close(new[agent], value), (agent, new[agent], value))
            self.assertIn("outsider", new)

    def test_a_credit_view_builds_the_worths_once_and_keeps_them(self):
        setup, record, view = economy(1)
        area_map = view._area_map
        kept = CreditView(record.memory, record.book, area_map, setup.currency_id, setup, labour_area)
        first = equity.producer_worths(setup, record, kept)
        self.assertEqual(first, equity.producer_worths(setup, record, view))
        record.producers = {}
        self.assertIs(equity.producer_worths(setup, record, kept), first)

    def test_no_producers_is_no_worth(self):
        setup, record, view = economy(0)
        record.producers = {}
        self.assertEqual(equity.producer_worths(setup, record, view), {})
        self.assertEqual(equity.holdings(setup, record, view), {})


if __name__ == "__main__":
    unittest.main()
