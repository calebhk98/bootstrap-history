"""A domestic haul priced by the one freight function: the cheapest route leg by leg, each leg at its mode's running
costs, capital and return trip, the tolls and dues of every change of mode, and, for live animals, their walk.

The return trip follows last year's domestic flow ledger (the goods the economy's merchants carried between tiles): the
share of capacity the opposite flow fills is not charged. With no ledger yet, the carrier is taken to return empty."""
import json

from sim.geography.api import cargo_cost, cargo_loss_per_day, flow_ledger, freight_cost, walking_cargo_modes
from sim.living_stock.api import stock_rates

from . import rules
from .constants import DOMESTIC_CART_MODE, LIVING_STOCK_CARGO, MATERIAL_ROUTES_KEPT
from .route import Leg, Route, cargo_class_of, domestic_cargo_cost_share, domestic_haul_mode, unjoined_haul_cost


class Haul:
    """Needs: legacy_world_map, built_ways, held_techniques, goods_carried_last_year, material_source_tiles,
    route_km_to, market_rate, material_price, plus what Models and Routes need."""

    def cargo_class(self, material):
        """"living_stock" for stock the living-stock data says walks (animals), else "goods" (seed, cuttings, eggs)."""
        return cargo_class_of(stock_rates().get(material))

    def domestic_flow_imbalance(self):
        """How one-sided last year's domestic carriage was (1 when nothing is recorded: carts return empty)."""
        return flow_ledger.overall_imbalance(self.needs.goods_carried_last_year())

    def domestic_haul_mode(self, cargo):
        """The mode a domestic haul of this class of cargo goes by: the cart for goods, the first mode whose cargo
        walks for living stock."""
        walking = walking_cargo_modes(self.needs.legacy_world_map()) if cargo == LIVING_STOCK_CARGO else ()
        return domestic_haul_mode(cargo, walking, DOMESTIC_CART_MODE)

    def material_haul_route(self, material):
        """The cheapest `Route` that brings `material` to the tiles held from the nearest of its places, over the
        modes held and the ways built, priced leg by leg by the one haul function foreign trade uses (return trip by
        last year's domestic flows). None when the geography places no source or no mode joins it; an empty route when
        a held tile has one."""
        sources = self.needs.material_source_tiles[material]
        if not sources:
            return None
        imbalance, cargo = self.domestic_flow_imbalance(), self.cargo_class(material)
        improvements = self.needs.built_ways()
        key = (tuple(sources), imbalance, cargo, self.needs.held_techniques(False),
               tuple(sorted(self.freight_mode_costs(imbalance).items())), json.dumps(improvements, sort_keys=True))
        kept = self._haul_routes
        if key not in kept:
            if len(kept) > MATERIAL_ROUTES_KEPT:
                kept.clear()
            kept[key] = (self.haul_route(sources, imbalance, cargo, improvements=improvements)
                         or self.unjoined_haul(material, imbalance))
        return kept[key]

    def material_distance_km(self, material):
        """Kilometres of the cheapest haul from the tiles held to the nearest tile whose deposits produce `material`;
        zero if a held tile has one, None if nothing places the material."""
        tiles = self.needs.material_source_tiles[material]
        return self.needs.route_km_to(tiles) if tiles else None

    def unjoined_haul(self, material, imbalance):
        """Where no way joins the source to the tiles held, the haul as one leg of the cargo's mode over the
        great-circle distance geography states, priced by the same leg pricing as a found route (None when geography
        places no source)."""
        distance_km = self.material_distance_km(material)
        if distance_km is None:
            return None
        mode = self.domestic_haul_mode(self.cargo_class(material))
        dues = self.freight_handling_costs().get(mode, 0.0)
        cost = unjoined_haul_cost(self.freight_mode_costs(imbalance, (mode,))[mode], distance_km, dues)
        days = freight_cost.days_on_leg(distance_km, self.carrier_models()[mode][0])
        return self.with_carried_provisions(Route((Leg("source", "home", mode, distance_km, cost, days),)))

    def domestic_cargo_cost_share(self, material, route):
        """The cargo's own cost over a domestic haul (a `Route`) as a share of its price: interest at the market rate
        while it travels, and what is lost to spoilage in that time (and, for a herd on the road, the daily loss each
        leg's mode states). No merchant margin (domestic carriers' margins are not modelled)."""
        return domestic_cargo_cost_share(
            cargo_cost.spoilage_rates().get(material, 0.0), cargo_loss_per_day(self.needs.legacy_world_map()), route,
            self.needs.market_rate())

    def material_freight_factor(self, material):
        """Multiplicative markup on a material's book price for hauling it here from the nearest place it comes from:
        1.0 for a material the geography does not place, one already made on held ground, or one with no book price.
        A markup (1.0 + freight / book price), not an added charge, because every other adjustment to a project's
        material price is a factor and freight must compose with them."""
        book_price_per_kg = self.needs.material_price[material]
        if not book_price_per_kg or book_price_per_kg <= 0:
            return 1.0
        route = self.material_haul_route(material)
        if route is None or not route.legs:
            return 1.0
        return rules.freight_markup(book_price_per_kg, route.cost_per_tonne, self.domestic_cargo_cost_share(material, route))

    def material_carriage_per_tonne(self, material, price_per_tonne):
        """Money per tonne to carry a material to the household from the nearest place it comes from, on top of its
        price where it is sold: the haul over the ways held and the cargo's own interest and spoilage as a share of
        that price. Zero for a material the geography cannot place or that is made where the household holds
        ground."""
        route = self.material_haul_route(material)
        if route is None or not route.legs:
            return 0.0
        return route.cost_per_tonne + self.domestic_cargo_cost_share(material, route) * price_per_tonne
