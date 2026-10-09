"""Mining techniques change the physical term of the works they act on:
the lift per hour of drainage labour, the head the pumps lift through, the
gravel a hydraulic working moves. No generic multiplier stands in for them."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.economy_mining import MiningMixin
from sim.world import deposits, mine_fire_setting, mine_technique, mine_works

BRANCH_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "data", "branches")
BRANCH_FILES = ("19_metallurgy_mining.json", "46_materials_deep.json")
CONVERTED_NODE_IDS = ("met_archimedean_screw", "met_bucket_wheel_battery",
                      "met_drainage_adit", "mt2_hydraulic_mining")


def _probe(depth_class="deep_vein", hardness_class="medium"):
    return deposits.Deposit(
        name="probe", metal="test", tile="nowhere", material_moved="ore",
        ore_grade_kg_per_tonne=10.0, depth_class=depth_class,
        hardness_class=hardness_class, quantity_tonnes_per_year=100.0, note="")


def _terms(deposit, effects=None):
    return mine_works.works_hours_per_tonne_ore(
        deposit.depth_class, deposit.hardness_class,
        deposits._lift_hours_per_tonne_metre(), deposits.shaft_depth_metres(deposit),
        mine_fire_setting.MINING_SHIFT_HOURS, effects=effects,
        drainage_hours_per_tonne_metre=deposits.drainage_lift_hours_per_tonne_metre(effects))


def _nodes():
    nodes = {}
    for name in BRANCH_FILES:
        with open(os.path.join(BRANCH_DIRECTORY, name)) as handle:
            nodes.update({node["id"]: node for node in json.load(handle)})
    return nodes


class _Host(MiningMixin):
    """Just enough of Sim for the mixin's technique collection."""

    def __init__(self, specs, running):
        self._specs, self._running = specs, running

    def _running_kept(self, name):
        return self.__dict__.setdefault("_kept_" + name, {})

    def _effect_terms(self, channel):
        return sorted(self._specs.items()) if channel == "mine_works" else []

    def running(self, node_id):
        return node_id in self._running


class MineTechniques(unittest.TestCase):

    def test_only_running_techniques_reach_the_works(self):
        specs = {"screw": {"drainage_lift_efficiency": 0.45},
                 "adit": {"gravity_drained_head_share": 0.4}}
        host = _Host(specs, running={"screw"})
        self.assertEqual(host.mine_works_effects(), {"drainage_lift_efficiency": 0.45})

    def test_a_technique_with_no_declared_effect_changes_nothing(self):
        deposit = _probe()
        bare = mine_technique.combine([{"unrelated_field": 7.0}, {}])
        self.assertEqual(_terms(deposit, bare), _terms(deposit, None))
        self.assertEqual(deposits.vein_hours_per_tonne_ore(deposit, bare),
                         deposits.vein_hours_per_tonne_ore(deposit))

    def test_a_screw_lowers_drainage_by_its_stated_lift_rate_and_nothing_else(self):
        deposit = _probe()
        efficiency = 0.45
        screw = mine_technique.combine([{"drainage_lift_efficiency": efficiency}])
        before, after = _terms(deposit), _terms(deposit, screw)
        self.assertAlmostEqual(
            after["drainage"] / before["drainage"],
            mine_technique.BAILING_MECHANICAL_EFFICIENCY / efficiency, places=9)
        self.assertLess(after["drainage"], before["drainage"])
        for term in ("hoist", "haulage", "timbering"):
            self.assertEqual(after[term], before[term])

    def test_a_less_efficient_device_than_the_baseline_does_not_raise_cost(self):
        weak = mine_technique.combine([{"drainage_lift_efficiency": 0.01}])
        self.assertEqual(weak, mine_technique.combine([]))

    def test_the_best_lift_device_wins_rather_than_stacking(self):
        both = mine_technique.combine([{"drainage_lift_efficiency": 0.45},
                                       {"drainage_lift_efficiency": 0.69}])
        self.assertEqual(both["drainage_lift_efficiency"], 0.69)

    def test_an_adit_removes_the_head_it_drains_by_gravity(self):
        deposit = _probe()
        adit = mine_technique.combine([{"gravity_drained_head_share": 0.4}])
        before, after = _terms(deposit), _terms(deposit, adit)
        self.assertAlmostEqual(after["drainage"] / before["drainage"], 0.6, places=9)
        self.assertEqual(after["hoist"], before["hoist"])

    def test_surface_ground_has_no_drainage_to_lower(self):
        screw = mine_technique.combine([{"drainage_lift_efficiency": 0.69}])
        self.assertEqual(_terms(_probe("surface"), screw)["drainage"], 0.0)

    def test_hydraulic_mining_raises_the_gravel_moved_per_hour(self):
        deposit = _probe("alluvial_hydraulic")
        monitor = mine_technique.combine([{"gravel_moved_multiple": 2.0}])
        self.assertAlmostEqual(
            deposits.extraction_cost_labour_hours_per_kg(deposit, monitor),
            deposits.extraction_cost_labour_hours_per_kg(deposit) / 2.0, places=12)

    def test_vein_cost_falls_with_a_screw(self):
        deposit = _probe()
        screw = mine_technique.combine([{"drainage_lift_efficiency": 0.45}])
        self.assertLess(deposits.vein_hours_per_tonne_ore(deposit, screw),
                        deposits.vein_hours_per_tonne_ore(deposit))

    def test_converted_techniques_declare_physics_and_no_generic_multiplier(self):
        nodes = _nodes()
        for node_id in CONVERTED_NODE_IDS:
            mechanics = nodes[node_id]["mechanics"]
            self.assertNotIn("mining_tech", mechanics, node_id)
            self.assertIn("mine_works", mechanics, node_id)
            self.assertTrue(mechanics["mine_works"].get("source"), node_id)


if __name__ == "__main__":
    unittest.main()
