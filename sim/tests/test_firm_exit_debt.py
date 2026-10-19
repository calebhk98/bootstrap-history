"""Complaint 477: a firm whose interest outruns its margin closes, however thin the positive margin. What it
owes is written off, so lenders are left no claim on a firm that no longer exists, and an indebted firm
whose margin covers its interest stays."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, Business, ActorRegistry, ActorsState
from sim.agents import firm_exit
from sim.agents.purses import COIN, EDGE_OUTSIDE, EDGE_SAVERS
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)
from sim.agents.tuning import EXIT_LOSS_YEARS
from sim.book import Transfer

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
	firm = registry.add("firm:1", ActorRecord(kind="firm", founded_year=0, business=Business.running(["shop"], opened_year=0)))
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
firm.record.last_margin = 1.0e6   # standing earning carries a debt of this size
years_until_closed(world, firm)
check("a firm whose margin covers its interest stays open", firm.record.exited_year is None,
	(firm.record.last_margin, firm.debt()))


# creditors come before the backer: a closing firm's cash repays its lenders first, the backer gets what is left,
# and only the unpaid part of the debt is written off
def closing_with(cash, owed):
	"""A firm holding `cash` while lenders hold claims of `owed` on it (put there directly: a purse that takes
	money in repays its claims at once, so the two meet only as a fixture)."""
	world = NoGrowthWorld(year=50)
	registry = ActorRegistry(ActorsState(home_country="home"))
	backer = registry.add("stratum:home:merchants", ActorRecord(kind="stratum", stratum="merchants", members=1.0, money=0.0))
	firm = registry.add("firm:2", ActorRecord(kind="firm", founded_year=0, business=Business.running(["shop"]), plan={"backer": backer.actor_id}))
	firm.find_actor = registry.actors.get
	purses = registry.state.purses
	if cash > 0.0:
		purses.book.transfer(Transfer(EDGE_OUTSIDE, firm.account_id, COIN, cash, "fixture"))
	purses.contracts.set_facility(firm.account_id, {EDGE_SAVERS: owed}, COIN)
	return world, registry, firm, backer


def close_and_measure(cash, owed):
	world, registry, firm, backer = closing_with(cash, owed)
	purses = registry.state.purses
	savers_before = purses.purse(EDGE_SAVERS)
	firm_exit.close_firm(firm, world)
	return (purses.purse(EDGE_SAVERS) - savers_before, backer.money, purses.debt(firm.account_id), purses.purse(firm.account_id))


recovered, to_backer, still_owed, left = close_and_measure(cash=150.0, owed=100.0)
check("a closing firm repays its lenders in full before its backer is paid", abs(recovered - 100.0) < 1e-9, recovered)
check("the backer gets what the lenders did not need", abs(to_backer - 50.0) < 1e-9, to_backer)
check("nothing is owed or held after closing", still_owed == 0.0 and abs(left) < 1e-9, (still_owed, left))

recovered, to_backer, still_owed, left = close_and_measure(cash=40.0, owed=100.0)
check("cash short of the debt goes wholly to the lenders", abs(recovered - 40.0) < 1e-9 and to_backer == 0.0, (recovered, to_backer))
check("the unpaid part is written off", still_owed == 0.0)

world, registry, firm, backer = closing_with(0.0, 100.0)
firm_exit.close_firm(firm, world)
check("a firm closing in debt pays its backer nothing, in either direction",
	backer.money == 0.0 and not backer.record.income and not backer.record.outlays, (backer.money, backer.record.income))
