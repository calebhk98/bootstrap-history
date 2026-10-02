"""Freight between this society and another economy: the cheapest route over
the map's links, each leg by the cheapest mode both economies can use.

Mode costs come from the physical models (`sim/geography/transport.py` for cart,
pack string and towed barge; `sim/geography/sea_freight.py` for a sailing hull),
priced with this society's feed price, wages, carrier prices and market rate,
with the empty return where flows are one-sided (`sim/geography/freight_cost.py`).
The legs of the chosen route are kept, with their travel days, so a player can
see where goods travel.
"""
import functools

from sim.constants import declare
from sim.world import trader_response
from sim.geography import cargo_cost, freight_cost, sea_freight, trade_routes
from sim.geography import transport as freight_physics

from .data import haversine_km, load_civ

CARAVAN_STRING_SIZE = declare(
    "CARAVAN_STRING_SIZE", 10.0, kind="engineering_estimate",
    unit="pack mules per handler",
    source="Pack trains in the ancient and medieval world went in strings "
           "of a few to a few dozen animals under a small crew.",
    confidence="C",
    why="One handler's day is spread over the string's cargo, which sets "
        "the driver hours per tonne-km of a caravan.")

SEA_CREW_WAGE_TRADE = "sailor"
# Vehicles and hulls are priced as their timber (their iron fittings are left out).
FREIGHT_VEHICLE_MATERIAL = "wood_kg"


@functools.lru_cache(maxsize=None)
def _river_inputs():
    return freight_physics.barge_freight_physical_inputs(
        freight_physics.OX, 2, freight_physics.BARGE)


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
            "caravan": (_caravan_inputs(),
                        freight_cost.CarrierPrices(
                            string * freight_physics.PACK_SADDLE.self_mass_kg * vehicle_wood,
                            string * mule_price), land_days, 0.0),
            "river": (_river_inputs(),
                      freight_cost.CarrierPrices(freight_physics.BARGE.self_mass_kg * vehicle_wood,
                                                 2.0 * ox_price), land_days, 0.0),
            "sea": (hull_inputs, freight_cost.CarrierPrices(hull_kg * vehicle_wood),
                    sea_freight.SAILING_DAYS_PER_YEAR, freight_cost.HULL_LOSS_PER_THOUSAND_KM)}

    def _freight_mode_costs(self, imbalance=1.0, modes=None):
        """{mode: home money per tonne-km}: feed and crew, the carrier's capital at the market
        rate, hull losses, and the return leg (`imbalance` 0 when flows balance, 1 when the
        carrier comes back empty). The same function prices foreign legs and domestic hauls."""
        feed_price = self._material_price_per_kg(self.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        land_wage = self.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE)
        sea_wage = self.wage_per_hour(SEA_CREW_WAGE_TRADE)
        rate = self.market_rate()
        return {mode: freight_cost.freight_money_per_tonne_km(
                    inputs, feed_price, sea_wage if mode == "sea" else land_wage, prices, rate,
                    working_days, imbalance, loss)
                for mode, (inputs, prices, working_days, loss) in self._carrier_models().items()
                if modes is None or mode in modes}

    def _freight_days_per_km(self):
        """{mode: days of travel per km over level ground}."""
        return {mode: 1.0 / inputs.distance_per_day_km
                for mode, (inputs, _prices, _days, _loss) in self._carrier_models().items()}

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
        """{mode: home money per tonne} charged once per leg of that mode."""
        return {"sea": (sea_freight.PORT_HANDLING_HOURS_PER_TONNE
                        * self.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE))}

    def _foreign_route(self, civilization, imbalance=None):
        """The cheapest `trade_routes.Route` from the foreign economy's home
        regions to this society's, or None when the map does not join them.
        `imbalance` is how one-sided the flows are (last year's, by default)."""
        network = trade_routes.load_network()
        civilization_record = civilization if isinstance(civilization, dict) else load_civ(civilization)
        foreign_techs = frozenset(civilization_record.get("starting_techs") or ())
        home_techs = frozenset(self.state.projects.done)
        if imbalance is None:
            imbalance = self._foreign_flow_imbalance(civilization_record.get("id"))
        return trade_routes.cheapest_route(
            network, self._regions,
            civilization_record.get("home_regions") or [], self.civ.get("home_regions") or [],
            trade_routes.usable_modes(network, (home_techs, foreign_techs)),
            home_techs | foreign_techs, haversine_km,
            self._freight_mode_costs(imbalance), self._freight_handling_costs(),
            days_per_km=self._freight_days_per_km())

    def _route_freight_per_tonne(self, civilization, imbalance=None):
        """Home money to haul a tonne over the cheapest route; infinite when
        no route joins the two."""
        route = self._foreign_route(civilization, imbalance)
        return float("inf") if route is None else route.cost_per_tonne
