"""Scenarios (Complaint 640): in a built game the refusal on a project one scholar short says to hire one, the closure
warning is silent for what an immortal founder guarantees, and `allocate ... useful` caps at the useful work. The rules are
in test_workforce_advice_and_allocate_cap."""
import unittest

from .harness import *  # noqa: F401,F403


def _scholar_blocked_node(household):
    for node_id, node in NODES.items():
        if node["sch"] == 2:
            _, why = household.start_reason(node_id)
            if why and "trained scholars" in why:
                return node_id, why
    raise AssertionError("no node blocked on two scholars")


class HireAdviceMatchesDeficit(unittest.TestCase):

    def test_one_scholar_short_says_hire_one(self):
        household = sim(civ="rome_100ad", capital=1e6)
        _, why = _scholar_blocked_node(household)
        self.assertIn('"n":1', why)
        self.assertNotIn('"n":2', why)


class ImmortalFounderScholarWarning(unittest.TestCase):

    def _household_with_concern(self):
        household = sim(civ="rome_100ad", capital=1e7)
        node_id = next(node_id for node_id, node in NODES.items()
                       if 0 < node["sch"] <= 1.0 and node["up"] > 0 and node["art"] == 0
                       and node_id not in household.done)
        household.done.add(node_id)
        household._done_changed()
        household.state.projects.operating.add(node_id)
        household.state.household.artisans = 50.0
        return household, node_id

    def test_no_scholar_warning_when_only_the_immortal_founder_holds_the_work(self):
        household, _node_id = self._household_with_concern()
        household.cfg["immortal"] = True
        household.state.household.scholars = 0.0
        scholar_rows = [row for row in household.staffing_closure_warnings() if row["of"] == "scholars"]
        self.assertEqual(scholar_rows, [])

    def test_mortal_founder_still_gets_the_scholar_warning(self):
        household, _node_id = self._household_with_concern()
        household.cfg["immortal"] = False
        household.state.household.scholars = 0.0
        scholar_rows = [row for row in household.staffing_closure_warnings() if row["of"] == "scholars"]
        self.assertTrue(scholar_rows)


class AllocateUseful(unittest.TestCase):

    def _household_with_small_project(self):
        household = sim(civ="rome_100ad", capital=1e7)
        node_id = next(iter(NODES))
        node = NODES[node_id]
        household.active[node_id] = dict(ph_left=360.0, yrs=0.0, spent=0.0, cost_left=0.0,
                                         lab_left=dict(node["lab"]))
        return household, node_id

    def test_useful_caps_the_order_at_what_the_project_can_use(self):
        household, node_id = self._household_with_small_project()
        useful = household.project_useful_hours(node_id)
        reply = S._agent_dispatch(household, NODES, {"cmd": "allocate", "id": node_id,
                                                      "hours": 540, "useful": True})
        self.assertTrue(reply["ok"], reply)
        self.assertAlmostEqual(reply["hours_a_year"], min(540.0, useful), places=1)
        self.assertLessEqual(household.hour_allocations[node_id], useful + 1e-6)
        self.assertLess(useful, 540.0)


if __name__ == "__main__":
    unittest.main()
