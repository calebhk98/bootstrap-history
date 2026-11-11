"""Complaint 106: the firm's expansion chooses equity over debt on cost. With lenders willing, a firm whose borrowing rate
is above what its shares cost notes an equity need; one whose borrowing rate is not above it borrows. A firm no
investor served recently borrows."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import capital_structure, equity_need
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Business

from .agents_fake_world import FakeWorld, make_node


class GrowthWorld(FakeWorld):
	def scale_ceiling(self, node_id):
		return 10.0

	def expansion_gain(self, node_id, opened_year, capacity, step, rivals):
		return 1.0e7

	def plant_cost(self, node_id, actor=None, capacity=1.0):
		return 1.0e3


def make_firm(borrowing_rate):
	world = GrowthWorld()
	world.setting.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(kind="firm", money=0.0, founded_year=0,
											  business=Business.running(["shop"], opened_year=0), last_margin=100000.0))
	firm.draw_limit = lambda world, amount: amount            # lenders will fund it
	firm.borrowing_rate = lambda world: borrowing_rate
	return world, firm


market = GrowthWorld().credit.market_rate()
world, firm = make_firm(market + 0.05)
firm.expansion.expand(world)
check("a firm whose lenders ask more than its shares cost sells shares though lenders would lend",
	  firm.record.plan.get(equity_need.NEED_KEY, 0.0) > 0.0, firm.record.plan)

world, firm = make_firm(market)
firm.expansion.expand(world)
check("a firm whose lenders ask no more than its shares cost borrows",
	  firm.record.plan.get(equity_need.NEED_KEY, 0.0) == 0.0, firm.record.plan)

world, firm = make_firm(market + 0.05)
firm.record.plan[capital_structure.EQUITY_REFUSED_KEY] = world.setting.year
firm.expansion.expand(world)
check("a firm no investor served this year borrows however dear the debt",
	  firm.record.plan.get(equity_need.NEED_KEY, 0.0) == 0.0, firm.record.plan)
