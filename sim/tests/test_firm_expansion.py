"""Complaint 331: a firm in a growing market grows before another firm is needed. An incumbent whose added capacity
earns more than the capital costs expands, an entrant expects what is left after that, and a market that stops growing
stops gaining capacity.

Rules, each called on the fake world: `Firm.expand` (the return on a step against the rate, the margin gate, the
scale ceiling, the outlay it books) and `ActorRegistry.rivals_of` (an expanded incumbent leaves an entrant a smaller
share). The whole-game wiring is `test_firm_expansion_scenario`."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Business
from sim.agents.tuning import EXPANSION_RATE

from .agents_fake_world import FakeWorld, make_node

PLANT_COST_PER_STEP = 1000.0


class ReturnWorld(FakeWorld):
	"""A concern whose added capacity returns `return_on_step` of what the step costs each year."""

	def __init__(self, return_on_step=0.5, ceiling=10.0):
		super().__init__()
		self.return_on_step = return_on_step
		self.ceiling = ceiling
		self.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)

	def scale_ceiling(self, node_id):
		return self.ceiling

	def plant_cost(self, node_id, actor=None, capacity=1.0):
		return PLANT_COST_PER_STEP * capacity

	def expansion_gain(self, node_id, opened_year, capacity, step, rivals):
		return self.return_on_step * self.plant_cost(node_id, None, step)


def make_firm(world, margin=1.0e5, money=1.0e6):
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(
		kind="firm", money=money, founded_year=0, business=Business.running(["shop"], opened_year=0), last_margin=margin))
	world.edge_book = registry.state
	return registry, firm


class ExpandTests(unittest.TestCase):
	def test_a_return_above_the_cost_of_capital_adds_capacity_and_books_the_outlay(self):
		world = ReturnWorld(return_on_step=0.5)
		world.rate = 0.12
		_registry, firm = make_firm(world)
		firm.expand(world)
		self.assertAlmostEqual(firm.capacity_of("shop"), 1.0 + EXPANSION_RATE)
		self.assertGreater(firm.record.outlays.get("expansion", 0.0), 0.0)

	def test_a_cost_of_capital_above_the_added_margin_stops_expansion(self):
		world = ReturnWorld(return_on_step=0.5)
		world.rate = 1.0
		_registry, firm = make_firm(world)
		firm.expand(world)
		self.assertEqual(firm.capacity_of("shop"), 1.0)

	def test_a_firm_with_no_margin_does_not_expand(self):
		world = ReturnWorld()
		_registry, firm = make_firm(world, margin=-1.0)
		firm.expand(world)
		self.assertEqual(firm.capacity_of("shop"), 1.0)

	def test_a_market_that_adds_nothing_to_a_step_stops_expansion(self):
		world = ReturnWorld(return_on_step=0.0)
		_registry, firm = make_firm(world)
		firm.expand(world)
		self.assertEqual(firm.capacity_of("shop"), 1.0)

	def test_a_firm_at_the_scale_ceiling_does_not_grow(self):
		world = ReturnWorld(ceiling=1.0)
		_registry, firm = make_firm(world)
		firm.expand(world)
		self.assertEqual(firm.capacity_of("shop"), 1.0)

	def test_a_firm_grows_one_step_a_year_however_good_the_return(self):
		world = ReturnWorld(return_on_step=100.0)
		world.rate = 0.0
		_registry, firm = make_firm(world)
		firm.expand(world)
		self.assertAlmostEqual(firm.capacity_of("shop"), 1.0 + EXPANSION_RATE)

	def test_the_owners_tell_the_registry_so_its_totals_follow(self):
		world = ReturnWorld()
		registry, firm = make_firm(world)
		before = registry.capacity_in("shop")
		firm.expand(world)
		self.assertGreater(registry.capacity_in("shop"), before)


class RivalsFollowCapacityTests(unittest.TestCase):
	def test_an_entrant_faces_more_rivals_once_an_incumbent_has_expanded(self):
		world = ReturnWorld()
		registry, firm = make_firm(world)
		before = registry.rivals_of("shop", "")
		firm.business.set_size("shop", 6.0)
		registry.note_capacity_change(firm.actor_id)
		self.assertAlmostEqual(registry.rivals_of("shop", "") - before, 5.0)

	def test_a_firm_does_not_count_its_own_capacity_among_its_rivals(self):
		world = ReturnWorld()
		registry, firm = make_firm(world)
		firm.business.set_size("shop", 6.0)
		registry.note_capacity_change(firm.actor_id)
		self.assertEqual(registry.rivals_of("shop", firm.actor_id), 0.0)


if __name__ == "__main__":
	unittest.main()
