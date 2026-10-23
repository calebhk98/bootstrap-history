"""SMOKE (Stage 3b of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md): on an unopened game `open`, `stuck` and the state
screen refuse a shut concern for the same cause. The loss rule on a built world is in test_business_review; the seat's
loss rule and the seizure of a plant are in test_seat_creditors_rule."""
import unittest

from .harness import NODES, unopened_sim

from sim.ui.proto import dispatch_inspection_stuck as dispatch_inspection, state_shut_staffing


class OpenAndStuckRefuseForOneCause(unittest.TestCase):
	CONCERN = "mirror_amalgam"   # earns from its output and needs a glassblower foreman to run

	def setUp(self):
		self.game = unopened_sim(capital=1e6)
		self.game.done.add(self.CONCERN)
		self.game._done_changed()
		self.game.state.household.artisans = 50.0
		self.game.state.household.scholars = 50.0

	def test_scenario_open_stuck_and_state_refuse_a_shut_concern_for_one_cause(self):
		reason = dispatch_inspection._stuck_shut_ventures(self.game, NODES)
		ok, stuck_refusal = self.game.open_venture(reason["the_best_one"])
		self.assertFalse(ok)
		self.assertEqual(reason["blocked_by"], stuck_refusal.cause)
		ok, refusal = self.game.open_venture(self.CONCERN)
		self.assertFalse(ok)
		self.assertEqual(refusal.cause, "foreman_missing")
		rows = {row["id"]: row for row in state_shut_staffing.shut_for_want_of_staff(self.game, NODES)}
		self.assertIn(refusal.facts["trade"], rows[self.CONCERN]["missing"])
		again = self.game.open_refusal(self.CONCERN, self.game.opening_fee(self.CONCERN)[1], with_advice=False)
		self.assertEqual((refusal.cause, refusal.facts), (again.cause, again.facts))


if __name__ == "__main__":
	unittest.main()
