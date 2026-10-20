"""Complaint 394 (wage quote): a trade's quoted wage weights each labour market by the hours hired there, so a market
where nobody is hired does not set the national figure. The rule is `economy.api.wages_by_trade_weighted`, called on a
record built here. (That the engine's quote is this figure times the coin: test_scenarios_batch3.)"""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import api
from sim.economy.setup import labour_area

TRADE = "weighted_wage_probe_trade"
UNSKILLED = "unskilled_probe_trade"


def economy_of(wages, hired, idle, countries=None):
    """An economy holding `wages`, `hired` and `idle` hours by market key. `countries` is {country: [tiles]}; the first
    is the home country."""
    countries = countries or {"home": ["tile_a", "tile_b"]}
    tiles = [tile for held in countries.values() for tile in held]
    record = SimpleNamespace(memory=SimpleNamespace(wages=dict(wages)), hours_hired=dict(hired), hours_idle=dict(idle))
    setup = SimpleNamespace(tiles=tiles, tiles_of=lambda country: countries[country], civ_id=next(iter(countries)),
                            countries=lambda: list(countries), unskilled_trade=UNSKILLED)
    return SimpleNamespace(record=record, setup=setup)


def market(trade, tile):
    return trade + "|" + labour_area(tile)


class WeightedWageTests(unittest.TestCase):
    def test_a_market_where_nobody_is_hired_does_not_set_the_figure(self):
        busy, empty = market(TRADE, "tile_a"), market(TRADE, "tile_b")
        economy = economy_of({busy: 10.0, empty: 1000.0}, {busy: 100.0}, {busy: 0.0})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)[TRADE], 10.0)

    def test_markets_are_weighted_by_the_hours_hired_in_each(self):
        first, second = market(TRADE, "tile_a"), market(TRADE, "tile_b")
        economy = economy_of({first: 10.0, second: 40.0}, {first: 300.0, second: 100.0}, {first: 0.0, second: 0.0})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)[TRADE], (10.0 * 300.0 + 40.0 * 100.0) / 400.0)

    def test_a_trade_that_hired_nothing_is_left_out(self):
        only = market(TRADE, "tile_a")
        economy = economy_of({only: 10.0}, {}, {only: 50.0})
        self.assertNotIn(TRADE, api.wages_by_trade_weighted(economy))

    def test_the_unskilled_trade_is_kept_even_when_it_hired_nothing(self):
        only = market(UNSKILLED, "tile_a")
        economy = economy_of({only: 7.0}, {}, {only: 50.0})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)[UNSKILLED], 7.0)

    def test_each_trade_is_weighted_on_its_own_markets(self):
        mine, other = market(TRADE, "tile_a"), market("other_probe_trade", "tile_a")
        economy = economy_of({mine: 10.0, other: 99.0}, {mine: 5.0, other: 5.0}, {mine: 0.0, other: 0.0})
        wages = api.wages_by_trade_weighted(economy)
        self.assertAlmostEqual(wages[TRADE], 10.0)
        self.assertAlmostEqual(wages["other_probe_trade"], 99.0)


class ForCountryTests(unittest.TestCase):
    def setUp(self):
        self.home_market, self.away_market = market(TRADE, "tile_a"), market(TRADE, "tile_c")
        self.economy = economy_of({self.home_market: 10.0, self.away_market: 50.0},
                                  {self.home_market: 100.0, self.away_market: 100.0},
                                  {self.home_market: 0.0, self.away_market: 0.0},
                                  countries={"home": ["tile_a", "tile_b"], "away": ["tile_c"]})

    def test_an_economy_holding_several_countries_answers_for_the_home_one(self):
        self.assertAlmostEqual(api.wages_by_trade_weighted(self.economy)[TRADE], 10.0)

    def test_a_country_asked_for_is_answered_from_its_own_markets_only(self):
        self.assertAlmostEqual(api.wages_by_trade_weighted(self.economy, "away")[TRADE], 50.0)
        self.assertAlmostEqual(api.wages_by_trade_weighted(self.economy, "home")[TRADE], 10.0)


if __name__ == "__main__":
    unittest.main()
