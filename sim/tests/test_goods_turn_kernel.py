"""`goods_turn_kernel.produce_turn` against `producers.production_lines` (the moves a producer's run books), and
`goods_turn_offers_kernel.offer_pairs` against `year_goods._quick_outputs` (the outputs it offers and at what price), on written-out and
random recipes with tool fallbacks, practised crews and short stocks. The tables the kernels read are those of a real `Book` and `YearLedger`."""
QUICK_TOPIC = True

import dataclasses
import random
import unittest

import numpy

from sim.book import Book
from sim.economy import goods_turn_spec, producers
from sim.economy.practice import practised_multiplier
from sim.economy.year_arrays_producers import practised_yields
from sim.economy.goods_turn_kernel import produce_turn
from sim.economy.goods_turn_offers_kernel import offer_pairs
from sim.economy.types import EDGE_CONSUMPTION, EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Recipe, ToolFallback
from sim.economy.year_arrays_recipes import build_recipe_matrices
from sim.economy.year_ledger import YearLedger

GOODS = ("axe", "bronze", "grain", "iron", "pick", "straw", "tin", "wheat", "zinc")
TRADES = ("miner", "smith")
TILE = "t1"


def random_recipe(rng, number):
    inputs = {good: rng.uniform(0.2, 3.0) for good in rng.sample(("grain", "iron", "tin", "zinc"), rng.randint(1, 3))}
    wear = {good: rng.uniform(0.05, 0.5) for good in rng.sample(("axe", "pick"), rng.randint(0, 2))}
    inputs.update(wear)
    fallbacks = {}
    for good in wear:
        steps = []
        for _step in range(rng.randint(0, 3)):
            kind = rng.choice(("tool", "hand", "dead"))
            trades = tuple(rng.sample(TRADES, rng.randint(0, 2)))
            if kind == "tool":
                steps.append(ToolFallback(rng.choice(("straw", "wheat", "bronze", "axe")), rng.uniform(0.1, 0.8), rng.choice((1.0, 1.5, 2.5)), trades))
            elif kind == "hand":
                steps.append(ToolFallback("", 0.0, rng.choice((1.0, 2.0, 3.0)), trades))
            else:
                steps.append(ToolFallback("straw", 0.0, 1.5, trades))
        fallbacks[good] = tuple(steps)
    hours = {trade: rng.uniform(1.0, 5.0) for trade in rng.sample(TRADES, rng.randint(1, 2))}
    for steps in fallbacks.values():     # a step's trades are among the recipe's own
        for step_number, step in enumerate(steps):
            steps = steps[:step_number] + (ToolFallback(step.good, step.units_per_run, step.hours_factor,
                                                        tuple(trade for trade in step.trades if trade in hours)),) + steps[step_number + 1:]
    fallbacks = {good: tuple(ToolFallback(step.good, step.units_per_run, step.hours_factor, tuple(t for t in step.trades if t in hours))
                             for step in steps) for good, steps in fallbacks.items()}
    outputs = {good: rng.uniform(0.5, 4.0) for good in rng.sample(("bronze", "grain", "iron", "tin"), rng.randint(1, 3))}
    return Recipe("r%d" % number, outputs, inputs, hours, tool_wear=wear, tool_fallbacks=fallbacks)


def Producer(agent_id, recipe, capacity, yield_factor, crew_runs):
    """A producer of the recipe (`production_lines` reads its yield factor lowered by the crew's spoilage)."""
    return producers.Producer(agent_id, "owner", recipe.recipe_id, TILE, capacity, yield_factor, crew_runs=crew_runs)


def world(seed):
    rng = random.Random(seed)
    recipes = {"r%d" % number: random_recipe(rng, number) for number in range(4)}
    book = Book()
    ledger = YearLedger(book=book)
    producers_made = []
    for number in range(6):
        recipe = rng.choice(list(recipes.values()))
        producers_made.append(Producer("p%d" % number, recipe, rng.uniform(1.0, 30.0), rng.choice((1.0, 0.8, 1.3)),
                                       {trade: rng.uniform(1.0, 200.0) for trade in recipe.labour_hours if rng.random() < 0.4}))
    for each in producers_made:
        for good in GOODS:
            if rng.random() < 0.7:
                book.post([], [GoodsMove(EDGE_MINT, each.agent_id, good, TILE, rng.choice((0.0, 0.3, 2.0, 15.0, 90.0)), "start")])
        for trade in TRADES:
            if rng.random() < 0.8:
                ledger.hours_hired.setdefault(each.agent_id, {})[trade] = rng.choice((0.0, 4.0, 30.0, 400.0, 5000.0))
    for name in (EDGE_CONSUMPTION, EDGE_PRODUCTION):
        book.agent_number(name)
    return rng, recipes, book, ledger, producers_made


def kernel_yield(matrices, made, practice_scale):
    """The yield factors the kernel is given: each producer's lowered by its crew's spoilage (`practised_yields`)."""
    booked = matrices.labour_hours[numpy.array([matrices.recipes.row[each.recipe_id] for each in made], dtype=numpy.int64)]
    crewed = [place for place, each in enumerate(made) if each.crew_runs]
    return practised_yields(numpy.array([each.yield_factor for each in made]), booked, practice_scale, crewed)


def kernel_moves(recipes, book, ledger, made, runs, practice_scale):
    """`produce_turn` for `made` with `runs` planned: its moves as (producer id, good, quantity, is output) tuples."""
    matrices = build_recipe_matrices(recipes, {}, GOODS)
    spec = goods_turn_spec.build(recipes, {}, matrices)
    ledger.tables.flush()
    stock, hours = book.stock_rows, ledger.tables.pairs["hours_hired"].rows
    goods = numpy.array([book.good_ids.numbers.get(good, -1) for good in matrices.goods.ids], dtype=numpy.int64)
    trades = numpy.array([ledger.tables.markets.trades.numbers.get(trade, -1) for trade in matrices.trades.ids], dtype=numpy.int64)
    agent = numpy.array([book.agent_ids.numbers[each.agent_id] for each in made], dtype=numpy.int64)
    tile = numpy.full(len(made), book.tile_ids.numbers[TILE], dtype=numpy.int64)
    place, good, quantity, output = produce_turn(
        numpy.array(runs, dtype=float), agent, tile, numpy.array([matrices.recipes.row[each.recipe_id] for each in made], dtype=numpy.int64),
        numpy.array([each.capacity_runs for each in made]), kernel_yield(matrices, made, practice_scale),
        numpy.arange(len(made)), practice_scale, spec.hard_ptr, spec.hard_good, spec.hard_per_run, spec.wear_ptr, spec.wear_draw,
        spec.wear_per_run, spec.step_ptr, spec.step_draw, spec.step_units, spec.step_factor, spec.step_trade_ptr, spec.step_trade_slot,
        spec.draw_ptr, spec.draw_good, spec.draw_listed, spec.labour_ptr, spec.labour_trade, spec.labour_hours, spec.output_ptr,
        spec.output_good, spec.output_per_run, spec.lines_most, goods, trades, stock.table.key, stock.table.quantity, stock.index,
        hours.table.key, hours.table.amount, hours.index)
    return [(made[each].agent_id, matrices.goods.ids[row], units, bool(is_output))
            for each, row, units, is_output in zip(place.tolist(), good.tolist(), quantity.tolist(), output.tolist())]


def python_moves(recipes, book, ledger, made, runs):
    moves = []
    for each, planned in zip(made, runs):
        if not planned > 0.0:
            continue
        recipe = recipes[each.recipe_id]
        held = {good: book.stock(each.agent_id, good, TILE) for good in recipe.inputs}
        hired = {trade: ledger.hours_hired.get(each.agent_id, {}).get(trade, 0.0) for trade in recipe.labour_hours}
        _achieved, lines = producers.production_lines(each, recipe, held, hired, planned)
        moves.extend((line[0] if line[5] == "input" else line[1], line[2], line[4], line[5] == "output") for line in lines)
    return moves


def scale_of(made, recipes):
    matrices = build_recipe_matrices(recipes, {}, GOODS)
    scale = numpy.ones((len(made), len(matrices.trades.ids)))
    for place, each in enumerate(made):
        for trade, units in each.crew_runs.items():
            scale[place, matrices.trades.row[trade]] = practised_multiplier(units)
    return scale


class ProduceTurnIsProductionLines(unittest.TestCase):

    def test_random_producers_make_the_moves_production_lines_books(self):
        short_runs = 0
        for seed in range(60):
            rng, recipes, book, ledger, made = world(seed)
            runs = [rng.choice((0.0, 1.0, 5.0, 40.0, numpy.nan)) for _each in made]
            expected = python_moves(recipes, book, ledger, made, runs)
            got = kernel_moves(recipes, book, ledger, made, runs, scale_of(made, recipes))
            self.assertEqual(got, expected, seed)
            short_runs += any(not output for _agent, _good, _quantity, output in expected)
        self.assertGreater(short_runs, 5)       # the stocks and hours are short often enough for the limits to bind

    def test_a_practised_crew_is_held_to_the_hours_its_multiplier_gives(self):
        for seed in range(200, 230):
            rng, recipes, book, ledger, made = world(seed)
            runs = [20.0] * len(made)
            made[:] = [dataclasses.replace(each, crew_runs={trade: 1.0 for trade in recipes[each.recipe_id].labour_hours}) for each in made]
            self.assertEqual(kernel_moves(recipes, book, ledger, made, runs, scale_of(made, recipes)),
                             python_moves(recipes, book, ledger, made, runs), seed)


class OfferPairsAreQuickOutputs(unittest.TestCase):

    def test_random_producers_offer_what_quick_outputs_would(self):
        for seed in range(40):
            rng, recipes, book, _ledger, made = world(seed)
            matrices = build_recipe_matrices(recipes, {}, GOODS)
            spec = goods_turn_spec.build(recipes, {}, matrices)
            slots = matrices.slot_goods.shape[1]
            expected = numpy.where(numpy.random.RandomState(seed).rand(len(made), slots) < 0.85,
                                   numpy.random.RandomState(seed + 1).rand(len(made), slots) + 0.5, numpy.nan)
            slot_of = numpy.full((len(recipes), len(matrices.goods.ids)), -1, dtype=numpy.int64)
            for row in range(len(recipes)):
                for slot, column in enumerate(matrices.slot_goods[row]):
                    if column >= 0:
                        slot_of[row, column] = slot
            stock = book.stock_rows
            goods = numpy.array([book.good_ids.numbers.get(good, -1) for good in matrices.goods.ids], dtype=numpy.int64)
            agent = numpy.array([book.agent_ids.numbers[each.agent_id] for each in made], dtype=numpy.int64)
            ptr, pair_good, units, price, spoilage, slow = offer_pairs(
                numpy.arange(len(made)), agent, numpy.full(len(made), book.tile_ids.numbers[TILE], dtype=numpy.int64),
                numpy.array([matrices.recipes.row[each.recipe_id] for each in made], dtype=numpy.int64),
                numpy.array([each.capacity_runs for each in made]), spec.output_ptr, spec.output_good, spec.output_kept, spec.spoilage,
                goods, expected, slot_of, stock.table.key, stock.table.quantity, stock.index)
            for place, each in enumerate(made):
                recipe = recipes[each.recipe_id]
                stocks = {good: book.stock(each.agent_id, good, TILE) for good in recipe.outputs}
                keep = {good: recipe.inputs.get(good, 0.0) * each.capacity_runs for good in recipe.outputs}
                row = matrices.recipes.row[each.recipe_id]
                prices = {good: expected[place, slot_of[row, matrices.goods.row[good]]] for good in recipe.outputs}
                wanted, none = [], False
                for good in sorted(recipe.outputs):
                    quantity = stocks[good] - keep[good]
                    if quantity <= 0.0:
                        continue
                    if prices[good] != prices[good]:
                        none = True
                        continue
                    wanted.append((good, quantity, prices[good]))
                self.assertEqual(bool(slow[place]), none, (seed, place))
                got = [(matrices.goods.ids[pair_good[each_pair]], units[each_pair], price[each_pair])
                       for each_pair in range(ptr[place], ptr[place + 1])]
                self.assertEqual(got, wanted, (seed, place))


if __name__ == "__main__":
    unittest.main()
