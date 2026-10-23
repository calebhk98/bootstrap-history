"""Complaint 421, Complaint 640: the automation phases over stand-ins: the auto_hire setting picks what the staff phase
does (hire_stance), the policy command stores replace-only, the start phase and the mine order record what they skipped
with a reason_kind, an auto_mine order carries its id from its audit row to the tranche and the working it became.
The decisions are in test_auto_start_rule and test_automation_modes."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import step_phase_project_start
from sim.engine.economy_mining import MiningMixin
from sim.engine.staff_replacement import GROW_STANCE, REPLACE_ONLY, REPLACE_STANCE, hire_stance
from sim.engine.step_phase_project_start import ProjectStartPhaseMixin
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
            state=types.SimpleNamespace(household=types.SimpleNamespace(reserve_craftsmen=0, reserve_scholars=0),
                                        projects=types.SimpleNamespace(excluded=set())))

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


class Phase(ProjectStartPhaseMixin):
    """The start phase and the materials phase over a household with nothing but what they read."""
    MAX_ACTIVE_PROJECTS_BASE = 5.0
    MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS = 2000.0
    MAX_ACTIVE_PROJECTS_PER_SCHOLAR = 12.0
    MAX_ACTIVE_PROJECTS_PER_ARTISAN = 40.0
    MINE_OPEX_MATERIALS = ("coal",)
    MATERIAL_CHECKS = {"coal_kg": ("coal", "coal")}
    FOREST_COST_PER_HA = 1.0

    def __init__(self, capital=1e9):
        self.manual = False
        self.price_index = 1.0
        self.mine_capacity = {}
        self.nodes = {"a": {"name": "a", "rev": 0.0, "up": 0.0}, "b": {"name": "b", "rev": 0.0, "up": 0.0}}
        self.order = ["a", "b"]
        self.bounty_set = set()
        self.opened = []
        household = types.SimpleNamespace(credit_frozen_until=0, scholars=0.0, artisans=0.0, capital=capital,
                                          automation_audit=[], log=[])
        self.state = types.SimpleNamespace(
            scenario=types.SimpleNamespace(year=100), household=household,
            projects=types.SimpleNamespace(active={}, bountied=set(), done=set()),
            founder=types.SimpleNamespace(policy={"auto_mine": True}),
            holdings=types.SimpleNamespace(binding="coal", mine_pending={}, forest_ha=0.0))
        self.labour = types.SimpleNamespace(director_pool=lambda: 0.0, director_hours_committed=lambda: 0.0,
                                            hired_cap=lambda: 0.0)

    def upkeep(self):
        return 0.0

    def revenue(self):
        return 1e6

    def living_cost(self, _rev=None, _upkeep=None):
        return 0.0

    def mine_operating_cost(self):
        return 0.0

    def can_start(self, node_id):
        return True

    def project_cost(self, node_id):
        return 10.0

    def funding_capacity(self):
        return 1e9

    def committed_spend(self):
        return 0.0

    def initialize_project(self, node_id):
        self.state.projects.active[node_id] = {}

    def start_refusal(self, node_id):
        return "not yet"

    def commission_mines(self):
        pass

    def resource_throttle(self):
        return 0.3

    def spending_power(self, kind):
        return 1e12

    def annual_material_demand(self):
        return {"coal_kg": 1_000_000.0}

    def _mine_capex(self, material):
        return 1.0

    def auto_prospect(self, material):
        pass

    CHARCOAL_PER_HA = 1.0
    NITRE_COST_PER_M2 = 1.0
    NITRE_BED_SPEND_CEILING = 100.0

    def pay_edge(self, edge, amount, text):
        self.state.household.capital -= amount

    def buy_forest(self, hectares):
        self.state.holdings.forest_ha += hectares
        self.state.household.capital -= hectares * self.FOREST_COST_PER_HA

    def open_mine(self, material, tonnes, order=""):
        self.opened.append((material, tonnes, order))
        return tonnes


def skip_rows(phase):
    return [row for row in phase.state.household.automation_audit if row["action"] == "skipped"]


class StartPhaseSkips(unittest.TestCase):
    def test_a_year_where_nothing_can_start_leaves_one_row_naming_the_first_blocked_candidate(self):
        phase = Phase()
        phase.can_start = lambda node_id: False
        phase._step_start_projects()
        rows = skip_rows(phase)
        self.assertEqual([(row["policy"], row["what"]) for row in rows], [("auto_start", "a")])
        self.assertTrue(rows[0]["reason"])

    def test_candidates_dearer_than_the_room_leave_one_row_with_the_cost_and_the_room(self):
        phase = Phase()
        phase.project_cost = lambda node_id: 1e18
        phase._step_start_projects()
        rows = skip_rows(phase)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason_kind"], "cost_over_room")
        self.assertEqual(rows[0]["candidates"], 2)
        self.assertLess(rows[0]["room"], rows[0]["cost"])

    def test_reaching_the_active_project_cap_is_recorded_once(self):
        phase = Phase()
        phase.MAX_ACTIVE_PROJECTS_BASE = -10_000
        phase._step_start_projects()
        rows = skip_rows(phase)
        self.assertEqual([row["reason_kind"] for row in rows], ["active_project_cap"])


class MineOrder(unittest.TestCase):
    def _step(self, phase):
        quiet = types.SimpleNamespace(slowed_projects=lambda game: [], clear_shortage=lambda game: None)
        with mock.patch.object(step_phase_project_start, "shortage_conditions", quiet):
            phase._step_materials()

    def test_a_mine_that_orders_nothing_says_why(self):
        phase = Phase(capital=0.0)
        self._step(phase)
        rows = [row for row in skip_rows(phase) if row["policy"] == "auto_mine"]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["reason"])
        self.assertEqual(phase.opened[0][1], 0.0)

    def test_an_order_is_audited_with_the_id_it_hands_to_the_mine(self):
        phase = Phase(capital=1e12)
        self._step(phase)
        rows = [row for row in phase.state.household.automation_audit if row["action"] == "mine"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["order"], "auto_mine:coal:100")
        self.assertEqual(rows[0]["reason_kind"], "mine_ordered")
        self.assertEqual([order for _material, _tonnes, order in phase.opened], [rows[0]["order"]])
        self.assertEqual(rows[0]["ordered"], phase.opened[0][1])


class OtherMaterialOrders(unittest.TestCase):
    def _rows(self, phase, binding, demand_key, policy):
        phase.state.holdings.binding = binding
        phase.state.holdings.nitre_bed_m2 = 0.0
        phase.state.founder.policy = {policy: True}
        phase.annual_material_demand = lambda: {demand_key: 1_000_000.0}
        quiet = types.SimpleNamespace(slowed_projects=lambda game: [], clear_shortage=lambda game: None)
        with mock.patch.object(step_phase_project_start, "shortage_conditions", quiet):
            phase._step_materials()
        return phase.state.household.automation_audit

    def test_auto_forest_records_the_coppice_it_bought_and_what_it_cost(self):
        rows = self._rows(Phase(capital=1e12), "charcoal", "charcoal_kg", "auto_forest")
        self.assertEqual([(row["policy"], row["action"]) for row in rows], [("auto_forest", "forest")])
        self.assertGreater(rows[0]["cost"], 0.0)

    def test_nitre_beds_record_the_capped_yearly_spend(self):
        phase = Phase(capital=1e12)
        rows = self._rows(phase, "saltpetre", "saltpetre_kg", "auto_mine")
        self.assertEqual([(row["policy"], row["action"]) for row in rows], [("auto_mine", "nitre")])
        self.assertGreater(rows[0]["cost"], 0.0)
        self.assertGreater(phase.state.holdings.nitre_bed_m2, 0.0)

    def test_a_manual_game_with_no_policy_set_records_nothing(self):
        phase = Phase(capital=1e12)
        phase.manual = True
        phase.state.founder.policy = {}
        phase.state.holdings.binding = "coal"
        quiet = types.SimpleNamespace(slowed_projects=lambda game: [], clear_shortage=lambda game: None)
        with mock.patch.object(step_phase_project_start, "shortage_conditions", quiet):
            phase._step_materials()
        self.assertEqual(phase.state.household.automation_audit, [])
        self.assertEqual(phase.opened, [])


class Commissioning(unittest.TestCase):
    def test_a_finished_tranche_becomes_a_working_that_keeps_its_order_id(self):
        class Mines(MiningMixin):
            def _advance_mine_depletion(self):
                pass
        mines = Mines()
        mines.state = types.SimpleNamespace(
            scenario=types.SimpleNamespace(year=105),
            holdings=types.SimpleNamespace(
                mines=[], mine_pending={"coal": 10.0},
                mine_tranches=[["coal", 10.0, 105, 50.0, "auto_mine:coal:100", None],
                               ["coal", 5.0, 120, 25.0, "", None]]))
        mines.commission_mines()
        holdings = mines.state.holdings
        self.assertEqual([(mine["material"], mine["order"]) for mine in holdings.mines], [("coal", "auto_mine:coal:100")])
        self.assertEqual(len(holdings.mine_tranches), 1)
        self.assertNotIn("coal", holdings.mine_pending)


if __name__ == "__main__":
    unittest.main()
