"""Complaint 623: a state borrows from named lenders (the depositors of the lending pool: households' savings, firms,
merchants, other states). A state that defaults writes down its lenders' claims, and its record raises the rate it pays
afterwards."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import borrowing_arrears
from sim.agents.api import ActorRecord, ActorsState
from sim.agents.government import Government

from .agents_fake_world import FakeWorld


class CreditWorld(FakeWorld):
	"""A world whose state may borrow, against a revenue of its own."""

	def state_may_borrow(self, state):
		return True

	def state_revenue(self):
		return 1000.0

	def state_capacity(self):
		return 0.5


def market(depositors):
	"""A state with an empty purse, and lenders that offer the given funds to the pool."""
	registry = ActorsState()
	state = Government("government:home", ActorRecord(kind="government"))
	state.attach(registry.purses)
	for name, funds in depositors.items():
		registry.purses.transfer("edge:outside the book", name, funds, "stake")
	registry.purses.set_offers(dict(depositors))
	registry.purses.named_lenders.name(state.account_id)
	return registry.purses, state


# ---- the draw is attributed to the lenders that funded it ---------------------------------------------
purses, state = market({"household:a": 200.0, "merchant:b": 100.0})
purses.cover(state.account_id, 150.0)
purses.transfer(state.account_id, "edge:outside the book", 150.0, "spent")
claims = purses.named_lenders.claims(state.account_id)
check("a state's debt is held by named lenders in proportion to what each put in the pool",
	  abs(claims["household:a"] - 100.0) < 1e-6 and abs(claims["merchant:b"] - 50.0) < 1e-6, claims)
check("the claims sum to the state's debt", abs(sum(claims.values()) - purses.debt(state.account_id)) < 1e-6, (claims, purses.debt(state.account_id)))

purses.transfer("edge:outside the book", state.account_id, 90.0, "revenue")
claims = purses.named_lenders.claims(state.account_id)
check("a repayment reduces every lender's claim in proportion",
	  abs(claims["household:a"] - 40.0) < 1e-6 and abs(claims["merchant:b"] - 20.0) < 1e-6, claims)

# ---- a default is the named lenders' loss, and a later lender is spared ----------------------------------
purses, state = market({"household:a": 200.0, "merchant:b": 100.0})
purses.cover(state.account_id, 150.0)
purses.transfer(state.account_id, "edge:outside the book", 150.0, "spent")
purses.transfer("edge:outside the book", "state:other", 500.0, "reserve")   # a lender that came after the loan
purses.set_offers({"household:a": 200.0, "merchant:b": 100.0, "state:other": 500.0})
before = {name: purses.deposit(name) for name in ("household:a", "merchant:b", "state:other")}
state.default(CreditWorld())
after = {name: purses.deposit(name) for name in before}
check("a defaulting state's debt is written off", purses.debt(state.account_id) < 1e-9, purses.debt(state.account_id))
check("each named lender's deposit is written down by its claim",
	  abs((before["household:a"] - after["household:a"]) - 100.0) < 1e-6
	  and abs((before["merchant:b"] - after["merchant:b"]) - 50.0) < 1e-6, (before, after))
check("a lender that came after the loan loses nothing", abs(before["state:other"] - after["state:other"]) < 1e-9, (before, after))
check("the lenders' losses are kept in the state's book",
	  abs(purses.named_lenders.lost(state.account_id)["household:a"] - 100.0) < 1e-6, purses.named_lenders.lost(state.account_id))

# ---- a default raises the rate the state pays afterwards, and the premium fades ------------------------------
purses, state = market({"household:a": 200.0})
world = CreditWorld()
state.money = -40.0
clean_rate = state.borrowing_rate(world)
state.default(world)
state.money = -40.0
marked_rate = state.borrowing_rate(world)
check("a state that has defaulted pays a higher rate on the same debt", marked_rate > clean_rate + 1e-9, (clean_rate, marked_rate))
check("the premium comes from the size of the loss the record holds", state.record.remembered_default_loss > 0.0,
	  state.record.remembered_default_loss)
for _ in range(60):
	state.fade_default_record()
check("the premium fades over the years", abs(state.borrowing_rate(world) - clean_rate) < 1e-3,
	  (state.borrowing_rate(world), clean_rate))

# ---- the 589 rule takes a state that cannot pay its interest to default ---------------------------------------
purses, state = market({"household:a": 200.0})
state.money = -1.0e7
world = CreditWorld()
for _ in range(borrowing_arrears.ARREARS_YEARS_BEFORE_DEFAULT + 1):
	state.pay_interest(world)
check("a state in arrears for the shared run of years defaults, and its record shows the loss",
	  state.record.remembered_default_loss > 0.0, state.record.remembered_default_loss)
