"""labour_productivity: the productivity multiplier, the leak of a venture's edge and the material-gating rule
(Complaint 640 audit: rules on inputs built here, no game; the same mechanisms through a game are
test_labour_productivity_scenario)."""
import types
import unittest

from sim.diffusion.diffusion_curve import knowledge_half_life, leaked_share
from sim.engine import validate_material_gating as _gating
from sim.labour.api import Labour

from .harness import check
from .harness import NODES, ROOT

QUICK_TOPIC = True


class _Stub:
    """What labour_productivity reads: the wired sources, the techniques done, the cap and the researchers' pace."""
    LABOUR_PRODUCTIVITY_CAP = 1.5

    def __init__(self, sources, done=(), research=1.0):
        self._world = types.SimpleNamespace(
            LABOUR_PRODUCTIVITY_SOURCES=tuple(sources),
            projects=types.SimpleNamespace(done=set(done)),
            research_productivity=lambda: research)


class Productivity(unittest.TestCase):
    SOURCES = (("trip_hammer", "smith", 0.2), ("bellows", "smith", 0.1), ("plough", "farmer", 0.3))

    def test_nothing_built_is_an_hour_for_an_hour(self):
        self.assertEqual(Labour.labour_productivity(_Stub(self.SOURCES), "smith"), 1.0)

    def test_a_built_technique_raises_its_trade_only(self):
        stub = _Stub(self.SOURCES, done=("trip_hammer",))
        self.assertAlmostEqual(Labour.labour_productivity(stub, "smith"), 1.2)
        self.assertEqual(Labour.labour_productivity(stub, "carpenter"), 1.0)

    def test_techniques_add_up(self):
        stub = _Stub(self.SOURCES, done=("trip_hammer", "bellows"))
        self.assertAlmostEqual(Labour.labour_productivity(stub, "smith"), 1.3)

    def test_stacking_everything_stays_under_the_cap(self):
        stub = _Stub((("a", "smith", 0.4), ("b", "smith", 0.4), ("c", "smith", 0.4)), done=("a", "b", "c"))
        self.assertEqual(Labour.labour_productivity(stub, "smith"), _Stub.LABOUR_PRODUCTIVITY_CAP)

    def test_an_unbuilt_source_adds_nothing(self):
        stub = _Stub(self.SOURCES, done=("plough",))
        self.assertEqual(Labour.labour_productivity(stub, "smith"), 1.0)


class DiffusionCurve(unittest.TestCase):

    def test_on_the_day_the_doors_open_nothing_has_leaked(self):
        self.assertEqual(leaked_share(0.0, 20.0, 0.65), 0.0)
        self.assertEqual(leaked_share(-5.0, 20.0, 0.65), 0.0)

    def test_half_the_edge_is_gone_after_one_half_life(self):
        self.assertAlmostEqual(leaked_share(20.0, 20.0, 0.9), 0.5)

    def test_a_first_mover_never_loses_all_of_it(self):
        self.assertEqual(leaked_share(10000.0, 20.0, 0.65), 0.65)

    def test_published_knowledge_leaks_faster(self):
        plain = knowledge_half_life(100.0, 1.0, 0.1, 0.3, 0.5, 1.0, 2.0, 0.1)
        published = knowledge_half_life(100.0, 2.0, 0.1, 0.3, 0.5, 1.0, 2.0, 0.1)
        self.assertLess(published, plain)
        self.assertLess(leaked_share(0.0, plain, 0.65), leaked_share(30.0, plain, 0.65))
        self.assertGreater(leaked_share(30.0, published, 0.65), leaked_share(30.0, plain, 0.65))

    def test_a_more_literate_country_leaks_faster(self):
        self.assertLess(knowledge_half_life(100.0, 1.0, 0.3, 0.3, 0.5, 1.0, 2.0, 0.1),
                        knowledge_half_life(100.0, 1.0, 0.03, 0.3, 0.5, 1.0, 2.0, 0.1))

    def test_the_pace_floor_bounds_the_half_life(self):
        self.assertEqual(knowledge_half_life(100.0, 0.0, 0.0, 0.3, 0.0, 0.0, 2.0, 0.25), 400.0)


# --- the rubber bug: a node consumed a material nothing in its own ancestry can produce, and the game sold it at a flat
# book price. The rule and its data live in data/material_gating.json and sim/engine/validate_material_gating.py.
_rules = _gating.load_gating(ROOT)
_gaps = _gating.check_material_gating(NODES, _rules)
check("every consumer of a gated material has a producer in its own ancestry, "
      "or a declared reason it does not", not _gaps, _gaps)
_probe_nodes = {"maker": {"pre": []}, "user": {"pre": ["maker"], "mat": {"widget_kg": 1}},
                "stranger": {"pre": [], "mat": {"widget_kg": 1}}}
_probe_rule = {"widget_kg": {"producer_nodes": ["maker"]}}
check("the gating rule flags a consumer with no producer and accepts a declared exemption",
      len(_gating.check_material_gating(_probe_nodes, _probe_rule)) == 1
      and _gating.check_material_gating(
          _probe_nodes, {"widget_kg": {**_probe_rule["widget_kg"],
                                       "ungated_consumers": {"stranger": "judged purchasable here"}}}) == [],
      _gating.check_material_gating(_probe_nodes, _probe_rule))


if __name__ == "__main__":
    unittest.main()
