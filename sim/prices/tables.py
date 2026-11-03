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
from typing import Dict, Optional, Tuple

from sim.assembly.api import Part

from . import rules
from . import prices as price_solver


class Tables(Part):

    def __init__(self, module):
        super().__init__(module)
        self._reading_market_rate = False                    # set while the market rate is asked for: it may need these prices
        self._price_tables_cache: Optional[Tuple] = None     # (granted, in use, tables, (farmed, rate)), compared by value
        self._incumbent_table_cache: Optional[Tuple] = None  # ((granted, farmed, rate), hours, basis)
        self._material_prices_cache: Optional[Tuple] = None  # (hours table, money per hour, prices)

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
        granted_now = frozenset(self.needs.techniques_granted())
        in_use = frozenset(self.needs.techniques_in_use())
        farmed = price_solver.band_farmed_hectares(self.needs.farm_land_hectares())
        rate = self.banded_market_rate()
        cached = self._price_tables_cache
        if cached is not None and cached[:2] == (granted_now, in_use) and cached[3] == (farmed, rate):
            return cached[2]
        granted = granted_now
        civ = self.needs.civilisation()
        document = self.parts.calculated_views.opening_schedule(civ).document()
        incumbent = self._incumbent_table_cache
        if incumbent is None or incumbent[0] != (granted, farmed, rate):
            incumbent = self._incumbent_table_cache = (
                (granted, farmed, rate), *price_solver.goods_in_hours(granted, document, civ, farmed, rate))
        hours, basis = incumbent[1], incumbent[2]
        if in_use != granted:
            run_hours, run_basis = price_solver.goods_in_hours(in_use, document, civ, farmed, rate)
            tables = rules.merge_by_reach(hours, basis, run_hours, run_basis)
        else:
            tables = (dict(hours), dict(basis))
        self._price_tables_cache = (granted_now, in_use, tables, (farmed, rate))
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
        key = rules.priced_key(tag, prices, self.parts.memos.commodity_record(tag))
        return None if key is None else prices[key]

    def material_price_basis(self, material: str) -> Optional[str]:
        """"solved", "gated", "imported" (no home producer in reach; a trading partner sells it) or None (no one does)."""
        return rules.basis_with_imports(self.price_tables()[1].get(material), self.needs.material_seller[material])

    def price_index(self) -> float:
        """The civilisation's price level for capital goods and land against the labour hour."""
        return float(self.needs.civilisation().get("price_index", 1.0))
