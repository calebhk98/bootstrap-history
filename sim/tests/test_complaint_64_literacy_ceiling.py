"""Complaints/64: direct technology literacy effects ignore the ceiling.

The schooling path in _advance_literacy() correctly clamps literacy to
literacy_ceiling_elite(), but the direct tech-effect path in apply_tech_effects()
only clamps to [0.0, 1.0], allowing technologies to push literacy past the
stated ceiling of 0.97.

unittest.TestCase style, like the other focused complaint suites.
"""
import os
import random
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)
from sim import simulator
from sim.engine.core import Sim

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim():
    return Sim(_NODES, list(_NODES), random.Random(1))


class LiteracyCeilingTests(unittest.TestCase):

    def test_direct_tech_effect_respects_elite_ceiling(self):
        # Create a sim and push elite literacy high through tech effects
        sim = _fresh_sim()

        # Start with a high elite literacy (close to ceiling)
        sim.civ["literacy_elite"] = 0.95

        # Apply tech effects that would push it over the ceiling.
        # printing_press adds 0.2 to literacy_elite
        sim.apply_tech_effects("printing_press")

        # Elite literacy should never exceed the ceiling
        elite_ceil = sim.literacy_ceiling_elite()
        self.assertLessEqual(
            sim.civ["literacy_elite"], elite_ceil,
            f"Elite literacy {sim.civ['literacy_elite']} exceeds ceiling {elite_ceil}")

    def test_multiple_tech_effects_respect_elite_ceiling(self):
        # Apply multiple tech effects that would collectively push past the ceiling
        sim = _fresh_sim()
        sim.civ["literacy_elite"] = 0.4

        # Apply several literacy_elite increasing techs
        elite_ceil = sim.literacy_ceiling_elite()

        # Apply tech effects
        for tech_id in ["printing_press", "arithmetic_positional", "school_founded"]:
            if tech_id in _NODES:
                sim.apply_tech_effects(tech_id)

        # Elite literacy should never exceed the ceiling
        self.assertLessEqual(
            sim.civ["literacy_elite"], elite_ceil,
            f"Elite literacy {sim.civ['literacy_elite']} exceeds ceiling {elite_ceil}")

    def test_schooling_path_respects_elite_ceiling(self):
        # The schooling path should already work correctly
        sim = _fresh_sim()
        sim.civ["literacy_elite"] = 0.95

        # Simulate having a school running
        sim.state.projects.operating.add("school_founded")

        # Call _advance_literacy which should respect the ceiling
        sim._advance_literacy(0)

        # Elite literacy should never exceed the ceiling
        elite_ceil = sim.literacy_ceiling_elite()
        self.assertLessEqual(
            sim.civ["literacy_elite"], elite_ceil,
            f"Schooling path: Elite literacy {sim.civ['literacy_elite']} exceeds ceiling {elite_ceil}")

    def test_direct_effect_cannot_exceed_one_zero(self):
        # Even with the current bug, literacy should not exceed 1.0
        # This test documents current behavior
        sim = _fresh_sim()
        sim.civ["literacy_elite"] = 0.99

        # Apply a high effect
        sim.apply_tech_effects("printing_press")

        # Should be clamped to [0, 1] at minimum
        self.assertLessEqual(sim.civ["literacy_elite"], 1.0)
        self.assertGreaterEqual(sim.civ["literacy_elite"], 0.0)


if __name__ == "__main__":
    unittest.main()
