"""Numba port item 6, entry: the entry rules' costing and siting read from the year arrays (entry_tables.py, entry_kernels.py)
give what the plain Python they stand in for gives, on random built economies (no game). Each test calls the one function
beside the old function it replaces: the cost of a recipe on a tile (`recipes_by_cost`), a recipe's return (`_returns_at`),
the tile a newcomer is sited on (`location.entry_siting`), the output makers could reach (`capacity_in_area`) and the
output idle capacity could add (`_spare_output`), and the producer columns read in bulk.

Tolerance: a relative 1e-9. The kernels sum over a recipe's goods in sorted order where the Python sums in dictionary order or
with math.fsum, so the last digits differ. A discrete rule (the cheapest tile, a rank by cost) could in principle flip under
that nudge; a siting that differs is compared only where the old siting's best two tiles are further apart than the tolerance,
and most sitings must be compared."""

QUICK_TOPIC = True

import dataclasses
import math
import random
import types
import unittest

import numpy as np

from sim.economy import entry, entry_kernels, entry_practice, entry_trial, entry_year, location, practice
from sim.economy.entry_tables import EntryTables
from sim.economy.entrant_rent import site_rent_per_run
from sim.economy.market_memory import KEY_SEPARATOR, MarketMemory, YearView
from sim.economy.producers import Producer
from sim.economy.setup import labour_area
from sim.economy.types import Bid, GoodSpec, MarketArea, Recipe, SiteLimit, TileSpec
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_producers import ProducerColumns
from sim.book import Book
from sim.tests import year_close_fixture as fixture

TILES = ("T0", "T1", "T2", "T3", "T4", "T5")
AREAS = {"north": ("T0", "T1", "T3"), "south": ("T2", "T4", "T5")}
GOODS = fixture.GOODS
MONEY = fixture.MONEY
TOLERANCE = 1e-9


def close(a, b):
    return a == b or abs(a - b) <= TOLERANCE * max(1.0, abs(a), abs(b))


class AreaMap:
    def goods(self):
        return GOODS

    def areas(self, good):
        return tuple(MarketArea(area, good, tiles, tiles[0]) for area, tiles in AREAS.items())

    def area_of(self, good, tile):
        return "north" if tile in AREAS["north"] else "south"

    def market_area_of(self, good, tile):
        return next(each for each in self.areas(good) if each.area_id == self.area_of(good, tile))


class Carriage:
    """Cost per tonne between tiles: symmetric, zero on the diagonal, infinite between two tiles that cannot reach each other."""

    scale = 1.0

    def __init__(self, rng):
        self.table = {}
        for index, first in enumerate(TILES):
            for second in TILES[index:]:
                cost = 0.0 if first == second else (math.inf if rng.random() < 0.05 else rng.uniform(0.2, 6.0))
                self.table[(first, second)] = self.table[(second, first)] = cost

    def costs_from(self, source):
        return {tile: self.table[(source, tile)] for tile in TILES if self.table[(source, tile)] < math.inf}

    def cost_per_tonne(self, source, tile):
        return self.table[(source, tile)]


def recipes():
    return {
        "dig": Recipe("dig", {"good0": 3.0}, {"good1": 1.0}, {"labourer": 2.0}, site_bound=True),
        "forge": Recipe("forge", {"good2": 2.0}, {"good0": 2.0}, {"smith": 1.5, "labourer": 1.0}, {"good3": 4.0}, {"smith": 3.0}, 12.0),
        "plough": Recipe("plough", {"good1": 4.0}, {}, {"labourer": 1.0}, site_bound=True),
        "mill": Recipe("mill", {"good3": 2.0, "good4": 1.0}, {"good2": 1.0}, {"miller": 2.0}, climate_classes=("temperate",)),
        "scrape": Recipe("scrape", {"good0": 2.0}, {"good5": 1.0}, {"labourer": 3.0}),
        "spin": Recipe("spin", {"good2": 1.5}, {"good1": 1.0}, {"labourer": 2.5, "miller": 1.0}, {"good6": 2.0}, {"labourer": 4.0}, 20.0),
    }


def economy(seed, producer_count=60):
    """(setup, record, view, area_map, carriage) of a random economy on six tiles."""
    rng = random.Random(seed)
    memory = fixture.memory_of(rng)
    for good in GOODS:
        for area in AREAS:
            memory.usual_prices[good + KEY_SEPARATOR + area] = memory.prices.get(good + KEY_SEPARATOR + area, 4.0) * rng.uniform(1.2, 4.0)
    for trade in fixture.TRADES:
        for tile in TILES:
            if tile not in fixture.TILES and rng.random() < 0.5:
                memory.wages[trade + KEY_SEPARATOR + labour_area(tile)] = rng.uniform(0.5, 4.0)
    for key in memory.wages:
        memory.wages[key] *= 0.15          # cheap hands, so that some recipes pay and the margin rules have newcomers to place
    all_recipes = recipes()
    specs = {good: GoodSpec(good, 1.0 if index != 5 else math.inf, 0.1, 0.0, "food") for index, good in enumerate(GOODS)}
    tiles = {tile: TileSpec(tile, 0.0, 0.0, 100.0, False, (), 0.5, 1.0, "temperate" if index % 3 else "arid",
                            "rival" if tile == "T5" else "") for index, tile in enumerate(TILES)}
    by_country = {"": set(all_recipes), "rival": {"dig", "plough", "scrape"}}
    setup = types.SimpleNamespace(
        recipes=all_recipes, specs=specs, currency_id=MONEY, unskilled_trade="labourer", opening_wages={"labourer": 0.15, "smith": 0.45},
        trades=fixture.setup_of(all_recipes).trades, tiles=tiles, working_hours_per_year=2000.0,
        land_per_run={"plough": 0.5, "dig": 0.2}, yield_factor_by_recipe_tile={"forge@T1": 0.8, "scrape@T0": 1.3},
        site_limits=(SiteLimit("dig", "T0", 40.0, 1.2), SiteLimit("dig", "T1", 15.0, 0.9), SiteLimit("dig", "T3", 25.0, 1.0)),
        recipes_by_country={"home": by_country[""], "rival": by_country["rival"]},
        country_of=lambda tile: "rival" if tile == "T5" else "home",
        recipe_allowed=lambda recipe_id, tile: recipe_id in (by_country["rival"] if tile == "T5" else by_country[""]))
    producers = {}
    for index in range(producer_count):
        recipe_id = rng.choice(sorted(all_recipes))
        crew = {trade: rng.uniform(1.0, 60.0) for trade in all_recipes[recipe_id].labour_hours if rng.random() < 0.6}
        tile = rng.choice(TILES[:4])
        if recipe_id == "dig" and tile not in ("T0", "T1", "T3"):
            tile = "T0"
        agent = "producer:%03d" % index
        capacity = rng.uniform(0.0, 50.0)
        producers[agent] = Producer(agent, "household:T0:0", recipe_id, tile, capacity, rng.uniform(0.6, 1.2), {}, 0, 5.0,
                                    rng.uniform(0.0, 30.0), capacity * rng.uniform(0.9, 1.0) if rng.random() < 0.9 else -1.0,
                                    land_run_cap=rng.choice((None, None, rng.uniform(0.0, 20.0))), crew_runs=crew)
    labour = types.SimpleNamespace(workers={labour_area(tile): {trade: [rng.uniform(0.0, 80.0), rng.uniform(0.0, 40.0)]
                                                                for trade in fixture.TRADES if rng.random() < 0.8}
                                            for tile in TILES if rng.random() < 0.85})
    record = types.SimpleNamespace(
        producers=producers, cohorts={}, memory=memory, book=Book(),
        credit=types.SimpleNamespace(loans=[], expansion_runs={each: rng.uniform(0.0, 10.0) for each in sorted(producers)[::7]}),
        land=types.SimpleNamespace(land_rent={tile: rng.uniform(0.0, 3.0) for tile in TILES[:4]},
                                   land_mean_value={tile: rng.choice((0.0, rng.uniform(1.0, 30.0))) for tile in TILES[:4]}),
        labour=types.SimpleNamespace(workforce=labour), goods=types.SimpleNamespace(volumes={}, margin_years={}))
    area_map = AreaMap()
    view = YearView(memory, record.book, area_map, MONEY, setup, labour_area)
    return setup, record, view, area_map, Carriage(rng)


def tables_of(setup, record, view, area_map, carriage):
    arrays = YearArrays.build(setup, record, area_map, view)
    return EntryTables.build(setup, record, view, area_map, arrays, carriage, entry_practice.crews_of_recipe(record.producers))


class CostsAreTheOldCosts(unittest.TestCase):
    def test_every_recipe_costed_on_a_tile_as_recipes_by_cost_does(self):
        compared = 0
        for seed in range(8):
            setup, record, view, area_map, carriage = economy(seed)
            with entry_practice.shared_crews(record.producers):
                tables = tables_of(setup, record, view, area_map, carriage)
                for good in GOODS:
                    makers = [recipe_id for recipe_id in sorted(setup.recipes) if good in setup.recipes[recipe_id].outputs]
                    for tile in ("T0", "T2", "T4"):
                        for output in (None, 3.0, 80.0):
                            old = entry_trial.recipes_by_cost(setup, record, view, good, tile, makers, output)
                            new = tables.recipes_by_cost(good, tile, makers, output)
                            many = tables.recipes_by_cost_many([(good, tile, makers, output)])[0]
                            self.assertEqual([each[0] for each in old], [each[0] for each in new])
                            self.assertEqual(new, many)
                            for (_a, old_cost), (_b, new_cost) in zip(old, new):
                                self.assertTrue(close(old_cost, new_cost), (old_cost, new_cost))
                            compared += len(old)
        self.assertGreater(compared, 100)

    def test_a_request_for_no_recipe_and_no_request_cost_nothing(self):
        setup, record, view, area_map, carriage = economy(1)
        with entry_practice.shared_crews(record.producers):
            tables = tables_of(setup, record, view, area_map, carriage)
            self.assertEqual(tables.recipes_by_cost_many([]), [])
            self.assertEqual(tables.recipes_by_cost("good0", "T0", [], 5.0), [])
        empty = entry_kernels.full_costs(np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64),
                                         np.zeros(0), 0.05, tables.tables)
        self.assertEqual(len(empty), 0)


class ReturnsAreTheOldReturns(unittest.TestCase):
    def test_a_recipes_return_on_a_tile_as_returns_at_gives_it(self):
        compared = 0
        for seed in range(8):
            setup, record, view, area_map, carriage = economy(seed)
            rate = 0.07
            with entry_practice.shared_crews(record.producers):
                tables = tables_of(setup, record, view, area_map, carriage)
                crews_of = entry_practice.crews_of_recipe(record.producers)
                requests = [(recipe_id, tile, runs, rate) for recipe_id in sorted(setup.recipes) for tile in TILES[:4]
                            for runs in (None, 2.0, 40.0)]
                new = tables.returns_many(requests)
                for (recipe_id, tile, runs, _rate), (gross, after) in zip(requests, new):
                    recipe = setup.recipes[recipe_id]
                    planned = recipe if runs is None else entry_practice.planned_recipe(recipe, crews_of(recipe_id), runs)
                    old_gross, old_after = entry._returns_at(planned, recipe_id, tile, view, rate, site_rent_per_run(
                        setup, record, view, recipe_id, tile))
                    self.assertEqual(gross is None, old_gross is None)
                    self.assertEqual(after is None, old_after is None)
                    if gross is not None and old_gross is not None:
                        self.assertTrue(close(gross, old_gross), (gross, old_gross))
                        self.assertTrue(close(after, old_after), (after, old_after))
                        compared += 1
        self.assertGreater(compared, 100)

    def test_no_request_has_no_return(self):
        setup, record, view, area_map, carriage = economy(2)
        with entry_practice.shared_crews(record.producers):
            self.assertEqual(tables_of(setup, record, view, area_map, carriage).returns_many([]), [])


class SitingIsTheOldSiting(unittest.TestCase):
    def test_the_tile_picked_for_each_newcomer_is_the_old_picks(self):
        compared = skipped = 0
        for seed in range(10):
            setup, record, view, area_map, carriage = economy(seed)
            rng = random.Random(seed + 100)
            with entry_practice.shared_crews(record.producers):
                tables = tables_of(setup, record, view, area_map, carriage)
                new_siting = location.entry_siting(setup, record, view, area_map, carriage, tables)
                old_siting = location.entry_siting(setup, record, view, area_map, carriage)
                for _call in range(40):
                    recipe_id = rng.choice(sorted(setup.recipes))
                    good = rng.choice(sorted(setup.recipes[recipe_id].outputs))
                    demand = entry.UnmetDemand(good, "north", rng.choice(("T0", "T2", "T3")), 10.0)
                    runs = rng.uniform(0.5, 60.0)
                    old, new = old_siting(recipe_id, demand, runs), new_siting(recipe_id, demand, runs)
                    if old is None or new is None:
                        self.assertEqual(old, new)
                    elif old[0] != new[0]:
                        skipped += 1       # the old pick and the new one are a nudge apart in cost: a discrete rule
                        break              # the two sitings no longer share their claims
                    else:
                        self.assertTrue(close(old[1], new[1]), (old, new))
                        compared += 1
        self.assertGreater(compared, 4 * skipped + 40)

    def test_a_recipe_with_no_candidate_tile_is_not_sited(self):
        setup, record, view, area_map, carriage = economy(3)
        with entry_practice.shared_crews(record.producers):
            tables = tables_of(setup, record, view, area_map, carriage)
            tables._ready_siting()
            row = tables.recipe_row["dig"]
            picked = entry_kernels.site_choice(
                row, 0, np.zeros(0, dtype=np.int64), 5.0, 1.0, tables.tables, tables.input_tonnes, tables.supply_weight,
                tables.supply_present, tables.carriage_matrix, tables.hauls, tables.yield_rt, tables.limit_rt, False,
                tables.short_of_land, tables.hands_hours, tables.capacity, tables.committed, 1.0)
            self.assertEqual(picked, (-1, 0.0))


class MarketsOfTheYear(unittest.TestCase):
    def test_the_output_makers_could_reach_is_capacity_in_area(self):
        for seed in range(6):
            setup, record, view, area_map, carriage = economy(seed)
            with entry_practice.shared_crews(record.producers):
                reach = tables_of(setup, record, view, area_map, carriage).capacity_in()
                terms = entry_trial.capacity_terms_by_good(record.producers, setup.recipes, record.credit.expansion_runs)
                for good in GOODS:
                    for area in area_map.areas(good):
                        self.assertTrue(close(reach(good, area.area_id), entry_trial.capacity_in_area(terms, good, area.tiles)))

    def test_the_output_idle_capacity_could_add_is_the_spare_output(self):
        for seed in range(6):
            setup, record, view, area_map, carriage = economy(seed)
            with entry_practice.shared_crews(record.producers):
                tables = tables_of(setup, record, view, area_map, carriage)
                grid = tables.spare_output()
                old = entry_year._spare_output(setup, record, view)
                for good in GOODS:
                    for area in AREAS:
                        found = entry_year._spare_at(grid, tables, good, area)
                        self.assertTrue(close(found, old.get((good, area), 0.0)), (found, old.get((good, area))))


class WholeEntry(unittest.TestCase):
    def test_the_year_plans_are_the_same_with_and_without_the_arrays(self):
        compared = 0
        for seed in range(6):
            setup, record, view, area_map, carriage = economy(seed, producer_count=80)
            rng = random.Random(seed)
            unmet = {(good, area): rng.uniform(0.0, 600.0) for good in GOODS for area in AREAS if rng.random() < 0.7}
            bids = {(good, area): [Bid("buyer", good, area, "T0", rng.uniform(20.0, 600.0), rng.uniform(0.0, 400.0), 3.0, 1.0,
                                       rng.uniform(2000.0, 20000.0))] for good in GOODS for area in AREAS if rng.random() < 0.8}
            record.goods.volumes.update({good + KEY_SEPARATOR + area: rng.uniform(0.0, 100.0) for good in GOODS for area in AREAS})
            for _year in range(3):         # the margin's streak builds over years
                arrays = YearArrays.build(setup, record, area_map, view)
                years = dict(record.goods.margin_years)
                old = entry_year.year_plans(setup, record, view, area_map, unmet, carriage, bids, None)
                record.goods.margin_years.clear()
                record.goods.margin_years.update(years)
                new = entry_year.year_plans(setup, record, view, area_map, unmet, carriage, bids, arrays)
                self.assertEqual([(each.recipe_id, each.tile, each.good) for each in old],
                                 [(each.recipe_id, each.tile, each.good) for each in new])
                for first, second in zip(old, new):
                    self.assertTrue(close(first.runs, second.runs) and close(first.yearly_return, second.yearly_return), (first, second))
                compared += len(old)
        self.assertGreater(compared, 20)


class ProducerColumnsInBulk(unittest.TestCase):
    def test_columns_read_a_column_at_a_time_are_the_columns_read_by_row(self):
        for seed in range(3):
            setup, record, view, area_map, carriage = economy(seed, producer_count=150)
            for index, producer_id in enumerate(sorted(record.producers)):
                if index % 3 == 0:
                    record.producers[producer_id] = dataclasses.replace(
                        record.producers[producer_id], expected_prices={"good0": 1.5 + index}, net_earnings_history=(1.0, float(index)),
                        revenue_history=(2.0,) * (index % 4))
            arrays = YearArrays.build(setup, record, area_map, view)
            bulk = arrays.producers
            by_row = ProducerColumns._empty(bulk.ids, bulk.records, bulk.earnings_history.shape[1], bulk.matrices, bulk.tiles)
            for position in range(len(bulk.ids)):
                by_row._read(position)
            for name in dataclasses.fields(bulk):
                held, expected = getattr(bulk, name.name), getattr(by_row, name.name)
                if isinstance(held, np.ndarray):
                    np.testing.assert_equal(held, expected, err_msg=name.name)

    def test_columns_rebuilt_after_an_entry_keep_the_rows_of_producers_that_stayed(self):
        setup, record, view, area_map, carriage = economy(4, producer_count=150)
        arrays = YearArrays.build(setup, record, area_map, view)
        before = arrays.producers
        leaving = sorted(record.producers)[3]
        template = record.producers[sorted(record.producers)[5]]
        del record.producers[leaving]
        record.producers["producer:zzz"] = dataclasses.replace(template, agent_id="producer:zzz", capacity_runs=77.0)
        rebuilt = arrays.sync(setup, record, view).producers
        fresh = ProducerColumns.build(record.producers, before.matrices, before.tiles)
        self.assertEqual(rebuilt.ids, fresh.ids)
        for name in dataclasses.fields(rebuilt):
            held = getattr(rebuilt, name.name)
            if isinstance(held, np.ndarray):
                np.testing.assert_equal(held, getattr(fresh, name.name), err_msg=name.name)


if __name__ == "__main__":
    unittest.main()
