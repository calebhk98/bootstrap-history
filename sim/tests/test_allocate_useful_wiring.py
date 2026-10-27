"""`allocate <project> <hours> useful` on a stand-in game (Complaint 640): the order is capped at what the project can use
(the rule is `capped_to_useful`, in test_workforce_advice_and_allocate_cap), and the cap is stored and reported."""
QUICK_TOPIC = True

from sim.tests import workforce_stand_in
import types
import unittest

from sim.ui.proto.dispatch_labour import _cmd_allocate

NODES = {"project": {"name": "A project"}}


def game(useful_hours):
    return workforce_stand_in.Game(active={"project": {}}, hour_allocations={},
                                   project_useful_hours=lambda node_id: useful_hours)


class AllocateUsefulWiringTests(unittest.TestCase):
    def test_an_order_above_the_useful_hours_is_stored_at_the_useful_hours(self):
        sim = game(360.0)
        reply = _cmd_allocate(sim, NODES, {"id": "project", "hours": 540, "useful": True}, None)
        self.assertEqual((reply["ok"], reply["hours_a_year"], reply["capped_to_useful_work_from"]),
                         (True, 360.0, 540.0))
        self.assertEqual(sim.hour_allocations, {"project": 360.0})

    def test_without_useful_the_order_is_stored_as_given(self):
        sim = game(360.0)
        reply = _cmd_allocate(sim, NODES, {"id": "project", "hours": 540}, None)
        self.assertEqual(reply["hours_a_year"], 540.0)
        self.assertNotIn("capped_to_useful_work_from", reply)
        self.assertEqual(sim.hour_allocations, {"project": 540.0})


if __name__ == "__main__":
    unittest.main()
