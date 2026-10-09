"""What merchants add to freight on a foreign route and how fast they respond.

The route's freight prices the carrier; the cargo's own cost is here, worked out from being a
merchant (`sim/world/merchant_terms.py`): interest at the market rate on money tied up over the
voyage and the wait for a sailing, agents' wages from the labour market, the expected loss of cargo
on the legs, and a markup that falls as carriers, and so merchants, are added to the route. The yearly
flow moves toward the arbitrage volume as fast as carriers can change cargo
(`sim/world/trader_response.py`) and is limited by the lift and by the capital merchants hold and
can borrow.
"""
import math

from sim.world import merchant_terms, trader_response
from sim.geography.api import cargo_cost, sea_freight

from .data import STARTING_KITS
from sim.agents.api import SAVING_SHARE_OF_SURPLUS
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR
from .foreign_payments import OPENING_CARRIERS_PER_ROUTE
from .foreign_routes import SEA_MODE

MERCHANTS_BORROWER = "merchants"


class ForeignTradersMixin:

    def _route_carriers(self, civilization_id, route):
        """Carriers on a route, each the venture of one merchant; endless for a route of no legs.
        With no partner named, the opening fleet."""
        years_per_tonne = self._route_lift_years_per_tonne(route)
        if years_per_tonne is None:
            return float("inf")
        if civilization_id is None:
            return OPENING_CARRIERS_PER_ROUTE
        return self.foreign_lift_capacity_tonnes(civilization_id, route) * years_per_tonne

    @staticmethod
    def _route_voyage_years(route):
        return 0.0 if route is None else sum(leg.travel_days for leg in route.legs) / CIVIL_DAYS_PER_YEAR

    def _trader_cycle_years(self, route, civilization_id=None):
        """Years money is tied up in a cargo: the voyage, and the wait for a sailing at the two ends."""
        voyage = self._route_voyage_years(route)
        return voyage + merchant_terms.wait_years(
            2.0 * voyage, self._route_carriers(civilization_id, route))

    def _trader_margin_share(self, civilization_id, route):
        """Markup over cost as a share of the price: it falls with the merchants on the route."""
        return merchant_terms.competition_markup_share(self._route_carriers(civilization_id, route))

    def _agent_cost_per_tonne(self, civilization_id, route):
        """Money for the agents kept at the two ends per tonne a carrier lifts, at the labour
        market's wage for a merchant."""
        years_per_tonne = self._route_lift_years_per_tonne(route)
        if years_per_tonne is None:
            return 0.0
        return (merchant_terms.AGENTS_PER_CARRIER * years_per_tonne * self.HOURS_PER_PERSON_YEAR
                * self.labour.market.quote("merchant"))

    @staticmethod
    def _route_cargo_loss_share(route):
        """Share of cargo lost on the route: the hull loss rate over its sea legs."""
        if route is None:
            return 0.0
        sailed_km = sum(leg.distance_km for leg in route.legs if leg.mode == SEA_MODE)
        return cargo_cost.sea_loss_share(sea_freight.hull_loss_per_thousand_km(), sailed_km)

    def _cargo_lost_share(self, route, material=None, civilization_id=None):
        """Share of a cargo lost on a route: with hulls at sea, and to spoilage over the voyage
        and the wait (a good that does not spoil, or none named, loses only to the sea)."""
        spoilage = 0.0
        if material is not None:
            spoilage = cargo_cost.spoilage_share(
                cargo_cost.spoilage_rates().get(material, 0.0),
                self._trader_cycle_years(route, civilization_id))
        return cargo_cost.lost_share(self._route_cargo_loss_share(route), spoilage)

    def _trader_cost_share(self, route, material=None, civilization_id=None):
        """Merchants' cost over freight as a share of the price paid, apart from agents' wages."""
        return trader_response.cost_share_of_price(
            self._trader_margin_share(civilization_id, route),
            self._cargo_lost_share(route, material, civilization_id), self.market_rate(),
            self._trader_cycle_years(route, civilization_id))

    def _spoiling_material(self, commodity):
        """The material of a commodity that spoils fastest, or None when none spoils."""
        if commodity is None:
            return None
        rates = cargo_cost.spoilage_rates()
        spoiling = [material for material in self._commodity_materials(commodity) if material in rates]
        return max(spoiling, key=rates.get) if spoiling else None

    def _fleet_value(self, civilization_id):
        """Money sunk in a route's carriers."""
        route = self._foreign_economy_facts(civilization_id)["route"]
        if self._route_lift_years_per_tonne(route) is None:
            return 0.0
        return (self.foreign_lift_capacity_tonnes(civilization_id, route)
                * self._route_capital_per_lift_tonne(route))

    def merchant_class_capital(self):
        """Money the home merchant class holds for goods in transit and inventory: each merchant the
        capital of the modest-merchant kit (the engine's authored capital for one real venture, in
        labourer-years of the labourer's wage), the earnings merchants have kept, less what is sunk
        in carriers."""
        merchants = self.labour.national_trade_population("merchant")
        each = STARTING_KITS["merchant"]["labourer_years"] * self.labour.market.quote_annual("labourer")
        ledgers = self.state.economy.foreign_ledger
        kept = sum(ledger["merchant_retained"] for ledger in ledgers.values())
        sunk = sum(self._fleet_value(civilization_id) for civilization_id in self.foreign_economies())
        return max(0.0, merchants * each + kept - sunk)

    def merchant_capital_left(self, civilization_id):
        """Home money merchants can still tie up in goods this year, over every partner: their own
        capital and what they borrow against it within lenders' room."""
        if self._route_lift_years_per_tonne(self._foreign_economy_facts(civilization_id)["route"]) is None:
            return float("inf")
        capital = merchant_terms.capital_to_finance(
            self.merchant_class_capital(), self.market_credit_room(MERCHANTS_BORROWER))
        year = self.state.scenario.year
        used = sum(ledger["merchant_capital_used"] for ledger in self.state.economy.foreign_ledger.values()
                   if ledger["lift_year"] == year)
        return max(0.0, capital - used)

    def trader_terms(self, civilization_id, facts, home_price, foreign_price, commodity=None):
        """`TraderTerms` for a route this year; capital limits in tonnes each way at these prices.
        A named commodity pays spoilage by its fastest-spoiling material."""
        route = facts["route"]
        cycle = self._trader_cycle_years(route, civilization_id)
        left = self.merchant_capital_left(civilization_id)
        round_trip = 2.0 * self._route_voyage_years(route)

        def tonnes_financed(price):
            return left / (price * cycle) if price > 0.0 and cycle > 0.0 else (
                math.inf if price > 0.0 else 0.0)
        return trader_response.TraderTerms(
            self._trader_cost_share(route, self._spoiling_material(commodity), civilization_id),
            merchant_terms.redirect_share_per_year(round_trip),
            capital_tonnes_in=tonnes_financed(foreign_price),
            capital_tonnes_out=tonnes_financed(home_price),
            agent_cost_per_tonne=self._agent_cost_per_tonne(civilization_id, route))

    def _flow_capital_tied(self, civilization_id, commodity, flow, home_entry, foreign_outcome, facts):
        """Home money merchants tied up in a flow for a cycle, at the exporter's price."""
        value = self._flow_value(civilization_id, commodity, flow, home_entry, foreign_outcome, facts)
        return 0.0 if value is None else value * self._trader_cycle_years(facts["route"], civilization_id)

    def _retain_merchant_earnings(self, civilization_id, commodity, flow, home_entry, foreign_outcome, facts):
        """Add to merchants' capital the saved part of the markup a flow earned them (what is not
        saved is spent, as households' income is)."""
        value = self._flow_value(civilization_id, commodity, flow, home_entry, foreign_outcome, facts)
        if value:
            self._foreign_ledger(civilization_id, create=True)["merchant_retained"] += (
                SAVING_SHARE_OF_SURPLUS * value * self._trader_margin_share(civilization_id, facts["route"]))
