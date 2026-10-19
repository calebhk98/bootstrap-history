"""A domestic haul priced by the one freight function: the cheapest route leg by leg, each leg at its
mode's running costs, capital and return trip, the tolls and dues of every change of mode, and, for live animals, their walk.

The return trip follows last year's domestic flow ledger (`sim.geography.flow_ledger`, kept by the
economy as the goods its merchants carried between tiles): the share of capacity the opposite flow
fills is not charged. With no ledger yet, the carrier is taken to return empty.
"""
import json

from sim.geography.api import flow_ledger, freight_cost, walking_cargo_modes

from .haul_route import Leg, Route
from .living_stock_yearly import stock_rates

DOMESTIC_CART_MODE = "cart"
MATERIAL_ROUTES_KEPT = 512


class DomesticHaulMixin:

    def _cargo_class(self, material):
        """"living_stock" for stock the living-stock data says walks (animals), else "goods" (seed, cuttings, eggs)."""
        return "living_stock" if stock_rates().get(material, {}).get("walks") else "goods"

    def _domestic_flow_ledger(self):
        """Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}; empty
        until the economy has run a year."""
        return self.economy.agent.carried_last_year()

    def _domestic_flow_imbalance(self):
        """How one-sided last year's domestic carriage was (1 when nothing is recorded: carts return empty)."""
        return flow_ledger.overall_imbalance(self._domestic_flow_ledger())

    def _domestic_haul_mode(self, cargo):
        """The mode a domestic haul of this class of cargo goes by: the cart for goods, the first mode
        whose cargo walks for living stock."""
        if cargo == "living_stock":
            walking = walking_cargo_modes(self.world_map)
            return walking[0] if walking else DOMESTIC_CART_MODE
        return DOMESTIC_CART_MODE

    def domestic_haul_dues_per_tonne(self, mode=DOMESTIC_CART_MODE):
        """Home money in tolls and dues a haul pays when it changes to the mode (the geography's hours of
        labour at the carriers' wage); the same charge a foreign leg of the mode pays."""
        return self._freight_handling_costs().get(mode, 0.0)

    def material_haul_route(self, material):
        """The cheapest `Route` that brings `material` to the tiles held from the nearest of its places,
        over the modes held and the ways built, priced leg by leg by the one haul function foreign trade
        uses (return trip by last year's domestic flows). None when the geography places no source or no
        mode joins it; an empty route when a held tile has one."""
        sources = self._material_source_tiles(material)
        if not sources:
            return None
        imbalance, cargo = self._domestic_flow_imbalance(), self._cargo_class(material)
        improvements = self.state.economy.improvements
        key = (tuple(sources), imbalance, cargo, self.held_and_running(include_starting=False),
               tuple(sorted(self._freight_mode_costs(imbalance).items())), json.dumps(improvements, sort_keys=True))
        kept = self.__dict__.setdefault("_material_haul_routes", {})
        if key not in kept:
            if len(kept) > MATERIAL_ROUTES_KEPT:
                kept.clear()
            kept[key] = (self._haul_route(sources, imbalance, cargo, improvements=improvements)
                         or self._unjoined_haul(material, imbalance))
        return kept[key]

    def _unjoined_haul(self, material, imbalance):
        """Where no way joins the source to the tiles held, the haul as one leg of the cargo's mode over the
        great-circle distance geography states, priced by the same leg pricing as a found route (None when
        geography places no source)."""
        distance_km = self.material_freight_distance_km(material)
        if distance_km is None:
            return None
        mode = self._domestic_haul_mode(self._cargo_class(material))
        cost = (self._freight_mode_costs(imbalance, (mode,))[mode] * distance_km
                + self.domestic_haul_dues_per_tonne(mode))
        days = freight_cost.days_on_leg(distance_km, self._carrier_models()[mode][0])
        return self._with_carried_provisions(Route((Leg("source", "home", mode, distance_km, cost, days),)))

    def domestic_haul_money_per_tonne(self, material):
        """Home money to haul a tonne of `material` from the nearest of its places: the route's legs at
        their modes' rates and the dues at each change of mode. Zero when it is made on held ground,
        None when no way joins it."""
        route = self.material_haul_route(material)
        return None if route is None else route.cost_per_tonne

    def _material_route(self, civilization, material, goods_route):
        """The route a partner's `material` travels: the goods route already found, or for living stock
        the route its own modes make (animals walk overland and are shipped over water)."""
        if self._cargo_class(material) == "goods":
            return goods_route
        return self._foreign_route(civilization, cargo="living_stock")
