"""Two durable metals held as wealth: the price per kilogram of each follows how much of it is held.

The market is the store's budget split among the metals against a fixed stock of each, solved by
iterating the clearing price on the pure weighting function (no game is built).
"""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import market_areas, tile_costs
from sim.economy.households_store import store_candidates
from sim.economy.types import GoodSpec
from sim.tests import economy_fixture as fixture
from sim.unit_conversions import KILOGRAMS_PER_TONNE

STAPLE_PRICE_PER_KG = 0.3
WEALTH_IN_STORE = 1.0e6
REFERENCE_PRICE = 500.0
BASE_STOCK_KG = 1000.0


def spec(good, mass=1.0):
    return GoodSpec(good, mass, 0.0, 100.0, "test")


def clearing_prices(stocks, references=None, specs=None, wealth=WEALTH_IN_STORE, steps=400):
    """The price per unit of each good at which the budget split buys exactly the stock held."""
    specs = specs or {good: spec(good) for good in stocks}
    references = references or {good: REFERENCE_PRICE for good in stocks}
    prices = dict(references)
    for _ in range(steps):
        weights = store_candidates(specs, prices, STAPLE_PRICE_PER_KG, references)
        for good in stocks:
            wanted = weights[good] * wealth / stocks[good]
            prices[good] = math.sqrt(prices[good] * wanted)
    return prices


def value_split(stocks, prices):
    values = {good: stocks[good] * prices[good] for good in stocks}
    total = sum(values.values())
    return {good: value / total for good, value in values.items()}


class StoreRatioTests(unittest.TestCase):
    def test_equal_stocks_keep_a_near_equal_value_split(self):
        stocks = {"a": BASE_STOCK_KG, "b": BASE_STOCK_KG}
        split = value_split(stocks, clearing_prices(stocks))
        self.assertAlmostEqual(split["a"], 0.5, delta=0.03)

    def test_a_tenfold_stock_gap_makes_the_scarcer_metal_dearer_but_by_less_than_the_gap(self):
        stocks = {"scarce": BASE_STOCK_KG, "plenty": 10.0 * BASE_STOCK_KG}
        prices = clearing_prices(stocks)
        ratio = prices["scarce"] / prices["plenty"]
        self.assertGreater(ratio, 1.5)
        self.assertLess(ratio, 9.0)

    def test_the_price_ratio_grows_with_the_stock_gap(self):
        ratios = []
        for gap in (3.0, 10.0, 30.0):
            prices = clearing_prices({"scarce": BASE_STOCK_KG, "plenty": gap * BASE_STOCK_KG})
            ratios.append(prices["scarce"] / prices["plenty"])
        self.assertEqual(ratios, sorted(ratios))
        self.assertGreater(ratios[-1], ratios[0] * 1.5)
        for gap, ratio in zip((3.0, 10.0, 30.0), ratios):
            self.assertLess(ratio, gap)

    def test_swapping_the_good_ids_changes_nothing(self):
        first = clearing_prices({"gold": BASE_STOCK_KG, "silver": 10.0 * BASE_STOCK_KG})
        swapped = clearing_prices({"silver": BASE_STOCK_KG, "gold": 10.0 * BASE_STOCK_KG})
        self.assertAlmostEqual(first["gold"], swapped["silver"], delta=1e-6 * first["gold"])
        self.assertAlmostEqual(first["silver"], swapped["gold"], delta=1e-6 * first["silver"])

    def test_a_dearer_good_draws_a_smaller_share_when_its_usual_price_is_unchanged(self):
        specs = {"a": spec("a"), "b": spec("b")}
        references = {"a": REFERENCE_PRICE, "b": REFERENCE_PRICE}
        cheap = store_candidates(specs, {"a": REFERENCE_PRICE, "b": REFERENCE_PRICE}, STAPLE_PRICE_PER_KG, references)
        risen = store_candidates(specs, {"a": 2.0 * REFERENCE_PRICE, "b": REFERENCE_PRICE}, STAPLE_PRICE_PER_KG, references)
        self.assertLess(risen["a"], cheap["a"])

    def test_without_a_usual_price_the_split_follows_carrying_cost_alone(self):
        specs = {"dense": spec("dense"), "bulky": spec("bulky", mass=5.0)}
        prices = {"dense": REFERENCE_PRICE, "bulky": REFERENCE_PRICE}
        weights = store_candidates(specs, prices, STAPLE_PRICE_PER_KG)
        self.assertGreater(weights["dense"], weights["bulky"])
        self.assertAlmostEqual(sum(weights.values()), 1.0)


class StoreCarriageTests(unittest.TestCase):
    """Two tiles apart by freight: the metal dearer per kilogram is carried at a smaller share of its value."""

    def test_the_metal_dearer_per_kilogram_shows_the_smaller_percentage_gap(self):
        prices = clearing_prices({"scarce": BASE_STOCK_KG, "plenty": 10.0 * BASE_STOCK_KG})
        setup = fixture.small_setup()
        probe = setup.carriage_table()
        per_kilogram = probe.cost_per_tonne(fixture.TOWN, fixture.HILLS) / KILOGRAMS_PER_TONNE
        # freight scaled so one kilogram costs half the cheaper metal's price: more than the share of
        # value that keeps two tiles in one market for it, less for the dearer metal
        scale = 0.5 * prices["plenty"] / per_kilogram
        rates = {mode: rate * scale for mode, rate in setup.carriage_rates.items()}
        handling = {mode: rate * scale for mode, rate in setup.handling_rates.items()}
        carriage = tile_costs.carriage_table(setup.tiles, rates, handling, world_map=setup.world_map)
        per_kilogram = carriage.cost_per_tonne(fixture.TOWN, fixture.HILLS) / KILOGRAMS_PER_TONNE
        pair = (fixture.TOWN, fixture.HILLS)
        population = {tile: setup.opening_population_by_tile[tile] for tile in pair}
        gaps = {}
        for good, price in prices.items():
            areas = market_areas.partition(pair, carriage, price * KILOGRAMS_PER_TONNE, population, label=good)
            gaps[good] = 0.0 if len(areas) == 1 else per_kilogram / price
        self.assertEqual(gaps["scarce"], 0.0)
        self.assertGreater(gaps["plenty"], 0.0)
        self.assertLess(per_kilogram / prices["scarce"], per_kilogram / prices["plenty"])


if __name__ == "__main__":
    unittest.main()
