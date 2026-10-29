"""Bridge entries the finance module reads until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached: legacy code
writes the state behind it directly. When the owner moves it publishes the same name and the entry is deleted."""

from . import cash_remedies
from .bridge import bridge_view


# ---- production and workforce ----

@bridge_view("cash_remedies", seat_scoped=True)
def remedies(sim):
	"""Lines naming the commands that raise cash or cut costs, largest amount first."""
	return cash_remedies.cash_remedies(sim)
