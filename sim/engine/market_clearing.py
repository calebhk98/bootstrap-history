"""The society's yearly market for materials, as the engine sees it.

Each commodity has a book entry: the society's producing capacity, stock held
over, and the capacity it started with. The year's price ratio (spot price
over the long-run cost the solver gives) comes from `sim/world/market.py`,
clearing that capacity, the actors' output, stock and what the founder has
sold this year against household demand (population and income, see
market_demand.py) and what the founder has bought or drawn. Quotes and
purchase bills multiply their long-run price by this ratio; the long-run
price itself is untouched and stays the anchor.

The founder's own workings enter as a net: output the founder uses himself
never reaches the market, so only what he buys, draws beyond his stock, and
sells does. Selling adds supply and takes sales from the society's producers.
At the turn of the year capacity follows the price and unsold goods carry on.
"""
from sim.world import market


class MarketClearingMixin:

    def actor_supply(self, material):
        """Tonnes a year every actor other than the society's own producers
        and the founder brings to market for `material`: firms, states,
        other players. One call, summed over all actors; zero until actors
        produce goods."""
        # TEMPORARY HEURISTIC: no actor produces material goods yet.
        return 0.0

    # ---- the year's flows ---------------------------------------------------

    def _market_flows(self):
        economy = self.state.economy
        year = self.state.scenario.year
        flows = economy.market_flows
        if not flows or flows.get("year") != year:
            flows = economy.market_flows = {"year": year, "bought": {}, "sold": {}, "drawn": {}}
        return flows

    def market_note_purchase(self, commodity, tonnes):
        """The founder bought `tonnes` of a commodity at the market this year."""
        if tonnes > 0:
            bought = self._market_flows()["bought"]
            bought[commodity] = bought.get(commodity, 0.0) + tonnes

    def market_note_sale(self, commodity, tonnes):
        """The founder sold `tonnes` of a commodity into the market this year."""
        if tonnes > 0:
            sold = self._market_flows()["sold"]
            sold[commodity] = sold.get(commodity, 0.0) + tonnes

    def market_reset_draws(self):
        """Start a fresh count of what running works draw from the market."""
        self._market_flows()["drawn"] = {}

    def market_note_draw(self, commodity, tonnes):
        """Running works used `tonnes` the founder neither held nor made."""
        if tonnes > 0:
            drawn = self._market_flows()["drawn"]
            drawn[commodity] = drawn.get(commodity, 0.0) + tonnes

    # ---- the book -----------------------------------------------------------

    def _market_entry(self, commodity):
        """The commodity's book entry, opened at the society's present output
        on first use; None for a commodity nothing produces."""
        book = self.state.economy.market_book
        entry = book.get(commodity)
        if entry is None:
            output = self._society_output_tonnes(commodity)
            if not output > 0.0:
                return None
            entry = book[commodity] = {
                "reference_tonnes": output, "capacity_tonnes": output,
                "stock_tonnes": 0.0, "price_ratio": 1.0,
                "society_sales_tonnes": output}
        return entry

    def market_add_stock(self, material, tonnes):
        """Goods appear in the society's hands (a windfall, a confiscation
        sold on): they join this year's supply."""
        entry = self._market_entry(self._material_tag(material)[0])
        if entry is not None and tonnes > 0:
            entry["stock_tonnes"] += tonnes

    def _market_conditions(self, commodity, entry):
        flows = self._market_flows()
        record = self._commodity_ledger().commodities.get(commodity) or {}
        return market.MarketConditions(
            household_demand_at_anchor_tonnes=(
                entry["reference_tonnes"] * self.household_demand_ratio(commodity)),
            committed_demand_tonnes=(flows["bought"].get(commodity, 0.0)
                                     + flows["drawn"].get(commodity, 0.0)),
            society_capacity_tonnes=entry["capacity_tonnes"],
            actor_supply_tonnes=self.actor_supply(commodity),
            founder_sales_tonnes=flows["sold"].get(commodity, 0.0),
            stock_tonnes=entry["stock_tonnes"],
            floor_ratio=float(record.get("price_floor_factor", market.DEFAULT_FLOOR_RATIO)),
            ceiling_ratio=float(record.get("price_ceiling_factor", market.DEFAULT_CEILING_RATIO)))

    def _market_outcome(self, commodity):
        """(conditions, outcome) for this year so far, or None; cached until
        something it depends on changes."""
        entry = self._market_entry(commodity)
        if entry is None:
            return None
        economy = self.state.economy
        flows = self._market_flows()
        signature = (self.population.total, economy.economy, id(self._material_prices()),
                     entry["capacity_tonnes"], entry["stock_tonnes"],
                     flows["bought"].get(commodity), flows["drawn"].get(commodity),
                     flows["sold"].get(commodity), flows["year"], self.actor_supply(commodity))
        cache = getattr(self.household, "_market_outcome_cache", None)
        if cache is None:
            cache = self.household._market_outcome_cache = {}
        cached = cache.get(commodity)
        if cached is not None and cached[0] == signature:
            return cached[1]
        conditions = self._market_conditions(commodity, entry)
        result = (conditions, market.clear_market(conditions))
        cache[commodity] = (signature, result)
        return result

    # ---- what callers read --------------------------------------------------

    def market_price_ratio(self, material):
        """This year's spot price over the long-run cost for a material;
        one where no society market exists for it."""
        result = self._market_outcome(self._material_tag(material)[0])
        return 1.0 if result is None else result[1].price_ratio

    def market_state(self, material):
        """The market for one material as of now, for reports and tests."""
        commodity = self._material_tag(material)[0]
        result = self._market_outcome(commodity)
        if result is None:
            return None
        conditions, outcome = result
        entry = self._market_entry(commodity)
        return {
            "material": commodity,
            "price_ratio": outcome.price_ratio,
            "floor_ratio": conditions.floor_ratio,
            "ceiling_ratio": conditions.ceiling_ratio,
            "capacity_tonnes": entry["capacity_tonnes"],
            "reference_capacity_tonnes": entry["reference_tonnes"],
            "stock_tonnes": entry["stock_tonnes"],
            "household_demand_tonnes_at_anchor": conditions.household_demand_at_anchor_tonnes,
            "founder_purchases_tonnes": conditions.committed_demand_tonnes,
            "founder_sales_tonnes": conditions.founder_sales_tonnes,
            "actor_supply_tonnes": conditions.actor_supply_tonnes,
            "society_sales_tonnes": outcome.society_sales_tonnes,
            "displaced_by_founder_tonnes":
                market.society_sales_displaced_by_founder(conditions),
            "unsold_tonnes": outcome.unsold_tonnes,
            "unmet_demand_tonnes": outcome.unmet_demand_tonnes,
        }

    # ---- the turn of the year -----------------------------------------------

    def _open_market_book(self):
        """An entry for every commodity the price table names, so each one's
        capacity follows its price from the first year."""
        for material in sorted(self._material_prices()):
            self._market_entry(self._material_tag(material)[0])

    def _step_market(self):
        """Close the year: capacity follows the price, unsold goods carry on."""
        self._open_market_book()
        book = self.state.economy.market_book
        for commodity in sorted(book):
            entry = book[commodity]
            conditions = self._market_conditions(commodity, entry)
            outcome = market.clear_market(conditions)
            entry["capacity_tonnes"] = market.adjusted_capacity(
                entry["capacity_tonnes"], outcome.price_ratio)
            entry["stock_tonnes"] = market.stock_after_year(outcome)
            entry["price_ratio"] = outcome.price_ratio
            entry["society_sales_tonnes"] = outcome.society_sales_tonnes
