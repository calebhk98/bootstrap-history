"""The herds the society holds at its opening are the head its herd producers keep.

A recipe that is a herd's yearly turn states `herd_stock` ({stock material: units one run keeps}). The agent
economy's opening sizes its producers to the opening's demand; the ledger's living stock starts as those runs times
what a run keeps, held to the pasture the held tiles carry. One figure, not two: nothing here names a species.
"""
from sim.geography.api import pasture_capacity_kg, tiles_held
from sim.labour.api import production_data

from .living_stock_growth import kilograms_per_unit


class LivingStockOpeningMixin:

    @property
    def society_herds(self):
        """{stock material: units} of the held herd that belongs to the society's producers, not the founder."""
        return self.state.economy.society_herds

    def opening_herd_units(self):
        """{stock material: units} the herd producers keep, before the pasture holds it down."""
        production = production_data()
        kept = {}
        for recipe_id, capacity_runs in self.economy.producer_capacities():
            for material, units in (production.get(recipe_id, {}).get("herd_stock") or {}).items():
                kept[material] = kept.get(material, 0.0) + capacity_runs * units
        return kept

    def grant_opening_herds(self):
        """Credit the opening herds to the ledger, scaled down together if the held tiles' pasture cannot carry them."""
        kept = self.opening_herd_units()
        carried = sum(pasture_capacity_kg(tile, self.state.economy.wild_stock, self.world_map)
                      for tile in tiles_held(self.civ, self.world_map))
        weight = sum(units * kilograms_per_unit(material) for material, units in kept.items())
        scale = min(1.0, carried / weight) if weight > 0.0 else 1.0
        for material, units in sorted(kept.items()):
            self.grant_stock(material, units * scale)
            self.society_herds[material] = units * scale
