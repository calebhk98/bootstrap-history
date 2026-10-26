"""The price tables: the incumbents' cost of making every good, in labour hours and in the home coin.

The incumbents are the producers the society started with, running the techniques it started with. Their unit cost,
in labour hours, is each good's reference; the price a good clears at comes from the market, where every producer offers
at its own cost. A technology that is held, or run by one producer, does not move this reference.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): a good no incumbent makes but some producer runs a technique for has no incumbent
cost, so its reference is the solver's cost under every technique now run (the cheapest route among them) until a
producer's own cost can anchor it. A good no one in reach makes has no cost here and no price.
retire: ONE_PRICE_OWNER_PLAN.md stage 5.

Money is the labour hour times what an hour is worth, which follows the one coin stock, so every price here, traded or
not, moves with money against goods."""
from typing import Any, Dict, Optional, Tuple

from . import engine_seam, rules
from . import prices as price_solver


class Tables:

    def banded_market_rate(self) -> float:
        """The live market rate, banded: the rate the solver charges plants and stock. Asking the market for its rate may
        itself need these prices, in which case the starting rate answers (the module's own re-entry guard)."""
        starting = float(self.needs.civilisation()["starting_interest_rate"])
        if self._reading_market_rate:
            return starting
        self._reading_market_rate = True
        try:
            return price_solver.band_interest_rate(self.needs.market_rate(), starting)
        finally:
            self._reading_market_rate = False

    def price_tables(self) -> Tuple[Dict[str, float], Dict[str, str]]:
        """(labour-hour price of each good, provenance of each), for the incumbents' techniques plus the baseline for
        goods only a producer's own technique reaches."""
        granted_now = self.needs.techniques_granted()
        in_use = self.needs.techniques_in_use()
        farmed = price_solver.band_farmed_hectares(self.needs.farm_land_hectares())
        rate = self.banded_market_rate()
        cached = self._price_tables_cache
        if (cached is not None and cached[0] is granted_now and cached[1] is in_use
                and cached[3] == len(granted_now) and cached[4] == (farmed, rate)):
            return cached[2]
        granted = frozenset(granted_now)
        civ = self.needs.civilisation()
        civilisation = dict(civilization_id=civ.get("id"), civilization=civ, farmed_hectares=farmed, interest_rate=rate)
        incumbent = self._incumbent_table_cache
        if incumbent is None or incumbent[0] != (granted, farmed, rate):
            incumbent = self._incumbent_table_cache = (
                (granted, farmed, rate), *engine_seam.calculated_goods_table(granted, **civilisation))
        hours, basis = incumbent[1], incumbent[2]
        if in_use != granted:
            run_hours, run_basis = engine_seam.calculated_goods_table(in_use, **civilisation)
            tables = rules.merge_by_reach(hours, basis, run_hours, run_basis)
        else:
            tables = (dict(hours), dict(basis))
        self._price_tables_cache = (granted_now, in_use, tables, len(granted_now), (farmed, rate))
        return tables

    def material_prices(self) -> Dict[str, float]:
        """{material: money per unit}: the incumbents' cost of making in this coin. What a buyer pays is the economy's
        price."""
        hours = self.price_tables()[0]
        per_hour = self.needs.money_per_labour_hour()
        cached = self._material_prices_cache
        if cached is not None and cached[0] is hours and cached[1] == per_hour:
            return cached[2]
        prices = rules.money_prices(hours, per_hour)
        self._material_prices_cache = (hours, per_hour, prices)
        return prices

    def material_price(self, tag: str) -> Optional[float]:
        """Money per kg in this civilisation's coin that it costs to make a raw material key or a curated commodity id,
        from the calculator-backed table; None if it cannot be priced at all. A cost: what a buyer pays is the goods
        market's price."""
        prices = self.material_prices()
        key = rules.priced_key(tag, prices, self.commodity_record(tag))
        return None if key is None else prices[key]

    def material_reach(self, material: str) -> Optional[str]:
        """"solved" (a technique some producer runs), "gated" (one nobody runs yet, within reach) or None, from the
        solver alone."""
        return self.price_tables()[1].get(material)

    def material_price_basis(self, material: str) -> Optional[str]:
        """"solved", "gated", "imported" (no home producer in reach; a trading partner sells it) or None (no one does)."""
        return rules.basis_with_imports(self.price_tables()[1].get(material), self.needs.material_seller[material])

    def price_index(self) -> float:
        """The civilisation's price level for capital goods and land against the labour hour."""
        return float(self.needs.civilisation().get("price_index", 1.0))
