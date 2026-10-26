"""Bridge entries the prices module reads until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached."""
from sim.assembly.api import KEYED

from .bridge import bridge_view


@bridge_view("farm_land_hectares")
def farm_land_hectares(sim):
    """The hectares the society's farm workforce works (the area the farmland model is sized for)."""
    return sim.farm_land.hectares


@bridge_view("material_seller", kind=KEYED)
def material_seller(sim, material):
    """Who sells a material to the home society: the home society's own id, a trading partner, or None when no one does."""
    return sim.goods_market.offered_by(material)


@bridge_view("agent_wage", kind=KEYED)
def agent_wage(sim, trade):
    """The wage in the acting seat's own labour markets, or None while the agent economy opens."""
    return sim.economy.agent_wage_per_hour(trade)


@bridge_view("agent_land_rent")
def agent_land_rent(sim):
    """Mean rent per hectare-year of the agent economy's land market, in coin; None while it opens."""
    return sim.economy.agent_land_rent_per_hectare()


@bridge_view("concern_baskets_now", kind=KEYED)
def concern_baskets_now(sim, node_id):
    """What a concern makes and buys in a year with the techniques held now; None for a node whose revenue is not derived
    from output."""
    return sim.concern_baskets_now(node_id)


@bridge_view("venture_ramp", kind=KEYED)
def venture_ramp(sim, node_id):
    """How much of its full takings a concern is making, 0..1."""
    return sim.venture_ramp(node_id)
