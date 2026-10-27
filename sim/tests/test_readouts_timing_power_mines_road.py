"""Readouts agree with the engine's own checks: Complaints/230, 234, 235, 264. Each rule runs on inputs or a stub the test
builds; the expected years against the earliest finish are test_expected_calendar_years_floor."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.tests import projects_host
from sim.projects.completion_schedule import calendar_floor_years, earliest_completion_years, payment_schedule_years
from sim.tests import materials_stand_in, resources_stand_in
from sim.engine.data import closure
from sim.seats.module import Seats
from sim.seats.state import SeatsSeat
from sim.tests import module_harness
from sim.ui.proto.economy import _power_tiers

THRESHOLD, MINIMUM, SCALE = 5, 2.0, 90.0


def floor(nominal, reputation, rebuild=1.0):
    return calendar_floor_years(nominal, reputation, rebuild, THRESHOLD, MINIMUM, SCALE)


class QuotedCompletion(unittest.TestCase):
    """Complaints/230: the quoted finish is the earliest the payment schedule allows."""

    def test_a_short_node_keeps_its_nominal_floor_whatever_the_reputation(self):
        self.assertEqual(floor(3, 0.0), 3)
        self.assertEqual(floor(3, 500.0), 3)

    def test_a_diffusion_limited_node_shrinks_with_reputation_but_not_below_the_minimum(self):
        self.assertEqual(floor(10, 0.0), 10)
        self.assertLess(floor(10, 80.0), floor(10, 0.0))
        self.assertAlmostEqual(floor(10, SCALE), 5.0)       # reputation of one scale halves the floor
        self.assertEqual(floor(10, 1.0e9), MINIMUM)

    def test_the_floor_scales_with_what_is_left_to_rebuild(self):
        self.assertAlmostEqual(floor(10, 0.0, 0.25), 2.5)

    def test_the_payment_schedule_is_the_nominal_years_and_reputation_never_shortens_it(self):
        self.assertEqual(payment_schedule_years(10, 1.0), 10)
        self.assertEqual(payment_schedule_years(10, 0.5), 5)
        self.assertEqual(payment_schedule_years(1, 0.1), 1.0)       # never under a year

    def test_the_calendar_floor_alone_stays_shorter_than_the_payment_schedule_at_high_reputation(self):
        self.assertLess(floor(10, 80.0), payment_schedule_years(10, 1.0))

    def test_the_earliest_completion_is_the_longer_of_floor_and_schedule(self):
        self.assertEqual(earliest_completion_years(5.0, 10.0), 10.0)
        self.assertEqual(earliest_completion_years(12.0, 10.0), 12.0)

    def test_a_running_attempt_has_its_served_years_taken_off_and_never_goes_below_zero(self):
        self.assertEqual(earliest_completion_years(5.0, 10.0, 4.0), 6.0)
        self.assertEqual(earliest_completion_years(5.0, 10.0, 0.0), 10.0)
        self.assertEqual(earliest_completion_years(5.0, 10.0, 99.0), 0.0)


class PowerCapabilityReadouts(unittest.TestCase):
    """Complaints/234: a capability flag is labelled as knowledge and shows the kW behind it."""

    NODES = {
        "cap_power_water": {"mechanics": {"power_tier": {"rank": 1, "label": "water", "scale": "workshop", "anchor_kw": 10.0}}},
        "cap_power_steam": {"mechanics": {"power_tier": {"rank": 2, "label": "steam", "scale": "workshop", "anchor_kw": 50.0}}},
        "cap_power_grid": {"mechanics": {"power_tier": {"rank": 3, "label": "grid", "scale": "grid", "anchor_kw": 900.0}}},
        "en_alternator": {"mechanics": {"power_generation": {"tier": "cap_power_steam", "role": "generator"}}},
        "power_line": {"mechanics": {"power_generation": {"tier": "cap_power_grid", "role": "transmission"}}},
    }

    def _installed(self, done):
        mechanic = {name: {node_id: node["mechanics"][name] for node_id, node in self.NODES.items() if name in node["mechanics"]}
                    for name in ("power_tier", "power_generation")}
        module = materials_stand_in.build(legacy_projects=materials_stand_in.projects(done=done), mechanic=mechanic)
        return module.installed_generation_kw_by_tier()

    def test_a_grid_capability_with_no_station_has_no_installed_generation(self):
        self.assertEqual(self._installed({"cap_power_grid"}), {})

    def test_generation_installed_is_counted_against_its_tier(self):
        self.assertEqual(self._installed({"en_alternator"}), {"cap_power_steam": 50.0})

    def test_transmission_is_not_generation(self):
        self.assertEqual(self._installed({"power_line"}), {})

    def _tiers(self, done, installed):
        host = SimpleNamespace(installed_generation_kw_by_tier=lambda: installed, is_visible=lambda node_id: True,
                               has=lambda node_id: node_id in done)
        tiers, highest = _power_tiers(host, self.NODES)
        return {tier["id"]: tier for tier in tiers}, highest

    def test_a_built_tier_with_nothing_installed_says_so(self):
        tiers, highest = self._tiers({"cap_power_grid"}, {})
        self.assertTrue(tiers["cap_power_grid"]["built"])
        self.assertEqual(tiers["cap_power_grid"]["installed_kw"], 0.0)
        self.assertTrue(tiers["cap_power_grid"]["no_generation_installed"])
        self.assertEqual(highest, "grid")

    def test_installed_generation_shows_against_its_tier(self):
        tiers, _highest = self._tiers({"cap_power_steam"}, {"cap_power_steam": 50.0})
        self.assertEqual(tiers["cap_power_steam"]["installed_kw"], 50.0)
        self.assertFalse(tiers["cap_power_steam"]["no_generation_installed"])

    def test_a_tier_not_visible_is_not_named(self):
        host = SimpleNamespace(installed_generation_kw_by_tier=dict, is_visible=lambda node_id: node_id == "cap_power_water",
                               has=lambda node_id: False)
        tiers, _highest = _power_tiers(host, self.NODES)
        self.assertEqual([tier["id"] for tier in tiers], ["cap_power_water"])

    def _gate_host(self, done):
        nodes = self.NODES

        return projects_host.build(
            tree=lambda node_id: nodes.get(node_id), techniques_held=set(done), visible_to_player=lambda node_id: True,
            prerequisite_message=lambda missing, memo: "needs " + ", ".join(missing), generation=120.0)

    def test_a_missing_power_capability_is_a_power_gate_that_installed_generation_does_not_satisfy(self):
        entries = self._gate_host({"en_alternator"})._missing_prereq_entries(
            "electric_thing", {"pre": ["cap_power_grid", "plain_node"]}, "text")
        by_kind = {entry["kind"]: entry for entry in entries}
        self.assertEqual(by_kind["power"]["cause"], "power_gate")
        self.assertEqual(by_kind["power"]["ids"], ["cap_power_grid"])
        self.assertEqual(by_kind["knowledge"]["ids"], ["plain_node"])
        # presentation: the gate says installed generation does not satisfy a knowledge gate
        self.assertIn("not installed capacity", by_kind["power"]["text"])
        self.assertIn("120 kW", by_kind["power"]["text"])

    def test_a_node_missing_only_a_power_capability_has_only_the_power_entry(self):
        entries = self._gate_host(set())._missing_prereq_entries("electric_thing", {"pre": ["cap_power_grid"]}, "text")
        self.assertEqual([entry["kind"] for entry in entries], ["power"])


class MineAlreadyBeingSunk(unittest.TestCase):
    """Complaints/235: a mine already being sunk is subtracted from the shortfall."""

    def _plan(self, tranches, shortfall=100.0):
        module = resources_stand_in.build()
        module.works_materials = lambda: ("coal", "lead")
        module.seat.mine_tranches = tranches
        return module.shortage_remedy_plan("coal", shortfall)

    def test_with_nothing_sunk_the_plan_proposes_the_full_mine(self):
        self.assertIn("buy mine coal 100", self._plan([])["commands"])

    def test_a_mine_already_being_sunk_is_not_recommended_again_and_the_plan_says_when_it_is_ready(self):
        plan = self._plan([["coal", 100.0, 1103, 1000.0]])
        self.assertEqual(plan["commands"], [])
        # presentation: the plan names the working being sunk and its year
        self.assertIn("already being sunk", plan["text"])
        self.assertIn("1103", plan["text"])

    def test_only_the_tonnage_still_uncovered_is_proposed(self):
        plan = self._plan([["coal", 40.0, 1103, 400.0]])
        self.assertIn("buy mine coal 60", plan["commands"])
        self.assertEqual(plan["short_tonnes"], 60.0)

    def test_a_mine_of_another_metal_does_not_count(self):
        self.assertIn("buy mine coal 100", self._plan([["lead", 100.0, 1103, 1000.0]])["commands"])


class OnTheRoadToTheGoal(unittest.TestCase):
    """Complaints/264: a fog-safe yes or no for what lies on the road to the goal."""

    def _seats(self):
        nodes = {"goal": {"pre": ["middle"], "req_any": []}, "middle": {"pre": ["root"], "req_any": []},
                 "root": {"pre": [], "req_any": []}, "side": {"pre": ["root"], "req_any": []}}
        module = module_harness.build(Seats, seat=SeatsSeat(), views={"legacy_goal_closure": None, "tree_closure": lambda goal: closure(nodes, goal)})
        module.needs.legacy_goal_closure = module_harness._FakeView(None)
        module.goal = lambda: {"node": "goal"}
        return module

    def test_a_node_the_goal_needs_is_on_the_road_and_one_it_does_not_is_off_it(self):
        module = self._seats()
        self.assertTrue(module.on_road_to_goal("middle"))
        self.assertTrue(module.on_road_to_goal("root"))
        self.assertFalse(module.on_road_to_goal("side"))

    def test_the_answer_is_a_bool_with_no_distance(self):
        self.assertIsInstance(self._seats().on_road_to_goal("middle"), bool)


if __name__ == "__main__":
    unittest.main()
