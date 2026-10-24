"""Royalty collection, one function per check on written-out holdings and takings: `royalty_due`,
`collect_patent_royalty` (a patent holder's royalty), `seat_royalties_due` (the seats that licensed an invention) and
`DisclosureView.collect_royalty` (both together, paid through the ledger)."""
QUICK_TOPIC = True

from types import SimpleNamespace

from sim.agents.licence import collect_patent_royalty, royalty_due
from sim.engine.agents_port_disclosure import DisclosureView
from sim.engine.seat_royalty import seat_royalties_due, seat_royalties_paid
from sim.engine.state import ProjectsState
from sim.tests.harness import check


class Party:
	"""An actor with a purse and a record: what the ledger moves money between."""

	def __init__(self, actor_id, money, patents=None, royalty_owed=None):
		self.actor_id = actor_id
		self.money = money
		self.record = SimpleNamespace(patents=patents or {}, royalty_owed=royalty_owed or {})

	def debit(self, amount, purpose):
		self.money -= amount

	def credit(self, amount, purpose):
		self.money += amount

	def note_outlay(self, purpose, amount):
		pass

	def note_income(self, purpose, amount):
		pass


def seat(done=(), granted=(), licensees=None, node="loom"):
	"""A seat's projects: it built `node` itself when `node` is in `done` and not in `granted`."""
	projects = ProjectsState(done=set(done), granted=set(granted))
	if licensees is not None:
		projects.disclosures[node] = {"mode": "license", "licensees": licensees}
	return SimpleNamespace(projects=projects)


def firm_owing(rate, holder="firm:1", node="loom", money=1000.0):
	return Party("firm:2", money, royalty_owed={node: {"holder": holder, "rate": rate}})


def holder_with(expires, money=100.0, node="loom"):
	return Party("firm:1", money, patents={node: {"granted": 90, "expires": expires, "licensees": ["firm:2"]}})


def finder(*parties):
	return {party.actor_id: party for party in parties}.get


# ---- royalty_due
check("royalty_due: a share of positive takings", royalty_due(2000.0, {"royalty": 0.1}) == 200.0)
check("royalty_due: losses owe nothing", royalty_due(-500.0, {"royalty": 0.1}) == 0.0)
check("royalty_due: a licence with no royalty owes nothing", royalty_due(2000.0, {"fee": 50.0}) == 0.0)

# ---- collect_patent_royalty
holder, firm = holder_with(110), firm_owing(0.1)
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder), firm, "loom", 2000.0)
check("collect_patent_royalty: the licensee pays the holder the agreed share of takings",
      paid == 200.0 and holder.money == 300.0 and firm.money == 800.0, (paid, holder.money, firm.money))
holder, firm = holder_with(110), firm_owing(0.1, money=20.0)
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder), firm, "loom", 2000.0)
check("collect_patent_royalty: never more than the licensee's purse", paid == 20.0 and holder.money == 120.0 and firm.money == 0.0,
      (paid, holder.money, firm.money))
holder, firm = holder_with(110), firm_owing(0.1, money=-5.0)
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder), firm, "loom", 2000.0)
check("collect_patent_royalty: a licensee in debt pays nothing", paid == 0.0 and holder.money == 100.0 and firm.money == -5.0,
      (paid, holder.money, firm.money))
holder, firm = holder_with(110), firm_owing(0.1)
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder), firm, "loom", 0.0)
check("collect_patent_royalty: no takings, no royalty", paid == 0.0 and holder.money == 100.0 and firm.money == 1000.0, paid)
holder, firm = holder_with(110), firm_owing(0.1)
paid = collect_patent_royalty(SimpleNamespace(year=111), finder(holder), firm, "loom", 2000.0)
check("collect_patent_royalty: nothing once the patent has expired", paid == 0.0 and holder.money == 100.0, paid)
holder, firm = holder_with(110), firm_owing(0.1)
paid = collect_patent_royalty(SimpleNamespace(year=110), finder(holder), firm, "loom", 2000.0)
check("collect_patent_royalty: the patent's last year still pays", paid == 200.0, paid)
holder, firm = holder_with(110), Party("firm:3", 1000.0)
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder), firm, "loom", 2000.0)
check("collect_patent_royalty: a firm that owes no royalty pays nothing", paid == 0.0 and holder.money == 100.0, paid)
firm = firm_owing(0.1, holder="firm:9")
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder_with(110)), firm, "loom", 2000.0)
check("collect_patent_royalty: no holder found, nothing is paid", paid == 0.0 and firm.money == 1000.0, paid)
holder = Party("firm:1", 100.0)
firm = firm_owing(0.1)
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder), firm, "loom", 2000.0)
check("collect_patent_royalty: a holder that no longer holds the patent is paid nothing", paid == 0.0 and holder.money == 100.0, paid)
holder, firm = holder_with(110), firm_owing(0.1)
paid = collect_patent_royalty(SimpleNamespace(year=100), finder(holder), firm, "wheel", 2000.0)
check("collect_patent_royalty: a royalty on one invention is not owed on another", paid == 0.0 and holder.money == 100.0, paid)

# ---- seat_royalties_due
seats = {"alpha": seat(["loom"], [], {"firm:2": {"fee": 0.0, "royalty": 0.1}}),
         "beta": seat(["loom"], [], {"firm:2": {"fee": 0.0, "royalty": 0.25}, "firm:3": {"fee": 0.0, "royalty": 0.5}})}
check("seat_royalties_due: each licensing seat is owed its own share, in joining order",
      seat_royalties_due(seats, "loom", "firm:2", 1000.0) == [("alpha", 100.0), ("beta", 250.0)])
check("seat_royalties_due: only the seats that licensed this firm are owed",
      seat_royalties_due(seats, "loom", "firm:3", 1000.0) == [("beta", 500.0)])
check("seat_royalties_due: a firm nobody licensed owes nothing", seat_royalties_due(seats, "loom", "firm:4", 1000.0) == [])
check("seat_royalties_due: no takings, nothing owed", seat_royalties_due(seats, "loom", "firm:2", 0.0) == [])
check("seat_royalties_due: losses owe nothing", seat_royalties_due(seats, "loom", "firm:2", -1000.0) == [])
check("seat_royalties_due: another invention has no licence", seat_royalties_due(seats, "wheel", "firm:2", 1000.0) == [])
check("seat_royalties_due: no seats, nothing owed", seat_royalties_due({}, "loom", "firm:2", 1000.0) == [])
check("seat_royalties_due: a licence with no royalty owes nothing",
      seat_royalties_due({"alpha": seat(["loom"], [], {"firm:2": {"fee": 50.0}})}, "loom", "firm:2", 1000.0) == [])
check("seat_royalties_due: a seat that was only granted the invention is not its licensor",
      seat_royalties_due({"alpha": seat(["loom"], ["loom"], {"firm:2": {"royalty": 0.1}})}, "loom", "firm:2", 1000.0) == [])
check("seat_royalties_due: a seat that never disclosed it owes and is owed nothing",
      seat_royalties_due({"alpha": seat(["loom"])}, "loom", "firm:2", 1000.0) == [])


# ---- seat_royalties_paid: what the licensee's purse can pay of what the seats are owed
check("seat_royalties_paid: a purse that covers every seat pays each in full",
      seat_royalties_paid([("alpha", 100.0), ("beta", 250.0)], 1000.0) == [("alpha", 100.0), ("beta", 250.0)])
check("seat_royalties_paid: a short purse pays the seats in joining order until it is empty",
      seat_royalties_paid([("alpha", 100.0), ("beta", 250.0)], 150.0) == [("alpha", 100.0), ("beta", 50.0)])
check("seat_royalties_paid: an empty purse pays nobody", seat_royalties_paid([("alpha", 100.0)], 0.0) == [])
check("seat_royalties_paid: a licensee in debt pays nobody", seat_royalties_paid([("alpha", 100.0)], -5.0) == [])


# ---- DisclosureView.collect_royalty: seats and the patent holder together, through the ledger
def view_over(seats, parties, year=100):
	seat_parties = {seat_id: Party(seat_id, 0.0) for seat_id in seats}
	simulation = SimpleNamespace(state=SimpleNamespace(seats=seats), seat_party=seat_parties.__getitem__)
	return SimpleNamespace(_sim=simulation, _holder=finder(*parties), year=year), seat_parties


firm, holder = firm_owing(0.1), holder_with(110)
view, seat_parties = view_over({"alpha": seat(["loom"], [], {"firm:2": {"royalty": 0.2}})}, [holder])
paid = DisclosureView.collect_royalty(view, firm, "loom", 1000.0)
check("collect_royalty: the seat and the patent holder are each paid their share, and the firm pays both",
      paid == 300.0 and seat_parties["alpha"].money == 200.0 and holder.money == 200.0 and firm.money == 700.0,
      (paid, seat_parties["alpha"].money, holder.money, firm.money))
firm = Party("firm:2", 1000.0)
view, seat_parties = view_over({"alpha": seat(["loom"])}, [])
paid = DisclosureView.collect_royalty(view, firm, "loom", 1000.0)
check("collect_royalty: with no licence and no patent nobody is paid", paid == 0.0 and seat_parties["alpha"].money == 0.0 and firm.money == 1000.0, paid)
firm = Party("firm:2", 1000.0)
view, seat_parties = view_over({}, [])
check("collect_royalty: with no seats and no holder there is nothing to collect", DisclosureView.collect_royalty(view, firm, "loom", 1000.0) == 0.0 and firm.money == 1000.0)
firm = firm_owing(0.1)
view, _ = view_over({}, [holder_with(110)])
check("collect_royalty: a patent holder alone is paid", DisclosureView.collect_royalty(view, firm, "loom", 1000.0) == 100.0 and firm.money == 900.0)
firm = Party("firm:2", 150.0)
two_seats = {"alpha": seat(["loom"], [], {"firm:2": {"royalty": 0.1}}), "beta": seat(["loom"], [], {"firm:2": {"royalty": 0.25}})}
view, seat_parties = view_over(two_seats, [])
paid = DisclosureView.collect_royalty(view, firm, "loom", 1000.0)
check("collect_royalty: a firm short of money pays the seats only what its purse holds and never goes below zero",
      paid == 150.0 and seat_parties["alpha"].money == 100.0 and seat_parties["beta"].money == 50.0 and firm.money == 0.0,
      (paid, seat_parties["alpha"].money, seat_parties["beta"].money, firm.money))
