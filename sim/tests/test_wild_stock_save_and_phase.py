"""The wild stock is saved with the economy (Complaint 411), and the yearly `wild_stock` phase calls the step."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine import year_phases
from sim.engine.state import EconomyState, deserialize_state, serialize_state


class WildStockSaveTests(unittest.TestCase):
    def test_the_stock_round_trips_through_serialize_and_deserialize(self):
        economy = EconomyState()
        economy.wild_stock = {"tile_a": {"steppe_grazers": 0.4}}
        again = deserialize_state(serialize_state(economy), EconomyState)
        self.assertEqual(again.wild_stock, {"tile_a": {"steppe_grazers": 0.4}})


class WildStockPhaseTests(unittest.TestCase):
    def test_the_wild_stock_phase_calls_the_step_once_for_the_world(self):
        calls = []
        sim = types.SimpleNamespace(step_wild_stock=lambda: calls.append("step"))
        phase = next(phase for phase in year_phases.SHIPPED if phase.name == "wild_stock")
        phase.handler(sim, ["seat"])
        self.assertEqual((phase.scope, calls), (year_phases.WORLD, ["step"]))


if __name__ == "__main__":
    unittest.main()
