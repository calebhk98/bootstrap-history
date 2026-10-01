"""A project short of a trade is told "booked" only when other work books it;
a trade the society cannot field at that pace is a staffing shortage."""
import unittest

from .harness import *  # noqa: F401,F403


def _lone_project_beyond_supply():
    household = sim(civ="rome_100ad", capital=1e9)
    for node_id, node in NODES.items():
        for trade_id, want in (node.get("lab") or {}).items():
            pace = want / max(1.0, node["yrs"])
            if 0 < household.hours_you_can_call_on(trade_id) < pace:
                household.active[node_id] = dict(
                    ph_left=float(node["ph"]), yrs=0.0, spent=0.0,
                    cost_left=household.project_cost(node_id), lab_left=dict(node["lab"]))
                return household, node_id, trade_id
    raise AssertionError("no node outruns a trade's supply")


class TradeShortageKind(unittest.TestCase):

    def test_alone_and_beyond_supply_is_staffing_not_booked(self):
        household, node_id, trade_id = _lone_project_beyond_supply()
        household.trade_hours_used = {}
        project_state = household.active[node_id]
        household.lab_year_draw(node_id, project_state, 1.0, 1e9)
        note = household.trade_shortfall_note(project_state)
        self.assertNotIn("already booked", note)
        self.assertIn("nobody to do the work", note)
        self.assertIn(trade_id, note)

    def test_booked_by_a_second_project_is_booked(self):
        household, node_id, trade_id = _lone_project_beyond_supply()
        supply = household.hours_you_can_call_on(trade_id)
        node = NODES[node_id]
        household.trade_hours_used = {trade_id: supply}
        project_state = household.active[node_id]
        household.lab_year_draw(node_id, project_state, 1.0, 1e9)
        project_state["short_of_trade_staffing"] = []
        self.assertIn("already booked", household.trade_shortfall_note(project_state))
        self.assertIn(trade_id, node["lab"])
