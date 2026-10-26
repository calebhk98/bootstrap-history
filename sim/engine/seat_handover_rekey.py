"""Everything the engine keeps keyed by a seat's id that is not a field of the seat: when a seat is moved to another id
(sim/engine/seat_move.py), the replacement takes its place in each of these stores.

Moved by renaming the leaver's id to the replacement's, so nothing is paid and no total changes: accounts, debts,
claims and goods (sim/agents/purses.py, sim/economy/api.py), the other seats' holdings, the other actors' records, and the
year's market flows. The seats module renames its own stores (offers, shares, licences and disclosures).
"""
from sim.rekey import rekey


def rename_seat_references(sim, from_id: str, to_id: str) -> None:
	"""`from_id` has left `sim.state.seats`; every reference to it elsewhere now names `to_id`."""
	state = sim.state
	if state.actors is not None:
		state.actors.purses.rename_account(from_id, to_id)
		for record in state.actors.records.values():
			rekey(record, from_id, to_id)
	agent_economy = getattr(getattr(sim, "economy", None), "agent", None)
	if agent_economy is not None:
		agent_economy.rename_agent(from_id, to_id)
	if state.economy is not None and state.economy.market_flows:
		rekey(state.economy.market_flows, from_id, to_id)
	for seat in state.seats.values():
		rekey(seat.holdings, from_id, to_id)
	parties = getattr(getattr(sim, "goods_market", None), "forget_seat_party", None)
	if parties is not None:
		parties(from_id)
