"""Complaint 330, part 1: entry is bounded by the market. An entrant expects what it would earn after its own output and
that of the entrants already waiting reaches the market, and enters only while that covers the capital it ties up at
the market's rate; nothing caps the number of firms.

`ActorRegistry.consider_entry` is called on the fake world with a concern whose takings are shared among its sellers.
The wiring of `SimWorld.entry_gross` and the rate in a game is `test_firm_entry_market_scenario`."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState

from .agents_fake_world import FakeWorld, make_node


class SharedMarketWorld(FakeWorld):
	"""A proven concern whose takings are shared among its sellers, with a copy dear enough that capital matters."""

	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id]["rev"]) / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step

	def ramp(self, opened_year, node_id=None):
		return min(1.0, (self.year - opened_year + 1) / 5.0)


def make_world(rate=0.12, takings=60000.0):
	world = SharedMarketWorld()
	world.rate = rate
	world.nodes["shop"] = make_node("shop", hours=100.0, revenue=takings, upkeep=1000.0)
	world.nodes["shop"]["cost"] = 6000.0
	world.demonstrated_nodes = {"shop"}
	world.proven = {"shop"}
	return world


def make_registry():
	registry = ActorRegistry(ActorsState(home_country="home"))
	registry.add("stratum:home:merchants", ActorRecord(
		kind="stratum", stratum="merchants", members=100.0, money=1.0e9, literacy=0.5))
	return registry


class EntryBoundedByTheMarketTests(unittest.TestCase):
	def test_some_firms_enter_a_proven_concern(self):
		self.assertGreater(len(make_registry().consider_entry(make_world())), 0)

	def test_entry_stops_by_itself_with_no_cap(self):
		registry = make_registry()
		world = make_world()
		first = registry.consider_entry(world)
		self.assertGreater(len(first), 1)
		self.assertEqual(registry.consider_entry(world), [])

	def test_a_bigger_market_holds_more_firms(self):
		small = len(make_registry().consider_entry(make_world(takings=60000.0)))
		large = len(make_registry().consider_entry(make_world(takings=240000.0)))
		self.assertGreater(large, small)

	def test_a_dearer_market_rate_for_capital_leaves_fewer_entrants(self):
		usual = len(make_registry().consider_entry(make_world(rate=0.12)))
		dear = len(make_registry().consider_entry(make_world(rate=120.0)))
		self.assertLess(dear, usual)


if __name__ == "__main__":
	unittest.main()
