"""Bridge entries the ledger reads until the founder's purse and tonnes ledger move into its own state."""
from .bridge import bridge_view
from sim.assembly.api import KEYED


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
	return sim._material_stock()


@bridge_view("legacy_opening_stock", seat_scoped=True)
def opening_stock(sim):
	return sim._material_opening_stock()
