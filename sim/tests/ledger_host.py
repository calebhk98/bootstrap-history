"""For a test host that keeps its own stock: `send = apply_to_own_stock` applies a ledger ChangeStock to it with the
ledger's own rule, as the ledger module does in a game. Goes with the hosts when living stock becomes a module."""
from sim.ledger.api import ChangeStock, rules


def apply_to_own_stock(host, command):
	if not isinstance(command, ChangeStock):
		raise TypeError("this host applies only ChangeStock, not %s" % type(command).__name__)
	if command.legacy_snapshot_after_change:
		host._material_stock()[command.commodity] += command.tonnes
		opening = host._material_opening_stock()
		opening[command.commodity] = opening.get(command.commodity, 0.0) + command.tonnes
	else:
		opening = host._material_opening_stock()
		rules.add_tonnes(host._material_stock(), opening, command.commodity, command.tonnes)
	host.state.household._stock_throttle_sig = None
