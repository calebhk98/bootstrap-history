"""Complaint 462: the concern totals follow entries, exits and capacity changes without walking every operator."""

QUICK_TOPIC = True

import random

from .harness import check

from sim.agents.business import Business
from sim.agents.registry import ActorRegistry
from sim.engine.state import ActorRecord, ActorsState

NODES = {"node_%d" % number: {"cat": "cat_%d" % (number % 3)} for number in range(8)}


class CountingSizes:
	"""Counts how often a business's plant sizes are read."""
	reads = 0
	real = Business.sizes

	@staticmethod
	def counted(business):
		CountingSizes.reads += 1
		return CountingSizes.real(business)


def registry_of(count):
	state = ActorsState()
	for number in range(count):
		state.records["firm:%03d" % number] = ActorRecord(kind="firm", business=Business.running(["node_0"]), workforce={})
	return ActorRegistry(state)


def full_totals(registry):
	totals, categories = {}, {}
	for operator in registry.market_operators():
		for held in operator.concerns:
			size = operator.capacity_of(held)
			totals[held] = totals.get(held, 0.0) + size
			category = NODES[held]["cat"]
			categories[category] = categories.get(category, 0.0) + size
	return totals, categories


def agrees(registry):
	totals, categories = full_totals(registry)
	return (all(abs(registry.capacity_in(node) - totals.get(node, 0.0)) < 1e-9 for node in NODES)
			and all(abs(registry.concerns_in(category, NODES) - categories.get(category, 0.0)) < 1e-9
					for category in ("cat_0", "cat_1", "cat_2")))


dice = random.Random(462)
registry = registry_of(12)
failures = []
for step in range(400):
	firm = registry.actors[dice.choice(sorted(registry.actors))]
	action = dice.choice(["open", "close", "grow", "exit", "enter"])
	node = dice.choice(sorted(NODES))
	if action == "open":
		firm.concerns.add(node)
	elif action == "close":
		firm.concerns.discard(node)
	elif action == "grow" and node in firm.concerns:
		firm.business.set_size(node, firm.capacity_of(node) * dice.uniform(1.0, 2.0))
		registry.note_capacity_change(firm.actor_id)
	elif action == "exit":
		firm.concerns.clear()
		firm.record.exited_year = 1
	elif action == "enter":
		registry.add("firm:new%03d" % step, ActorRecord(kind="firm", business=Business.running([node]), workforce={}))
	if not agrees(registry):
		failures.append((step, action))
		break
check("totals equal a full recomputation after random entries, exits and capacity changes", not failures, failures)


def reads_for_one_change(count):
	registry = registry_of(count)
	Business.sizes = CountingSizes.counted
	try:
		CountingSizes.reads = 0
		registry.actors["firm:000"].business.set_size("node_0", 3.0)
		registry.note_capacity_change("firm:000")
		registry.capacity_in("node_0")
		registry.concerns_in("cat_0", NODES)
		return CountingSizes.reads
	finally:
		Business.sizes = CountingSizes.real


small, large = reads_for_one_change(10), reads_for_one_change(400)
check("one capacity change costs the same work with many operators as with few", small == large and small > 0, (small, large))
