"""Bridge entries the production module reads until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached."""
from sim.assembly.api import QUOTE

from .bridge import bridge_view
from .data import calculated_goods_prices


@bridge_view("held_goods_prices_in_hours", kind=QUOTE)
def held_goods_prices_in_hours(sim, held):
	"""{material: labour-hour price} of every material the solver prices when the techniques `held` are known, at the
	farming the civilisation opens with (one solve per set)."""
	return calculated_goods_prices(held, civilization_id=sim.civ.get("id"), civilization=sim.civ, money_per_labour_hour=1.0)
