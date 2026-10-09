"""Freight between this society and another economy: the cheapest route over
the map's tiles (`sim.geography.api.route`), each leg by a mode both economies can use.

Mode costs come from the physical models (`sim/geography/transport.py` for cart,
pack string and towed barge; `sim/geography/sea_freight.py` for a sailing hull),
priced with this society's feed price, wages, carrier prices and market rate,
with the empty return where flows are one-sided (`sim/geography/freight_cost.py`).
The legs of the chosen route are kept, with their travel days, so a player can
see where goods travel.
"""
import dataclasses
import functools
from dataclasses import dataclass
from typing import Tuple

from sim.constants import declare
from sim.world import trader_response
from sim.geography.api import cargo_cost, freight_cost, provisions, sea_freight, tiles_held
from sim.geography.api import route as route_over_tiles
from sim.geography.api import dues_hours_per_tonne
from sim.geography.api import usable_modes as usable_route_modes
from sim.geography.api import transport as freight_physics

from .data import load_civ

CARAVAN_STRING_SIZE = declare(
    "CARAVAN_STRING_SIZE", 10.0, kind="engineering_estimate",
    unit="pack mules per handler",
    source="Pack trains in the ancient and medieval world went in strings "
           "of a few to a few dozen animals under a small crew.",
    confidence="C",
    why="One handler's day is spread over the string's cargo, which sets "
        "the driver hours per tonne-km of a caravan.")

SEA_CREW_WAGE_TRADE = "sailor"
SEA_MODE = "sail"
# Vehicles and hulls are priced as their timber (their iron fittings are left out).
FREIGHT_VEHICLE_MATERIAL = "wood_kg"


@dataclass(frozen=True)
class Leg:
    origin: str
    destination: str
    mode: str
    distance_km: float
    cost_per_tonne: float
    travel_days: float = 0.0


@dataclass(frozen=True)
class Route:
    """A haul over tiles: legs in order from the partner's tiles to this society's."""
    legs: Tuple[Leg, ...]

    @property
    def cost_per_tonne(self):
        return sum(leg.cost_per_tonne for leg in self.legs)

    @property
    def distance_km(self):
        return sum(leg.distance_km for leg in self.legs)

    @property
    def travel_days(self):
        return sum(leg.travel_days for leg in self.legs)

    def describe(self):
        return " > ".join("%s -%s-> %s" % (leg.origin, leg.mode, leg.destination) for leg in self.legs)


def route_from_geography(found):
    """A `Route` from the geography contract's answer (its handling days count as travel)."""
    return Route(tuple(
        Leg(leg["from"], leg["to"], leg["mode"], leg["km"], leg["cost_per_tonne"],
            leg["days"] + leg.get("handling_days", 0.0))
        for leg in found["legs"]))


@functools.lru_cache(maxsize=None)
def _river_inputs():
    return freight_physics.barge_freight_physical_inputs(
        freight_physics.OX, 2, freight_physics.BARGE)


@functools.lru_cache(maxsize=None)
def _paved_road_inputs(team_size):
    return freight_physics.draught_freight_physical_inputs(
        freight_physics.OX, team_size, freight_physics.CART, freight_physics.PAVED_ROAD)


@functools.lru_cache(maxsize=None)
def _caravan_inputs():
    return freight_physics.pack_freight_physical_inputs(
        freight_physics.MULE, int(CARAVAN_STRING_SIZE))


class ForeignRoutesMixin:

    def _carrier_models(self):
        """{mode: (physical inputs, carrier prices, working days a year, hull loss per 1000 km)}:
        the carrier unit each mode's inputs describe, priced from this society's prices."""
        vehicle_wood = self._material_price_per_kg(FREIGHT_VEHICLE_MATERIAL) or 0.0
        ox_price = self._material_prices().get("ox", 0.0)
        mule_price = self._material_prices().get("mule", 0.0)
        team = float(self.LAND_FREIGHT_TEAM_SIZE)
        string = int(CARAVAN_STRING_SIZE)
        land_days = freight_cost.LAND_WORKING_DAYS_PER_YEAR
        hull_inputs = sea_freight.sailing_freight_physical_inputs()
        hull_kg = hull_inputs.cargo_tonnes * sea_freight.HULL_TIMBER_KG_PER_CARGO_TONNE
        return {
            "cart": (self._land_freight_physical_inputs(),
                     freight_cost.CarrierPrices(freight_physics.CART.self_mass_kg * vehicle_wood,
                                                team * ox_price), land_days, 0.0),
            "road": (_paved_road_inputs(int(self.LAND_FREIGHT_TEAM_SIZE)),
                     freight_cost.CarrierPrices(freight_physics.CART.self_mass_kg * vehicle_wood,
                                                team * ox_price), land_days, 0.0),
            "pack": (_caravan_inputs(),
                        freight_cost.CarrierPrices(
                            string * freight_physics.PACK_SADDLE.self_mass_kg * vehicle_wood,
                            string * mule_price), land_days, 0.0),
            "river_boat": (_river_inputs(),
                      freight_cost.CarrierPrices(freight_physics.BARGE.self_mass_kg * vehicle_wood,
                                                 2.0 * ox_price), land_days, 0.0),
            SEA_MODE: (hull_inputs, freight_cost.CarrierPrices(hull_kg * vehicle_wood),
                    sea_freight.SAILING_DAYS_PER_YEAR, sea_freight.hull_loss_per_thousand_km())}

    def _freight_mode_costs(self, imbalance=1.0, modes=None):
        """{mode: home money per tonne-km}: feed and crew, the carrier's capital at the market
        rate, hull losses, and the return leg (`imbalance` 0 when flows balance, 1 when the
        carrier comes back empty). The same function prices foreign legs and domestic hauls."""
        feed_price = self._material_price_per_kg(self.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        land_wage = self.labour.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE)
        sea_wage = self.labour.wage_per_hour(SEA_CREW_WAGE_TRADE)
        rate = self.market_rate()
        return {mode: freight_cost.freight_money_per_tonne_km(
                    inputs, feed_price, sea_wage if mode == SEA_MODE else land_wage, prices, rate,
                    working_days, imbalance, loss)
                for mode, (inputs, prices, working_days, loss) in self._carrier_models().items()
                if modes is None or mode in modes}

    def land_freight_money_per_tonne_km(self, imbalance=1.0):
        """Home money per tonne-km for a domestic cart haul: the foreign routes' freight function,
        with the carrier's capital at the market rate and the empty return. A domestic haul of a
        material has no flow ledger back, so by default (heuristic, `imbalance` 1) the cart returns
        empty."""
        return self._freight_mode_costs(imbalance, ("cart",))["cart"]

    def domestic_cargo_cost_share(self, material, distance_km):
        """The cargo's own cost over a domestic cart haul as a share of its price: interest at the
        market rate while it travels, and what is lost to spoilage in that time. No merchant margin
        (domestic carriers' margins are not modelled)."""
        years = freight_cost.days_on_leg(distance_km, self._land_freight_physical_inputs()) / 365.0
        spoilage = cargo_cost.spoilage_share(cargo_cost.spoilage_rates().get(material, 0.0), years)
        return trader_response.cost_share_of_price(
            0.0, cargo_cost.lost_share(spoilage), self.market_rate(), years)

    def _foreign_flow_imbalance(self, civilization_id):
        """How one-sided last year's trade with a partner was, from its book: 1 when nothing
        flowed back (or nothing is known), 0 when tonnes in and out match."""
        entries = self.state.economy.foreign_market_book.get(civilization_id, {}).values()
        tonnes_out = sum(max(0.0, entry.get("trade_tonnes", 0.0)) for entry in entries)
        tonnes_in = sum(max(0.0, -entry.get("trade_tonnes", 0.0)) for entry in entries)
        return freight_cost.imbalance_of_flows(tonnes_out, tonnes_in)

    def _freight_handling_costs(self):
        """{mode: home money per tonne} charged once per leg of that mode: port handling at sea, and
        the tolls or port dues the geography states for each mode (paid at the carrier's wage)."""
        wage = self.labour.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE)
        costs = {mode: hours * wage for mode, hours in dues_hours_per_tonne(self.world_map).items() if hours > 0.0}
        costs[SEA_MODE] = costs.get(SEA_MODE, 0.0) + sea_freight.PORT_HANDLING_HOURS_PER_TONNE * wage
        return costs

    def _foreign_route(self, civilization, imbalance=None):
        """The cheapest `Route` from the foreign economy's home tiles to this society's, or None
        when no mode both can use joins them. `imbalance` is how one-sided the flows are
        (last year's, by default)."""
        civilization_record = civilization if isinstance(civilization, dict) else load_civ(civilization)
        foreign_techs = frozenset(civilization_record.get("starting_techs") or ())
        home_techs = frozenset(self.state.projects.done)
        if imbalance is None:
            imbalance = self._foreign_flow_imbalance(civilization_record.get("id"))
        mode_costs = self._freight_mode_costs(imbalance)
        modes = [mode for mode in usable_route_modes((home_techs, foreign_techs), self.world_map)
                 if mode in mode_costs]
        found = route_over_tiles(
            tiles_held(civilization_record, self.world_map),
            tiles_held(self.civ, self.world_map), modes,
            mode_costs=mode_costs, handling_costs=self._freight_handling_costs(),
            held_nodes=home_techs | foreign_techs, world_map=self.world_map)
        return None if found is None else self._with_carried_provisions(route_from_geography(found))

    def _with_carried_provisions(self, route):
        """The route with each leg priced per tonne delivered: the crew's and animals' food and water
        ride on the carrier and take lift from the cargo (`provisions.delivered_share`), the carrier
        restocking at each leg's end. The route was chosen on the per-km rates; handling is not
        scaled; the share is floored at what the cargo-loss cap leaves."""
        models = self._carrier_models()
        handling = self._freight_handling_costs()
        least_share = 1.0 - cargo_cost.MAX_LOST_SHARE
        legs = []
        for leg in route.legs:
            if leg.mode not in models:
                legs.append(leg)
                continue
            fee = handling.get(leg.mode, 0.0)
            share = max(least_share, provisions.delivered_share(models[leg.mode][0], leg.distance_km))
            legs.append(dataclasses.replace(leg, cost_per_tonne=fee + max(0.0, leg.cost_per_tonne - fee) / share))
        return Route(tuple(legs))

    def _route_freight_per_tonne(self, civilization, imbalance=None):
        """Home money to haul a tonne over the cheapest route; infinite when
        no route joins the two."""
        route = self._foreign_route(civilization, imbalance)
        return float("inf") if route is None else route.cost_per_tonne
