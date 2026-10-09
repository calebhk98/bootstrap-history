"""What merchants add to freight on a foreign route and how fast they respond.

The route's freight prices the carrier; the cargo's own cost is here, worked out from being a
merchant (`sim/world/merchant_terms.py`, `sim/world/merchant_house.py`): interest at the market rate on
money tied up over the voyage, the wait for a sailing and the sailing season, and the time to sell into
the destination's demand; agents' wages from the labour market; the expected loss of cargo on the legs;
and a markup that follows the destination's price response and falls as houses are added to the route.
A house owns the carriers its capital buys and is staffed from the labour market. The yearly flow moves
toward the arbitrage volume as fast as carriers can change cargo (`sim/world/trader_response.py`) and
is limited by the lift and by the capital merchants hold and can borrow.
"""
import dataclasses
import math

from sim.world import market, merchant_house, merchant_terms, trader_response
from sim.geography.api import cargo_cost, sea_freight

from sim.unit_conversions import CIVIL_DAYS_PER_YEAR
from .foreign_payments import OPENING_CARRIERS_PER_ROUTE
from .foreign_routes import SEA_MODE

MERCHANTS_BORROWER = "merchants"


class ForeignTradersMixin:

    MERCHANTS_BORROWER = MERCHANTS_BORROWER

    def _route_carriers(self, civilization_id, route):
        """Carriers on a route; endless for a route of no legs. With no partner named, the opening
        fleet."""
        years_per_tonne = self._route_lift_years_per_tonne(route)
        if years_per_tonne is None:
            return float("inf")
        if civilization_id is None:
            return OPENING_CARRIERS_PER_ROUTE
        return self.foreign_lift_capacity_tonnes(civilization_id, route) * years_per_tonne

    @staticmethod
    def _route_voyage_years(route):
        return 0.0 if route is None else sum(leg.travel_days for leg in route.legs) / CIVIL_DAYS_PER_YEAR

    def _route_cargo_tonnes(self, route):
        """Tonnes one sailing of the route's smallest carrier brings."""
        models = self._carrier_models()
        return min((models[leg.mode][0].cargo_tonnes for leg in route.legs), default=0.0)

    def _carriers_per_house(self, civilization_id, route):
        """Carriers a house on the route owns: the capital of a merchant with what he can borrow
        against it, over a carrier's price (one when the route has no carriers to own)."""
        years_per_tonne = self._route_lift_years_per_tonne(route)
        if civilization_id is None or not years_per_tonne:
            return 1.0
        carrier_value = self._route_capital_per_lift_tonne(route) / years_per_tonne
        return merchant_house.carriers_per_house(
            (1.0 + merchant_terms.BORROWING_PER_OWN_CAPITAL) * self._capital_per_merchant(), carrier_value)

    def _route_houses(self, civilization_id, route):
        """Merchant houses on the route: its carriers over those a house owns, as many as the merchants
        in the labour market (shared among the partners) can staff."""
        carriers = self._route_carriers(civilization_id, route)
        if math.isinf(carriers):
            return carriers
        merchants = self.labour.national_trade_population("merchant") / max(1, len(self.foreign_economies()))
        return merchant_house.houses_on_route(
            carriers, self._carriers_per_house(civilization_id, route), merchants)

    def _trader_cycle_years(self, route, civilization_id=None, destination_demand_tonnes=None):
        """Years money is tied up in a cargo: the voyage, the wait for a sailing at the two ends and for
        the sailing season to open, and (where the destination's yearly demand is given) the time to
        sell the cargo into it among the route's houses."""
        voyage = self._route_voyage_years(route)
        cycle = voyage + merchant_terms.wait_years(
            2.0 * voyage, self._route_carriers(civilization_id, route))
        if route is not None and any(leg.mode == SEA_MODE for leg in route.legs):
            cycle += merchant_terms.season_wait_years(
                sea_freight.SAILING_DAYS_PER_YEAR / CIVIL_DAYS_PER_YEAR)
        if destination_demand_tonnes is not None and route is not None:
            cycle += merchant_terms.selling_years(
                self._route_cargo_tonnes(route), destination_demand_tonnes,
                self._route_houses(civilization_id, route))
        return cycle

    def _trader_margin_share(self, civilization_id, route, price_flexibility=None):
        """Markup over cost as a share of the price: the lone merchant's, from the destination's price
        response, falling with the houses on the route."""
        return merchant_terms.competition_markup_share(
            self._route_houses(civilization_id, route),
            merchant_terms.price_flexibility_or_default(price_flexibility))

    def _agent_cost_per_tonne(self, civilization_id, route):
        """Money for the agents kept at the two ends per tonne a carrier lifts, at the labour
        market's wage for a merchant, a house's agents shared among its carriers."""
        return merchant_terms.agent_cost_per_tonne(
            self._route_lift_years_per_tonne(route), self.HOURS_PER_PERSON_YEAR,
            self.labour.market.quote("merchant"),
            merchant_house.agents_per_carrier(self._carriers_per_house(civilization_id, route)))

    def _route_cargo_loss_share(self, route):
        """Share of cargo lost on the route: the hull loss rate, for the crew the hull sails with, over
        its sea legs."""
        if route is None:
            return 0.0
        sailed_km = sum(leg.distance_km for leg in route.legs if leg.mode == SEA_MODE)
        return cargo_cost.sea_loss_share(sea_freight.hull_loss_per_thousand_km(self._sea_crew()), sailed_km)

    def _cargo_lost_share(self, route, material=None, civilization_id=None, destination_demand_tonnes=None):
        """Share of a cargo lost on a route: with hulls at sea, and to spoilage over the voyage
        and the wait (a good that does not spoil, or none named, loses only to the sea)."""
        spoilage = 0.0
        if material is not None:
            spoilage = cargo_cost.spoilage_share(
                cargo_cost.spoilage_rates().get(material, 0.0),
                self._trader_cycle_years(route, civilization_id, destination_demand_tonnes))
        return cargo_cost.lost_share(self._route_cargo_loss_share(route), spoilage)

    def _trader_cost_share(self, route, material=None, civilization_id=None, price_flexibility=None,
                           destination_demand_tonnes=None):
        """Merchants' cost over freight as a share of the price paid, apart from agents' wages."""
        return trader_response.cost_share_of_price(
            self._trader_margin_share(civilization_id, route, price_flexibility),
            self._cargo_lost_share(route, material, civilization_id, destination_demand_tonnes),
            self.market_rate(),
            self._trader_cycle_years(route, civilization_id, destination_demand_tonnes))

    def _destination_price_flexibility(self, commodity, conditions, destination_is_home, cargo_tonnes):
        """How far the destination's price falls per rise in the quantity on its market once a cargo
        lands: the agent economy's response for the good where it answers for the home market, else the
        market's own clearing with the cargo added; None where neither gives one."""
        traded = market.clear_market(conditions).quantity_traded_tonnes
        if not traded > 0.0 or not cargo_tonnes > 0.0:
            return None
        landed_share = cargo_tonnes / traded
        if destination_is_home and commodity is not None:
            for material in self._commodity_materials(commodity):
                factor = self.economy.agent_price_response(material, cargo_tonnes, 0.0)
                if factor is not None:
                    return merchant_terms.price_flexibility(factor, landed_share)
        landed = dataclasses.replace(conditions, actor_supply_tonnes=conditions.actor_supply_tonnes + cargo_tonnes)
        factor = market.clearing_price_ratio(landed) / market.clearing_price_ratio(conditions)
        return merchant_terms.price_flexibility(factor, landed_share)

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

    def _households_loanable_funds(self):
        """Funds households put into the loanable pool: at the last meeting of the capital market, or
        what their saving would put in before it has met."""
        record = self._market_record()
        if record is not None and record.supply > 0.0:
            return record.supply_by_source.get("households", 0.0)
        from .agents_port import SimWorld
        from .economy_capital_market import LENDING_HORIZON_YEARS
        return LENDING_HORIZON_YEARS * SimWorld(self).household_saving()

    def _merchant_own_capital(self):
        """Money the home merchant class holds of its own: its share of the funds households save,
        by its wage bill against the working population's."""
        wages = self.labour.market
        return merchant_house.class_own_capital(
            self._households_loanable_funds(), self.labour.national_trade_population("merchant"),
            wages.quote("merchant"), self.population.working_age, wages.quote("labourer"))

    def _capital_per_merchant(self):
        merchants = self.labour.national_trade_population("merchant")
        return self._merchant_own_capital() / merchants if merchants > 0.0 else 0.0

    def merchant_class_capital(self):
        """Money the home merchant class holds for goods in transit and inventory: its own share of
        the households' funds, the earnings merchants have kept, less what is sunk in carriers."""
        ledgers = self.state.economy.foreign_ledger
        kept = sum(ledger["merchant_retained"] for ledger in ledgers.values())
        sunk = sum(self._fleet_value(civilization_id) for civilization_id in self.foreign_economies())
        return max(0.0, self._merchant_own_capital() + kept - sunk)

    def merchant_borrowing(self):
        """Money the merchant class owes the pool: what it put into goods in its last year of trade,
        beyond its own."""
        used = sum(ledger["merchant_capital_used"] for ledger in self.state.economy.foreign_ledger.values())
        if used <= 0.0:
            return 0.0
        return merchant_house.borrowing(used, self.merchant_class_capital())

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

    def trader_terms(self, civilization_id, facts, home_price, foreign_price, commodity=None,
                     destination=None, destination_is_home=True):
        """`TraderTerms` for a route this year; capital limits in tonnes each way at these prices.
        A named commodity pays spoilage by its fastest-spoiling material. `destination` is the
        conditions of the market the goods go to (the dearer side): its price response sets the markup
        and its demand the time to sell."""
        route = facts["route"]
        flexibility, demand = None, None
        if destination is not None and route is not None:
            flexibility = self._destination_price_flexibility(
                commodity, destination, destination_is_home, self._route_cargo_tonnes(route))
            demand = (destination.household_demand_at_anchor_tonnes + destination.committed_demand_tonnes
                      + destination.actor_demand_tonnes)
        cycle = self._trader_cycle_years(route, civilization_id, demand)
        left = self.merchant_capital_left(civilization_id)
        round_trip = 2.0 * self._route_voyage_years(route)

        def tonnes_financed(price):
            return left / (price * cycle) if price > 0.0 and cycle > 0.0 else (
                math.inf if price > 0.0 else 0.0)
        return trader_response.TraderTerms(
            self._trader_cost_share(route, self._spoiling_material(commodity), civilization_id,
                                    flexibility, demand),
            merchant_terms.redirect_share_per_year(round_trip),
            capital_tonnes_in=tonnes_financed(foreign_price),
            capital_tonnes_out=tonnes_financed(home_price),
            agent_cost_per_tonne=self._agent_cost_per_tonne(civilization_id, route),
            margin_share=self._trader_margin_share(civilization_id, route, flexibility),
            cycle_years=cycle)

    def _flow_capital_tied(self, civilization_id, commodity, flow, home_entry, foreign_outcome, facts):
        """Home money merchants tied up in a flow for a cycle, at the exporter's price."""
        value = self._flow_value(civilization_id, commodity, flow, home_entry, foreign_outcome, facts)
        if value is None:
            return 0.0
        cycle = self.state.economy.foreign_market_book[civilization_id][commodity].get("trader_cycle_years")
        return value * (self._trader_cycle_years(facts["route"], civilization_id) if cycle is None else cycle)

    def _retain_merchant_earnings(self, civilization_id, commodity, flow, home_entry, foreign_outcome, facts):
        """Add to merchants' capital the part of the markup a flow earned them that they put back into
        trade, from their own return on the money tied up (the markup over the cycle) against the market
        rate; the rest is spent. The terms the flow was cleared on are on the book's entry."""
        value = self._flow_value(civilization_id, commodity, flow, home_entry, foreign_outcome, facts)
        if value:
            entry = self.state.economy.foreign_market_book[civilization_id][commodity]
            margin = entry.get("trader_margin_share")
            if margin is None:
                margin = self._trader_margin_share(civilization_id, facts["route"])
            cycle = entry.get("trader_cycle_years")
            if cycle is None:
                cycle = self._trader_cycle_years(facts["route"], civilization_id)
            kept = merchant_terms.retained_share(margin / cycle if cycle > 0.0 else math.inf, self.market_rate())
            self._foreign_ledger(civilization_id, create=True)["merchant_retained"] += value * margin * kept
