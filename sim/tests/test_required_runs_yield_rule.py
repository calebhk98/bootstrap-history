"""`opening_runs.required_runs` counts the runs that make a demand; a run at a lower yield makes less, so more runs are
needed. A hand-built recipe; no game."""
import unittest

from sim.economy import opening_runs
from sim.economy.types import Recipe

QUICK_TOPIC = True


class RequiredRunsYieldTests(unittest.TestCase):
    def test_a_run_counted_at_a_lower_yield_takes_more_runs(self):
        recipe = Recipe("grow", {"grain": 4.0}, {}, {"labourer": 1.0})
        demand = {"town": {"grain": 1000.0}}
        full = opening_runs.required_runs(demand, {"grain": ["grow"]}, {"grow": recipe})
        half = opening_runs.required_runs(demand, {"grain": ["grow"]}, {"grow": recipe}, None, {"grow": 0.5})
        self.assertAlmostEqual(full["grow"], 250.0)
        self.assertAlmostEqual(half["grow"], 2.0 * full["grow"], delta=1e-9 * full["grow"])


if __name__ == "__main__":
    unittest.main()
