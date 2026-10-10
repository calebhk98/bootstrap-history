"""Entry drawn by a lasting margin: a market whose smoothed price stays above its cheapest recipe's entry
price gains makers, at the pace incumbents grow, without chasing one year's spike (Complaint 398)."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import entry_margin
from sim.economy.economy import Economy
from sim.economy.producers_close import LOSS_YEARS_BEFORE_EXIT
from sim.economy.types import Bid, Recipe
from sim.tests import economy_fixture as fixture

TRINKET, CARVE = "trinket", "carve_trinket"


def bid(floor, budget):
    return Bid("buyer", "grain", "area", "tile", floor, 0.0, 1.0, 2.0, budget)


class StreakTests(unittest.TestCase):
    def test_a_margin_must_last_before_it_counts(self):
        years = 0
        for _ in range(LOSS_YEARS_BEFORE_EXIT - 1):
            years = entry_margin.margin_streak(years, expected_price=2.0, entry_price=1.0)
        self.assertFalse(entry_margin.margin_has_lasted(years))
        years = entry_margin.margin_streak(years, expected_price=2.0, entry_price=1.0)
        self.assertTrue(entry_margin.margin_has_lasted(years))

    def test_one_year_at_or_under_the_entry_price_ends_the_streak(self):
        self.assertEqual(entry_margin.margin_streak(5, expected_price=1.0, entry_price=1.0), 0)
        self.assertEqual(entry_margin.margin_streak(5, expected_price=0.5, entry_price=1.0), 0)


class SizeTests(unittest.TestCase):
    def test_newcomers_add_a_share_of_the_gap_no_faster_than_incumbents_grow(self):
        added = entry_margin.added_output(gap=1000.0, capacity=100.0)
        self.assertAlmostEqual(added, entry_margin.MARGIN_ENTRY_GROWTH_SHARE * 100.0)
        small = entry_margin.added_output(gap=10.0, capacity=100.0)
        self.assertAlmostEqual(small, entry_margin.MARGIN_ENTRY_SHARE_OF_GAP * 10.0)

    def test_there_is_no_gap_when_makers_already_cover_what_buyers_take_at_the_entry_price(self):
        self.assertEqual(entry_margin.gap_at_entry_price([bid(10.0, 20.0)], 1.0, 2.0, capacity=50.0), 0.0)
        self.assertAlmostEqual(entry_margin.gap_at_entry_price([bid(10.0, 20.0)], 1.0, 2.0, capacity=4.0), 6.0)


def variety_setup():
    """The fixture with a trinket, bought only for ornament (a variety good, no floor)."""
    recipes = fixture.recipes()
    recipes[CARVE] = Recipe(CARVE, {TRINKET: 10.0}, {}, {fixture.SMITH: 10.0})
    specs = fixture.specs()
    specs[TRINKET] = dataclasses.replace(specs[fixture.METAL], good_id=TRINKET, category="ornament")
    basket = fixture.basket()
    needs = tuple(dataclasses.replace(need, goods=need.goods + ((TRINKET, 1.0),)) if need.need_id == fixture.ORNAMENT
                  else need for need in basket.needs)
    prices = dict(fixture.small_setup().opening_prices, **{TRINKET: 1.5})
    return fixture.small_setup(recipes=recipes, specs=specs, basket=dataclasses.replace(basket, needs=needs),
                               opening_prices=prices)


class MarketTests(unittest.TestCase):
    def _shrunk(self, setup, recipe_id, share):
        economy = Economy(setup)
        for producer_id, producer in list(economy.record.producers.items()):
            if producer.recipe_id == recipe_id:
                economy.record.producers[producer_id] = dataclasses.replace(
                    producer, capacity_runs=producer.capacity_runs * share)
        return economy

    def _capacity(self, economy):
        return sum(producer.capacity_runs for producer in economy.record.producers.values()
                   if producer.recipe_id == CARVE)

    def test_a_good_left_with_few_makers_gains_makers_while_its_margin_lasts(self):
        setup = variety_setup()
        economy = self._shrunk(setup, CARVE, 0.05)
        start = self._capacity(economy)
        for _year in range(20):
            economy.step(fixture.quiet_year(setup))
        self.assertGreater(self._capacity(economy), 2.0 * start)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())

    def test_a_high_expected_price_draws_newcomers_only_once_it_has_lasted(self):
        setup = variety_setup()
        economy = self._shrunk(setup, CARVE, 0.5)
        economy.step(fixture.quiet_year(setup))
        economy.record.margin_years.clear()
        view = economy.view()
        area = economy.area_map.areas(TRINKET)[0]
        bids = {(TRINKET, area.area_id): [Bid("buyer", TRINKET, area.area_id, area.anchor_tile, 0.0, 0.0, 1.0, 1e3, 1e6)]}
        for key in list(economy.record.memory.usual_prices):
            if key.startswith(TRINKET):
                economy.record.memory.usual_prices[key] = 1e3
        counts = [len(entry_margin.margin_entry_plans(setup, economy.record, view, economy.area_map, bids))
                  for _year in range(LOSS_YEARS_BEFORE_EXIT)]
        self.assertEqual(counts[:-1], [0] * (LOSS_YEARS_BEFORE_EXIT - 1))
        self.assertGreater(counts[-1], 0)

    def test_no_newcomer_where_no_buyer_bid(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        bids = {(fixture.GRAIN, area.area_id): [] for area in economy.area_map.areas(fixture.GRAIN)}
        self.assertEqual(entry_margin.margin_entry_plans(setup, economy.record, economy.view(), economy.area_map, bids), [])


if __name__ == "__main__":
    unittest.main()
