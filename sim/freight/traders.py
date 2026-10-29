"""What merchants add to freight on a foreign route and how fast they respond.

The route's freight prices the carrier; the cargo's own cost is here, worked out from being a merchant
(`sim/world/merchant_terms.py`, `sim/world/merchant_house.py`): interest at the market rate on money tied up over the
voyage, the wait for a sailing and the sailing season, and the time to sell into the destination's demand; agents'
wages from the labour market; the expected loss of cargo on the legs; and a markup that follows the destination's price
response and falls as houses are added to the route. A house owns the carriers its capital buys and is staffed from the
labour market."""
import math

from sim.geography.api import cargo_cost, sea_freight
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR
from sim.world import merchant_house, merchant_terms, trader_response

from . import rules
from .constants import SEA_MODE


class Traders:
    """Needs: foreign_economies, hour_wage, hours_per_person_year, trade_population, working_age, households_loanable_funds, market_rate,
    route_lift_years_per_tonne, route_capital_per_lift_tonne, lift_capacity_tonnes, opening_carriers_per_route,
    carriage_facts, plus what Models needs."""

    def route_carriers(self, civilization_id, route):
        """Carriers on a route; endless for a route of no legs. With no partner named, the opening fleet."""
        years_per_tonne = self.needs.route_lift_years_per_tonne(route)
        if years_per_tonne is None:
            return float("inf")
        if civilization_id is None:
            return self.needs.opening_carriers_per_route()
        return self.needs.lift_capacity_tonnes(civilization_id, route) * years_per_tonne

    @staticmethod
    def route_voyage_years(route):
        return 0.0 if route is None else sum(leg.travel_days for leg in route.legs) / CIVIL_DAYS_PER_YEAR

    def route_cargo_tonnes(self, route):
        """Tonnes one sailing of the route's smallest carrier brings."""
        models = self.carrier_models()
        return min((models[leg.mode][0].cargo_tonnes for leg in route.legs), default=0.0)

    def carriers_per_house(self, civilization_id, route):
        """Carriers a house on the route owns: the capital of a merchant with what he can borrow against it, over a
        carrier's price (one when the route has no carriers to own)."""
        years_per_tonne = self.needs.route_lift_years_per_tonne(route)
        if civilization_id is None or not years_per_tonne:
            return 1.0
        carrier_value = self.needs.route_capital_per_lift_tonne(route) / years_per_tonne
        return merchant_house.carriers_per_house(
            (1.0 + merchant_terms.BORROWING_PER_OWN_CAPITAL) * self.capital_per_merchant(), carrier_value)

    def route_houses(self, civilization_id, route):
        """Merchant houses on the route: its carriers over those a house owns, as many as the merchants in the labour
        market (shared among the partners) can staff."""
        carriers = self.route_carriers(civilization_id, route)
        if math.isinf(carriers):
            return carriers
        merchants = self.needs.trade_population["merchant"] / max(1, len(self.needs.foreign_economies()))
        return merchant_house.houses_on_route(
            carriers, self.carriers_per_house(civilization_id, route), merchants)

    def merchant_own_capital(self):
        """Money the home merchant class holds of its own: its share of the funds households save, by its wage bill
        against the working population's."""
        return merchant_house.class_own_capital(
            self.needs.households_loanable_funds(), self.needs.trade_population["merchant"],
            self.needs.hour_wage["merchant"], self.needs.working_age(), self.needs.hour_wage["labourer"])

    def capital_per_merchant(self):
        merchants = self.needs.trade_population["merchant"]
        return self.merchant_own_capital() / merchants if merchants > 0.0 else 0.0

    def trader_cycle_years(self, route, civilization_id=None, destination_demand_tonnes=None):
        """Years money is tied up in a cargo: the voyage, the wait for a sailing at the two ends and for the sailing
        season to open, and (where the destination's yearly demand is given) the time to sell the cargo into it among
        the route's houses."""
        voyage = self.route_voyage_years(route)
        cycle = voyage + merchant_terms.wait_years(2.0 * voyage, self.route_carriers(civilization_id, route))
        if route is not None and any(leg.mode == SEA_MODE for leg in route.legs):
            cycle += merchant_terms.season_wait_years(sea_freight.SAILING_DAYS_PER_YEAR / CIVIL_DAYS_PER_YEAR)
        if destination_demand_tonnes is not None and route is not None:
            cycle += merchant_terms.selling_years(
                self.route_cargo_tonnes(route), destination_demand_tonnes, self.route_houses(civilization_id, route))
        return cycle

    def trader_margin_share(self, civilization_id, route, price_flexibility=None):
        """Markup over cost as a share of the price: the lone merchant's, from the destination's price response,
        falling with the houses on the route."""
        return merchant_terms.competition_markup_share(
            self.route_houses(civilization_id, route), merchant_terms.price_flexibility_or_default(price_flexibility))

    def trader_agent_cost(self, civilization_id, route):
        """Money for the agents kept at the two ends per tonne a carrier lifts, at the labour market's wage for a
        merchant, a house's agents shared among its carriers."""
        return merchant_terms.agent_cost_per_tonne(
            self.needs.route_lift_years_per_tonne(route), self.needs.hours_per_person_year(), self.needs.hour_wage["merchant"],
            merchant_house.agents_per_carrier(self.carriers_per_house(civilization_id, route)))

    def cargo_lost_share(self, route, material=None, civilization_id=None, destination_demand_tonnes=None):
        """Share of a cargo lost on a route: with hulls at sea, and to spoilage over the voyage and the wait (a good
        that does not spoil, or none named, loses only to the sea)."""
        spoilage = 0.0
        if material is not None:
            spoilage = cargo_cost.spoilage_share(
                cargo_cost.spoilage_rates().get(material, 0.0),
                self.trader_cycle_years(route, civilization_id, destination_demand_tonnes))
        return cargo_cost.lost_share(self.route_cargo_loss_share(route), spoilage)

    def route_cargo_loss_share(self, route):
        """Share of cargo lost on the route: the hull loss rate, for the crew the hull sails with, over its sea legs,
        and the daily loss of a herd over its legs on the road."""
        if route is None:
            return 0.0
        daily = self.needs.carriage_facts()["loss_per_day"]
        return rules.cargo_loss_share(route, daily, sea_freight.hull_loss_per_thousand_km(self.sea_crew()))

    def trader_cost_share(self, route, material=None, civilization_id=None, price_flexibility=None,
                          destination_demand_tonnes=None):
        """Merchants' cost over freight as a share of the price paid, apart from agents' wages."""
        return trader_response.cost_share_of_price(
            self.trader_margin_share(civilization_id, route, price_flexibility),
            self.cargo_lost_share(route, material, civilization_id, destination_demand_tonnes),
            self.needs.market_rate(),
            self.trader_cycle_years(route, civilization_id, destination_demand_tonnes))
