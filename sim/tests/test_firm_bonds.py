"""Complaint 106: a firm, not only a state, sells bonds for the cash it lacks once its society holds the bond market
(a node declaring `bond_market`). The coupon is the going rate and the price follows the firm's own borrowing rate (its
leverage and standing), so a firm deep in debt sells the same coupon for less; a society without the market has the
firm draw on its facility as before. A default costs the depositors what they paid."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, Business, ActorRegistry, ActorsState
from sim.agents.purses import POOL
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from .agents_fake_world import FakeWorld

BOND_NODE = "fin_bond"
OUTSIDE = "edge:outside the book"


class BondWorld(FakeWorld):
	"""A society whose tree has a node declaring the bond market."""

	def nodes_with_mechanic(self, mechanic):
		return (BOND_NODE,) if mechanic == "bond_market" else ()


def firm_with_savers(world, knows, debt=0.0, margin=50.0):
	registry = ActorRegistry(ActorsState(home_country="home"))
	firm = registry.add("firm:1", ActorRecord(kind="firm", founded_year=49, last_margin=margin, business=Business()))
	if knows:
		firm.knowledge.add(BOND_NODE)
	purses = registry.state.purses
	purses.transfer(OUTSIDE, "household:a", 1000.0, "stake")
	purses.set_offers({"household:a": 1000.0})
	if debt:
		firm.money = -debt
	return registry, firm, purses


world = BondWorld(year=50)
registry, firm, purses = firm_with_savers(world, knows=True)
firm.prepare_bonds(world)
coupon, asked = purses.bonds.terms[firm.account_id]
check("a firm whose society holds the bond market sells at the going rate as coupon", abs(coupon - world.market_rate()) < 1e-12, coupon)
check("and at the yield its own borrowing rate gives", abs(asked - firm.borrowing_rate(world)) < 1e-12, asked)
purses.cover(firm.account_id, 100.0)
check("a shortfall is met by a bond, not a facility draw", purses.bonds.debt(firm.account_id) > 0.0 and not purses.contracts.facility_of(firm.account_id),
	  (purses.bonds.debt(firm.account_id), purses.contracts.facility_of(firm.account_id)))
check("the firm owes the face, at least the cash it raised", purses.debt(firm.account_id) >= 100.0 - 1e-9, purses.debt(firm.account_id))

registry, firm, purses = firm_with_savers(world, knows=False)
firm.prepare_bonds(world)
check("a firm that does not know the bond market sets no terms", firm.account_id not in purses.bonds.terms)
purses.cover(firm.account_id, 100.0)
check("it draws on its facility as before", purses.bonds.debt(firm.account_id) == 0.0 and purses.contracts.facility_of(firm.account_id))

registry, plain_world_firm, purses = firm_with_savers(FakeWorld(year=50), knows=True)
plain_world_firm.prepare_bonds(FakeWorld(year=50))
check("a society with no node declaring the market lets no firm issue", plain_world_firm.account_id not in purses.bonds.terms)

# the more leveraged firm is asked a higher yield, so the same cash costs it more face
world = BondWorld(year=50)
light_registry, light, light_purses = firm_with_savers(world, knows=True, debt=1.0)
heavy_registry, heavy, heavy_purses = firm_with_savers(world, knows=True, debt=900.0)
light.prepare_bonds(world)
heavy.prepare_bonds(world)
check("a firm closer to its ceiling is asked a higher yield for the same coupon",
	  heavy_purses.bonds.terms[heavy.account_id][1] > light_purses.bonds.terms[light.account_id][1] + 1e-9,
	  (heavy_purses.bonds.terms, light_purses.bonds.terms))
check("so its bonds sell for less on the face",
	  heavy_purses.bonds.price_per_face(heavy.account_id) < light_purses.bonds.price_per_face(light.account_id) - 1e-9)

# a default costs the depositors what they paid
registry, firm, purses = firm_with_savers(world, knows=True)
firm.prepare_bonds(world)
purses.cover(firm.account_id, 100.0)
purses.transfer(firm.account_id, OUTSIDE, 100.0, "spent")
before = purses.deposit("household:a")
firm.default(world)
check("a defaulting firm's bonds are gone and its depositors lose what they paid",
	  purses.debt(firm.account_id) < 1e-9 and abs((before - purses.deposit("household:a")) - 100.0) < 1e-6,
	  (purses.debt(firm.account_id), before, purses.deposit("household:a")))
check("the pool's books balance", purses.book.check_conservation(1e-9).ok and purses.purse(POOL) >= -1e-9)
