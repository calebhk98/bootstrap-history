"""Freight between this society and another economy: the cheapest route over
the map's links, each leg by the cheapest mode both economies can use.

Mode costs come from the physical models (`sim/world/transport.py` for cart,
pack string and towed barge; `sim/world/sea_freight.py` for a sailing hull),
priced with this society's feed price and wages. The legs of the chosen
route are kept so a player can see where goods travel.
"""
import functools

from sim.constants import declare
from sim.world import sea_freight, trade_routes
from sim.world import transport as freight_physics

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


@functools.lru_cache(maxsize=None)
def _river_inputs():
    return freight_physics.barge_freight_physical_inputs(
        freight_physics.OX, 2, freight_physics.BARGE)


@functools.lru_cache(maxsize=None)
def _caravan_inputs():
    return freight_physics.pack_freight_physical_inputs(
        freight_physics.MULE, int(CARAVAN_STRING_SIZE))


class ForeignRoutesMixin:

    def _freight_mode_costs(self):
        """{mode: home money per tonne-km} from each mode's physical inputs."""
        feed_price = self._material_price_per_kg(self.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        land_wage = self.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE)
        sea_wage = self.wage_per_hour(SEA_CREW_WAGE_TRADE)

        def money(inputs, wage):
            return inputs.feed_kg_per_tonne_km * feed_price + inputs.driver_hours_per_tonne_km * wage

        return {"cart": money(self._land_freight_physical_inputs(), land_wage),
                "caravan": money(_caravan_inputs(), land_wage),
                "river": money(_river_inputs(), land_wage),
                "sea": money(sea_freight.sailing_freight_physical_inputs(), sea_wage)}

    def _freight_handling_costs(self):
        """{mode: home money per tonne} charged once per leg of that mode."""
        return {"sea": (sea_freight.PORT_HANDLING_HOURS_PER_TONNE
                        * self.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE))}

    def _foreign_route(self, civilization):
        """The cheapest `trade_routes.Route` from the foreign economy's home
        regions to this society's, or None when the map does not join them."""
        network = trade_routes.load_network()
        civilization_record = civilization if isinstance(civilization, dict) else load_civ(civilization)
        foreign_techs = frozenset(civilization_record.get("starting_techs") or ())
        home_techs = frozenset(self.state.projects.done)
        return trade_routes.cheapest_route(
            network, self._regions,
            civilization_record.get("home_regions") or [], self.civ.get("home_regions") or [],
            trade_routes.usable_modes(network, (home_techs, foreign_techs)),
            home_techs | foreign_techs, haversine_km, self._freight_mode_costs(),
            self._freight_handling_costs())

    def _route_freight_per_tonne(self, civilization):
        """Home money to haul a tonne over the cheapest route; infinite when
        no route joins the two."""
        route = self._foreign_route(civilization)
        return float("inf") if route is None else route.cost_per_tonne
