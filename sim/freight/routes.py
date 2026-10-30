"""The cheapest route over the map's tiles, each leg by a mode its users can employ, with the dues of every change of
mode: the one haul pricing foreign trade and domestic hauls share. The legs of the chosen route are kept, with their
travel days, so a player can see where goods travel."""
from . import rules
from .constants import GOODS_CARGO, LIVING_STOCK_CARGO
from .route import route_from_geography
from .route_choice import choose_route


class Routes:
    """Needs: tiles_listed_by, modes_usable, cheapest_route, civilisation, held_techniques, techniques_with_results, partner_market_book, plus what
    Models needs."""

    def foreign_flow_imbalance(self, civilization_id):
        """How one-sided last year's trade with a partner was, from its book: 1 when nothing flowed back (or nothing
        is known), 0 when tonnes in and out match."""
        return rules.foreign_flow_imbalance(self.needs.partner_market_book[civilization_id].values())

    def foreign_route(self, civilization, imbalance=None, cargo=GOODS_CARGO):
        """The cheapest `Route` from the foreign economy's home tiles (its civilisation record) to this society's, or
        None when no mode both can use joins them. `imbalance` is how one-sided the flows are (last year's, by
        default). `cargo` is the class of cargo carried ("goods", or "living_stock", which walks overland and is
        shipped over water)."""
        foreign_techs = self.needs.techniques_with_results(frozenset(civilization.get("starting_techs") or ()))
        if imbalance is None:
            imbalance = self.foreign_flow_imbalance(civilization.get("id"))
        return self.haul_route(self.needs.tiles_listed_by(civilization), imbalance, cargo, foreign_techs)

    def haul_route(self, origin_tiles, imbalance, cargo, partner_techs=None, improvements=None):
        """The cheapest `Route` from `origin_tiles` to this society's tiles, leg by leg, each leg at its mode's money
        rate with the mode's dues at every change of mode. The modes are those this society holds (and, for a foreign
        haul, `partner_techs` too) that carry the cargo. None when no mode joins the tiles."""
        home_techs = self.needs.held_techniques(False)
        techs = home_techs | partner_techs if partner_techs is not None else home_techs
        mode_costs = self.freight_mode_costs(imbalance)
        modes = [mode for mode in self.needs.modes_usable(
                    (home_techs, partner_techs) if partner_techs is not None else (home_techs,), cargo)
                 if mode in mode_costs]
        destination_tiles = self.needs.tiles_listed_by(self.needs.civilisation())
        handling = self.freight_handling_costs()

        def search(rates):
            found = self.needs.cheapest_route(
                origin_tiles, destination_tiles, modes, improvements, mode_costs=rates, handling_costs=handling,
                held_nodes=techs)
            return None if found is None else self.with_carried_provisions(
                route_from_geography(found), mode_costs, rates)
        return choose_route(search, lambda route: route.cost_per_tonne, mode_costs, self.share_delivered_on)

    def share_delivered_on(self, mode, route):
        return rules.delivered_share(self.carrier_models(), mode, route)

    def with_carried_provisions(self, route, base_rates=None, searched_rates=None):
        return rules.route_with_provisions(route, self.carrier_models(), self.freight_handling_costs(), base_rates,
                                           searched_rates)

    def route_freight_per_tonne(self, civilization, imbalance=None):
        """Home money to haul a tonne over the cheapest route; infinite when no route joins the two."""
        route = self.foreign_route(civilization, imbalance)
        return float("inf") if route is None else route.cost_per_tonne

    def material_route(self, civilization, material, goods_route):
        """The route a partner's `material` travels: the goods route already found, or for living stock the route its
        own modes make (animals walk overland and are shipped over water)."""
        if self.cargo_class(material) == GOODS_CARGO:
            return goods_route
        return self.foreign_route(civilization, cargo=LIVING_STOCK_CARGO)

    def partner_route_cost(self, civilization_id):
        """Home money to carry a tonne over the route to a partner (the route its economy's facts hold); None where
        no route is known."""
        route = self.needs.partner_route[civilization_id]
        return None if route is None else route.cost_per_tonne

    def tile_haul_cost(self, origin, destination):
        """Home money to haul a tonne over the cheapest route between two tiles; nothing where none joins them.
        Remembered for the year."""
        cache = self._carriage_cache
        year = self.needs.year()
        if cache.get("year") != year:
            cache.clear()
            cache["year"] = year
        key = (origin, destination)
        if key not in cache:
            home_techs = self.needs.held_techniques(False)
            mode_costs = self.freight_mode_costs(0.0)
            modes = [mode for mode in self.needs.modes_usable((home_techs,)) if mode in mode_costs]
            found = self.needs.cheapest_route([origin], [destination], modes, mode_costs=mode_costs,
                                              handling_costs=self.freight_handling_costs(), held_nodes=home_techs)
            cache[key] = 0.0 if found is None else self.with_carried_provisions(
                route_from_geography(found)).cost_per_tonne
        return cache[key]
