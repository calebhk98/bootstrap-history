"""Complaint 103: strata and the founder invest in shares. A firm that lenders will not fund for an expansion that pays
raises equity from the best-placed household of a stratum at the investor's own valuation; the shares, the money and
the later dividends move through the books, and money is conserved."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import equity_need, equity_round, joint_stock
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from .agents_fake_world import FakeWorld, make_node, total_money


class GrowthWorld(FakeWorld):
	def scale_ceiling(self, node_id):
		return 10.0

	def expansion_gain(self, node_id, opened_year, capacity, step, rivals):
		return 1.0e7

	def plant_cost(self, node_id, actor=None, capacity=1.0):
		return 1.0e8


def make_world():
	world = GrowthWorld()
	world.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
	return world


def make_registry(savings=1.0e9):
	registry = ActorRegistry(ActorsState(home_country="home"))
	registry.add("stratum:home:merchants", ActorRecord(kind="stratum", stratum="merchants", members=1000.0, money=savings))
	firm = registry.add("firm:1", ActorRecord(kind="firm", money=0.0, founded_year=0, concerns={"shop"},
											  opened_year={"shop": 0}, last_margin=100000.0))
	return registry, firm


# ---- a firm lenders will not fund notes the equity it needs ------------------------------------------------
world = make_world()
registry, firm = make_registry()
firm.expand(world)
need = firm.record.plan.get(equity_need.NEED_KEY, 0.0)
check("an expansion lenders will not fund that pays leaves a need for equity", need > 0.0, firm.record.plan)

# ---- the round sells shares to a stratum household at the investor's valuation ----------------------------
stratum = registry.actors["stratum:home:merchants"]
before = total_money(registry.actors.values())
raised = equity_round.raise_equity(registry, world, firm)
check("the firm raises money", raised > 0.0 and abs(firm.money - raised) < 1e-6, (raised, firm.money))
check("the stratum holds the shares it paid for", 0.0 < stratum.record.holdings.get("firm:1", 0.0) <= 1.0, stratum.record.holdings)
check("the firm's issued equity matches what the stratum holds", abs(firm.record.issued - stratum.record.holdings["firm:1"]) < 1e-9)
check("the price is the investor's own valuation of that share, discounted a year", abs(
	raised - stratum.record.holdings["firm:1"] * equity_round.whole_equity_worth(firm, world)) < 1e-6)
check("money is conserved", abs(total_money(registry.actors.values()) - before) < 1e-6)
check("the need is spent", equity_need.NEED_KEY not in firm.record.plan)
check("the household that invested has the money committed", sum(stratum.record.plan.get("committed", {}).values()) > 0.0)

# ---- and the firm then pays the stratum a dividend by share ----------------------------------------------
firm.record.last_margin = 100000.0
firm.record.income.clear()
stratum_before = stratum.money
paid = joint_stock.pay_dividends(registry, world)
check("a dividend flows back to the investing stratum", paid > 0.0 and stratum.money > stratum_before)

# ---- no investor with savings, no equity -----------------------------------------------------------------
registry, firm = make_registry(savings=0.0)
firm.record.plan[equity_need.NEED_KEY] = 1000.0
check("with no household able to invest, nothing is raised", equity_round.raise_equity(registry, world, firm) == 0.0 and firm.record.issued == 0.0)

# ---- a firm with no margin has nothing to sell -----------------------------------------------------------
registry, firm = make_registry()
firm.record.last_margin = 0.0
firm.record.plan[equity_need.NEED_KEY] = 1000.0
check("a firm that earns nothing sells no equity", equity_round.raise_equity(registry, world, firm) == 0.0)

check("the spawner is registered", "equity_rounds" in dict(__import__("sim.agents.registry", fromlist=["SPAWNERS"]).SPAWNERS))
