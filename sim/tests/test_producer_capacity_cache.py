"""The per-material producer capacity table equals the per-material loop and is rebuilt when a producer is replaced."""
QUICK_TOPIC = True

import dataclasses
import types
import unittest

from sim.materials import capacity as material_capacity

RECIPES = {"a": types.SimpleNamespace(outputs={"glass_kg": 200.0, "ash_kg": 7.0}),
           "b": types.SimpleNamespace(outputs={"glass_kg": 100.0})}


@dataclasses.dataclass(frozen=True)
class Plant:
    recipe_id: str
    capacity_runs: float


class CapacityCacheTests(unittest.TestCase):
    def test_the_table_matches_the_single_material_loop_exactly(self):
        producers = [Plant("a", 0.1), Plant("b", 0.7), Plant("gone", 9.0), Plant("a", 0.3)]
        table = material_capacity.producer_units_by_material(producers, RECIPES)
        for material in ("glass_kg", "ash_kg", "tin_kg"):
            loop = material_capacity.producer_capacity_tonnes(producers, RECIPES, material, 1.0)
            self.assertEqual(table.get(material, 0.0), loop)

    def test_the_cache_follows_a_replaced_producer_and_keeps_the_table_otherwise(self):
        cache = material_capacity.ProducerCapacityCache()
        owner = object()
        producers = [Plant("a", 1.0), Plant("b", 2.0)]
        builds = []

        def scoped():
            builds.append(1)
            return producers

        first = cache.units_by_material(owner, producers, scoped, RECIPES)
        self.assertEqual(first["glass_kg"], 400.0)
        self.assertIs(cache.units_by_material(owner, list(producers), scoped, RECIPES), first)
        self.assertEqual(len(builds), 1)
        producers[0] = Plant("a", 3.0)
        self.assertEqual(cache.units_by_material(owner, producers, scoped, RECIPES)["glass_kg"], 800.0)
        self.assertEqual(len(builds), 2)


if __name__ == "__main__":
    unittest.main()
