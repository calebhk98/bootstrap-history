"""One good's tonnes by tile (`output_tonnes_of`, summed by `Revenue.output_tonnes`) equal the sum over the table of every good's tonnes."""

QUICK_TOPIC = True

from sim.tests import repository_tables
import random
import unittest
from types import SimpleNamespace

from sim.actors.world_revenue import Revenue
from sim.markets.reads_producers import ProducerReads
from sim.tests.output_tonnes_plain import output_tonnes_by_table
from sim.tests.world_stand_in import fake_needs

GOODS = ["wheat_kg", "cloth_kg", "iron_bar_kg", "salt_kg"]


def _reads(output_by_tile):
    economy = SimpleNamespace(record=SimpleNamespace(goods=SimpleNamespace(output_by_tile=output_by_tile)))
    return ProducerReads(SimpleNamespace(economy=lambda: economy, tonnes_per_unit=repository_tables.tonnes_per_unit))


class OutputTonnesTests(unittest.TestCase):
    def test_written_out_tiles(self):
        reads = _reads({"b": {"cloth_kg": 1000.0}, "a": {"cloth_kg": 4000.0, "wheat_kg": 9000.0}})
        self.assertEqual(list(reads.output_tonnes_of("cloth_kg").items()), [("a", 4.0), ("b", 1.0)])
        self.assertEqual(reads.output_tonnes_of("wheat_kg"), {"a": 9.0, "b": 0.0})

    def test_random_tiles_sum_as_the_whole_table_did(self):
        for seed in range(40):
            generator = random.Random(seed)
            tiles = ["t%02d" % number for number in generator.sample(range(30), generator.randint(0, 12))]
            output = {tile: {good: generator.random() * 5000.0 for good in generator.sample(GOODS, generator.randint(0, 4))} for tile in tiles}
            held = set(generator.sample(tiles, len(tiles) // 2))
            reads = _reads(output)
            for good in GOODS:
                view = Revenue(SimpleNamespace(needs=fake_needs(agent_output_tonnes_of={good: reads.output_tonnes_of(good)})))
                view.held_tiles = lambda held=held: sorted(held)
                self.assertEqual(view.output_tonnes(good), output_tonnes_by_table(output, good, held), (seed, good))
