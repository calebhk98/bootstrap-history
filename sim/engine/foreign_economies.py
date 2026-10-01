"""Other economies as participants in the home society's markets.

An economy named in `data/world/foreign_economies.json` has its own solved
long-run costs (its civilisation file's technologies, wage and coin), a
population that sizes its market, and a place on the map. For each commodity
it keeps a book like the society's (capacity, stock, price ratio) and clears
it every year together with the home market through
`sim/world/trade_between.py`: goods cross when the price gap exceeds the
freight over the route, so imports cap a home shortage and exports lift the
price abroad. The founder's purchases and sales are part of the home market
and so part of the trade.

Prices of both sides are compared in home money: a foreign price in its own
coin is worth the coin's metal at the home price of that metal.
"""
import dataclasses
import functools
import json
import os

from sim.world import market, trader_response

from .data import ROOT, calculated_goods_prices, goods_provenance, load_civ, starting_schedule
from .foreign_capacity import ForeignCapacityMixin
from .foreign_payments import ForeignPaymentsMixin
from .foreign_routes import ForeignRoutesMixin
from .foreign_traders import ForeignTradersMixin
from .project_materials import tonnes_per_unit

FOREIGN_ECONOMIES_PATH = os.path.join(ROOT, "data", "world", "foreign_economies.json")


@functools.lru_cache(maxsize=None)
def foreign_economy_records():
    """The economies the data file names."""
    with open(FOREIGN_ECONOMIES_PATH, encoding="utf-8") as handle:
        return tuple(json.load(handle)["economies"])


@functools.lru_cache(maxsize=None)
def not_traded_materials():
    """Materials that cannot cross a border, from the data file."""
    with open(FOREIGN_ECONOMIES_PATH, encoding="utf-8") as handle:
        return frozenset(json.load(handle).get("not_traded_materials") or ())


@functools.lru_cache(maxsize=None)
def _foreign_solved_materials(civilization_id):
    """Materials the economy can make with its own technologies; the rest are
    priced only as if some technology were held."""
    civilization = load_civ(civilization_id)
    provenance = goods_provenance(frozenset(civilization["starting_techs"]),
                                  civilization_id=civilization_id)
    return frozenset(material for material, source in provenance.items() if source == "solved")


@functools.lru_cache(maxsize=None)
def _foreign_prices_in_own_coin(civilization_id):
    """{material: price in the economy's own coin} under its own opening
    technologies (frozen for the game)."""
    civilization = load_civ(civilization_id)
    return calculated_goods_prices(
        frozenset(civilization["starting_techs"]), civilization_id=civilization_id,
        money_per_labour_hour=starting_schedule(civilization_id).money_per_labour_hour)


class ForeignEconomiesMixin(ForeignRoutesMixin, ForeignCapacityMixin, ForeignPaymentsMixin,
                            ForeignTradersMixin):

    def foreign_economies(self):
        """Economies trading with this society this year, sorted by id."""
        year = self.state.scenario.year
        own = self.civ.get("id")
        return sorted(record["civilization"] for record in foreign_economy_records()
                      if record.get("enabled", False) and record["civilization"] != own
                      and record["from_year"] <= year <= record["until_year"])

    def _foreign_economy_facts(self, civilization_id):
        """Population, route and prices of one foreign economy in home money,
        remembered until the home price table changes."""
        prices = self._material_prices()
        cache = getattr(self.household, "_foreign_facts_cache", None)
        if cache is None:
            cache = self.household._foreign_facts_cache = {}
        cached = cache.get(civilization_id)
        known_techs = len(self.state.projects.done)
        if cached is not None and cached[0] is prices and cached[2] == known_techs:
            return cached[1]
        civilization = load_civ(civilization_id)
        coin = civilization["coin_standard"]
        coin_price = prices.get(coin["material"])
        foreign_prices = {}
        if coin_price:
            home_money_per_coin = coin["kg_per_unit"] * coin_price
            foreign_prices = {material: price * home_money_per_coin for material, price
                              in _foreign_prices_in_own_coin(civilization_id).items()}
        route = self._foreign_route(civilization)
        facts = {"solved_materials": _foreign_solved_materials(civilization_id),
                 "home_solved_materials": frozenset(
                     material for material, source in goods_provenance(
                         frozenset(self.state.projects.done),
                         civilization_id=self.civ.get("id")).items() if source == "solved"),
                 "population": float(civilization.get("population") or 0.0),
                 "prices_in_home_money": foreign_prices,
                 "route": route,
                 "freight_per_tonne": self._route_freight_per_tonne(civilization)}
        cache[civilization_id] = (prices, facts, known_techs)
        return facts

    def _commodity_materials(self, commodity):
        """Material keys that count as the commodity: the commodity's own
        name, the ledger's grouping and every priced material the engine
        files under it. Remembered until the price table changes."""
        prices = self._material_prices()
        cache = getattr(self.household, "_commodity_materials_cache", None)
        if cache is None or cache[0] is not prices:
            cache = self.household._commodity_materials_cache = (prices, {})
        keys = cache[1].get(commodity)
        if keys is None:
            if "members" not in cache[1]:
                grouped = {}
                for material in prices:
                    grouped.setdefault(self._material_tag(material)[0], set()).add(material)
                cache[1]["members"] = grouped
            members = set(cache[1]["members"].get(commodity, ()))
            members.update(self._commodity_ledger().commodities.get(
                commodity, {}).get("material_keys", []))
            keys = cache[1][commodity] = [commodity] + sorted(members - {commodity})
        return keys

    def _foreign_trade_key(self, commodity, facts):
        """(material key, home can make the commodity, partner can make it)
        for the material of the commodity priced on both sides that may
        cross a border, preferring one both can make; None when neither side
        makes any."""
        home_prices = self._material_prices()
        foreign_prices = facts["prices_in_home_money"]
        keys = [key for key in self._commodity_materials(commodity)
                if key in home_prices and key in foreign_prices
                and key not in not_traded_materials()]
        home_makes = [key for key in keys if key in facts["home_solved_materials"]]
        foreign_makes = [key for key in keys if key in facts["solved_materials"]]
        both = [key for key in home_makes if key in foreign_makes]
        if both:
            return both[0], True, True
        if home_makes or foreign_makes:
            return (home_makes or foreign_makes)[0], bool(home_makes), bool(foreign_makes)
        return None

    def _foreign_price_pair(self, commodity, facts):
        """(home, foreign) long-run price per tonne of a commodity in home
        money. A side that cannot make the good takes the other side's price
        as its cost of supply (freight is added by the route); None when
        neither side can make it."""
        found = self._foreign_trade_key(commodity, facts)
        if found is None:
            return None
        key, home_can, foreign_can = found
        per_tonne = 1.0 / tonnes_per_unit(key)
        home_price = self._material_prices()[key] * per_tonne
        foreign_price = facts["prices_in_home_money"][key] * per_tonne
        return (home_price if home_can else foreign_price,
                foreign_price if foreign_can else home_price)

    def _output_is_sourced(self, commodity):
        """Whether the society's output of the commodity comes from a sourced
        table (resources.json or commodities.json) rather than the generic
        estimate."""
        # TEMPORARY HEURISTIC: a generic estimate (often the ceiling) is not a
        # level to trade against, so a good this society makes crosses a
        # border only where its output is sourced (Complaints/113).
        return (commodity in self.res["empire_output_100ad"]
                or commodity in self._commodity_ledger().commodities)

    def _foreign_sides(self, commodity, facts):
        """(home can make it, partner can make it)."""
        found = self._foreign_trade_key(commodity, facts)
        return (False, False) if found is None else found[1:]

    def _foreign_entry(self, civilization_id, commodity, facts):
        """The foreign economy's book entry for a commodity, opened from its
        own society (foreign_capacity.py); None when it neither makes nor
        wants the good."""
        book = self.state.economy.foreign_market_book.setdefault(civilization_id, {})
        entry = book.get(commodity)
        if entry is None:
            capacity, demand = self.foreign_opening(
                civilization_id, commodity, facts["solved_materials"])
            if not demand > 0.0:
                return None
            entry = book[commodity] = {
                "reference_tonnes": demand, "capacity_tonnes": capacity,
                "stock_tonnes": 0.0, "price_ratio": 1.0, "trade_tonnes": 0.0}
        return entry

    @staticmethod
    def _foreign_conditions(entry, home_conditions):
        return market.MarketConditions(
            household_demand_at_anchor_tonnes=entry["reference_tonnes"],
            committed_demand_tonnes=0.0, society_capacity_tonnes=entry["capacity_tonnes"],
            actor_supply_tonnes=0.0, founder_sales_tonnes=0.0,
            stock_tonnes=entry["stock_tonnes"],
            floor_ratio=home_conditions.floor_ratio, ceiling_ratio=home_conditions.ceiling_ratio)

    def foreign_trade(self, commodity, home_entry, home_conditions):
        """The home market's conditions after trade with every foreign
        economy, and [(economy id, tonnes imported (negative when exported),
        the foreign economy's outcome)]. Nearest partner first. A good this
        society cannot make has no home capacity once a partner offers it."""
        partners = []
        for civilization_id in self.foreign_economies():
            facts = self._foreign_economy_facts(civilization_id)
            pair = self._foreign_price_pair(commodity, facts)
            if pair is not None:
                partners.append((facts["freight_per_tonne"], civilization_id, facts, pair))
        flows = []
        unmet = self.household.__dict__.setdefault("_foreign_unmet_tonnes", {})
        home_level = self.home_price_level()
        for freight, civilization_id, facts, (home_price, foreign_price) in sorted(
                partners, key=lambda partner: partner[:2]):
            home_makes = self._foreign_sides(commodity, facts)[0]
            if home_makes and not self._output_is_sourced(commodity):
                continue
            entry = self._foreign_entry(civilization_id, commodity, facts)
            if entry is None:
                continue
            if not home_makes:
                home_demand = self.home_unmade_demand_tonnes(commodity)
                if not home_demand > 0.0:
                    continue
                home_conditions = dataclasses.replace(
                    home_conditions, society_capacity_tonnes=0.0, stock_tonnes=0.0,
                    household_demand_at_anchor_tonnes=home_demand)
            home_price *= home_level
            foreign_price *= self.partner_price_level(civilization_id)
            foreign_conditions = self._foreign_conditions(entry, home_conditions)
            lift_in, lift_out = self.foreign_lift_left_tonnes(civilization_id, facts["route"])
            terms = self.trader_terms(civilization_id, facts, home_price, foreign_price)
            previous = -entry["trade_tonnes"]
            outcome = trader_response.clear_with_traders(
                home_conditions, foreign_conditions, home_price, foreign_price, freight, terms,
                previous, lift_in, lift_out)
            flow = outcome.flow_tonnes
            unmet[(commodity, civilization_id)] = 0.0
            if flow and abs(flow) >= (lift_in if flow > 0.0 else lift_out) * (1.0 - 1e-9):
                wanted = trader_response.clear_with_traders(
                    home_conditions, foreign_conditions, home_price, foreign_price, freight,
                    terms, previous)
                unmet[(commodity, civilization_id)] = abs(wanted.flow_tonnes) - abs(flow)
            home_conditions = outcome.home_conditions
            flows.append((civilization_id, flow, outcome.foreign))
        return home_conditions, flows

    def home_makes_commodity(self, commodity, flows):
        """Whether this society can make the commodity, as the partners in this year's trade see it;
        true when none trade. A good only a partner makes gets no home capacity from its price."""
        for civilization_id, _flow, _outcome in flows:
            return self._foreign_sides(commodity, self._foreign_economy_facts(civilization_id))[0]
        return True

    def foreign_trade_year_end(self, commodity, home_entry, flows):
        """Close the year abroad: each partner's capacity follows its price,
        its unsold goods carry on, the year's flow is paid for in coin and
        counted against the route's lift, and the flow is recorded."""
        home_entry["trade_tonnes"] = sum(flow for _id, flow, _outcome in flows)
        unmet = self.household.__dict__.get("_foreign_unmet_tonnes", {})
        for civilization_id, flow, outcome in flows:
            entry = self.state.economy.foreign_market_book[civilization_id][commodity]
            entry["capacity_tonnes"] = market.adjusted_capacity(
                entry["capacity_tonnes"], outcome.price_ratio)
            entry["stock_tonnes"] = market.stock_after_year(outcome)
            entry["price_ratio"] = outcome.price_ratio
            entry["trade_tonnes"] = -flow
            facts = self._foreign_economy_facts(civilization_id)
            if flow:
                self._pay_for_flow(civilization_id, commodity, flow, home_entry, outcome, facts)
            shortfall = unmet.get((commodity, civilization_id), 0.0)
            if flow or shortfall:
                self._record_lift(civilization_id, facts["route"], flow, shortfall,
                                  self._flow_capital_tied(civilization_id, commodity, flow, home_entry, outcome, facts))

    def _flow_value(self, civilization_id, commodity, flow, home_entry, foreign_outcome, facts):
        """Home money value of a flow at the price of the side that ships it; None when the good
        has no price pair."""
        pair = self._foreign_price_pair(commodity, facts)
        if pair is None:
            return None
        home_price, foreign_price = pair
        if flow > 0.0:
            return flow * foreign_price * self.partner_price_level(civilization_id) \
                * foreign_outcome.price_ratio
        return -flow * home_price * self.home_price_level() * home_entry.get("price_ratio", 1.0)

    def _pay_for_flow(self, civilization_id, commodity, flow, home_entry, foreign_outcome, facts):
        """Settle a commodity's flow in coin at the price of the side that ships it."""
        value = self._flow_value(civilization_id, commodity, flow, home_entry, foreign_outcome, facts)
        if value is None:
            return
        coin = load_civ(civilization_id)["coin_standard"]
        coin_price = self._material_prices().get(coin["material"])
        if coin_price:
            self._settle_flow(civilization_id, flow, value, coin["kg_per_unit"] * coin_price)

    def foreign_route_legs(self, civilization_id):
        """The legs goods travel from a partner's regions to this society's:
        [(from region, to region, mode, km, home money per tonne)]."""
        route = self._foreign_economy_facts(civilization_id)["route"]
        return [] if route is None else [
            (leg.origin, leg.destination, leg.mode, leg.distance_km, leg.cost_per_tonne)
            for leg in route.legs]

    def foreign_trade_summary(self):
        """Tonnes imported and exported over every commodity in the last year
        closed."""
        imports = exports = 0.0
        for entry in self.state.economy.market_book.values():
            flow = entry.get("trade_tonnes", 0.0)
            imports += max(0.0, flow)
            exports += max(0.0, -flow)
        return {"imports_tonnes": imports, "exports_tonnes": exports}
