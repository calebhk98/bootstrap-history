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
from sim.engine.projects_ventures import VenturesMixin as Ventures

Depth = industry_depth.IndustryDepthMixin


def world(experience=None, founding_staff=2.0, concerns=None, seeded=True, granted=None, opening=None, people=None):
    """A bare stand-in for the Sim with only what the depth, ramp and risk code read. `experience` is
    worker-years a node holds in the artisan trade."""
    tenure = {"artisan": {node: years for node, years in (experience or {}).items()}} if experience else {}
    projects = types.SimpleNamespace(
        tenure=tenure, tenure_headcount={}, industry_seeded=seeded, industry_opening_rate={}, granted=set(granted or ()),
        opened_year={"loom": 10}, done_year={}, failed_attempts=collections.defaultdict(int), done=set(), operating=set())
    stub = types.SimpleNamespace(
        state=types.SimpleNamespace(projects=projects, scenario=types.SimpleNamespace(year=10)),
        cfg={"revenue_ramp_years": 4.0}, nodes={"loom": {"risk": 0.3, "ph": 4000.0}},
        CONTROL_RELIEF_FACTOR=ProgressMixin.CONTROL_RELIEF_FACTOR, HOURS_PER_PERSON_YEAR=2000.0,
        labour=types.SimpleNamespace(people_who_exist=lambda trade: (people or {}).get(trade, 100.0)))
    stub.founding_staff_by_trade = lambda node_id: {"artisan": founding_staff}
    stub.founding_worker_years = lambda node_id: Depth.founding_worker_years(stub, node_id)
    stub.attempt_worker_years_by_trade = lambda node_id: Depth.attempt_worker_years_by_trade(stub, node_id)
    stub.concern_worker_years_this_year = lambda: dict(concerns or {})
    stub.tenure_leavers_share = lambda: 0.1
    stub.tenure_weights = lambda node_id: {"artisan": 1.0}
    stub.industry_tenure = lambda: Depth.industry_tenure(stub)
    stub.industry_experience = lambda node_id: Depth.industry_experience(stub, node_id)
    stub.industry_tenure_by_trade = lambda node_id: Depth.industry_tenure_by_trade(stub, node_id)
    stub.industry_depth = lambda node_id: Depth.industry_depth(stub, node_id)
    stub.add_industry_years = lambda node_id, years: Depth.add_industry_years(stub, node_id, years)
    stub.learn_from_failed_attempt = lambda node_id: Depth.learn_from_failed_attempt(stub, node_id)
    stub.after_failed_attempts = lambda node_id, count: Depth.after_failed_attempts(stub, node_id, count)
    stub.fade_industry_tenure = lambda: Depth.fade_industry_tenure(stub)
    stub.opening_worker_years_by_node = lambda: dict(opening or {})
    stub.is_venture = lambda node_id: True
    stub.seed_opening_industry_experience = lambda: Depth.seed_opening_industry_experience(stub)
    stub.nodes_with_mechanic = lambda name: []
    stub.mechanic = lambda node_id, name: None
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

    def test_experience_fades_at_the_rate_people_leave_work(self):
        stub = world(experience={"loom": 10.0})
        Depth.accrue_industry_experience(stub)
        self.assertAlmostEqual(stub.industry_experience("loom"), 9.0)

    def test_tenure_goes_with_people_who_leave_the_trade(self):
        stub = world(experience={"loom": 10.0}, people={"artisan": 50.0})
        stub.state.projects.tenure_headcount = {"artisan": 100.0}
        Depth.accrue_industry_experience(stub)
        self.assertLess(stub.industry_experience("loom"), 9.0)

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

    def test_a_diagnosed_failed_attempt_adds_to_the_same_stock(self):
        stub = world()
        before = ProgressMixin.effective_risk(stub, "loom", precaution=False)
        stub.learn_from_failed_attempt("loom")
        self.assertAlmostEqual(stub.industry_experience("loom"), 2.0)
        self.assertLess(ProgressMixin.effective_risk(stub, "loom", precaution=False), before)

    def test_quoting_odds_after_more_failures_leaves_the_stock_as_it_was(self):
        stub = world(experience={"loom": 3.0})
        with stub.after_failed_attempts("loom", 4):
            self.assertAlmostEqual(stub.industry_experience("loom"), 11.0)
        self.assertAlmostEqual(stub.industry_experience("loom"), 3.0)

    def test_the_reachable_scale_rises_with_experience(self):
        self.assertEqual(Depth.industry_scale_ceiling(world(), "loom"), 1.0)
        self.assertGreater(Depth.industry_scale_ceiling(world(experience={"loom": 40.0}), "loom"), 1.0)

    def test_an_opening_technique_starts_established_and_an_unrun_one_at_zero(self):
        opening = world(seeded=False, granted={"loom"})
        self.assertGreater(opening.industry_depth("loom"), 0.25)
        self.assertGreater(Depth.industry_scale_ceiling(opening, "loom"), 1.0)
        self.assertEqual(opening.industry_depth("anvil"), 0.0)

    def test_an_opening_workforce_of_many_workshops_sizes_the_seed(self):
        one = world(seeded=False, granted={"loom"})
        many = world(seeded=False, granted={"loom"}, opening={"loom": 40.0})
        self.assertGreater(Depth.industry_scale_ceiling(many, "loom"), 5.0 * Depth.industry_scale_ceiling(one, "loom"))
        self.assertGreater(many.industry_depth("loom"), 0.9)

    def test_the_seeded_stock_is_the_steady_state_of_its_own_upkeep(self):
        opening = world(seeded=False, granted={"loom"}, opening={"loom": 7.0})
        opening.concern_worker_years_this_year = lambda: Depth.concern_worker_years_this_year(opening)
        opening.state.actors = None
        before = opening.industry_experience("loom")
        Depth.accrue_industry_experience(opening)
        self.assertAlmostEqual(opening.industry_experience("loom"), before, places=6)

    def test_a_concern_runs_without_its_founder_once_its_staff_hold_a_years_running(self):
        green = world(experience={"loom": 1.9}, founding_staff=2.0)
        seasoned = world(experience={"loom": 2.0}, founding_staff=2.0)
        self.assertFalse(Depth.concern_runs_without_founder(green, "loom"))
        self.assertTrue(Depth.concern_runs_without_founder(seasoned, "loom"))

    def test_the_founders_scholars_are_released_when_the_concern_runs_without_him(self):
        for experience, scholars in ((0.0, 1.0), (50.0, 0.0)):
            stub = world(experience={"loom": experience})
            stub.venture_hands_founder_staffed = lambda node_id: (1.0, 3.0)
            stub.concern_runs_without_founder = lambda node_id, stub=stub: Depth.concern_runs_without_founder(stub, node_id)
            self.assertEqual(Ventures.venture_hands(stub, "loom"), (scholars, 3.0))

    def test_nothing_reads_a_depth_written_on_the_tree(self):
        stub = world()
        stub.nodes = {"loom": {"risk": 0.3, "ph": 4000.0, "depth": 0.9, "supplier_depth": 0.9, "maturity": 0.9}}
        self.assertAlmostEqual(ProgressMixin.effective_risk(stub, "loom", precaution=False), 0.3)
        self.assertEqual(stub.industry_depth("loom"), 0.0)


if __name__ == "__main__":
    unittest.main()
