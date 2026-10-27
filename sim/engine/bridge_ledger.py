"""Bridge entries the ledger reads until the founder's purse moves into its own state."""
from .bridge import bridge_view


@bridge_view("legacy_acting_household", seat_scoped=True)
def acting_household(sim):
	return sim.state.household
