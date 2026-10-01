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
import functools
import json
import os

from sim.constants import declare
from sim.world import market, trade_between

from .data import (ROOT, calculated_goods_prices, goods_provenance, haversine_km, load_civ,
                   starting_schedule)
from .project_materials import tonnes_per_unit

FOREIGN_CAPACITY_PER_HEAD_OF_HOME = declare(
    "FOREIGN_CAPACITY_PER_HEAD_OF_HOME", 1.0, kind="temporary_heuristic",
    unit="foreign output per head over the home society's output per head",
    source=None, confidence="D",
    why="A foreign economy's capacity for a commodity it can price is the "
        "home society's, scaled by population: its mines and workshops are "
        "not yet read from its own regions' geology (Complaints/113). The "
        "foreign household demand at the opening equals that capacity, so "
        "its market opens in balance.")

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


class ForeignEconomiesMixin:

    def foreign_economies(self):
        """Economies trading with this society this year, sorted by id."""
        year = self.state.scenario.year
        own = self.civ.get("id")
        return sorted(record["civilization"] for record in foreign_economy_records()
                      if record["civilization"] != own
                      and record["from_year"] <= year <= record["until_year"])

    def _foreign_economy_facts(self, civilization_id):
        """Population, route and prices of one foreign economy in home money,
        remembered until the home price table changes."""
        prices = self._material_prices()
        cache = getattr(self.household, "_foreign_facts_cache", None)
        if cache is None:
            cache = self.household._foreign_facts_cache = {}
        cached = cache.get(civilization_id)
        if cached is not None and cached[0] is prices:
            return cached[1]
        civilization = load_civ(civilization_id)
        coin = civilization["coin_standard"]
        coin_price = prices.get(coin["material"])
        foreign_prices = {}
        if coin_price:
            home_money_per_coin = coin["kg_per_unit"] * coin_price
            foreign_prices = {material: price * home_money_per_coin for material, price
                              in _foreign_prices_in_own_coin(civilization_id).items()}
        facts = {"solved_materials": _foreign_solved_materials(civilization_id),
                 "home_solved_materials": frozenset(
                     material for material, source in goods_provenance(
                         frozenset(self.state.projects.done),
                         civilization_id=self.civ.get("id")).items() if source == "solved"),
                 "population": float(civilization.get("population") or 0.0),
                 "prices_in_home_money": foreign_prices,
                 "freight_per_tonne": self._route_freight_per_tonne(civilization)}
        cache[civilization_id] = (prices, facts)
        return facts

    def _route_freight_per_tonne(self, civilization):
        """Home money to haul a tonne from the foreign economy's home regions
        to this society's: great-circle distance, scaled by the routes'
        difficulty, at the land freight cost per tonne-km."""
        regions = [self._regions[region_id] for region_id in civilization.get("home_regions") or []
                   if region_id in self._regions]
        if not regions:
            return float("inf")
        latitude = sum(region["lat"] for region in regions) / len(regions)
        longitude = sum(region["lon"] for region in regions) / len(regions)
        distance_km = haversine_km(*self._home_centroid, latitude, longitude)
        own = [self._regions[region_id] for region_id in self.civ.get("home_regions") or []
               if region_id in self._regions]
        difficulty = [region.get("route_difficulty", 1.0) for region in regions + own]
        inputs = self._land_freight_physical_inputs()
        feed_price = self._material_price_per_kg(self.FREIGHT_FEED_PRICE_MATERIAL) or 0.0
        per_tonne_km = (inputs.feed_kg_per_tonne_km * feed_price
                        + inputs.driver_hours_per_tonne_km
                        * self.wage_per_hour(self.FREIGHT_DRIVER_WAGE_TRADE))
        return per_tonne_km * distance_km * (sum(difficulty) / len(difficulty))

    def _foreign_price_pair(self, commodity, facts):
        """(home, foreign) long-run price per tonne of a commodity in home
        money, from the first material of it both economies can make and may sell
        across a border; None when there is none."""
        home_prices = self._material_prices()
        foreign_prices = facts["prices_in_home_money"]
        keys = [commodity] + sorted(self._commodity_ledger().commodities.get(
            commodity, {}).get("material_keys", []))
        for key in keys:
            if (key in home_prices and key in foreign_prices
                    and key in facts["solved_materials"] and key in facts["home_solved_materials"]
                    and key not in not_traded_materials()):
                per_tonne = 1.0 / tonnes_per_unit(key)
                return home_prices[key] * per_tonne, foreign_prices[key] * per_tonne
        return None

    def _foreign_entry(self, civilization_id, commodity, home_entry, facts):
        """The foreign economy's book entry for a commodity, opened at the
        home society's reference output scaled by population."""
        book = self.state.economy.foreign_market_book.setdefault(civilization_id, {})
        entry = book.get(commodity)
        if entry is None:
            scale = (FOREIGN_CAPACITY_PER_HEAD_OF_HOME * facts["population"]
                     / self._opening_population())
            reference = home_entry["reference_tonnes"] * scale
            entry = book[commodity] = {
                "reference_tonnes": reference, "capacity_tonnes": reference,
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
        the foreign economy's outcome)]. Nearest partner first."""
        partners = []
        for civilization_id in self.foreign_economies():
            facts = self._foreign_economy_facts(civilization_id)
            pair = self._foreign_price_pair(commodity, facts)
            if pair is not None:
                partners.append((facts["freight_per_tonne"], civilization_id, facts, pair))
        flows = []
        for freight, civilization_id, facts, (home_price, foreign_price) in sorted(
                partners, key=lambda partner: partner[:2]):
            entry = self._foreign_entry(civilization_id, commodity, home_entry, facts)
            outcome = trade_between.clear_trading_markets(
                home_conditions, self._foreign_conditions(entry, home_conditions),
                home_price, foreign_price, freight)
            home_conditions = outcome.home_conditions
            flows.append((civilization_id, outcome.flow_tonnes, outcome.foreign))
        return home_conditions, flows

    def foreign_trade_year_end(self, commodity, home_entry, flows):
        """Close the year abroad: each partner's capacity follows its price,
        its unsold goods carry on, and the year's flow is recorded."""
        home_entry["trade_tonnes"] = sum(flow for _id, flow, _outcome in flows)
        for civilization_id, flow, outcome in flows:
            entry = self.state.economy.foreign_market_book[civilization_id][commodity]
            entry["capacity_tonnes"] = market.adjusted_capacity(
                entry["capacity_tonnes"], outcome.price_ratio)
            entry["stock_tonnes"] = market.stock_after_year(outcome)
            entry["price_ratio"] = outcome.price_ratio
            entry["trade_tonnes"] = -flow

    def foreign_trade_summary(self):
        """Tonnes imported and exported over every commodity in the last year
        closed."""
        imports = exports = 0.0
        for entry in self.state.economy.market_book.values():
            flow = entry.get("trade_tonnes", 0.0)
            imports += max(0.0, flow)
            exports += max(0.0, -flow)
        return {"imports_tonnes": imports, "exports_tonnes": exports}
