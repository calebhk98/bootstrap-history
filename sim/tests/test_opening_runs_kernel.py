"""Numba port, the opening's runs: `opening_runs_pack.RunSolver` (the kernel over recipe matrices) agrees with
`opening_runs.required_runs`, and `opening_runs.fit_to_supply` (the sweeps on arrays) agrees with the producer-by-producer
loop it replaced, kept here as `reference_fit_to_supply`, on random recipe systems; no game.

The kernel sums left to right where the old code summed in dict order and with `math.fsum`, and both stop their
fixed-point passes at a relative 1e-9, so figures agree to a relative tolerance, not bit for bit."""

QUICK_TOPIC = True

import math
import random
import types
import unittest

import numpy as np

from sim.economy import opening_runs, opening_runs_pack, producer_table, sites
from sim.economy.producers import Producer
from sim.economy.replaced import replaced
from sim.economy.types import Recipe, SiteLimit, ToolFallback

TOLERANCE = 1e-6


def random_recipes(rng):
    """Recipes in layers: raw goods dug or grown from nothing (some site-bound), goods made from lower layers (some joint, some
    wearing tools with a fallback), and a plant in some."""
    recipes = {}
    layers = [["g%d_%d" % (layer, index) for index in range(rng.randint(2, 4))] for layer in range(4)]
    for layer, goods in enumerate(layers):
        for good in goods:
            for variant in range(rng.randint(1, 2)):
                recipe_id = "r_%s_%d" % (good, variant)
                lower = [each for lower_layer in layers[:layer] for each in lower_layer]
                inputs = {each: rng.uniform(0.1, 3.0) for each in rng.sample(lower, min(len(lower), rng.randint(0, 3)))}
                outputs = {good: rng.uniform(0.5, 5.0)}
                if rng.random() < 0.3:
                    outputs[rng.choice(layers[layer])] = rng.uniform(0.1, 1.0)
                tool_wear, fallbacks = {}, {}
                if inputs and rng.random() < 0.4:
                    tool = rng.choice(sorted(inputs))
                    tool_wear[tool] = inputs[tool] * rng.uniform(0.2, 1.0)
                    other = rng.choice(lower)
                    fallbacks[tool] = (ToolFallback(other, rng.uniform(0.5, 2.0), 1.2, ("labour",)),) if rng.random() < 0.7 else ()
                plant = {rng.choice(lower): rng.uniform(1.0, 5.0)} if lower and rng.random() < 0.2 else {}
                recipes[recipe_id] = Recipe(recipe_id, outputs, inputs, {"labour": rng.uniform(1.0, 20.0)},
                                            plant_goods=plant, plant_life_years=rng.choice([0.0, 10.0]) if plant else 0.0,
                                            site_bound=layer == 0 and rng.random() < 0.5, tool_wear=tool_wear,
                                            tool_fallbacks=fallbacks)
    return recipes, layers


def random_system(rng):
    recipes, layers = random_recipes(rng)
    goods = sorted({good for recipe in recipes.values() for good in recipe.outputs})
    prices = {good: rng.uniform(0.5, 20.0) for good in goods}
    wages = {"labour": rng.uniform(0.5, 3.0)}
    limits = [SiteLimit(recipe_id, "t1", rng.uniform(5.0, 200.0)) for recipe_id, recipe in sorted(recipes.items())
              if recipe.site_bound and rng.random() < 0.8]
    yields = {recipe_id: rng.uniform(0.5, 1.5) for recipe_id in sorted(recipes) if rng.random() < 0.2}
    final = {tile: {good: rng.uniform(1.0, 300.0) for good in rng.sample(goods, rng.randint(2, 8))} for tile in ("t1", "t2")}
    return recipes, prices, wages, limits, yields, final


class RunsAgreeTests(unittest.TestCase):
    def test_the_kernel_finds_the_runs_the_old_fixed_point_finds(self):
        rng = random.Random(5)
        compared = 0
        for _case in range(50):
            recipes, prices, wages, limits, yields, final = random_system(rng)
            ranked = opening_runs.ranked_recipes(recipes, prices, wages, 0.05, None, yields)
            ceilings = opening_runs.run_ceilings(recipes, sites.limits_by_recipe(limits))
            main = opening_runs.main_outputs(recipes, prices)
            expected = opening_runs.required_runs(final, ranked, recipes, ceilings, yields, main)
            solver = opening_runs_pack.RunSolver(recipes, ranked, ceilings, yields, main, wages)
            totals = opening_runs.national_totals(final)
            goods = sorted(totals)
            vector = solver.national_vector(solver.mapping(goods), np.array([totals[good] for good in goods]))
            got = solver.runs_by_recipe(solver.runs(vector))
            scale = max(expected.values(), default=1.0)
            for recipe_id, count in expected.items():
                self.assertAlmostEqual(got[recipe_id], count, delta=TOLERANCE * max(scale, 1.0), msg=recipe_id)
            for recipe_id, count in got.items():
                if recipe_id not in expected:
                    self.assertAlmostEqual(count, 0.0, delta=TOLERANCE * max(scale, 1.0), msg=recipe_id)
            compared += 1
        self.assertEqual(compared, 50)


class ByProductCeilingTests(unittest.TestCase):
    def test_a_user_of_a_by_product_runs_only_as_far_as_the_runs_driven_by_the_main_output_supply_it(self):
        recipes = {"grow": Recipe("grow", {"grain": 100.0}, {}, {"labour": 10.0}),
                   "mill": Recipe("mill", {"flour": 10.0, "bran": 2.0}, {"grain": 12.0}, {"labour": 5.0}),
                   "feed": Recipe("feed", {"pork": 5.0}, {"bran": 3.0}, {"labour": 2.0})}
        prices = {"grain": 0.1, "flour": 2.0, "bran": 0.1, "pork": 5.0}
        wages = {"labour": 1.0}
        ranked = opening_runs.ranked_recipes(recipes, prices, wages, 0.05)
        main = opening_runs.main_outputs(recipes, prices)
        final = {"t1": {"flour": 100.0, "pork": 100.0}}
        expected = opening_runs.required_runs(final, ranked, recipes, {}, {}, main)
        self.assertAlmostEqual(expected["feed"], 2.0 * 10.0 / 3.0)       # ten mill runs make twenty bran, three to a run
        solver = opening_runs_pack.RunSolver(recipes, ranked, {}, {}, main, wages)
        vector = solver.national_vector(solver.mapping(["flour", "pork"]), np.array([100.0, 100.0]))
        got = solver.runs_by_recipe(solver.runs(vector))
        for recipe_id, count in expected.items():
            self.assertAlmostEqual(got[recipe_id], count, delta=TOLERANCE * max(1.0, count))


def reference_fit_to_supply(setup, record) -> None:
    """The producer-by-producer loop `opening_runs.fit_to_supply` was before its sweeps ran on arrays."""
    by_limits = sites.limits_by_recipe(setup.site_limits)
    fixed = opening_runs.limited_goods(setup.recipes, by_limits)
    for _sweep in range(2 * opening_runs.CEILING_SWEEPS):
        held = False
        for good in sorted(fixed):
            supply = math.fsum(producer.expected_sales * producer.yield_factor * setup.recipes[producer.recipe_id].outputs.get(good, 0.0)
                               for producer in record.producers.values())
            users = []
            for producer_id, producer in sorted(record.producers.items()):
                recipe = setup.recipes[producer.recipe_id]
                used = recipe.hard_inputs.get(good, 0.0)
                if recipe.plant_life_years > 0.0:
                    used += recipe.plant_goods.get(good, 0.0) / recipe.plant_life_years
                if used > 0.0 and not sites.is_sited(recipe, by_limits):
                    users.append((producer_id, producer, used))
            wanted = math.fsum(producer.expected_sales * used for _id, producer, used in users)
            if wanted > supply * (1.0 + 1e-9) and wanted > 0.0:
                factor = supply / wanted
                for producer_id, producer, _used in users:
                    producer_table.put_producer(record.producers, replaced(
                        producer, capacity_runs=producer.capacity_runs * factor,
                        expected_sales=producer.expected_sales * factor))
                held = True
        if not held:
            break


def random_producers(rng, recipes):
    producers = {}
    for index in range(rng.randint(4, 40)):
        recipe_id = rng.choice(sorted(recipes))
        sales = rng.uniform(1.0, 100.0)
        producer = Producer("producer:%s@t%d" % (recipe_id, index), "owner", recipe_id, "t1", sales * rng.uniform(1.0, 1.6),
                            yield_factor=rng.uniform(0.6, 1.2), expected_sales=sales)
        producers[producer.agent_id] = producer
    return producers


class FitToSupplyAgreesTests(unittest.TestCase):
    def test_the_sweeps_on_arrays_hold_the_users_the_old_loop_holds(self):
        rng = random.Random(9)
        held_cases = 0
        for _case in range(60):
            recipes, _prices, _wages, limits, _yields, _final = random_system(rng)
            setup = types.SimpleNamespace(recipes=recipes, site_limits=limits)
            producers = random_producers(rng, recipes)
            old = types.SimpleNamespace(producers=dict(producers))
            new = types.SimpleNamespace(producers=dict(producers))
            reference_fit_to_supply(setup, old)
            opening_runs.fit_to_supply(setup, new)
            self.assertEqual(sorted(old.producers), sorted(new.producers))
            for producer_id, expected in old.producers.items():
                self.assertAlmostEqual(new.producers[producer_id].expected_sales, expected.expected_sales,
                                       delta=1e-9 * max(1.0, expected.expected_sales))
                self.assertAlmostEqual(new.producers[producer_id].capacity_runs, expected.capacity_runs,
                                       delta=1e-9 * max(1.0, expected.capacity_runs))
            held_cases += any(old.producers[each].expected_sales != producers[each].expected_sales for each in producers)
        self.assertGreater(held_cases, 5, "the random systems hold some producers back")


if __name__ == "__main__":
    unittest.main()
