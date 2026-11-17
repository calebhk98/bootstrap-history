"""Entry drawn by a lasting margin: a market whose smoothed price stays above its cheapest recipe's entry
price gains makers, at the pace incumbents grow, without chasing one year's spike (Complaint 398)."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import entry_margin
from sim.economy.market_memory import market_key
from sim.economy.producers import Producer
from sim.economy.producers_close import LOSS_YEARS_BEFORE_EXIT
from sim.economy.types import Bid, Recipe

TRINKET, CARVE = "trinket", "carve_trinket"


def bid(floor, budget):
    return Bid("buyer", "grain", "area", "tile", floor, 0.0, 1.0, 2.0, budget)


class StandingTests(unittest.TestCase):
    def test_a_clear_margin_must_last_before_it_counts(self):
        standing = 0.0
        for _ in range(LOSS_YEARS_BEFORE_EXIT - 1):
            standing = entry_margin.margin_standing(standing, expected_price=2.0, entry_price=1.0)
        self.assertEqual(entry_margin.margin_share(standing), 0.0)
        standing = entry_margin.margin_standing(standing, expected_price=2.0, entry_price=1.0)
        self.assertEqual(entry_margin.margin_share(standing), 1.0)

    def test_a_price_at_cost_takes_a_year_off_the_standing(self):
        self.assertAlmostEqual(entry_margin.margin_standing(LOSS_YEARS_BEFORE_EXIT, expected_price=0.8, entry_price=1.0), LOSS_YEARS_BEFORE_EXIT - 1)
        self.assertEqual(entry_margin.margin_standing(0.5, expected_price=0.5, entry_price=1.0), 0.0)


class SizeTests(unittest.TestCase):
    def test_there_is_no_gap_when_makers_already_cover_what_buyers_take_at_the_entry_price(self):
        self.assertEqual(entry_margin.gap_at_entry_price([bid(10.0, 20.0)], 1.0, 2.0, capacity=50.0), 0.0)
        self.assertAlmostEqual(entry_margin.gap_at_entry_price([bid(10.0, 20.0)], 1.0, 2.0, capacity=4.0), 6.0)


TILE = "t"
AREA = "area"
KEY = market_key(TRINKET, AREA)
CARVE_RECIPE = Recipe(CARVE, {TRINKET: 10.0}, {}, {"smith": 10.0})
INCUMBENT_RUNS = 10.0
INCUMBENT_OUTPUT = INCUMBENT_RUNS * 10.0     # what the one maker of the trinket reaches a year


def market(price=1e3, usual=1e3, makers=True):
    """(setup, record, view, area_map) for a trinket market of one area and one tile, at `price`; with `makers` one carver works there."""
    setup = types.SimpleNamespace(recipes={CARVE: CARVE_RECIPE})
    producers = {"carver": Producer("carver", "owner", CARVE, TILE, INCUMBENT_RUNS)} if makers else {}
    record = types.SimpleNamespace(producers=producers, goods=types.SimpleNamespace(margin_years={}), memory=types.SimpleNamespace(usual_prices={KEY: usual}), credit=types.SimpleNamespace(expansion_runs={}))
    area = types.SimpleNamespace(area_id=AREA, anchor_tile=TILE, tiles=(TILE,))
    area_map = types.SimpleNamespace(goods=lambda: [TRINKET], areas=lambda good: [area])
    return setup, record, types.SimpleNamespace(price=lambda good, area_id: price, offered_price=lambda good, area_id: price,
                                              present_prices_at=lambda names, tile: {}, price_kind=lambda good, area_id: None,
                                              cleared_price=lambda good, area_id: None), area_map


def plans(setup, record, view, area_map, bids, cost=10.0):
    """margin_entry_plans with the cheapest recipe costing `cost` a unit (recipes_by_cost is entry_trial's, tested there)."""
    with mock.patch.object(entry_margin, "recipes_by_cost", lambda *_args: [(CARVE, cost)]):
        return entry_margin.margin_entry_plans(setup, record, view, area_map, bids)


def buyer(floor=0.0, flexible=1e6, budget=1e9):
    return {(TRINKET, AREA): [Bid("buyer", TRINKET, AREA, TILE, floor, flexible, 1e3, 1.0, budget)]}


class MarketTests(unittest.TestCase):
    def test_a_market_with_no_maker_loses_its_streak(self):
        setup, record, view, area_map = market(makers=False)
        record.goods.margin_years[KEY] = 5
        plans(setup, record, view, area_map, buyer())
        self.assertNotIn(KEY, record.goods.margin_years)

    def test_a_market_absent_from_the_bids_loses_its_streak(self):
        setup, record, view, area_map = market()
        record.goods.margin_years[KEY] = 5
        plans(setup, record, view, area_map, {})
        self.assertNotIn(KEY, record.goods.margin_years)

    def test_a_high_expected_price_draws_newcomers_only_once_it_has_lasted(self):
        setup, record, view, area_map = market()
        counts = [len(plans(setup, record, view, area_map, buyer())) for _year in range(LOSS_YEARS_BEFORE_EXIT)]
        self.assertEqual(counts[:-1], [0] * (LOSS_YEARS_BEFORE_EXIT - 1))
        self.assertGreater(counts[-1], 0)
        self.assertEqual(record.goods.margin_years[KEY], LOSS_YEARS_BEFORE_EXIT)

    def test_newcomers_once_the_margin_has_lasted_add_no_faster_than_incumbents_grow(self):
        setup, record, view, area_map = market()
        record.goods.margin_years[KEY] = LOSS_YEARS_BEFORE_EXIT
        found = plans(setup, record, view, area_map, buyer())
        added = sum(plan.runs * CARVE_RECIPE.outputs[TRINKET] for plan in found)
        self.assertAlmostEqual(added, entry_margin.MARGIN_ENTRY_GROWTH_SHARE * INCUMBENT_OUTPUT)

    def test_a_price_that_falls_under_the_entry_price_draws_nobody_and_lowers_the_standing(self):
        setup, record, view, area_map = market(price=12.0, usual=1e3)    # the year's price is under the entry price (10 times 1.25 is 12.5)
        record.goods.margin_years[KEY] = LOSS_YEARS_BEFORE_EXIT
        self.assertEqual(plans(setup, record, view, area_map, buyer()), [])
        # a fifth of the margin under the entry price takes a fifth of a year off the standing
        self.assertAlmostEqual(record.goods.margin_years[KEY], LOSS_YEARS_BEFORE_EXIT - 0.2)

    def test_no_newcomer_where_no_buyer_bid(self):
        setup, record, view, area_map = market()
        record.goods.margin_years[KEY] = LOSS_YEARS_BEFORE_EXIT
        self.assertEqual(plans(setup, record, view, area_map, {(TRINKET, AREA): []}), [])

    def test_a_market_with_no_maker_is_left_to_the_trial_newcomer(self):
        setup, record, view, area_map = market(makers=False)
        record.goods.margin_years[KEY] = LOSS_YEARS_BEFORE_EXIT
        self.assertEqual(plans(setup, record, view, area_map, buyer()), [])


if __name__ == "__main__":
    unittest.main()
