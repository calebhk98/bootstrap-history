"""SCENARIO (Stage 3b of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md): on a game the founder's seat reviews its loss rule
as a firm does, and `open` and `stuck` refuse a shut concern for the same cause. The loss rule on a built world is in
test_business_review and the seizure of a plant in test_seat_creditors_rule."""
import unittest

from .harness import NODES, unopened_sim

from sim.agents import business_review
from sim.engine.agents_port import SimWorld
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)
from sim.agents.tuning import EXIT_LOSS_YEARS
from sim.ui.proto import dispatch_inspection_stuck as dispatch_inspection, state_shut_staffing

from .test_business_review import years_until_closed
from .test_founder_and_firm_agree import founder_running_an_artisan_concern


def a_seat_that_sheds_losses():
	game, node_id = founder_running_an_artisan_concern()
	game.state.founder.policy["auto_shed"] = True
	return game, node_id


class LossRuleOnASeat(unittest.TestCase):
	def test_scenario_a_seat_reviews_its_loss_rule_as_a_firm_does(self):
		game, node_id = a_seat_that_sheds_losses()
		years, closed = years_until_closed(game.state.projects.business, game.household, SimWorld(game), margin=-1.0)
		self.assertEqual(years, EXIT_LOSS_YEARS)
		self.assertEqual([(closure.entry_key, closure.reason) for closure in closed], [(node_id, business_review.LOSS_MAKING)])
		self.assertEqual(game.state.projects.business.state_of(node_id), "mothballed")
		self.assertEqual(game.closure_of(node_id)["reason"], game.CLOSED_LOSS_MAKING)
		self.assertIn(node_id, game.done)   # the shop shuts; the knowledge stays
		# a capability institution is not shed for a loss
		school = sorted(game.CAPABILITY_INSTITUTIONS)[0]
		game.state.projects.business.open_plant(school, game.year)
		for _ in range(2 * EXIT_LOSS_YEARS):
			game.state.projects.business.note_year(school, -1.0)
			game.state.projects.business.review(game.household, SimWorld(game), rules=(business_review.LOSS_MAKING,))
		self.assertEqual(game.state.projects.business.state_of(school), "operating")
		# a seat that switched auto_shed off keeps its plant
		kept, kept_id = founder_running_an_artisan_concern()
		kept.state.founder.policy["auto_shed"] = False
		never, _closed = years_until_closed(kept.state.projects.business, kept.household, SimWorld(kept), margin=-1.0)
		self.assertIsNone(never)
		self.assertEqual(kept.state.projects.business.state_of(kept_id), "operating")


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
