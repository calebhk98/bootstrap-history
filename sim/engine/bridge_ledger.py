"""Bridge entries the ledger reads until the founder's purse and tonnes ledger move into its own state."""
from .bridge import bridge_view
from sim.assembly.api import KEYED
from sim.ledger.api import rules as ledger_rules


@bridge_view("legacy_acting_household", seat_scoped=True)
def acting_household(sim):
	return sim.state.household


@bridge_view("legacy_edge_account", kind=KEYED)
def edge_account(sim, name):
	return sim.edge(name)


@bridge_view("legacy_actor_registry")
def actor_registry(sim):
	return sim.actors


@bridge_view("legacy_stock_ledger", seat_scoped=True)
def stock_ledger(sim):
	"""The seat's tonnes ledger, made on first use, with the capacity keys swept into the economy's capacity pool."""
	holdings = sim.state.holdings
	holdings._material_stock_ledger = ledger_rules.settled_stock(holdings._material_stock_ledger,
	                                                              sim.state.economy.capacity_pool)
	return holdings._material_stock_ledger


@bridge_view("legacy_opening_stock", seat_scoped=True)
def opening_stock(sim):
	"""The tonnes as the year's accounting began; the snapshot is taken here if this year has none."""
	holdings = sim.state.holdings
	holdings._material_stock_opening = ledger_rules.year_opening_record(
		holdings._material_stock_opening, sim.state.scenario.year, stock_ledger(sim))
	return holdings._material_stock_opening["tonnes"]


@bridge_view("legacy_opening_record", seat_scoped=True)
def opening_record(sim):
	"""The snapshot of the year's opening stock as the state holds it (None before the first), for reading only."""
	return sim.state.holdings._material_stock_opening
