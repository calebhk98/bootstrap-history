"""Scenario (Complaint 640): in a built game `allocate ... useful` caps at the useful work. The rule is in
test_workforce_advice_and_allocate_cap; the scholar gate, whose refusal on a project one scholar short says to hire one, is
called on built numbers in test_founder_hours_rules."""
import unittest

from .harness import *  # noqa: F401,F403


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
