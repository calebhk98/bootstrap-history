"""Bridge entries the foreign-trade module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine as the old mixin code did, and
is never cached. `legacy_agent_economy` is the agent economy's record, where the traders' cargo legs are kept; it goes when the
markets module owns that record."""
from sim.assembly.api import KEYED, QUOTE

from . import foreign_economy_data, partner_demand
from .bridge import bridge_view
from .data import load_civ, starting_schedule


# ---- the partners' files and opening economies ----

@bridge_view("foreign_economy_records")
def foreign_economy_records(sim):
    """The economies the data file names, with installed mods applied (the module function is looked up on each call)."""
    return foreign_economy_data.foreign_economy_records()


@bridge_view("civilisation_record", kind=KEYED)
def civilisation_record(sim, civilization_id):
    """The civilisation `civilization_id` as its file gives it (mods applied, checked)."""
    return load_civ(civilization_id)


@bridge_view("partner_own_economy", kind=KEYED)
def partner_own_economy(sim, civilization_id):
    """What a civilisation makes and charges at its own opening technologies, frozen for the game: {solved_materials, the
    prices in its own coin, money_per_labour_hour}."""
    return {"solved_materials": partner_demand.foreign_solved_materials(civilization_id),
            "prices_in_own_coin": partner_demand.foreign_prices_in_own_coin(civilization_id),
            "money_per_labour_hour": starting_schedule(civilization_id).money_per_labour_hour}


@bridge_view("partner_household_demand", kind=KEYED)
def partner_household_demand(sim, civilization_id):
    """{material: tonnes a year} a civilisation's households buy at its own solved prices."""
    return partner_demand.household_tonnes_by_material(civilization_id)


# ---- the home market ----

@bridge_view("home_unit_price", kind=KEYED)
def home_unit_price(sim, material):
    """Money per unit the home society's sellers ask for a material (or a curated commodity, by the material it is priced as);
    None when no home seller offers it."""
    return sim.goods_market.home_unit_price(material)


@bridge_view("market_floor_ratio", kind=KEYED)
def market_floor_ratio(sim, commodity):
    """The lowest price over the incumbents' cost their producers sell a commodity at."""
    return sim._floor_ratio(commodity)


# ---- the map ----


# ---- knowledge and the cast ----

@bridge_view("partner_reached", kind=QUOTE)
def partner_reached(sim, civilization_id):
    """Whether trade with a partner can begin: no action returns it, or the acting seat holds the one that does."""
    return sim.partner_gate_refusal(civilization_id) is None


@bridge_view("legacy_agent_economy")
def legacy_agent_economy(sim):
    return sim.state.economy.agent_economy


