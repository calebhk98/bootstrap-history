"""The year's turn of held living stock: breeding and loss by the rates in data/world/living_stock.json, growth held to
the land at the stock's place and hired in the labour core. A held lot stands on one tile, the holder's: the held tile
nearest the middle of what the holder holds. A row whose data says `grows_on` "pasture" is fed from that tile's grass
less the live weight already grazing; one that says "arable" is raised in a nursery on the tile's arable land at the
output per hectare its production entry gives. Growth the land cannot hold or the labour hired does not cover is not made; the labour a year's growth takes is
posted for the next clearing."""
from sim.workforce.api import ONCE_STOCK, PostHoursOnce

from . import rules
from .data import kilograms_per_unit, stock_entry, stock_rates
from .holding import HERDS

GROWS_ON_PASTURE = "pasture"
GROWS_ON_ARABLE = "arable"


class Yearly:
    """The phase `living_stock` (needs: stock_land, endemic_stock_loss, nursery_room_units, hours_hired_once;
    sends PostHoursOnce)."""

    def nursery_room_units(self, material, place):
        """Units of the material the place's arable land can raise in a year at its production entry's output per
        hectare; None where nothing limits it (no place, or an entry that works no land)."""
        entry = stock_entry(material)
        if entry is None:
            return None
        return self.needs.nursery_room_units(
            place, entry["outputs"][material], float(entry.get("land_hectare_years") or 0.0))

    def hire_growth_labour(self, material, units, hired, wanted):
        """The share of raising `units` more of stock that the hours hired at the last clearing cover (1 when all of
        it). The labour it takes is added to `wanted`, which the year's step posts to the labour core."""
        hours_by_trade = rules.growth_labour(stock_entry(material), material, units)
        for trade, hours in hours_by_trade.items():
            wanted[trade] = wanted.get(trade, 0.0) + hours
        return rules.hired_share(hours_by_trade, hired)

    def step_living_stock(self, seat_id):
        """Breed and lose each held stock for a year. Expected values, no dice, so a save and load cannot change a
        herd."""
        rates_by_material = stock_rates()
        land = self.needs.stock_land()
        place = land["place"]
        pastured = [material for material, rates in sorted(rates_by_material.items())
                    if rates.get("grows_on") == GROWS_ON_PASTURE]
        grazing = sum(self.held(material) * kilograms_per_unit(material) for material in pastured)
        pasture_room = rules.pasture_room_kg(place, land["pasture_kg"], grazing)
        society_herds = self.world.society_herds
        hired, wanted = dict(self.needs.hours_hired_once(ONCE_STOCK)), {}
        for material, rates in sorted(rates_by_material.items()):
            held = self.held(material)
            if held <= 0.0:
                continue
            room = None
            loss = rates["annual_loss"] + self.needs.endemic_stock_loss(place, rates.get("species"))
            if rates.get("grows_on") == GROWS_ON_PASTURE and pasture_room is not None:
                room = pasture_room / kilograms_per_unit(material)
            elif rates.get("grows_on") == GROWS_ON_ARABLE:
                room = self.nursery_room_units(material, place)
            after, grown = rules.material_year(
                held, rates, room, loss, society_herds.get(material, 0.0),
                lambda billed, material=material: self.hire_growth_labour(material, billed, hired, wanted))
            if rates.get("grows_on") == GROWS_ON_PASTURE and pasture_room is not None:
                pasture_room = max(0.0, pasture_room - grown * kilograms_per_unit(material))
            if material in society_herds:
                society_herds[material] = rules.society_herd_after(society_herds[material], held, after)
                self.bump(HERDS)
            self.change(material, after - held)
        for trade, hours in sorted(wanted.items()):
            self.needs.send(PostHoursOnce(ONCE_STOCK, trade, hours))
