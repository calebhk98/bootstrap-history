"""Complaint 497, numba port items 6 and 7: the reads the producers' plan, close and entry make of the market memory (a
trade's wage by tile, a price on offer, who sells a good on a tile, an entrant's planned recipe, the haul of a run's
inputs) are kept for the part of the year the memory does not change, and a kept read equals the plain one. Each test
calls the one function beside a copy of the old code on random built inputs; no game."""

QUICK_TOPIC = True

import math
import random
import types
import unittest

from sim.economy import entry_practice, land_bid, labour_state, location_inputs, practice, trade_wages
from sim.economy.market_memory import KEY_SEPARATOR, MarketMemory, YearView
from sim.economy.producers import Producer
from sim.economy.types import GoodSpec, Recipe

TRADES = ("labourer", "smith", "miller")
AREAS = ("north", "south", "east")
GOODS = ("grain", "iron", "flour")


def setup():
    return types.SimpleNamespace(
        opening_wages={"labourer": 1.0, "smith": 3.0}, unskilled_trade="labourer", currency_id="coin",
        trades={"labourer": types.SimpleNamespace(training_years=0.0), "smith": types.SimpleNamespace(training_years=5.0),
                "miller": types.SimpleNamespace(training_years=2.0)})


def area_map():
    return types.SimpleNamespace(goods=lambda: list(GOODS), area_of=lambda good, tile: "A" + tile)


def view_of(memory):
    return YearView(memory, None, area_map(), "coin", setup(), lambda tile: tile)


def random_wages(rng):
    return {trade + KEY_SEPARATOR + area: rng.uniform(0.5, 5.0) for trade in TRADES for area in AREAS if rng.random() < 0.5}


class KeptReadsAreThePlainOnes(unittest.TestCase):
    def test_wages_of_trades_on_a_tile_are_the_wage_rule(self):
        rng = random.Random(1)
        for _round in range(40):
            view = view_of(MarketMemory(wages=random_wages(rng)))
            for tile in AREAS:
                trades = tuple(sorted(rng.sample(TRADES, rng.randrange(1, 4))))
                plain = {trade: trade_wages.wage_in_view(setup(), view, trade, view.area_of(trade, tile)) for trade in trades}
                self.assertEqual(view.wages_at(trades, tile), plain)
                self.assertEqual(view.wages_at(trades, tile), plain)       # the second read is the kept one

    def test_wages_rebuilt_by_the_labour_mirror_are_read_again(self):
        memory = MarketMemory(wages={"smith|north": 2.0})
        view = view_of(memory)
        trades = ("smith",)
        self.assertEqual(view.wages_at(trades, "north"), {"smith": 2.0})
        state = types.SimpleNamespace(wages={"north": {"smith": 7.0}})
        labour_state.mirror_wages(memory.wages, state)
        self.assertEqual(view.wages_at(trades, "north"), {"smith": 7.0})

    def test_a_trade_is_held_anywhere_as_the_old_prefix_scan_says(self):
        rng = random.Random(2)
        for _round in range(40):
            wages = random_wages(rng)
            memory = MarketMemory(wages=wages)
            for trade in TRADES + ("other",):
                self.assertEqual(memory.holds_wage_for(trade), any(key.startswith(trade + KEY_SEPARATOR) for key in wages))
            labour_state.mirror_wages(memory.wages, types.SimpleNamespace(wages={"north": {"smith": 1.0}}))
            self.assertTrue(memory.holds_wage_for("smith"))
            self.assertFalse(memory.holds_wage_for("miller"))

    def test_the_price_on_offer_follows_a_price_set_after_it_was_read(self):
        rng = random.Random(3)
        memory = MarketMemory()
        for good in GOODS:
            for area in AREAS:
                key = good + KEY_SEPARATOR + area
                memory.set_price(key, rng.uniform(1.0, 9.0))
                if rng.random() < 0.6:
                    memory.trade_age[key] = rng.randrange(0, 3)
        view = YearView(memory, None, types.SimpleNamespace(goods=lambda: list(GOODS), area_of=lambda good, tile: tile), "coin", setup(), lambda tile: tile)
        for good in GOODS:
            for area in AREAS:
                self.assertEqual(view.offered_price(good, area), memory.offered_price(good + KEY_SEPARATOR + area))
        memory.set_price("grain|north", 123.0)
        memory.trade_age["grain|north"] = 0
        memory.note_trading(["grain|north"])
        self.assertEqual(view.offered_price("grain", "north"), 123.0)
        self.assertEqual(view.price_kind("grain", "north"), memory.price_kind("grain|north"))

    def test_present_prices_follow_a_price_set_after_they_were_read(self):
        memory = MarketMemory()
        memory.set_price("grain|Anorth", 2.0)
        view = view_of(memory)
        names = ("grain", "iron")
        self.assertEqual(view.present_prices_at(names, "north"), {"grain": 2.0})
        memory.set_price("iron|Anorth", 5.0)
        self.assertEqual(view.present_prices_at(names, "north"), {"grain": 2.0, "iron": 5.0})


def old_owners_of_sellers(producers, recipes, good, tile):
    return sorted({producer.owner for producer in producers.values()
                   if producer.tile == tile and good in recipes[producer.recipe_id].outputs})


class SellerIndex(unittest.TestCase):
    def test_owners_of_sellers_are_the_old_scan(self):
        rng = random.Random(4)
        recipes = {name: Recipe(name, {good: 1.0}, {}, {}) for name, good in zip(("a", "b", "c"), GOODS)}
        for _round in range(30):
            producers = {"p%d" % index: Producer("p%d" % index, rng.choice(("o1", "o2", "o3")), rng.choice(list(recipes)),
                                                 rng.choice(AREAS), 1.0) for index in range(rng.randrange(0, 25))}
            record = types.SimpleNamespace(producers=producers, memory=types.SimpleNamespace(year=_round))
            for good in GOODS:
                for tile in AREAS:
                    self.assertEqual(land_bid.owners_of_sellers(record, recipes, good, tile),
                                     old_owners_of_sellers(producers, recipes, good, tile))

    def test_a_producer_added_after_a_read_is_a_seller(self):
        recipes = {"a": Recipe("a", {"grain": 1.0}, {}, {})}
        producers = {"p1": Producer("p1", "o1", "a", "north", 1.0)}
        record = types.SimpleNamespace(producers=producers, memory=types.SimpleNamespace(year=1))
        self.assertEqual(land_bid.owners_of_sellers(record, recipes, "grain", "north"), ["o1"])
        producers["p2"] = Producer("p2", "o2", "a", "north", 1.0)
        self.assertEqual(land_bid.owners_of_sellers(record, recipes, "grain", "north"), ["o1", "o2"])


class PlannedRecipeIsOneObjectPerHours(unittest.TestCase):
    def test_the_same_hours_give_the_same_recipe_object_with_the_old_hours(self):
        recipe = Recipe("r", {"g": 1.0}, {}, {"smith": 5.0, "miller": 3.0})
        crews = [{"smith": 40.0, "miller": 15.0}, {"smith": 25.0}]
        with entry_practice.shared_crews({"a": types.SimpleNamespace(recipe_id="r", crew_runs=crews[0]),
                                          "b": types.SimpleNamespace(recipe_id="r", crew_runs=crews[1])}) as crews_of:
            peers = crews_of("r")
            first = entry_practice.planned_recipe(recipe, peers, 12.0)
            again = entry_practice.planned_recipe(recipe, peers, 12.0)
        self.assertIs(first, again)
        crew = practice.entrant_crew_runs(recipe, crews)
        totals = {trade: [] for trade in recipe.labour_hours}
        for _year in range(entry_practice.LOSS_YEARS_BEFORE_EXIT):
            hours = practice.recipe_for(recipe, crew).labour_hours
            for trade in totals:
                totals[trade].append(hours[trade])
            crew = practice.crew_runs_after_year(crew, 12.0, 0.0, {})
        for trade, each in totals.items():
            self.assertTrue(math.isclose(first.labour_hours[trade], math.fsum(each) / len(each), rel_tol=1e-12))


class HaulMemo(unittest.TestCase):
    def test_a_run_inputs_haul_with_a_memo_is_the_haul_without(self):
        rng = random.Random(5)
        specs = {good: GoodSpec(good, 1.0, 0.0, 0.0, "") for good in GOODS}
        carriage = types.SimpleNamespace(cost_per_tonne=lambda source, tile: 1.0 + (hash((source, tile)) % 7))
        recipe = Recipe("r", {"grain": 2.0, "iron": 1.0}, {}, {})
        memo = {}
        for _round in range(30):
            supplies = {good: {tile: rng.uniform(0.0, 9.0) for tile in AREAS if rng.random() < 0.6} for good in ("grain", "iron")}
            memo.clear()
            for tile in AREAS:
                self.assertEqual(location_inputs.input_haul_cost(recipe, specs, carriage, supplies, tile, memo),
                                 location_inputs.input_haul_cost(recipe, specs, carriage, supplies, tile))


if __name__ == "__main__":
    unittest.main()
