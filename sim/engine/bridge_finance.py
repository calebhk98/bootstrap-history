"""Bridge entries the finance module reads until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached: legacy code
writes the state behind it directly. When the owner moves it publishes the same name and the entry is deleted."""
from sim.assembly.api import QUOTE

from . import cash_remedies
from .bridge import bridge_view


# ---- markets: the agent economy's credit market and the economy itself ----

@bridge_view("agent_rate")
def agent_rate(sim):
	"""The agent economy's loanable-funds rate, or None while it opens."""
	return sim.economy.agent_rate()


@bridge_view("agent_credit_room", kind=QUOTE)
def agent_credit_room(sim, borrower_id):
	"""(True, room) when the agent economy answers, with room None before lenders have met; (False, None) while it opens."""
	return sim.economy.agent_credit_room(borrower_id)


@bridge_view("agent_economy_opened")
def agent_economy_opened(sim):
	return sim.economy.agent.opened()


@bridge_view("agent_economy")
def agent_economy(sim):
	"""The agent economy itself (its record, its setup): a bank founded from outside goes into it."""
	return sim.economy.agent.economy()


# ---- production and workforce ----

@bridge_view("wage_bill", seat_scoped=True)
def wage_bill(sim):
	return sim.labour.wage_bill()


@bridge_view("cash_remedies", seat_scoped=True)
def remedies(sim):
	"""Lines naming the commands that raise cash or cut costs, largest amount first."""
	return cash_remedies.cash_remedies(sim)
