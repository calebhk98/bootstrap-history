"""Complaint 79: every event in a real step reply carries a severity tier name."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.ui.proto import event_severity


class StepReplyCarriesSeverity(unittest.TestCase):

    def test_every_step_event_has_a_severity_name(self):
        from sim.ui.protocol import _agent_dispatch
        household = sim(civ="rome_100ad", capital=1e5)
        household.end_year = household.cfg["start_year"] + 50
        reply = _agent_dispatch(household, NODES, {"cmd": "step", "years": 3})
        self.assertTrue(reply["events"])
        for event in reply["events"]:
            self.assertIn(event["severity"], event_severity.TIER_NAMES)


if __name__ == "__main__":
    unittest.main()
