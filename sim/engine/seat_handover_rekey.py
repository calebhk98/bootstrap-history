"""Everything keyed by a seat's id that is not a field of the seat: when a seat is handed over, the replacement
takes its place in each of these stores (sim/engine/seat_handover.py).

Moved by renaming the leaver's id to the replacement's, so nothing is paid and no total changes: accounts, debts,
claims and goods (sim/agents/purses.py, sim/economy/api.py), the other seats' offers, shares, licences and
disclosures, the other actors' records, and the year's market flows.
"""
from sim.diffusion.api import RekeyDisclosures
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
	for seat_id, seat in state.seats.items():
		rekey(seat.holdings, from_id, to_id)
		sim.send(RekeyDisclosures(seat_id, from_id, to_id))
		seat.holdings.offers[:] = [offer for offer in seat.holdings.offers if offer.get("from") != offer.get("to")]
	state.seats[to_id].holdings.shares_held.pop(to_id, None)   # a stake in oneself is no stake
	parties = getattr(getattr(sim, "goods_market", None), "forget_seat_party", None)
	if parties is not None:
		parties(from_id)
