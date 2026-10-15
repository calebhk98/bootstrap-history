"""Complaint 473: a processor of a weight-losing run settles beside its inputs, and a processor of a good only fixed
sites supply is built no larger than the supply that can reach it (sim/economy/location_inputs.py)."""

QUICK_TOPIC = True

import math
import unittest
from types import SimpleNamespace

from sim.economy import entry_sizing, location, location_inputs
from sim.economy.producers import Producer
from sim.economy.types import GoodSpec, MarketArea, Recipe

ORE, METAL, FUEL = "ore_kg", "metal_kg", "fuel_kg"
SPECS = {good: GoodSpec(good, 1.0, 0.0, 0.0, "x") for good in (ORE, METAL, FUEL)}
# a smelter: two tonnes of ore and a little fuel make one tonne of metal (the run loses mass)
SMELT = Recipe("smelt", {METAL: 1000.0}, {ORE: 2000.0, FUEL: 100.0}, {"labourer": 10.0})
MINE = Recipe("mine", {ORE: 1000.0}, {}, {"miner": 1.0}, site_bound=True)
# a foundry: one tonne of metal makes two tonnes of casting (the run gains mass)
CASTING = "casting_kg"
CAST = Recipe("cast", {CASTING: 2000.0}, {METAL: 1000.0}, {"labourer": 10.0})
DISTANCE = {("mine", "market"): 100.0, ("mine", "mine"): 0.0, ("market", "market"): 0.0, ("market", "mine"): 100.0}


class Carriage:
    def cost_per_tonne(self, source, destination):
        return DISTANCE.get((source, destination), math.inf)


class Areas:
    def area_of(self, good, tile):
        if good == METAL:
            return "everywhere"       # a dear good is one market across the tiles
        return good + "@" + tile      # a bulky one is each tile's own


def world(producers, recipes, people):
    record = SimpleNamespace(producers={producer.agent_id: producer for producer in producers})
    setup = SimpleNamespace(recipes=recipes, specs=dict(SPECS, **{CASTING: GoodSpec(CASTING, 1.0, 0.0, 0.0, "x")}),
                            opening_population_by_tile=people, working_share=0.5, working_hours_per_year=2000.0)
    return setup, record


def area(tile):
    return MarketArea("%s@%s" % (tile, "metal"), METAL, (tile,), tile)


class MaterialOrientationTests(unittest.TestCase):
    def setUp(self):
        self.people = {"mine": 1000.0, "market": 1000.0}
        self.recipes = {"smelt": SMELT, "mine": MINE, "cast": CAST}
        mine = Producer("producer:mine@mine", "owner", "mine", "mine", 100.0)
        self.setup, self.record = world([mine], self.recipes, self.people)

    def test_a_run_that_loses_mass_settles_at_its_ore_though_its_metal_is_wanted_elsewhere(self):
        placed = location_inputs.place_oriented(self.setup, self.record, Areas(), Carriage(), SMELT, {ORE: "mine"},
                                                [(area("market"), 10.0)], ["market", "mine"])
        self.assertEqual(placed, {"mine": 10.0})

    def test_a_run_that_gains_mass_settles_at_its_market(self):
        smelter = Producer("producer:smelt@mine", "owner", "smelt", "mine", 50.0)
        setup, record = world(list(self.record.producers.values()) + [smelter], self.recipes, self.people)
        placed = location_inputs.place_oriented(setup, record, Areas(), Carriage(), CAST, {METAL: "smelt"},
                                                [(area("market"), 10.0)], ["market", "mine"])
        self.assertEqual(placed, {"market": 10.0})

    def test_the_cost_of_a_tile_is_inputs_in_plus_output_out_by_the_recipes_masses(self):
        supplies = location_inputs.input_supplies(self.record, self.setup, SMELT)
        at_market = location_inputs.input_haul_cost(SMELT, SPECS, Carriage(), supplies, "market")
        at_mine = location_inputs.input_haul_cost(SMELT, SPECS, Carriage(), supplies, "mine")
        self.assertEqual((at_mine, at_market), (0.0, 2.0 * 100.0))      # two tonnes of ore a run, at 100 a tonne

    def test_a_supply_too_small_for_the_capacity_is_a_shortage_not_a_smaller_opening(self):
        # the mine makes 100 runs of 1000 kg, a smelting run takes 2000 kg: fifty runs fed, eighty wanted
        placed = location_inputs.place_oriented(self.setup, self.record, Areas(), Carriage(), SMELT, {ORE: "mine"},
                                                [(area("market"), 80.0)], ["market", "mine"])
        self.assertEqual(placed, {"mine": 80.0})

    def test_the_ore_other_users_claim_ranks_the_tiles_that_remain(self):
        second = Producer("producer:mine@second", "owner", "mine", "second", 100.0)
        other = Producer("producer:smelt@mine", "owner", "smelt", "mine", 50.0)
        people = dict(self.people, second=1000.0)
        setup, record = world(list(self.record.producers.values()) + [second, other], self.recipes, people)

        class Flat:
            def cost_per_tonne(self, source, destination):
                return 0.0 if source == destination else 100.0
        placed = location_inputs.place_oriented(setup, record, Areas(), Flat(), SMELT, {ORE: "mine"},
                                                [(area("market"), 40.0)], ["second", "mine"])
        # the first mine's ore is spoken for, so the new runs are fed from the second
        self.assertEqual(placed, {"second": 40.0})

    def test_no_ore_in_reach_means_no_processor(self):
        record = SimpleNamespace(producers={})
        placed = location_inputs.place_oriented(self.setup, record, Areas(), Carriage(), SMELT, {ORE: "mine"},
                                                [(area("market"), 10.0)], ["market"])
        self.assertEqual(placed, {})

    def test_a_tile_without_hands_for_the_run_takes_only_what_it_can_staff(self):
        setup, record = world(list(self.record.producers.values()), self.recipes, {"mine": 0.1, "market": 1000.0})
        placed = location_inputs.place_oriented(setup, record, Areas(), Carriage(), SMELT, {ORE: "mine"},
                                                [(area("market"), 10.0)], ["market", "mine"])
        self.assertEqual(placed, {})      # the mine tile has nobody and the market tile no ore

    def test_fixed_inputs_are_those_a_sited_recipe_makes(self):
        limits = {"mine": {"mine": SimpleNamespace()}}
        recipes = dict(self.recipes, fuel_burn=Recipe("fuel_burn", {FUEL: 1.0}, {}, {"labourer": 1.0}))
        self.assertEqual(location_inputs.fixed_inputs(SMELT, {ORE: "mine", FUEL: "fuel_burn"}, recipes, limits),
                         {ORE: "mine"})
        self.assertEqual(location_inputs.fixed_inputs(SMELT, {ORE: "mine"}, self.recipes, {}), {})

    def test_masses_of_goods_with_nothing_to_carry_are_left_out(self):
        specs = dict(SPECS, heat=GoodSpec("heat", math.inf, 0.0, 0.0, "x"))
        self.assertEqual(location_inputs.tonnes_of({ORE: 2000.0, "heat": 5.0}, specs), {ORE: 2.0})


class SitingCostTests(unittest.TestCase):
    def test_hauling_inputs_adds_to_a_runs_cost(self):
        near = location.cost_per_run(SMELT, {"labourer": 1.0}, {ORE: 1.0, FUEL: 1.0}, 0.0, 0.0, 1.0, 1.0, 0.0)
        far = location.cost_per_run(SMELT, {"labourer": 1.0}, {ORE: 1.0, FUEL: 1.0}, 0.0, 0.0, 1.0, 1.0, 50.0)
        self.assertEqual(far - near, 50.0)


class EntrySizingTests(unittest.TestCase):
    def test_inputs_are_weighed_where_the_newcomer_is_built_not_where_its_output_is_wanted(self):
        volumes = {(METAL, "market"): 1e9, (ORE, "market"): 0.0, (FUEL, "market"): 1e9,
                   (ORE, "mine"): 1e9, (FUEL, "mine"): 1e9}

        def traded(good, tile):
            return volumes.get((good, tile))
        at_demand = entry_sizing.sized_runs(SMELT, METAL, 1000.0, 1000.0, "market", traded)
        where_built = entry_sizing.sized_runs(SMELT, METAL, 1000.0, 1000.0, "market", traded, "mine")
        self.assertLess(at_demand, where_built)
        self.assertEqual(where_built, 1000.0)


if __name__ == "__main__":
    unittest.main()
