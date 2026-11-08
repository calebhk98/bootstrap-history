"""The economy's readers of the labour core (hours cleared, people by trade, flight income, the wage mirror, scaling) give, bit for bit,
what the per-item readers over the state's dict views gave; each reference below is the loop it replaced, written out."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import api, country_figures, flight_step, labour_state
from sim.economy.market_memory import KEY_SEPARATOR, market_key
from sim.labour.api import MarketState
from sim.tests.labour_record_stand_in import labour_record


def awkward_state() -> MarketState:
    return MarketState(
        workers={"work@t2": {"smith": [0.1, 0.2, 0.3], "farmer": [1e16, 1.0, -1e16], "weaver": [0.0, 0.0, 0.0]},
                 "work@t1": {"smith": [0.7, 0.1, 0.2], "farmer": [3.3, 0.1, 0.01]},
                 "work@t3": {"smith": [0.3, 0.3, 0.3]}},
        trainees={"work@t1": {"smith": [[2.0, [0.1, 0.2, 0.7], 0.0]]}},
        wages={"work@t1": {"smith": 1.1, "farmer": 0.7, "baker": 0.3}, "work@t2": {"smith": 2.3, "farmer": 0.9, "weaver": 0.0},
               "work@t3": {"smith": 0.4}},
        hired_hours={"work@t1": {"smith": {"x": 0.1, "y": 0.2, "z": 0.3}}, "work@t2": {"farmer": {"y": 7.5, "x": 1e-9}}})


class MarketHours(unittest.TestCase):
    def test_hours_cleared_in_markets_are_the_fsum_of_the_views_in_the_order_of_the_keys(self):
        record = labour_record()
        record.workforce = awkward_state()
        keys = [market_key("farmer", "work@t2"), market_key("smith", "work@t1"), market_key("smith", "work@t9"), market_key("cook", "work@t1")]
        expected = [math.fsum(record.workforce.hired_hours.get(key.split(KEY_SEPARATOR)[1], {}).get(key.split(KEY_SEPARATOR)[0], {}).values())
                    for key in keys]
        self.assertEqual(record.hours_cleared_in_markets(keys), expected)
        self.assertEqual([record.hours_cleared_in(key) for key in keys], expected)
        self.assertEqual(record.hours_cleared_in_markets([]), [])

    def test_people_in_markets_are_the_fsum_of_the_bands(self):
        record = labour_record()
        record.workforce = awkward_state()
        keys = [market_key("farmer", "work@t2"), market_key("weaver", "work@t2"), market_key("weaver", "work@t1"), market_key("smith", "work@t9")]
        self.assertEqual(record.people_in_markets(keys), [math.fsum(record.workforce.workers["work@t2"]["farmer"]), 0.0, 0.0, 0.0])


class PeopleByTrade(unittest.TestCase):
    def test_country_people_by_trade_adds_tile_by_tile_in_tile_order(self):
        state = awkward_state()
        economy = types.SimpleNamespace(record=types.SimpleNamespace(labour=types.SimpleNamespace(workforce=state)),
                                        setup=types.SimpleNamespace(tiles=["t3", "t1", "t2", "t0"], civ_id="rome"))
        expected = {}
        for tile in sorted(["t3", "t1", "t2", "t0"]):
            for trade, bands in state.workers.get("work@" + tile, {}).items():
                expected[trade] = expected.get(trade, 0.0) + math.fsum(bands)
        self.assertEqual(country_figures.people_by_trade(economy, None), dict(sorted(expected.items())))

    def test_people_by_trade_of_an_area_lists_trades_in_name_order(self):
        state = awkward_state()
        self.assertEqual(labour_state.people_by_trade(state, "work@t2"),
                         {trade: math.fsum(bands) for trade, bands in sorted(state.workers["work@t2"].items())})
        self.assertEqual(labour_state.people_by_trade(state, "work@nowhere"), {})
        self.assertEqual(list(labour_state.PeopleByTile(state)["t1"]), ["farmer", "smith"])

    def test_everyone_working_on_some_tiles_is_fsum_of_fsums_and_ignores_a_tile_without_workers(self):
        state = awkward_state()
        by_tile = labour_state.PeopleByTile(state)
        tiles = ["t2", "t1", "t7"]
        expected = math.fsum(math.fsum(by_tile.get(tile, {}).values()) for tile in tiles)
        self.assertEqual(by_tile.working_people(tiles), expected)


class FlightAndMirror(unittest.TestCase):
    def test_mean_year_income_is_the_people_weighted_mean_wage_of_the_views(self):
        state = awkward_state()
        expected = {}
        for area, wages in sorted(state.wages.items()):
            trades = sorted(wages)
            people = [math.fsum(state.workers.get(area, {}).get(trade, ())) for trade in trades]
            total = math.fsum(people)
            mean = math.fsum(wages[trade] * count for trade, count in zip(trades, people)) / total if total > 0.0 else \
                math.fsum(wages[trade] for trade in trades) / len(trades)
            expected[area] = 2000.0 * mean
        self.assertEqual(flight_step.mean_year_income(state, 2000.0), expected)

    def test_people_before_counts_workers_and_trainees_of_each_area_with_workers_in_the_views_order(self):
        state = awkward_state()
        found = flight_step.people_before(types.SimpleNamespace(workforce=state))
        self.assertEqual(list(found), list(state.workers))
        for area in state.workers:
            total = 0.0
            for bands in state.workers[area].values():
                total += sum(list(bands))
            for cohorts in state.trainees.get(area, {}).values():
                for cohort in cohorts:
                    total += sum(list(cohort[1]))
            self.assertEqual(found[area], total)

    def test_the_mirror_lists_positive_wages_in_the_order_of_the_views(self):
        state = awkward_state()
        mirrored = {"stale|key": 1.0}
        labour_state.mirror_wages(mirrored, state)
        expected = {market_key(trade, area): wage for area, by_trade in state.wages.items() for trade, wage in by_trade.items() if wage > 0.0}
        self.assertEqual(list(mirrored.items()), list(expected.items()))
        self.assertNotIn(market_key("weaver", "work@t2"), mirrored)

    def test_scaling_an_area_scales_its_workers_and_trainees(self):
        state = awkward_state()
        labour_state.scale_people(state, "work@t1", 0.9)
        self.assertEqual(state.workers["work@t1"]["smith"], [0.7 * 0.9, 0.1 * 0.9, 0.2 * 0.9])
        self.assertEqual(state.trainees["work@t1"]["smith"][0][1], [0.1 * 0.9, 0.2 * 0.9, 0.7 * 0.9])
        self.assertEqual(state.workers["work@t2"]["smith"], [0.1, 0.2, 0.3])


class MarketRows(unittest.TestCase):
    def test_labour_market_rows_are_people_offered_and_hired_per_market_in_key_order(self):
        record = labour_record(hired_by_market={market_key("smith", "work@t1"): 5.0}, idle_by_market={
            market_key("smith", "work@t1"): 2.5, market_key("farmer", "work@t2"): 1.0, market_key("plough", "work@t1"): 4.0})
        workforce = awkward_state()
        workforce.hired_hours["work@t1"]["smith"] = {"employer": 5.0}
        record.workforce = workforce
        economy = types.SimpleNamespace(record=types.SimpleNamespace(labour=record),
                                        setup=types.SimpleNamespace(recipes={}, land_per_run={}))
        rows = api.labour_market_rows(economy)
        expected = []
        for key in sorted(record.hours_idle):
            trade, area = key.split(KEY_SEPARATOR, 1)
            if trade == labour_state.plot_trade(economy.setup):
                continue
            hired = math.fsum(workforce.hired_hours.get(area, {}).get(trade, {}).values())
            expected.append((math.fsum(workforce.workers.get(area, {}).get(trade, ())), hired + record.hours_idle[key], hired))
        self.assertEqual(rows, expected)
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
