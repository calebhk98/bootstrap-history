"""The year's turn of held living stock: breeding and loss, by the rates in data/world/living_stock.json."""
import functools
import json
import os

from sim.ledger.api import ChangeStock
from sim.world import stock_dynamics

from .data import ROOT
from .living_stock_growth import GROWS_ON_ARABLE, GROWS_ON_PASTURE, LivingStockGrowthMixin, kilograms_per_unit
from .material_units import tonnes_per_unit
from .stock_growth_billing import founder_billed_growth

LIVING_STOCK_PATH = os.path.join(ROOT, "data", "world", "living_stock.json")


@functools.lru_cache(maxsize=None)
def stock_rates():
    """{material: {natural_increase, annual_loss, breeding_minimum_units, basis}} from the data file."""
    with open(LIVING_STOCK_PATH, encoding="utf-8") as handle:
        return json.load(handle)["materials"]


class LivingStockYearlyMixin(LivingStockGrowthMixin):

    def step_living_stock(self):
        """Breed and lose each held stock for a year. Expected values, no dice, so a save and load cannot
        change a herd. Growth is held to the pasture or nursery land at the stock's place and is paid for in
        labour; loss needs neither."""
        rates_by_material = stock_rates()
        place = self.stock_place()
        pastured = [material for material, rates in sorted(rates_by_material.items())
                    if rates.get("grows_on") == GROWS_ON_PASTURE]
        pasture_room = self.pasture_room_kg(place, pastured)
        society_herds = self.society_herds
        for material, rates in sorted(rates_by_material.items()):
            held = self.stock_held(material)
            if held <= 0.0:
                continue
            room = None
            loss = rates["annual_loss"] + self.endemic_stock_loss(rates, place)
            if rates.get("grows_on") == GROWS_ON_PASTURE and pasture_room is not None:
                room = pasture_room / kilograms_per_unit(material)
            elif rates.get("grows_on") == GROWS_ON_ARABLE:
                room = self.nursery_room_units(material, place)
            grown = stock_dynamics.next_units(
                held, rates["natural_increase"], 0.0, rates["breeding_minimum_units"], room) - held
            if grown > 0.0:
                # the society's herd is raised by its producers' recipes; only the founder's own head is billed here
                billed = founder_billed_growth(grown, held, society_herds.get(material, 0.0))
                grown -= billed * (1.0 - self.pay_growth_labour(material, billed))
            after = stock_dynamics.next_units(
                held, rates["natural_increase"], loss, rates["breeding_minimum_units"], grown)
            if rates.get("grows_on") == GROWS_ON_PASTURE and pasture_room is not None:
                pasture_room = max(0.0, pasture_room - grown * kilograms_per_unit(material))
            if material in society_herds:
                society_herds[material] = min(held, society_herds[material]) * after / held
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
        self.send(ChangeStock(self._stock_key(material), float(units) * tonnes_per_unit(material),
                              legacy_snapshot_after_change=True))
