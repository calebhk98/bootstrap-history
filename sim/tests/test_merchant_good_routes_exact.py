"""The route search for one good skips what no destination can pay for (flat prices, sources above every
kept destination price) and must give the rows of a plain search that tries every destination."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import merchants
from sim.economy.types import GoodSpec, MarketArea
from sim.unit_conversions import KILOGRAMS_PER_TONNE

TILES = tuple("t%d" % number for number in range(7))


class LineCarriage:
    """Tiles on a line: a tonne costs its distance times a rate; the days follow the distance."""
    scale = 1.0

    def __init__(self, rate, days_per_step):
        self.rate, self.days_per_step = rate, days_per_step

    def costs_from(self, source):
        return {tile: abs(TILES.index(tile) - TILES.index(source)) * self.rate for tile in TILES if tile != "t6"}

    def days_between(self, from_tile, to_tile):
        return abs(TILES.index(from_tile) - TILES.index(to_tile)) * self.days_per_step


def plain_routes(good, spec, areas, prices, carriage, interest_rate, source_ids=None):
    """Every source against every priced destination, dearest first, no shortcut."""
    interest = max(0.0, interest_rate)
    spoilage = min(1.0, max(0.0, spec.spoilage_per_year))
    rows = []
    destinations = sorted((area for area in areas if prices[area.area_id]),
                          key=lambda area: (-prices[area.area_id], area.area_id))
    for source in areas:
        price_here = prices[source.area_id]
        if (source_ids is not None and source.area_id not in source_ids) or not price_here or price_here <= 0.0:
            continue
        best = None
        best_net, best_years = 0.0, 1
        for destination in destinations:
            price_there = prices[destination.area_id]
            per_tonne = carriage.costs_from(source.anchor_tile).get(destination.anchor_tile, math.inf)
            carriage_per_unit = per_tonne * spec.unit_mass_kg / KILOGRAMS_PER_TONNE
            net = price_there - price_here - (carriage_per_unit + price_here * interest + price_there * spoilage
                                              + merchants.MERCHANT_MARGIN_SHARE * price_here)
            if net > 0.0:
                years = merchants.merchants_transit.years_between(carriage, source.anchor_tile, destination.anchor_tile)
                if years > 1:
                    net -= price_here * interest * (years - 1) + price_there * (
                        merchants.merchants_transit.lost_share(spec.spoilage_per_year, years) - spoilage)
                if net > best_net:
                    best, best_net, best_years = (destination, per_tonne), net, years
        if best is None:
            continue
        destination, per_tonne = best
        carriage_per_unit = per_tonne * spec.unit_mass_kg / KILOGRAMS_PER_TONNE
        outlay = price_here + carriage_per_unit
        rows.append((-best_net / outlay, good, source, destination, price_here, outlay,
                     merchants._break_even_price(spec, prices[destination.area_id], carriage_per_unit,
                                                 interest_rate, best_years)))
    return rows


class GoodRoutesTests(unittest.TestCase):
    def setUp(self):
        self.areas = [MarketArea("area%d" % number, "salt", (tile,), tile) for number, tile in enumerate(TILES)]

    def check(self, prices, spec, rate, carriage, source_ids=None):
        by_area = {area.area_id: price for area, price in zip(self.areas, prices)}
        self.assertEqual(merchants._good_routes("salt", spec, self.areas, by_area, carriage, rate, source_ids),
                         plain_routes("salt", spec, self.areas, by_area, carriage, rate, source_ids))

    def test_random_prices_give_the_rows_of_a_plain_search(self):
        generator = random.Random(7)
        found = 0
        for _trial in range(400):
            spec = GoodSpec("salt", generator.choice((1000.0, 250.0)), generator.choice((0.0, 0.3, 1.0)), 0.0, "food")
            carriage = LineCarriage(generator.choice((0.0, 0.05, 0.4)), generator.choice((10.0, 200.0, 900.0)))
            prices = [generator.choice((None, 0.0, 1.0, generator.uniform(0.5, 6.0))) for _ in self.areas]
            rate = generator.choice((0.0, 0.05, 0.4))
            sources = generator.choice((None, {"area1", "area3", "area5"}))
            self.check(prices, spec, rate, carriage, sources)
            found += bool(merchants._good_routes("salt", spec, self.areas, dict(zip((a.area_id for a in self.areas), prices)),
                                                 carriage, rate, sources))
        self.assertGreater(found, 20)

    def test_flat_prices_give_no_rows(self):
        spec = GoodSpec("salt", 1000.0, 0.0, 0.0, "food")
        by_area = {area.area_id: 3.0 for area in self.areas}
        self.assertEqual(merchants._good_routes("salt", spec, self.areas, by_area, LineCarriage(0.0, 10.0), 0.05), [])

    def test_a_good_with_no_price_gives_no_rows(self):
        spec = GoodSpec("salt", 1000.0, 0.0, 0.0, "food")
        by_area = {area.area_id: None for area in self.areas}
        self.assertEqual(merchants._good_routes("salt", spec, self.areas, by_area, LineCarriage(0.0, 10.0), 0.05), [])


if __name__ == "__main__":
    unittest.main()
