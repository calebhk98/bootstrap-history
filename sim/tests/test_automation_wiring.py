"""Complaint 421, Complaint 640: the automation phases over stand-ins: the auto_hire setting picks what the staff phase
does (hire_stance), the policy command stores replace-only, the start phase and the mine order record what they skipped
with a reason_kind, an auto_mine order carries its id from its audit row to the tranche and the working it became.
The decisions are in test_auto_start_rule and test_automation_modes."""
QUICK_TOPIC = True

import types
import unittest

from sim.workforce.staff_replacement import GROW_STANCE, REPLACE_ONLY, REPLACE_STANCE, hire_stance
from sim.ledger.api import PayEdge
from sim.materials.api import ApplyThrottle
from sim.reporting.api import RecordAutomation, RecordAutomationSkip
from sim.tests import module_harness, projects_host, resources_stand_in
from sim.ui.proto.dispatch_ventures import _cmd_policy


class HireStance(unittest.TestCase):
    def test_the_setting_and_the_credit_room_pick_the_stance(self):
        self.assertEqual(hire_stance(True, True), GROW_STANCE)
        self.assertEqual(hire_stance(REPLACE_ONLY, True), REPLACE_STANCE)

    def test_off_or_no_room_does_nothing(self):
        self.assertIsNone(hire_stance(False, True))
        self.assertIsNone(hire_stance(None, True))
        self.assertIsNone(hire_stance(True, False))
        self.assertIsNone(hire_stance(REPLACE_ONLY, False))


class PolicyCommand(unittest.TestCase):
    def _sim(self):
        return types.SimpleNamespace(
            policy={"auto_hire": True, "auto_open": True}, capital=100.0, year=0, credit_frozen_until=0,
            view=lambda name: (lambda: {"reserve_craftsmen": 0, "reserve_scholars": 0}),
            state=types.SimpleNamespace(projects=types.SimpleNamespace(excluded=set())))

    def test_replace_sets_the_replace_only_mode_and_off_turns_it_off(self):
        sim = self._sim()
        reply = _cmd_policy(sim, {}, {"set": {"auto_hire": "replace"}}, False)
        self.assertTrue(reply["ok"])
        self.assertEqual(sim.policy["auto_hire"], REPLACE_ONLY)
        reply = _cmd_policy(sim, {}, {"set": {"auto_hire": "off"}}, False)
        self.assertTrue(reply["ok"])
        self.assertIs(sim.policy["auto_hire"], False)

    def test_replace_is_for_auto_hire_only(self):
        sim = self._sim()
        _cmd_policy(sim, {}, {"set": {"auto_open": "replace"}}, False)
        self.assertNotEqual(sim.policy["auto_open"], REPLACE_ONLY)

    def test_an_unknown_policy_is_refused(self):
        self.assertFalse(_cmd_policy(self._sim(), {}, {"set": {"no_such": True}}, False)["ok"])


def skips(module):
    """The audit rows the start phase asked to have written, as (policy, what, reason, facts)."""
    return [(command.policy, command.what, command.reason, command.facts) for command in module_harness.sent(module)
            if isinstance(command, RecordAutomationSkip)]


class StartPhaseSkips(unittest.TestCase):
    def test_a_year_where_nothing_can_start_leaves_one_row_naming_the_first_blocked_candidate(self):
        module = projects_host.start_phase_module(start_check=lambda *call: (False, None), start_refusal=lambda node_id: "not yet")
        module.start_projects_phase("founder")
        rows = skips(module)
        self.assertEqual([(policy, what) for policy, what, _reason, _facts in rows], [("auto_start", "a")])
        self.assertTrue(rows[0][2])

    def test_candidates_dearer_than_the_room_leave_one_row_with_the_cost_and_the_room(self):
        module = projects_host.start_phase_module(project_cost=1e18)
        module.start_projects_phase("founder")
        rows = skips(module)
        self.assertEqual(len(rows), 1)
        facts = rows[0][3]
        self.assertEqual(facts["reason_kind"], "cost_over_room")
        self.assertEqual(facts["candidates"], 2)
        self.assertLess(facts["room"], facts["cost"])

    def test_reaching_the_active_project_cap_is_recorded_once(self):
        module = projects_host.start_phase_module(
            project_limits={"base": -10_000, "per_director_hours": 2000.0, "per_scholar": 12.0, "per_artisan": 40.0})
        module.start_projects_phase("founder")
        self.assertEqual([facts["reason_kind"] for _policy, _what, _reason, facts in skips(module)], ["active_project_cap"])


def phase_module(capital=1e9, binding="coal", demand_key="coal_kg", policies=("auto_mine", "auto_forest"), throttle=0.3):
    """The resources module with the materials phase's reads written out; mining itself is recorded, not run."""
    module = resources_stand_in.build(budget=1e12, answers={ApplyThrottle: throttle}, views={
        "acting_balance": capital, "material_binding": binding,
        "automatic_policy": lambda name: name in policies, "material_demand": {demand_key: 1_000_000.0},
        "material_checks": {"coal_kg": ("coal", "coal")}, "charcoal_per_hectare": 1.0, "year": 100})
    module.opened = []
    module.works_materials = lambda: ("coal",)
    module.mine_capex = lambda material: 1.0
    module.auto_prospect = lambda material: False
    module.commission_mines = lambda: None
    module.forest_land_ceiling = lambda: 1e12
    module.open_mine = lambda command: module.opened.append((command.material, command.tonnes_per_year, command.order)) \
        or command.tonnes_per_year
    return module


def audit(module, kind):
    return [command for command in module_harness.sent(module) if isinstance(command, kind)]


class MineOrder(unittest.TestCase):
    def test_a_mine_that_orders_nothing_says_why(self):
        module = phase_module(capital=0.0)
        module.step_materials()
        (row,) = [command for command in audit(module, RecordAutomationSkip) if command.policy == "auto_mine"]
        self.assertTrue(row.reason)
        self.assertEqual(module.opened[0][1], 0.0)

    def test_an_order_is_audited_with_the_id_it_hands_to_the_mine(self):
        module = phase_module(capital=1e12)
        module.step_materials()
        (row,) = [command for command in audit(module, RecordAutomation) if command.action == "mine"]
        self.assertEqual(row.facts["order"], "auto_mine:coal:100")
        self.assertEqual(row.facts["reason_kind"], "mine_ordered")
        self.assertEqual([order for _material, _tonnes, order in module.opened], [row.facts["order"]])
        self.assertEqual(row.facts["ordered"], module.opened[0][1])


class OtherMaterialOrders(unittest.TestCase):
    def test_auto_forest_records_the_coppice_it_bought_and_what_it_cost(self):
        module = phase_module(binding="charcoal", demand_key="charcoal_kg", policies=("auto_forest",))
        module.step_materials()
        self.assertEqual([(row.policy, row.action) for row in audit(module, RecordAutomation)], [("auto_forest", "forest")])
        self.assertGreater(module.seat.forest_ha, 0.0)
        self.assertGreater(sum(command.amount for command in audit(module, PayEdge)), 0.0)

    def test_nitre_beds_record_the_capped_yearly_spend(self):
        module = phase_module(binding="saltpetre", demand_key="saltpetre_kg", policies=("auto_mine",))
        module.step_materials()
        self.assertEqual([(row.policy, row.action) for row in audit(module, RecordAutomation)], [("auto_mine", "nitre")])
        self.assertGreater(sum(command.amount for command in audit(module, PayEdge)), 0.0)
        self.assertGreater(module.seat.nitre_bed_m2, 0.0)

    def test_a_manual_game_with_no_policy_set_records_nothing(self):
        module = phase_module(policies=())
        module.step_materials()
        self.assertEqual([command for command in module_harness.sent(module) if not isinstance(command, ApplyThrottle)], [])
        self.assertEqual(module.opened, [])


class Commissioning(unittest.TestCase):
    def test_a_finished_tranche_becomes_a_working_that_keeps_its_order_id(self):
        module = resources_stand_in.build(year=105)
        module.seat.mine_pending = {"coal": 10.0}
        module.seat.mine_tranches = [["coal", 10.0, 105, 50.0, "auto_mine:coal:100", None], ["coal", 5.0, 120, 25.0, "", None]]
        module.advance_depletion = lambda: None
        module.commission_mines()
        seat = module.seat
        self.assertEqual([(mine["material"], mine["order"]) for mine in seat.mines], [("coal", "auto_mine:coal:100")])
        self.assertEqual(len(seat.mine_tranches), 1)
        self.assertNotIn("coal", seat.mine_pending)


if __name__ == "__main__":
    unittest.main()
