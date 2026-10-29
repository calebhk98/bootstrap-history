"""Bridge entries the markets module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine as the old mixin code did,
and is never cached."""
from sim.agents.api import relations
from sim.assembly.api import QUOTE
from sim.markets.api import RepriceOpeningMoney

from . import opening_money
from sim.content import api as content
from .bridge import bridge_command, bridge_view
from .data import MODDIR, ROOT, calculated_goods_table
from sim.content.api import get_ordered_mods


# ---- core: facts of the game the module cannot read from an owner yet ----

@bridge_view("opening_farmed_hectares")
def opening_farmed_hectares(sim):
    """The area the opening's farm cleared (an initial condition)."""
    return sim._opening_farmed_hectares


@bridge_view("installed_mod_ids")
def installed_mod_ids(sim):
    """The ids of the installed mods in load order: what the content the household need model is built from depends on."""
    return tuple(manifest.id for manifest in get_ordered_mods(MODDIR))


@bridge_view("household_need_data")
def household_need_data(sim):
    """{"needs", "goods"}: the needs households spend on and the goods that serve them, from the base file and each mod's."""
    return content.load_needs(ROOT)


# ---- prices ----

@bridge_view("calculated_goods_prices", kind=QUOTE)
def calculated_goods_prices(sim, held, farmed_hectares):
    """{material: labour-hour price} of every material the solver prices when `held` techniques are known and
    `farmed_hectares` are farmed (banded), from one solve."""
    from sim.prices.api import prices as price_solver
    in_hours, _basis = calculated_goods_table(
        held, civilization_id=sim.civ.get("id"), civilization=sim.civ,
        farmed_hectares=price_solver.band_farmed_hectares(farmed_hectares))
    return in_hours


# ---- the need data and the relations store ----

@bridge_view("border_terms", kind=QUOTE)
def border_terms(sim, destination, source):
    """(tariff share, embargoed) that the state of `destination` holds toward goods crossing from `source`, read from the
    relations store."""
    return relations.tariff_on(sim.stores, destination, source), relations.embargoes(sim.stores, destination, source)


# ---- commands: the opening's money ----

@bridge_command(RepriceOpeningMoney)
def reprice_opening_money(sim, command):
    """Every seat's purse and the tree's money fields move to the money an hour of work is worth at the economy."""
    opening_money.reprice_opening_money(sim, command.before)


# ---- the module's own objects, for engine code that still reaches them through the game ----

@bridge_view("legacy_economy")
def legacy_economy(sim):
    """The port over the agent economy (the markets module's `economy`)."""
    return sim.assembly.modules["markets"].economy


@bridge_view("legacy_goods_market")
def legacy_goods_market(sim):
    """The one goods market every buyer and seller asks (the markets module's `goods_market`)."""
    return sim.assembly.modules["markets"].goods_market
