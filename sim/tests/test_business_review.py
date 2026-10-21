"""Stage 3b of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md: the yearly rules are one `Business.review`.

The loss rule of a firm is tested on a built world; the founder's seat, the creditors' seizure and the refusals of
`open` and `stuck` are named scenarios on a game.

A business that loses money for consecutive years closes under one rule for a seat and a firm; a creditor's
seizure takes the plant and leaves the knowledge; `open` and `stuck` refuse a shut concern for the same cause."""
import unittest

from .harness import NODES, sim

from sim.agents import business_review
from sim.engine.agents_port import SimWorld
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Business
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)
from sim.agents.tuning import EXIT_LOSS_YEARS
from sim.ui.proto import dispatch_inspection_stuck as dispatch_inspection, state_shut_staffing

from .agents_fake_world import FakeWorld, make_node
from .test_founder_and_firm_agree import founder_running_an_artisan_concern


def a_firm_running(entry_key):
	world = FakeWorld(year=50)
	world.nodes[entry_key] = make_node(entry_key, hours=100.0, revenue=10.0, upkeep=1.0)
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(kind="firm", founded_year=0, business=Business.running([entry_key], opened_year=0)))
	return world, firm


def a_seat_that_sheds_losses():
	game, node_id = founder_running_an_artisan_concern()
	game.state.founder.policy["auto_shed"] = True
	return game, node_id


def years_until_closed(business, owner, world, margin, limit=3 * EXIT_LOSS_YEARS):
	"""Tally `margin` year after year, reviewing the loss rule each time; the number of years until a plant is closed."""
	entry_key = next(iter(business.entry_keys()))
	for years in range(1, limit + 1):
		business.note_year(entry_key, margin)
		closed = business.review(owner, world, rules=(business_review.LOSS_MAKING,))
		if closed:
			return years, closed
	return None, []


class LossRuleIsOneRule(unittest.TestCase):
	def test_a_firm_closes_a_plant_after_the_shared_run_of_loss_years(self):
		world, firm = a_firm_running("shop")
		years, closed = years_until_closed(firm.business, firm, world, margin=-1.0)
		self.assertEqual(years, EXIT_LOSS_YEARS)
		self.assertEqual([(closure.entry_key, closure.reason) for closure in closed], [("shop", business_review.LOSS_MAKING)])
		self.assertIsNone(firm.business.plant_of("shop"))

	def test_a_profitable_year_restarts_the_count(self):
		world, firm = a_firm_running("shop")
		for margin in [-1.0] * (EXIT_LOSS_YEARS - 1) + [1.0] + [-1.0] * (EXIT_LOSS_YEARS - 1):
			firm.business.note_year("shop", margin)
			self.assertEqual(firm.business.review(firm, world, rules=(business_review.LOSS_MAKING,)), [])
		self.assertEqual(firm.business.plant_of("shop").loss_years, EXIT_LOSS_YEARS - 1)

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


class SeizureTakesTheBusiness(unittest.TestCase):
	def test_scenario_creditors_take_a_plant_that_does_not_pay_and_leave_one_that_does(self):
		game, node_id = founder_running_an_artisan_concern()
		node = game.nodes[node_id]
		saved = (node["rev"], node["up"])
		node["rev"], node["up"] = 0.0, max(node["up"], 1000.0)
		try:
			game.state.household.capital = -(game.credit_limit() + 10 * node["up"])
			before = game.state.household.capital
			game.answer_exhausted_credit(game.year)
			self.assertEqual(game.state.projects.business.state_of(node_id), "mothballed")
			self.assertEqual(game.closure_of(node_id)["reason"], game.CLOSED_CREDITOR_SEIZURE)
			self.assertIn(node_id, game.done)
			self.assertGreater(game.state.household.capital, before)   # the creditors' proceeds
		finally:
			node["rev"], node["up"] = saved
		paying, paying_id = founder_running_an_artisan_concern()
		node = paying.nodes[paying_id]
		saved = (node["rev"], node["up"])
		node["rev"], node["up"] = 10.0 * max(node["up"], 1.0), max(node["up"], 1.0)
		try:
			paying.state.household.capital = -(paying.credit_limit() + 1.0)
			paying.answer_exhausted_credit(paying.year)
			self.assertEqual(paying.state.projects.business.state_of(paying_id), "operating")
		finally:
			node["rev"], node["up"] = saved


class OpenAndStuckRefuseForOneCause(unittest.TestCase):
	CONCERN = "mirror_amalgam"   # earns from its output and needs a glassblower foreman to run

	def setUp(self):
		self.game = sim(capital=1e6)
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

	def test_scenario_a_running_gate_is_a_coded_refusal(self):
		gated = [node_id for node_id in sorted(NODES) if self.game.is_venture(node_id) and NODES[node_id].get("requires_running")]
		self.assertTrue(gated, "no concern in the data requires another work running")
		for node_id in gated:
			if self.game.unmet_running_gates(node_id):
				refusal = self.game.open_refusal(node_id)
				self.assertEqual(refusal.cause, "running_gate")
				return
		self.fail("every gate in the data is met at the start")


if __name__ == "__main__":
	unittest.main()
