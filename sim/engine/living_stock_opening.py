"""The herds the society holds at its opening are the head its herd producers keep.

A recipe that is a herd's yearly turn states `herd_stock` ({stock material: units one run keeps}). The agent
economy's opening sizes its producers to the opening's demand; the ledger's living stock starts as those runs times
what a run keeps, held to the pasture the held tiles carry. One figure, not two: nothing here names a species.
"""
from sim.labour.api import production_data

from .living_stock_growth import kilograms_per_unit
from .living_stock_yearly import stock_rates
from .opening_herd_rules import herd_units_kept, opening_herds


class LivingStockOpeningMixin:

    @property
    def society_herds(self):
        """{stock material: units} of the held herd that belongs to the society's producers, not the founder."""
        return self.state.economy.society_herds

    def opening_herd_units(self):
        """{stock material: units} the herd producers keep, before the pasture holds it down."""
        return herd_units_kept(self.economy.producer_capacities(), production_data())

    def endemic_keeping(self, material):
        """0 to 1: the share of an opening herd that can be kept where it stands. Disease at the place takes
        a share of the herd every year, and the herd holds only if breeding outruns that loss."""
        rates = stock_rates().get(material) or {}
        loss = self.endemic_stock_loss(rates)
        return 1.0 if loss <= 0.0 else max(0.0, 1.0 - loss / rates["natural_increase"])

    def grant_opening_herds(self):
        """Credit the opening herds to the ledger, scaled down together if the held tiles' pasture cannot carry them."""
        herds = opening_herds(self.opening_herd_units(), self.geography.held_pasture_kg(self.state.economy.wild_stock),
                              kilograms_per_unit, self.endemic_keeping)
        for material, units in herds.items():
            self.grant_stock(material, units)
            self.society_herds[material] = units
