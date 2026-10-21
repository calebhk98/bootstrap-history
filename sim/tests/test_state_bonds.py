"""Complaint 106: a state raises cash by selling bonds that the lending pool's depositors buy at a price from the
going rate and the state's default record (Complaint 623's premium), instead of drawing on the pool at par. A
bond's price is the present value of its coupons and face at the yield asked; the state owes the face; a default
costs the depositors what they paid."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import bonds
from sim.agents.api import ActorRecord, ActorsState
from sim.agents.government import Government
from sim.agents.purses import POOL

from .agents_fake_world import FakeWorld

OUTSIDE = "edge:outside the book"


class CreditWorld(FakeWorld):
	"""A world whose state may borrow, against a revenue of its own."""

	def state_may_borrow(self, state):
		return True

	def state_revenue(self):
		return 1000.0

	def state_reach(self):
		return 0.5


def market(depositors):
	"""A state with an empty purse and lenders that offer the given funds to the pool."""
	registry = ActorsState()
	state = Government("government:home", ActorRecord(kind="government"))
	state.attach(registry.purses)
	for name, funds in depositors.items():
		registry.purses.transfer(OUTSIDE, name, funds, "stake")
	registry.purses.set_offers(dict(depositors))
	return registry.purses, state


# ---- the price is the present value of the coupons and the face at the yield asked -------------------------
check("a bond whose coupon is the yield is worth its face", abs(bonds.bond_price(100.0, 0.05, 10, 0.05) - 100.0) < 1e-9)
check("one year to run at a yield of ten per cent pays a coupon and the face a year hence",
	  abs(bonds.bond_price(100.0, 0.05, 1, 0.10) - 105.0 / 1.10) < 1e-9, bonds.bond_price(100.0, 0.05, 1, 0.10))
prices = [bonds.bond_price(100.0, 0.05, 10, rate) for rate in (0.03, 0.05, 0.08, 0.15)]
check("the price falls as the yield the market asks rises", all(a > b for a, b in zip(prices, prices[1:])), prices)

# ---- the state sells a bond for the cash it lacks: it owes the face, the depositors paid the price -----------
purses, state = market({"household:a": 200.0, "merchant:b": 100.0})
purses.bonds.set_terms(state.account_id, 0.05, 0.08)
price_per_face = purses.bonds.price_per_face(state.account_id)
purses.cover(state.account_id, 150.0)
check("the state holds the cash the bond raised", abs(purses.purse(state.account_id) - 150.0) < 1e-6, purses.purse(state.account_id))
check("it owes the bond's face, which is more than the cash when the yield is above the coupon",
	  abs(purses.debt(state.account_id) - 150.0 / price_per_face) < 1e-6 and purses.debt(state.account_id) > 150.0,
	  (purses.debt(state.account_id), price_per_face))
check("it holds no facility on the pool: the bond is the debt", purses.contracts.facility_of(state.account_id) == {},
	  purses.contracts.facility_of(state.account_id))
claims = purses.named_lenders.claims(state.account_id)
check("the depositors that bought it are named in proportion to what each put in the pool, at what they paid",
	  abs(claims["household:a"] - 100.0) < 1e-6 and abs(claims["merchant:b"] - 50.0) < 1e-6, claims)
check("the state's net position is the cash less the face", abs(state.money - (150.0 - 150.0 / price_per_face)) < 1e-6, state.money)

# ---- the coupon is a fixed rate on the face, not the floating rate on the debt ----------------------------
check("the coupons due are the coupon rate on the face",
	  abs(purses.bonds.coupons_due(state.account_id) - 0.05 * 150.0 / price_per_face) < 1e-6)
received = purses.pay_interest(state.account_id, purses.bonds.coupons_due(state.account_id))
check("a state with bonds and no facility pays its interest to the pool", list(received) == [POOL], received)

# ---- a default record cuts the price: the same cash costs more face -----------------------------------------
clean_purses, clean = market({"household:a": 500.0})
marked_purses, marked = market({"household:a": 500.0})
world = CreditWorld()
marked.record.remembered_default_loss = 400.0
clean.set_bond_terms(world)
marked.set_bond_terms(world)
check("a state with a default on its record is asked a higher yield, same coupon",
	  marked_purses.bonds.terms[marked.account_id][1] > clean_purses.bonds.terms[clean.account_id][1] + 1e-9
	  and marked_purses.bonds.terms[marked.account_id][0] == clean_purses.bonds.terms[clean.account_id][0],
	  (marked_purses.bonds.terms, clean_purses.bonds.terms))
check("so its bonds sell for less on the face",
	  marked_purses.bonds.price_per_face(marked.account_id) < clean_purses.bonds.price_per_face(clean.account_id) - 1e-9,
	  (marked_purses.bonds.price_per_face(marked.account_id), clean_purses.bonds.price_per_face(clean.account_id)))
clean_purses.cover(clean.account_id, 100.0)
marked_purses.cover(marked.account_id, 100.0)
check("and it owes more face for the same cash", marked_purses.debt(marked.account_id) > clean_purses.debt(clean.account_id) + 1e-9,
	  (marked_purses.debt(marked.account_id), clean_purses.debt(clean.account_id)))

# ---- a default costs the depositors what they paid, not the face ----------------------------------------------
purses, state = market({"household:a": 200.0, "merchant:b": 100.0})
purses.bonds.set_terms(state.account_id, 0.05, 0.10)
purses.cover(state.account_id, 150.0)
purses.transfer(state.account_id, OUTSIDE, 150.0, "spent")
before = {name: purses.deposit(name) for name in ("household:a", "merchant:b")}
state.default(CreditWorld())
after = {name: purses.deposit(name) for name in before}
check("a defaulting state's bonds are gone", purses.debt(state.account_id) < 1e-9, purses.debt(state.account_id))
check("each depositor that bought them loses what it paid",
	  abs((before["household:a"] - after["household:a"]) - 100.0) < 1e-6
	  and abs((before["merchant:b"] - after["merchant:b"]) - 50.0) < 1e-6, (before, after))

# ---- a bond falls due at the end of its term: the state repays the face, borrowing anew if it must -------------
purses, state = market({"household:a": 1000.0})
purses.bonds.set_terms(state.account_id, 0.05, 0.05)
purses.cover(state.account_id, 100.0)
purses.transfer(state.account_id, OUTSIDE, 100.0, "spent")
for _year in range(int(bonds.BOND_TERM_YEARS) - 1):
	check("a bond not yet at its term is not repaid", purses.redeem_bonds(state.account_id) == 0.0)
repaid = purses.redeem_bonds(state.account_id)
check("at its term the face is repaid", abs(repaid - 100.0) < 1e-6, repaid)
check("short of cash the state sold a new bond to repay it, so it still owes the face",
	  abs(purses.debt(state.account_id) - 100.0) < 1e-6, purses.debt(state.account_id))
check("the old bond is gone and the new one is a year old", len(purses.bonds.held[state.account_id]) == 1
	  and purses.bonds.held[state.account_id][0].years_left == bonds.BOND_TERM_YEARS)

# ---- the bonds survive the save -----------------------------------------------------------------------------
loaded = type(purses).from_record(purses.to_canon_dict())
check("the terms and the bonds outstanding are saved", loaded.bonds.to_canon_dict() == purses.bonds.to_canon_dict())
