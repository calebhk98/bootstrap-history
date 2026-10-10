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
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import trader_response
from sim.geography.api import cargo_cost, freight_cost, provisions, sea_freight, tiles_held, train_carrier
from sim.geography.api import route as route_over_tiles
from sim.geography.api import cargo_loss_per_day, droving_carrier, dues_hours_per_tonne, modes_carrying, walking_cargo_modes
from sim.geography.api import usable_modes as usable_route_modes
from sim.geography.api import transport as freight_physics

from . import action_results, foreign_route_choice
from .domestic_haul import DomesticHaulMixin
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
RAIL_MODE = "rail"
CANAL_MODE = "canal"
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


class ForeignRoutesMixin(DomesticHaulMixin):

    def _train_carrier(self):
        """Geography's train as a freight carrier ({inputs, fuel_material, stock_material, stock_kg})."""
        return train_carrier(RAIL_MODE, self.world_map)

    def _carrier_feed_material(self, mode):
        """The material whose price a mode's feed (or fuel) is counted at: coal for a train, the draught
        animals' feed otherwise."""
        train = self._train_carrier() if mode == RAIL_MODE else None
        return train["fuel_material"] if train else self.FREIGHT_FEED_PRICE_MATERIAL

    def _sea_crew(self):
        """Hands a merchant hull sails with: what its rig needs, and the defenders worth their keep
        against the expected loss of the hull and a cargo of the cheapest grain (the grain price
        stands in for the cargo, which a carrier's rate does not name)."""
        hull_inputs = sea_freight.sailing_freight_physical_inputs()
        rig = sea_freight.crew_to_sail(hull_inputs.cargo_tonnes)
        grain_price = self._material_price_per_kg(self.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        hull_value = (hull_inputs.cargo_tonnes * sea_freight.HULL_TIMBER_KG_PER_CARGO_TONNE
                      * (self._material_price_per_kg(FREIGHT_VEHICLE_MATERIAL) or 0.0))
        cargo_value = hull_inputs.cargo_tonnes * KILOGRAMS_PER_TONNE * grain_price
        defender_cost_per_day = (
            sea_freight.CREW_HOURS_AT_SEA_PER_DAY * self.labour.wage_per_hour(SEA_CREW_WAGE_TRADE)
            + provisions.PERSON_GRAIN_RATION_KG_PER_DAY * grain_price)
        return rig + sea_freight.defenders_to_hire(rig, defender_cost_per_day, hull_value + cargo_value)

    def _carrier_models(self):
        """{mode: (physical inputs, carrier prices, working days a year, hull loss per 1000 km)}:
        the carrier unit each mode's inputs describe, priced from this society's prices."""
        vehicle_wood = self._material_price_per_kg(FREIGHT_VEHICLE_MATERIAL) or 0.0
        ox_price = self._material_prices().get("ox", 0.0)
        mule_price = self._material_prices().get("mule", 0.0)
        team = float(self.LAND_FREIGHT_TEAM_SIZE)
        string = int(CARAVAN_STRING_SIZE)
        land_days = freight_cost.LAND_WORKING_DAYS_PER_YEAR
        crew = self._sea_crew()
        hull_inputs = sea_freight.sailing_freight_physical_inputs(crew=crew)
        hull_kg = hull_inputs.cargo_tonnes * sea_freight.HULL_TIMBER_KG_PER_CARGO_TONNE
        train = self._train_carrier()
        stock_price = self._material_price_per_kg(train["stock_material"]) or 0.0
        river_boat = (_river_inputs(), freight_cost.CarrierPrices(freight_physics.BARGE.self_mass_kg * vehicle_wood,
                                                                   2.0 * ox_price), land_days, 0.0)
        walking = {mode: (droving_carrier(mode, self.world_map)["inputs"], freight_cost.CarrierPrices(0.0), land_days, 0.0)
                   for mode in walking_cargo_modes(self.world_map)}
        return {
            **walking,
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
            "river_boat": river_boat,
            CANAL_MODE: river_boat,
            RAIL_MODE: (train["inputs"], freight_cost.CarrierPrices(train["stock_kg"] * stock_price), land_days, 0.0),
            SEA_MODE: (hull_inputs, freight_cost.CarrierPrices(hull_kg * vehicle_wood),
                    sea_freight.SAILING_DAYS_PER_YEAR, sea_freight.hull_loss_per_thousand_km(crew))}

    def _freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
        """{mode: home money per tonne-km}: feed and crew, the carrier's capital at the market
        rate, hull losses, and the return leg (`imbalance` 0 when flows balance, 1 when the
        carrier comes back empty). The same function prices foreign legs and domestic hauls."""
        land_wage = self.labour.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE)
        sea_wage = self.labour.wage_per_hour(SEA_CREW_WAGE_TRADE)
        rate = self.market_rate()
        walking = frozenset(walking_cargo_modes(self.world_map))
        carrying = frozenset(modes_carrying(cargo, self.world_map)) if cargo else frozenset()
        return {mode: freight_cost.freight_money_per_tonne_km(
                    inputs, self._material_price_per_kg(self._carrier_feed_material(mode)) or 0.0, sea_wage if mode == SEA_MODE else land_wage, prices, rate,
                    working_days, imbalance, loss, cargo_walks=mode in walking)
                for mode, (inputs, prices, working_days, loss) in self._carrier_models().items()
                if (modes is None or mode in modes) and (cargo is None or mode in carrying)}

    def land_freight_money_per_tonne_km(self, imbalance=1.0):
        """Home money per tonne-km for a domestic cart haul: the foreign routes' freight function,
        with the carrier's capital at the market rate and the empty return (`imbalance` 1 by default;
        a haul of a material takes it from the domestic flow ledger, `domestic_haul_money_per_tonne`)."""
        return self._freight_mode_costs(imbalance, ("cart",))["cart"]

    def domestic_cargo_cost_share(self, material, distance_km):
        """The cargo's own cost over a domestic haul as a share of its price: interest at the market
        rate while it travels, and what is lost to spoilage in that time (and, for a herd on the
        road, the daily loss the mode states). No merchant margin (domestic carriers' margins are
        not modelled)."""
        mode = self._domestic_haul_mode(self._cargo_class(material))
        years = freight_cost.days_on_leg(distance_km, self._carrier_models()[mode][0]) / 365.0
        spoilage = cargo_cost.spoilage_share(cargo_cost.spoilage_rates().get(material, 0.0), years)
        road = cargo_cost.daily_loss_share(cargo_loss_per_day(self.world_map).get(mode, 0.0), years * 365.0)
        return trader_response.cost_share_of_price(
            0.0, cargo_cost.lost_share(spoilage, road), self.market_rate(), years)

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

    def _foreign_route(self, civilization, imbalance=None, cargo="goods"):
        """The cheapest `Route` from the foreign economy's home tiles to this society's, or None
        when no mode both can use joins them. `imbalance` is how one-sided the flows are
        (last year's, by default). `cargo` is the class of cargo carried ("goods", or "living_stock",
        which walks overland and is shipped over water)."""
        civilization_record = civilization if isinstance(civilization, dict) else load_civ(civilization)
        foreign_techs = action_results.expand(self.nodes, frozenset(civilization_record.get("starting_techs") or ()))
        home_techs = self.held_and_running(include_starting=False)
        if imbalance is None:
            imbalance = self._foreign_flow_imbalance(civilization_record.get("id"))
        mode_costs = self._freight_mode_costs(imbalance)
        modes = [mode for mode in usable_route_modes((home_techs, foreign_techs), self.world_map, cargo)
                 if mode in mode_costs]
        origin_tiles, destination_tiles = tiles_held(civilization_record, self.world_map), tiles_held(self.civ, self.world_map)
        handling = self._freight_handling_costs()

        def search(rates):
            found = route_over_tiles(
                origin_tiles, destination_tiles, modes, mode_costs=rates, handling_costs=handling,
                held_nodes=home_techs | foreign_techs, world_map=self.world_map)
            return None if found is None else self._with_carried_provisions(route_from_geography(found))
        return foreign_route_choice.choose_route(
            search, lambda route: route.cost_per_tonne, mode_costs, self._share_delivered_on)

    def _share_delivered_on(self, mode, route):
        """Share of a mode's lift that arrives as cargo on the legs of `route` in that mode (the mean
        leg; with no route yet, a land carrier's stage and a hull's none): what the route search
        divides the mode's rate by."""
        models = self._carrier_models()
        if mode not in models:
            return 1.0
        restock_days = self._restock_days(mode)
        legs = [leg.distance_km for leg in (route.legs if route else ()) if leg.mode == mode]
        if legs:
            distance = sum(legs) / len(legs)
        else:
            distance = 0.0 if restock_days is None else float("inf")
        return provisions.restocked_share(models[mode][0], distance, restock_days)

    @staticmethod
    def _restock_days(mode):
        """Days of travel between places a mode's carrier restocks; none for a hull at sea."""
        return None if mode == SEA_MODE else provisions.RESTOCK_INTERVAL_DAYS

    def _with_carried_provisions(self, route):
        """The route with each leg priced per tonne delivered: the crew's and animals' food and water
        ride on the carrier and take lift from the cargo (`provisions.restocked_share`), a land carrier
        restocking every few days and a hull at the leg's ends. Handling is not scaled; a stage the
        carrier cannot provision makes the leg impassable."""
        models = self._carrier_models()
        handling = self._freight_handling_costs()
        legs = []
        for leg in route.legs:
            if leg.mode not in models:
                legs.append(leg)
                continue
            fee = handling.get(leg.mode, 0.0)
            share = provisions.restocked_share(models[leg.mode][0], leg.distance_km, self._restock_days(leg.mode))
            legs.append(dataclasses.replace(
                leg, cost_per_tonne=fee + max(0.0, leg.cost_per_tonne - fee) / share if share > 0.0 else float("inf")))
        return Route(tuple(legs))

    def _route_freight_per_tonne(self, civilization, imbalance=None):
        """Home money to haul a tonne over the cheapest route; infinite when
        no route joins the two."""
        route = self._foreign_route(civilization, imbalance)
        return float("inf") if route is None else route.cost_per_tonne
