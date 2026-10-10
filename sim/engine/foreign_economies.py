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

from .data import calculated_goods_prices, goods_provenance, load_civ, starting_schedule
from .foreign_economy_data import foreign_economy_document
from .foreign_actor_trade import ForeignActorTradeMixin
from .trader_cargo import TraderCargoMixin
from .foreign_capacity import ForeignCapacityMixin
from .foreign_payments import ForeignPaymentsMixin
from .foreign_routes import ForeignRoutesMixin
from .foreign_traders import ForeignTradersMixin

@functools.lru_cache(maxsize=None)
def foreign_economy_records():
    """The economies the data file names, with installed mods applied."""
    return tuple(foreign_economy_document()["economies"])


@functools.lru_cache(maxsize=None)
def not_traded_materials():
    """Materials that cannot cross a border, from the data file."""
    return frozenset(foreign_economy_document()["not_traded_materials"])


@functools.lru_cache(maxsize=None)
def exports_refused(civilization_id):
    """Materials this partner will not sell abroad: its own `will_not_sell` data. A transitional
    field; a state actor's export policy would replace it."""
    return frozenset(load_civ(civilization_id).get("will_not_sell") or ())


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
                            ForeignTradersMixin, ForeignActorTradeMixin, TraderCargoMixin):

    def partner_countries(self):
        """Every economy enabled for this year, sorted by id: those trading by the legacy partner books and
        those that are part of the agent economy."""
        year = self.state.scenario.year
        own = self.civ.get("id")
        return sorted(record["civilization"] for record in foreign_economy_records()
                      if record.get("enabled", False) and record["civilization"] != own
                      and record["from_year"] <= year <= record["until_year"])

    def partners_in_agent_economy(self):
        """The enabled economies whose tiles, people and producers are in the agent economy itself."""
        inside = {record["civilization"] for record in foreign_economy_records() if record.get("agent_economy", False)}
        return [partner for partner in self.partner_countries() if partner in inside]

    def foreign_economies(self):
        """Economies trading with this society this year by the partner books, sorted by id: the enabled ones
        that are not themselves in the agent economy."""
        inside = set(self.partners_in_agent_economy())
        return [partner for partner in self.partner_countries() if partner not in inside]

    def partner_refusal(self, civilization_id, material):
        """Why the partner will not sell the material, else None."""
        gate = self.partner_gate_refusal(civilization_id)
        if gate:
            return gate
        if material in exports_refused(civilization_id):
            return "%s will not sell %s" % (load_civ(civilization_id).get("name", civilization_id), material)
        return None

    def _foreign_economy_facts(self, civilization_id):
        """Population, route and prices of one foreign economy in home money,
        remembered until the home price table changes or the year turns (freight follows last year's
        flows, the market rate and wages). A partner is named by
        id in the foreign-economies data, so it is looked up by id; the home
        society is always `self.civ`."""
        prices = self._material_prices()
        cache = getattr(self.household, "_foreign_facts_cache", None)
        if cache is None:
            cache = self.household._foreign_facts_cache = {}
        cached = cache.get(civilization_id)
        known_techs = (len(self.state.projects.done), self.state.scenario.year)
        if cached is not None and cached[0] is prices and cached[2] == known_techs:
            return cached[1]
        civilization = load_civ(civilization_id)
        coin = civilization["coin_standard"]
        coin_price = self._coin_metal_price(coin["material"])
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
                         civilization_id=self.civ.get("id"),
                         civilization=self.civ).items() if source == "solved"),
                 "population": float(civilization.get("population") or 0.0),
                 "prices_in_home_money": foreign_prices,
                 "route": route,
                 "freight_per_tonne": self._route_freight_per_tonne(civilization)}
        cache[civilization_id] = (prices, facts, known_techs)
        return facts

    def _commodity_materials(self, commodity):
        """Material keys that count as the commodity: the commodity's own
        name, the ledger's grouping and every material the engine files under it that has a seller
        in reach. Remembered until the offers change."""
        prices = self.goods_market.household_prices()
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
