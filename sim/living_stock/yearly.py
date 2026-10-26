"""The year's turn of held living stock: breeding and loss by the rates in data/world/living_stock.json, growth held to
the land at the stock's place and paid for in labour. A held lot stands on one tile, the holder's: the held tile
nearest the middle of what the holder holds. A row whose data says `grows_on` "pasture" is fed from that tile's grass
less the live weight already grazing; one that says "arable" is raised in a nursery on the tile's arable land at the
output per hectare its production entry gives. Growth the land cannot hold or the purse cannot pay is not made."""
from sim.agents.api import edges
from sim.ledger.api import PayEdge
from sim.workforce.api import PressLabour

from . import rules
from .data import kilograms_per_unit, stock_entry, stock_rates
from .holding import HERDS

GROWS_ON_PASTURE = "pasture"
GROWS_ON_ARABLE = "arable"


class Yearly:
    """The phase `living_stock` (needs: stock_land, endemic_stock_loss, nursery_room_units, hour_wage, can_pay,
    acting_balance; sends PayEdge, PressLabour)."""

    def nursery_room_units(self, material, place):
        """Units of the material the place's arable land can raise in a year at its production entry's output per
        hectare; None where nothing limits it (no place, or an entry that works no land)."""
        entry = stock_entry(material)
        if entry is None:
            return None
        return self.needs.nursery_room_units(
            place, entry["outputs"][material], float(entry.get("land_hectare_years") or 0.0))

    def pay_growth_labour(self, material, units):
        """Hire the labour of raising `units` more and pay it; the share of the growth the purse could pay for
        (1 when all of it)."""
        hours_by_trade = rules.growth_labour(stock_entry(material), material, units)
        cost = sum(hours * self.needs.hour_wage[trade] for trade, hours in hours_by_trade.items())
        if cost <= 0.0:
            return 1.0
        share = 1.0 if self.needs.can_pay(cost) else min(1.0, max(0.0, self.needs.acting_balance()) / cost)
        if share <= 0.0:
            return 0.0
        for trade, hours in hours_by_trade.items():
            self.needs.send(PressLabour(trade, hours * share))
        self.needs.send(PayEdge(edges.EDGE_MARKET, cost * share, "stock raised"))
        return share

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
                lambda billed, material=material: self.pay_growth_labour(material, billed))
            if rates.get("grows_on") == GROWS_ON_PASTURE and pasture_room is not None:
                pasture_room = max(0.0, pasture_room - grown * kilograms_per_unit(material))
            if material in society_herds:
                society_herds[material] = rules.society_herd_after(society_herds[material], held, after)
                self.bump(HERDS)
            self.change(material, after - held)
