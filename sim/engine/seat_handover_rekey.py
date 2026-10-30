"""Everything the engine keeps keyed by a seat's id that is not a field of the seat: when a seat is moved to another id
(sim/engine/seat_move.py), the replacement takes its place in each of these stores.

Moved by renaming the leaver's id to the replacement's, so nothing is paid and no total changes: accounts, debts,
claims and goods (sim/agents/purses.py, sim/economy/api.py), the other seats' holdings, the other actors' records, and the
markets module's books and the year's market flows. The seats module renames its own stores (offers, shares, licences and disclosures).
"""
from sim.markets.api import RenameMarketSeat
from sim.rekey import rekey


def rename_seat_references(sim, from_id: str, to_id: str) -> None:
	"""`from_id` has left `sim.state.seats`; every reference to it elsewhere now names `to_id`."""
	state = sim.state
	if state.actors is not None:
		state.actors.purses.rename_account(from_id, to_id)
		for record in state.actors.records.values():
			rekey(record, from_id, to_id)
	sim.send(RenameMarketSeat(from_id, to_id))      # the markets module: the agent economy's books, the year's flows, the seat's party
	for seat in state.seats.values():
		rekey(seat.holdings, from_id, to_id)
