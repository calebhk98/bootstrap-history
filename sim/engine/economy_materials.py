"""What the price and market topics still read through `Sim` from the old raw-material supply: the commodity catalogue and the
material-to-commodity map, the price lookups, the memos for answers that hold while the techniques held and the producers do
not change, and the founder's trade at the goods market.

The supply, demand, throttle, electricity and project bills are the materials module's (sim/materials/); what remains here
goes with the prices module and the markets module. The catalogue and its map are kept on the class, not the game: the file
does not change mid-run and loading it involves a JSON load. The class name in each cache access MUST match the class that
holds the method: a stale name fails silently, surfacing only when a command first needs the catalogue."""
from . import commodities as _commod


class MaterialSupplyMixin:

    def _commodity_ledger(self):
        """The curated commodities from commodities.json, as a CommodityLedger, cached on the class."""
        cached = getattr(MaterialSupplyMixin, "_commod_ledger_cache", None)
        if cached is None:
            cached = MaterialSupplyMixin._commod_ledger_cache = _commod.CommodityLedger()
        return cached

    def _material_commodity_map(self):
        """material key -> curated commodity id, from commodities.json's own material_keys lists. Cached on the class."""
        cached = getattr(MaterialSupplyMixin, "_material_commod_map_cache", None)
        if cached is None:
            cached = {}
            for commodity_id, commodity in sorted(self._commodity_ledger().commodities.items()):
                for material_key in commodity.get("material_keys", []):
                    cached[material_key] = commodity_id
            MaterialSupplyMixin._material_commod_map_cache = cached
        return cached

    def _done_memo(self, name, key, compute):
        """`compute()` remembered per (name, key) while the done set, the techniques in use and the economy's
        producers (they change as its year closes) are unchanged; for answers that depend only on what is
        built and run."""
        projects = self.state.projects
        stamp = (self.price_epoch(), len(projects.done), self.economy.producers_stamp())
        memo = getattr(self, "_done_memo_store", None)
        if memo is None or memo[0] != stamp or memo[1] is not projects.done:
            memo = self._done_memo_store = (stamp, projects.done, {})
        table = memo[2]
        entry = (name, key)
        if entry not in table:
            table[entry] = compute()
        return table[entry]

    def _producers_memo(self, name, key, compute):
        """`compute()` remembered per (name, key) while the economy's producers are unchanged (they change only
        as its year closes); for answers that read nothing but the producers. An answer of None is not kept."""
        stamp = self.economy.producers_stamp()
        memo = getattr(self, "_producers_memo_store", None)
        if memo is None or memo[0] != stamp:
            memo = self._producers_memo_store = (stamp, {})
        entry = (name, key)
        if entry not in memo[1]:
            answer = compute()
            if answer is None:      # not yet known (the economy is opening): ask again
                return None
            memo[1][entry] = answer
        return memo[1][entry]

    def _priced_key(self, tag, prices):
        """The key of `prices` that prices a raw material key (for example aluminium_kg) or a curated commodity id
        (the material its `price_material` names). None if `prices` cannot price it."""
        if tag in prices:
            return tag
        commodity = self._commodity_ledger().commodities.get(tag)
        if commodity and prices.get(commodity.get("price_material")):
            return commodity["price_material"]
        return None

    def _material_price_per_kg(self, tag):
        """Money per kg in this civilisation's coin that it costs to make a raw material key or a curated
        commodity id, from the calculator-backed table. None if this file cannot price it at all. This is a
        cost; what a buyer pays is `GoodsMarket.unit_price`."""
        prices = self._material_prices()
        key = self._priced_key(tag, prices)
        return None if key is None else prices[key]

    def material_trade_quote(self, material):
        """Current buy/sell quote for one tonne of a material commodity."""
        return self.goods_market.quote(material)

    def buy_material_stock(self, material, tonnes):
        """The founder buys a material at the market (see GoodsMarket.buy)."""
        return self.goods_market.buy(self.goods_market.acting, material, tonnes)

    def sell_material_stock(self, material, tonnes):
        """The founder sells stock at the market (see GoodsMarket.sell)."""
        return self.goods_market.sell(self.goods_market.acting, material, tonnes)

    def material_purchase_cost(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as the order is filled. None
        when it has no price (see GoodsMarket.quote_buy)."""
        return self.goods_market.quote_buy(material, tonnes, already)
