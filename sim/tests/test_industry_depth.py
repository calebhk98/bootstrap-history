"""Complaint 111: how established an industry is comes out of the simulation, never out of the tree.

Depth is worker-years actually spent running a technique (anyone's concern), decayed year on year. It shortens
the ramp, lowers the failure risk and lifts the scale a concern can reach."""

QUICK_TOPIC = True

import collections
import types
import unittest

from sim.engine import industry_depth
from sim.engine.economy_production import ProductionMixin
from sim.engine.projects_progress import ProgressMixin

Depth = industry_depth.IndustryDepthMixin


def world(experience=None, founding_staff=2.0, concerns=None, seeded=True, granted=None):
    """A bare stand-in for the Sim with only what the depth, ramp and risk code read."""
    projects = types.SimpleNamespace(
        industry_years=dict(experience or {}), industry_seeded=seeded, granted=set(granted or ()), opened_year={"loom": 10}, done_year={},
        failed_attempts=collections.defaultdict(int), uninformed_failures={}, done=set(), operating=set())
    stub = types.SimpleNamespace(
        state=types.SimpleNamespace(projects=projects, scenario=types.SimpleNamespace(year=10)),
        cfg={"revenue_ramp_years": 4.0}, nodes={"loom": {"risk": 0.3}},
        RETRY_RISK_FLOOR=ProgressMixin.RETRY_RISK_FLOOR, RETRY_RISK_DECAY=ProgressMixin.RETRY_RISK_DECAY,
        CONTROL_RELIEF_FACTOR=ProgressMixin.CONTROL_RELIEF_FACTOR)
    stub.founding_worker_years = lambda node_id: founding_staff
    stub.concern_worker_years_this_year = lambda: dict(concerns or {})
    stub.industry_experience = lambda node_id: Depth.industry_experience(stub, node_id)
    stub.industry_depth = lambda node_id: Depth.industry_depth(stub, node_id)
    stub.is_venture = lambda node_id: True
    stub.seed_opening_industry_experience = lambda: Depth.seed_opening_industry_experience(stub)
    stub.nodes_with_mechanic = lambda name: []
    stub.mechanic = lambda node_id, name: None
    stub._retry_risk_multiplier = lambda node_id: ProgressMixin._retry_risk_multiplier(stub, node_id)
    stub._control_relief_multiplier = lambda node_id: 1.0
    return stub


class IndustryDepth(unittest.TestCase):

    def test_the_first_of_its_kind_has_no_depth(self):
        self.assertEqual(world().industry_depth("loom"), 0.0)

    def test_depth_grows_only_from_simulated_worker_years(self):
        quiet = world()
        for _ in range(20):
            Depth.accrue_industry_experience(quiet)
        self.assertEqual(quiet.industry_depth("loom"), 0.0)
        busy = world(concerns={"loom": 2.0})
        before = busy.industry_depth("loom")
        Depth.accrue_industry_experience(busy)
        self.assertGreater(busy.industry_depth("loom"), before)

    def test_experience_fades_when_nobody_runs_the_technique(self):
        stub = world(experience={"loom": 10.0})
        Depth.accrue_industry_experience(stub)
        self.assertLess(stub.industry_experience("loom"), 10.0)

    def test_depth_is_a_share_below_one_and_rises_with_experience(self):
        shallow, deep = world(experience={"loom": 1.0}), world(experience={"loom": 500.0})
        self.assertLess(shallow.industry_depth("loom"), deep.industry_depth("loom"))
        self.assertLess(deep.industry_depth("loom"), 1.0)

    def test_the_same_experience_is_deeper_for_a_smaller_concern(self):
        small = world(experience={"loom": 6.0}, founding_staff=1.0)
        large = world(experience={"loom": 6.0}, founding_staff=10.0)
        self.assertGreater(small.industry_depth("loom"), large.industry_depth("loom"))

    def test_an_established_industry_ramps_faster_than_the_first_of_its_kind(self):
        first, established = world(), world(experience={"loom": 40.0})
        self.assertGreater(ProductionMixin.venture_ramp(established, "loom"), ProductionMixin.venture_ramp(first, "loom"))
        self.assertLessEqual(ProductionMixin.venture_ramp(established, "loom"), 1.0)

    def test_the_first_of_its_kind_ramps_over_the_configured_years(self):
        self.assertAlmostEqual(ProductionMixin.venture_ramp(world(), "loom"), 1.0 / 4.0)

    def test_an_established_industry_fails_less_than_the_first_of_its_kind(self):
        first, established = world(), world(experience={"loom": 40.0})
        self.assertAlmostEqual(ProgressMixin.effective_risk(first, "loom", precaution=False), 0.3)
        self.assertLess(ProgressMixin.effective_risk(established, "loom", precaution=False), 0.3)

    def test_depth_and_retry_learning_do_not_stack(self):
        both = world(experience={"loom": 40.0})
        both.state.projects.failed_attempts["loom"] = 3
        retry_alone = world()
        retry_alone.state.projects.failed_attempts["loom"] = 3
        depth_alone = world(experience={"loom": 40.0})
        lower = min(ProgressMixin.effective_risk(retry_alone, "loom", precaution=False),
                    ProgressMixin.effective_risk(depth_alone, "loom", precaution=False))
        self.assertAlmostEqual(ProgressMixin.effective_risk(both, "loom", precaution=False), lower)

    def test_the_reachable_scale_rises_with_experience(self):
        self.assertEqual(Depth.industry_scale_ceiling(world(), "loom"), 1.0)
        self.assertGreater(Depth.industry_scale_ceiling(world(experience={"loom": 40.0}), "loom"), 1.0)

    def test_an_opening_technique_starts_established_and_an_unrun_one_at_zero(self):
        opening = world(seeded=False, granted={"loom"})
        self.assertGreater(opening.industry_depth("loom"), 0.25)
        self.assertGreater(Depth.industry_scale_ceiling(opening, "loom"), 1.0)
        self.assertEqual(opening.industry_depth("anvil"), 0.0)

    def test_the_seeded_stock_is_the_steady_state_of_its_own_upkeep(self):
        opening = world(seeded=False, granted={"loom"}, concerns={"loom": 2.0})
        before = opening.industry_experience("loom")
        Depth.accrue_industry_experience(opening)
        self.assertAlmostEqual(opening.industry_experience("loom"), before, places=6)

    def test_nothing_reads_a_depth_written_on_the_tree(self):
        stub = world()
        stub.nodes = {"loom": {"risk": 0.3, "depth": 0.9, "supplier_depth": 0.9, "maturity": 0.9}}
        self.assertAlmostEqual(ProgressMixin.effective_risk(stub, "loom", precaution=False), 0.3)
        self.assertEqual(stub.industry_depth("loom"), 0.0)


if __name__ == "__main__":
    unittest.main()
