"""The year's turn of held living stock: breeding and loss, by the rates in data/world/living_stock.json."""
import functools
import json
import os

from sim.world import stock_dynamics

from .data import ROOT
from .material_units import tonnes_per_unit

LIVING_STOCK_PATH = os.path.join(ROOT, "data", "world", "living_stock.json")


@functools.lru_cache(maxsize=None)
def stock_rates():
    """{material: {natural_increase, annual_loss, breeding_minimum_units, basis}} from the data file."""
    with open(LIVING_STOCK_PATH, encoding="utf-8") as handle:
        return json.load(handle)["materials"]


class LivingStockYearlyMixin:

    def step_living_stock(self):
        """Breed and lose each held stock for a year. Expected values, no dice, so a save and load
        cannot change a herd."""
        for material, rates in sorted(stock_rates().items()):
            held = self.stock_held(material)
            if held <= 0.0:
                continue
            after = stock_dynamics.next_units(
                held, rates["natural_increase"], rates["annual_loss"], rates["breeding_minimum_units"])
            self.change_stock(material, after - held)

    def held_living_stock(self):
        """{material: units} of each living stock now held, for the screens."""
        held = {material: round(self.stock_held(material), 3) for material in sorted(stock_rates())}
        return {material: units for material, units in held.items() if units > 0.0}

    def stock_needed_by(self, node_id):
        """[{material, needed, held}] for the stock a node's `holds` names, for rows that list nodes."""
        return [{"material": gate["material"], "needed": gate["needed"], "held": gate["held"]}
                for gate in self.stock_gates(node_id) if not gate["brought_by"]]

    def change_stock(self, material, units):
        """Add (or, negative, take away) units of a held material: the same ledger entries a grant writes."""
        tonnes = float(units) * tonnes_per_unit(material)
        key = self._stock_key(material)
        self._material_stock()[key] += tonnes
        opening = self._material_opening_stock()
        opening[key] = opening.get(key, 0.0) + tonnes
        self.state.household._stock_throttle_sig = None
