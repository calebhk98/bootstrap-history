"""Bridge entries the reporting module reads until the modules that own these facts move.

Each view answers through `Sim` exactly as the old mixin code asked, and is never cached; when its owner moves it
publishes the same name and the entry is deleted."""
from sim.labour import trade_data, wage_provider

from .bridge import bridge_view


# ---- markets: the agent economy and the households' demand ----

@bridge_view("agent_prices")
def agent_prices(sim):
    """{good: the agent economy's price now}, or None while the economy opens."""
    return sim.economy.agent_prices()


@bridge_view("agent_opening_basket")
def agent_opening_basket(sim):
    """(units a year households bought at the opening, their opening prices in labour hours), or None while it opens."""
    return sim.economy.agent_opening_basket()


@bridge_view("agent_volume_baseline")
def agent_volume_baseline(sim):
    """{good: the volume traded in the first year it cleared any}, or None before a year has closed."""
    return sim.economy.agent_volume_baseline()


@bridge_view("agent_traded_volumes")
def agent_traded_volumes(sim):
    """{good: units the home markets traded last year}, or None before a year has closed."""
    return sim.economy.agent_traded_volumes()


@bridge_view("new_goods_units")
def new_goods_units(sim):
    """{material: units a year households want} of goods offered now that the opening did not offer."""
    return sim.household_new_goods_units()


@bridge_view("household_prices")
def household_prices(sim):
    """{material: what a household pays per unit now}."""
    return sim.goods_market.household_prices()


# ---- workforce ----

@bridge_view("wage_materials")
def wage_materials(sim):
    """The materials a wage is set against, in order: the staple, and every trade's tool materials."""
    registry = trade_data.registry_of(sim)
    materials = {wage_provider.staple_material(sim.civ)}
    for trade in registry:
        materials.update(trade_data.tool_basket(registry, trade))
    return sorted(materials)
