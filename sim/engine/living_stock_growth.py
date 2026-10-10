"""What held stock draws on as it grows: the place it stands, the pasture or nursery land there, the labour.

A held lot stands on one tile, the holder's: the held tile nearest the middle of what the holder holds. A
row whose data says `grows_on` "pasture" is fed from that tile's grass (geography's pasture capacity, less
the live weight already grazing); one that says "arable" is raised in a nursery on the tile's arable land,
at the output per hectare its production entry gives. The labour of the growth is the labour that entry
states, bought at the going wage. Growth the land cannot hold or the purse cannot pay is not made.
"""
import functools

from sim.geography.api import arable_hectares, pasture_capacity_kg, tile_facts, tiles_held
from sim.labour.api import production_data
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from .material_units import tonnes_per_unit

GROWS_ON_PASTURE = "pasture"
GROWS_ON_ARABLE = "arable"


@functools.lru_cache(maxsize=None)
def _centre_of(tile_ids, world_map):
    """The tile of `tile_ids` nearest their mean position, or None for none."""
    if not tile_ids:
        return None
    facts = [tile_facts(tile_id, world_map) for tile_id in tile_ids]
    mean_lat = sum(fact["lat"] for fact in facts) / len(facts)
    mean_lon = sum(fact["lon"] for fact in facts) / len(facts)
    return min(facts, key=lambda fact: ((fact["lat"] - mean_lat) ** 2 + (fact["lon"] - mean_lon) ** 2,
                                        fact["id"]))["id"]


@functools.lru_cache(maxsize=None)
def stock_entry(material):
    """The production entry that makes a stock material, which states the labour and land of raising more
    of it, or None when the data has no such entry."""
    for _key, entry in sorted(production_data().items()):
        if (entry.get("outputs") or {}).get(material, 0.0) > 0.0:
            return entry
    return None


def kilograms_per_unit(material):
    return tonnes_per_unit(material) * KILOGRAMS_PER_TONNE


class LivingStockGrowthMixin:

    def stock_place(self):
        """The tile the held stock stands on: the holder's seat, taken as the held tile nearest the middle of
        the holding (the ledger has one holder, so one place). None for a holder with no tiles."""
        return _centre_of(tuple(sorted(tiles_held(self.civ, self.world_map))), self.world_map)

    def pasture_room_kg(self, place, pastured_materials):
        """Live weight more that the place's grass keeps beside what already grazes there; None where the
        stock has no place."""
        if place is None:
            return None
        grazing = sum(self.stock_held(material) * kilograms_per_unit(material) for material in pastured_materials)
        return max(0.0, pasture_capacity_kg(place, self.state.economy.wild_stock, self.world_map) - grazing)

    def nursery_room_units(self, material, place):
        """Units of the material the place's arable land can raise in a year at its production entry's output
        per hectare; None where nothing limits it (no place, or an entry that works no land)."""
        entry = stock_entry(material)
        if place is None or entry is None or float(entry.get("land_hectare_years") or 0.0) <= 0.0:
            return None
        return arable_hectares(place, self.world_map) * entry["outputs"][material] / entry["land_hectare_years"]

    def growth_labour(self, material, units):
        """{trade: hours} the labour of raising `units` more of the material, from its production entry."""
        entry = stock_entry(material)
        if entry is None or units <= 0.0:
            return {}
        batches = units / entry["outputs"][material]
        return {trade: hours * batches for trade, hours in sorted((entry.get("labour_hours") or {}).items())}

    def pay_growth_labour(self, material, units):
        """Hire the labour of raising `units` more and pay it; the share of the growth the purse could pay for
        (1 when all of it)."""
        hours_by_trade = self.growth_labour(material, units)
        market = self.labour.market
        cost = sum(hours * market.quote(trade) for trade, hours in hours_by_trade.items())
        if cost <= 0.0:
            return 1.0
        acting = self.goods_market.acting
        share = 1.0 if acting.can_pay(cost) else min(1.0, max(0.0, self.capital) / cost)
        if share <= 0.0:
            return 0.0
        for trade, hours in hours_by_trade.items():
            market.press(trade, hours * share)
        acting.pay(cost * share, "stock raised")
        return share
