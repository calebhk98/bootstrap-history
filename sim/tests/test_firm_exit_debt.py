"""Complaint 477: a firm whose interest outruns its margin closes, however thin the positive margin. What it
owes is written off, so lenders are left no claim on a firm that no longer exists, and an indebted firm
whose margin covers its interest stays."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents.tuning import EXIT_LOSS_YEARS

from .agents_fake_world import FakeWorld, make_node


class NoGrowthWorld(FakeWorld):
	"""A world whose concerns cannot be made larger, so only the firm's debt and margin are in question."""

	def scale_ceiling(self, node_id):
		return 1.0


def indebted_firm(debt, revenue):
	"""A firm running a concern past its ramp that owes `debt`, in a world where the concern earns `revenue` less costs."""
	world = NoGrowthWorld(year=50)
	world.nodes["shop"] = make_node("shop", hours=100.0, revenue=revenue, upkeep=1000.0)
	world.demonstrated_nodes = {"shop"}
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(kind="firm", founded_year=0, concerns={"shop"}, opened_year={"shop": 0}))
	firm.money = -debt
	return world, registry, firm


def years_until_closed(world, firm, limit=3 * EXIT_LOSS_YEARS + 10):
	for _ in range(limit):
		if firm.record.exited_year is not None:
			break
		world.year += 1
		firm.act(world)
	return firm


# a thin positive margin, a large debt compounding at the market rate: the firm stays in business today
world, registry, firm = indebted_firm(debt=200000.0, revenue=1300.0)
owed_at_start = firm.debt()
years_until_closed(world, firm)
check("a firm whose interest outruns its margin closes", firm.record.exited_year is not None,
	(firm.record.last_margin, firm.debt(), owed_at_start))
check("what a closed firm owed is written off: no lender holds a claim on it",
	firm.debt() == 0.0 and not registry.state.purses.claims.get(firm.account_id), registry.state.purses.claims)
check("a closed firm runs nothing and owes nothing", not firm.concerns and firm.money == 0.0, firm.money)

# the same margin with a debt its margin carries stays open and pays the interest
world, registry, firm = indebted_firm(debt=500.0, revenue=1300.0)
years_until_closed(world, firm)
check("a firm whose margin covers its interest stays open", firm.record.exited_year is None,
	(firm.record.last_margin, firm.debt()))
