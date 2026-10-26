"""The wild stock is saved with the agriculture module's state (Complaint 411), and the yearly `wild_stock` phase calls the step."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine import year_phases
from sim.agriculture.state import AgricultureWorld
from sim.engine.state import deserialize_state, serialize_state


class WildStockSaveTests(unittest.TestCase):
    def test_the_stock_round_trips_through_serialize_and_deserialize(self):
        world = AgricultureWorld(wild_stock={"tile_a": {"steppe_grazers": 0.4}})
        again = deserialize_state(serialize_state(world), AgricultureWorld)
        self.assertEqual(again.wild_stock, {"tile_a": {"steppe_grazers": 0.4}})


class WildStockPhaseTests(unittest.TestCase):
    def test_the_wild_stock_phase_calls_the_step_once_for_the_world(self):
        calls = []
        sim = types.SimpleNamespace(assembly=types.SimpleNamespace(phase_handler=lambda name: (lambda seats: calls.append((name, seats)))))
        phase = next(phase for phase in year_phases.SHIPPED if phase.name == "wild_stock")
        phase.handler(sim, ["seat"])
        self.assertEqual((phase.scope, calls), (year_phases.WORLD, [("wild_stock", ["seat"])]))


if __name__ == "__main__":
    unittest.main()
