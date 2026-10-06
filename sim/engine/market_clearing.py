"""The society's yearly market for materials, as the engine sees it.

Each commodity has a book entry: the society's producing capacity, stock held
over, and the capacity it started with. The year's posted price ratio (spot
price over the incumbents' cost, incumbent_prices.py) comes from `sim/world/market.py`,
clearing that capacity, the stock, the producers' offers (each at its own cost, from
the entry it runs; producer_costs.py) and the actors' output against household demand
(population and income, see market_demand.py). Quotes and purchase bills
multiply the incumbents' price by this ratio.

Everyone who buys or sells goes through `Sim.goods_market` (goods_market_api.py),
which writes the year's flows by party. The founder's own workings enter as a
net: output the founder uses himself never reaches the market, so only what he
buys, draws beyond his stock, and sells does. What a firm or the state buys or
sells is the same kind of entry. Flows are counted through the year and enter
the clearing when it closes: selling adds supply and takes sales from the
society's producers, buying adds demand, and capacity follows the resulting
price while unsold goods carry on, so next year's posted price carries them.
Within the year the founder's own orders keep the marginal price curves that
already move a bill as it is filled (material_price_factor), which is why the
posted price leaves out the founder's flows and counts everyone else's.
`market_state` shows the year's clearing so far.
"""
from sim.world import market

from .goods_market_api import FOUNDER, GoodsMarket


class MarketClearingMixin:

    # ---- the year's flows ---------------------------------------------------

    def _market_flows(self):
        """{"year", "bought": {commodity: {party: tonnes}}, "sold": {commodity: {party: tonnes}},
        "drawn": {commodity: tonnes}}, written by `goods_market`. When the year turns the founder's
        flows and draws start again from nothing; every other party's entries stand until it deals
        again (`GoodsMarket.forget`), as a firm's output and the state's purchases are standing orders."""
        economy = self.state.economy
        year = self.state.scenario.year
        flows = economy.market_flows
        if not flows or flows.get("year") != year:
            previous = flows or {}
            flows = economy.market_flows = {"year": year, "drawn": {}}
            for kind in ("bought", "sold", "reservation"):
                standing = {commodity: {party: tonnes for party, tonnes in parties.items() if party != FOUNDER}
                            for commodity, parties in (previous.get(kind) or {}).items()}
                flows[kind] = {commodity: parties for commodity, parties in standing.items() if parties}
        return flows

    @property
    def goods_market(self):
        """The one goods market every buyer and seller asks."""
        market_api = self.__dict__.get("_goods_market")
        if market_api is None:
            market_api = self._goods_market = GoodsMarket(self)
        return market_api

    # ---- the book -----------------------------------------------------------

    def _market_entry(self, commodity):
        """The commodity's book entry, opened at the society's present output
        on first use; None for a commodity nothing produces or nothing offers."""
        book = self.state.economy.market_book
        entry = book.get(commodity)
        if entry is None:
            output = self._society_output_tonnes(commodity)
            if not output > 0.0 or self.goods_market.commodity_is_unsourced(commodity):
                return None
            entry = book[commodity] = {
                "reference_tonnes": output, "capacity_tonnes": output,
                "stock_tonnes": 0.0, "price_ratio": 1.0,
                "society_sales_tonnes": output, "traded_tonnes": output}
        return entry

    def _market_flow_figures(self, commodity, with_flows):
        """(committed demand, founder sales, supply of sellers who take any price, actors' demand, offers
        of producers who name their cost) from this year's flows and the concerns running. The founder's
        own orders count only `with_flows`; every other party's always do."""
        market_api = self.goods_market
        committed = founder_sales = 0.0
        if with_flows:
            committed = (market_api.bought_tonnes(commodity, FOUNDER)
                         + market_api.drawn_tonnes(commodity))
            founder_sales = market_api.sold_tonnes(commodity, FOUNDER)
        offers = market_api.others_offers(commodity)
        price_takers = market_api.others_sold_tonnes(commodity) - sum(offer.tonnes for offer in offers)
        return (committed, founder_sales, max(0.0, price_takers), market_api.others_bought_tonnes(commodity),
                offers + self.founder_concern_offers(commodity))

    def _market_conditions(self, commodity, entry, with_flows):
        committed, founder_sales, actor_supply, actor_demand, offers = self._market_flow_figures(
            commodity, with_flows)
        record = self._commodity_ledger().commodities.get(commodity) or {}
        return market.MarketConditions(
            household_demand_at_anchor_tonnes=(
                entry["reference_tonnes"] * self.household_demand_ratio(commodity)),
            committed_demand_tonnes=committed,
            society_capacity_tonnes=entry["capacity_tonnes"],
            actor_supply_tonnes=actor_supply,
            actor_demand_tonnes=actor_demand, offers=offers,
            founder_sales_tonnes=founder_sales,
            stock_tonnes=entry["stock_tonnes"],
            floor_ratio=float(record.get("price_floor_factor", market.DEFAULT_FLOOR_RATIO)),
            ceiling_ratio=float(record.get("price_ceiling_factor", market.DEFAULT_CEILING_RATIO)))

    def _market_outcome(self, commodity, with_flows=False):
        """(conditions, outcome) of the clearing, or None for a commodity
        nothing produces. Without `with_flows` it is the posted price (the
        founder's trades this year left out); with them, the year as it would
        close now. Cached until something it depends on changes."""
        entry = self._market_entry(commodity)
        if entry is None:
            return None
        signature = (self.population.total,
                     entry["capacity_tonnes"], entry["stock_tonnes"],
                     self._market_flow_figures(commodity, with_flows),
                     self.actor_market_version(), self.state.scenario.year,
                     tuple(self.foreign_economies()), self.actor_trade_signature())
        cache = getattr(self.household, "_market_outcome_cache", None)
        if cache is None:
            cache = self.household._market_outcome_cache = {}
        prices = self._material_prices()
        cached = cache.get((commodity, with_flows))
        if cached is not None and cached[0] == signature and cached[2] is prices:
            return cached[1]
        conditions, trade_flows = self.foreign_trade(
            commodity, entry, self._market_conditions(commodity, entry, with_flows))
        result = (conditions, market.clear_market(conditions))
        cache[(commodity, with_flows)] = (signature, result, prices)
        self.household._trade_tonnes_cache = getattr(self.household, "_trade_tonnes_cache", {})
        self.household._trade_tonnes_cache[(commodity, with_flows)] = sum(
            flow for _id, flow, _outcome in trade_flows)
        return result

    # ---- what callers read --------------------------------------------------

    def market_price_ratio(self, material):
        """This year's posted spot price over the long-run cost for a
        material; one where no society market exists for it. On the agent economy, its price over the
        same cost."""
        commodity = self._material_tag(material)[0]
        ratio = self.economy.agent_price_ratio([material] + self.economy.materials_in(commodity))
        if ratio is not None:
            return ratio
        result = self._market_outcome(commodity)
        return 1.0 if result is None else result[1].price_ratio

    def market_state(self, material):
        """The market for one material as of now, for reports and tests."""
        commodity = self._material_tag(material)[0]
        result = self._market_outcome(commodity)
        if result is None:
            return None
        conditions, outcome = result
        entry = self._market_entry(commodity)
        closing_conditions, closing = self._market_outcome(commodity, with_flows=True)
        return {
            "material": commodity,
            "price_ratio": outcome.price_ratio,
            "price_ratio_if_year_closed_now": closing.price_ratio,
            "floor_ratio": conditions.floor_ratio,
            "ceiling_ratio": conditions.ceiling_ratio,
            "capacity_tonnes": entry["capacity_tonnes"],
            "reference_capacity_tonnes": entry["reference_tonnes"],
            "stock_tonnes": entry["stock_tonnes"],
            "household_demand_tonnes_at_anchor": conditions.household_demand_at_anchor_tonnes,
            "founder_purchases_tonnes": (self.goods_market.bought_tonnes(commodity, FOUNDER)
                                        + self.goods_market.drawn_tonnes(commodity)),
            "founder_sales_tonnes": closing_conditions.founder_sales_tonnes,
            "actor_supply_tonnes": conditions.actor_supply_tonnes + sum(
                offer.tonnes for offer in self.goods_market.others_offers(commodity)),
            "actor_demand_tonnes": conditions.actor_demand_tonnes,
            "society_sales_tonnes": closing.society_sales_tonnes,
            "displaced_by_founder_tonnes":
                market.society_sales_displaced_by_founder(closing_conditions),
            "unsold_tonnes": closing.unsold_tonnes,
            "unmet_demand_tonnes": closing.unmet_demand_tonnes,
            "trade_tonnes": self.household._trade_tonnes_cache[(commodity, True)],
        }

    # ---- the turn of the year -----------------------------------------------

    def _open_market_book(self):
        """An entry for every commodity the price table names, so each one's
        capacity follows its price from the first year."""
        for material in sorted(self._material_prices()):
            self._market_entry(self._material_tag(material)[0])

    def _step_market(self):
        """Close the year: capacity follows the price, unsold goods carry on. Every commodity clears at the
        price level the year opened with; the coin the year's trade moves counts from the next year."""
        self._open_market_book()
        if self.economy.run_agent_year():
            self.close_partner_books()
            self._close_real_output()
            return
        self._price_level_held = self.home_price_level()
        try:
            self._close_commodities()
        finally:
            self._price_level_held = None
        self.close_partner_books(cargo_only=True)
        self.foreign_fleet_year_end()
        self._close_real_output()

    def _close_commodities(self):
        book = self.state.economy.market_book
        for commodity in sorted(book):
            entry = book[commodity]
            conditions, trade_flows = self.foreign_trade(
                commodity, entry, self._market_conditions(commodity, entry, True))
            outcome = market.clear_market(conditions)
            self.foreign_trade_year_end(commodity, entry, trade_flows)
            if self.home_makes_commodity(commodity, trade_flows):
                entry["capacity_tonnes"] = market.adjusted_capacity(
                    entry["capacity_tonnes"], outcome.price_ratio)
            entry["stock_tonnes"] = market.stock_after_year(outcome)
            entry["price_ratio"] = outcome.price_ratio
            entry["society_sales_tonnes"] = outcome.society_sales_tonnes
            entry["traded_tonnes"] = outcome.quantity_traded_tonnes
            wanted = outcome.quantity_traded_tonnes + outcome.unmet_demand_tonnes
            entry["cleared_share"] = outcome.quantity_traded_tonnes / wanted if wanted > 0.0 else 1.0
