"""`goods_turn_offer_kernel.offer_turn` against the numpy steps `TurnWorld.offer` took before it (`goods_turn_offer_plain`), on random
producers with short stocks, missing prices, unnumbered agents and cash shortfalls: every output equal."""
QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import goods_turn_spec
from sim.economy.goods_turn_offer_kernel import offer_turn
from sim.economy.year_arrays_recipes import build_recipe_matrices

from .goods_turn_offer_plain import offer_plain
from .test_goods_turn_kernel import GOODS, TILE, world


def arguments_of(seed):
    rng, recipes, book, _ledger, made = world(seed)
    matrices = build_recipe_matrices(recipes, {}, GOODS)
    spec = goods_turn_spec.build(recipes, {}, matrices)
    count = len(made)
    generator = numpy.random.RandomState(seed)
    slots = matrices.slot_goods.shape[1]
    expected = numpy.where(generator.rand(count, slots) < 0.85, generator.rand(count, slots) + 0.5, numpy.nan)
    slot_of = numpy.full((len(recipes), len(matrices.goods.ids)), -1, dtype=numpy.int64)
    for row in range(len(recipes)):
        for slot, column in enumerate(matrices.slot_goods[row]):
            if column >= 0:
                slot_of[row, column] = slot
    stock = book.stock_rows
    goods = numpy.array([book.good_ids.numbers.get(good, -1) for good in matrices.goods.ids], dtype=numpy.int64)
    agent_of = numpy.array([book.agent_ids.numbers[each.agent_id] for each in made], dtype=numpy.int64)
    if seed % 3 == 0:
        agent_of[rng.randrange(count)] = -1
    position = numpy.array(sorted(rng.sample(range(count), rng.randint(1, count))), dtype=numpy.int64)
    recipe_row = numpy.array([matrices.recipes.row[each.recipe_id] for each in made], dtype=numpy.int64)
    capacity = numpy.array([each.capacity_runs for each in made])
    tile_row = numpy.zeros(count, dtype=numpy.int64)
    tile_of_row = numpy.array([book.tile_ids.numbers[TILE]], dtype=numpy.int64)
    cash = generator.choice([0.0, 5.0, 100.0, 1e4], len(position))
    running = generator.choice([0.0, 3.0, 400.0], len(position))
    cash_target = generator.choice([0.0, 50.0, 700.0, 5e4], count)
    last_runs = generator.choice([-1.0, 0.0, 2.0, 40.0], count)
    sales = generator.rand(count) * 30.0
    pays = generator.rand(count)
    return (position, agent_of, tile_of_row, tile_row, recipe_row, capacity, spec.output_ptr, spec.output_good, spec.output_kept,
            spec.spoilage, goods, expected, slot_of, stock.table.key, stock.table.quantity, stock.index, cash, running, cash_target,
            last_runs, sales, pays, rng.choice([-0.5, 0.0, 0.05, 0.3]), 0.1, 2.0)


class OfferTurnIsTheNumpySteps(unittest.TestCase):

    def test_random_producers_give_the_columns_the_numpy_steps_gave(self):
        slow_seen = quick_seen = 0
        for seed in range(80):
            arguments = arguments_of(seed)
            got, expected = offer_turn(*arguments), offer_plain(*arguments)
            for name, one, other in zip(("slow", "shortfall", "place", "good", "units", "reservation"), got, expected):
                numpy.testing.assert_array_equal(one, other, "%s seed %d" % (name, seed))
            slow_seen += int(got[0].any())
            quick_seen += len(got[5]) > 0
        self.assertGreater(slow_seen, 5)
        self.assertGreater(quick_seen, 20)

    def test_a_written_out_producer_without_a_price_is_slow_and_one_with_is_priced(self):
        arguments = list(arguments_of(1))
        arguments[0] = arguments[0][:1]
        arguments[16], arguments[17] = numpy.array([0.0]), numpy.array([0.0])
        slow, shortfall, _place, _good, _units, reservation = offer_turn(*arguments)
        expected_slow, expected_shortfall, *_rest = offer_plain(*arguments)
        self.assertEqual(slow.tolist(), expected_slow.tolist())
        self.assertEqual(shortfall.tolist(), expected_shortfall.tolist())


if __name__ == "__main__":
    unittest.main()
