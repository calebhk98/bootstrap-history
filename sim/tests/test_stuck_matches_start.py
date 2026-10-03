"""`stuck` counts as payable exactly the starts `start` accepts, and a
refusal states the rule and the amount short."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.ui.proto import dispatch_inspection


def _in_debt(capital):
    household = sim(civ="rome_100ad", capital=5000)
    household.state.household.capital = capital
    return household


class StuckAndStartShareOneRule(unittest.TestCase):

    def test_every_start_stuck_calls_payable_is_accepted(self):
        for capital in (0, -3000, -6000, -9000):
            household = _in_debt(capital)
            _, payable = dispatch_inspection._stuck_startable_and_afford(
                household, NODES, False)
            refused = [node_id for node_id in payable if household.start_refusal(node_id)]
            self.assertEqual(refused, [], "capital %s" % capital)

    def test_refusal_states_rule_and_amount_short(self):
        household = _in_debt(-6000)
        startable = [node_id for node_id in NODES
                     if node_id not in household.done and household.start_reason(node_id)[0]]
        text = next(household.start_refusal(node_id) for node_id in startable
                    if household.start_refusal(node_id))
        self.assertIn("short", text)
        self.assertIn("credit line", text)
