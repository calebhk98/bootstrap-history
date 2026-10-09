"""Every mining technique changes the physical term of the works it acts on, in the running cost and in
the shaft bill alike; the generic yield and cost multiplier and its bounds are gone (Complaint 374)."""

QUICK_TOPIC = True

import glob
import json
import os
import unittest

from sim.constants import REGISTRY
from sim.engine import economy_mining
from sim.world import deposits, mine_technique, mine_works

BRANCH_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "data", "branches")


def _probe(depth_class="deep_vein", hardness_class="hard"):
    return deposits.Deposit(
        name="probe", metal="test", tile="nowhere", material_moved="ore",
        ore_grade_kg_per_tonne=10.0, depth_class=depth_class,
        hardness_class=hardness_class, quantity_tonnes_per_year=100.0, note="")


def _terms(deposit, effects=None):
    return deposits.works_terms(deposit, effects)


def _nodes():
    nodes = {}
    for path in sorted(glob.glob(os.path.join(BRANCH_DIRECTORY, "*.json"))):
        with open(path) as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            data = data.get("nodes", [])
        nodes.update({node["id"]: node for node in data})
    return nodes


NEWCOMEN = {"drainage_engine": {"lift_power_watts": 30000.0, "attendants": 2,
                                "fuel_kg_per_tonne_metre": 0.03}}
WINDING = {"hoist_engine": {"lift_power_watts": 7500.0, "attendants": 2,
                            "fuel_kg_per_tonne_metre": 0.012}}
POWDER = {"blasting": {"drilling_hours_per_tonne_rock": {"soft": 1.5, "medium": 3.0, "hard": 4.5},
                       "charging_hours_per_tonne_rock": 0.5}}


class GenericMultiplierIsGone(unittest.TestCase):

    def test_no_node_declares_the_generic_multiplier(self):
        offenders = [node_id for node_id, node in _nodes().items()
                     if "mining_tech" in node.get("mechanics", {})]
        self.assertEqual(offenders, [])

    def test_the_method_and_its_bounds_are_deleted(self):
        self.assertFalse(hasattr(economy_mining.MiningMixin, "mining_tech"))
        for name in ("MINING_TECH_YIELD_CEILING", "MINING_TECH_COST_FLOOR"):
            self.assertNotIn(name, REGISTRY)
            self.assertFalse(hasattr(economy_mining.MiningMixin, name))

    def test_each_converted_node_states_its_physics_with_a_source(self):
        nodes = _nodes()
        for node_id in ("blast_furnace", "railway", "steam_atmospheric", "mat_bulk_steel", "pwr_rotary_drilling",
                        "met_mine_pumping", "met_black_powder_blasting", "met_dynamite_blasting",
                        "met_winding_engine"):
            works = nodes[node_id]["mechanics"].get("mine_works")
            self.assertTrue(works and works.get("source"), node_id)


class Drainage(unittest.TestCase):

    def test_an_engine_lifts_water_for_attendants_and_fuel_not_for_bailers(self):
        deposit = _probe()
        before, after = _terms(deposit), _terms(deposit, mine_technique.combine([NEWCOMEN]))
        self.assertLess(after["drainage"], before["drainage"] / 10.0)
        self.assertGreater(after["drainage"], 0.0)

    def test_the_cheapest_lift_wins_rather_than_stacking(self):
        screw = {"drainage_lift_efficiency": 0.45}
        both = _terms(_probe(), mine_technique.combine([screw, NEWCOMEN]))
        engine = _terms(_probe(), mine_technique.combine([NEWCOMEN]))
        self.assertEqual(both["drainage"], engine["drainage"])

    def test_the_shaft_bill_follows_the_head_an_adit_leaves_and_the_lift_device(self):
        deposit = _probe()
        base = deposits.shaft_cost_labour_hours(deposit)
        adit = mine_technique.combine([{"gravity_drained_head_share": 0.4}])
        screw = mine_technique.combine([{"drainage_lift_efficiency": 0.45}])
        self.assertLess(deposits.shaft_cost_labour_hours(deposit, adit), base)
        self.assertLess(deposits.shaft_cost_labour_hours(deposit, screw), base)

    def test_surface_ground_has_no_shaft_to_drain(self):
        adit = mine_technique.combine([{"gravity_drained_head_share": 0.4}])
        self.assertEqual(deposits.shaft_cost_labour_hours(_probe("surface"), adit), 0.0)


class Winding(unittest.TestCase):

    def test_a_winding_engine_lowers_the_hoist_term_and_the_spoil_lift_of_sinking(self):
        deposit = _probe()
        effects = mine_technique.combine([WINDING])
        self.assertLess(_terms(deposit, effects)["hoist"], _terms(deposit)["hoist"] / 10.0)
        self.assertLess(deposits.shaft_cost_labour_hours(deposit, effects), deposits.shaft_cost_labour_hours(deposit))

    def test_an_engine_raises_what_one_shaft_can_raise_so_fewer_shafts_are_needed(self):
        deposit = _probe()
        effects = mine_technique.combine([WINDING])
        self.assertGreater(deposits.shaft_rock_capacity_tonnes_per_year(deposit, effects),
                           deposits.shaft_rock_capacity_tonnes_per_year(deposit))
        self.assertLess(deposits.shafts_needed_fractional(deposit, 50.0, effects),
                        deposits.shafts_needed_fractional(deposit, 50.0))


class Breaking(unittest.TestCase):

    def test_powder_replaces_hand_breaking_and_fire_setting_in_hard_rock(self):
        deposit = _probe(hardness_class="hard")
        effects = mine_technique.combine([POWDER])
        self.assertLess(deposits.vein_hours_per_tonne_ore(deposit, effects), deposits.vein_hours_per_tonne_ore(deposit))

    def test_powder_never_costs_more_than_digging_soft_ground(self):
        deposit = _probe(hardness_class="soft")
        slow = {"blasting": {"drilling_hours_per_tonne_rock": {"soft": 90.0, "medium": 90.0, "hard": 90.0},
                             "charging_hours_per_tonne_rock": 5.0}}
        self.assertEqual(deposits.vein_hours_per_tonne_ore(deposit, mine_technique.combine([slow])),
                         deposits.vein_hours_per_tonne_ore(deposit))

    def test_powder_lowers_the_breaking_in_the_shaft_bill_too(self):
        deposit = _probe()
        self.assertLess(deposits.shaft_cost_labour_hours(deposit, mine_technique.combine([POWDER])),
                        deposits.shaft_cost_labour_hours(deposit))

    def test_machine_drilling_speeds_only_the_drilling_of_a_blasted_face(self):
        deposit = _probe()
        powder = mine_technique.combine([POWDER])
        drilled = mine_technique.combine([POWDER, {"drilling_rate_multiple": 2.5}])
        self.assertLess(deposits.vein_hours_per_tonne_ore(deposit, drilled), deposits.vein_hours_per_tonne_ore(deposit, powder))
        self.assertEqual(deposits.vein_hours_per_tonne_ore(deposit, mine_technique.combine([{"drilling_rate_multiple": 2.5}])),
                         deposits.vein_hours_per_tonne_ore(deposit))

    def test_the_stronger_explosive_wins_rather_than_stacking(self):
        stronger = {"blasting": {"drilling_hours_per_tonne_rock": {"soft": 1.0, "medium": 2.0, "hard": 3.0},
                                 "charging_hours_per_tonne_rock": 0.5}}
        both = mine_technique.combine([POWDER, stronger])
        self.assertEqual(deposits.vein_hours_per_tonne_ore(_probe(), both),
                         deposits.vein_hours_per_tonne_ore(_probe(), mine_technique.combine([stronger])))


class Haulage(unittest.TestCase):

    def test_a_larger_load_per_trip_cuts_haulage_and_nothing_else(self):
        deposit = _probe()
        rails = mine_technique.combine([{"haulage_load_kilograms": 2500.0}])
        before, after = _terms(deposit), _terms(deposit, rails)
        self.assertAlmostEqual(after["haulage"], before["haulage"] * mine_works.CARRY_LOAD_KILOGRAMS / 2500.0)
        self.assertEqual(after["hoist"], before["hoist"])

    def test_a_load_smaller_than_the_barrow_does_not_raise_haulage(self):
        weak = mine_technique.combine([{"haulage_load_kilograms": 10.0}])
        self.assertEqual(_terms(_probe(), weak), _terms(_probe()))


if __name__ == "__main__":
    unittest.main()
