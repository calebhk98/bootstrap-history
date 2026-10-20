"""The herds the society holds at its opening are the head its herd producers keep.

A recipe that is a herd's yearly turn states `herd_stock` ({stock material: units one run keeps}). The agent
economy's opening sizes its producers to the opening's demand; the ledger's living stock starts as those runs times
what a run keeps, held to the pasture the held tiles carry. One figure, not two: nothing here names a species.
"""
from sim.labour.api import production_data

from .living_stock_growth import kilograms_per_unit
from .living_stock_yearly import stock_rates


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

    def endemic_keeping(self, material):
        """0 to 1: the share of an opening herd that can be kept where it stands. Disease at the place takes
        a share of the herd every year, and the herd holds only if breeding outruns that loss."""
        rates = stock_rates().get(material) or {}
        loss = self.endemic_stock_loss(rates)
        return 1.0 if loss <= 0.0 else max(0.0, 1.0 - loss / rates["natural_increase"])

    def grant_opening_herds(self):
        """Credit the opening herds to the ledger, scaled down together if the held tiles' pasture cannot carry them."""
        kept = self.opening_herd_units()
        carried = self.geography.held_pasture_kg(self.state.economy.wild_stock)
        weight = sum(units * kilograms_per_unit(material) for material, units in kept.items())
        scale = min(1.0, carried / weight) if weight > 0.0 else 1.0
        for material, units in sorted(kept.items()):
            units *= scale * self.endemic_keeping(material)
            self.grant_stock(material, units)
            self.society_herds[material] = units
