"""What a partner economy's own society makes, at its own opening technologies (data, frozen for the game).

The foreign-trade module reads these through the bridge (`partner_own_economy`). What its households buy is the markets module's
(`partner_household_demand`, sim/markets/household_views.py)."""
import functools

from .data import calculated_goods_prices, goods_provenance, load_civ, starting_schedule


@functools.lru_cache(maxsize=None)
def foreign_solved_materials(civilization_id):
    """Materials the economy can make with its own technologies; the rest are priced only as if some technology were held."""
    civilization = load_civ(civilization_id)
    provenance = goods_provenance(frozenset(civilization["starting_techs"]), civilization_id=civilization_id)
    return frozenset(material for material, source in provenance.items() if source == "solved")


@functools.lru_cache(maxsize=None)
def foreign_prices_in_own_coin(civilization_id):
    """{material: price in the economy's own coin} under its own opening technologies (frozen for the game)."""
    civilization = load_civ(civilization_id)
    return calculated_goods_prices(
        frozenset(civilization["starting_techs"]), civilization_id=civilization_id,
        money_per_labour_hour=starting_schedule(civilization_id).money_per_labour_hour)
