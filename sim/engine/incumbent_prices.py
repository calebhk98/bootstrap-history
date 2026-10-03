"""The cost reference of every good: what the society's incumbent producers make it for.

The incumbents are the producers the society started with, running the techniques it started with
(`projects.granted`). Their unit cost, in labour hours, is each good's reference; the price a good clears
at comes from the market (market_clearing.py), where every producer offers at its own cost
(producer_offers.py). A technology that is held, or run by one producer, does not move this reference.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): a good no incumbent makes but some producer runs a technique for has
no incumbent cost, so its reference is the solver's cost under every technique now run (the cheapest route
among them) until a producer's own cost can anchor it.

Money is the labour hour times what an hour is worth, which follows the one coin stock (labour_wages.py), so
every price here, traded or not, moves with money against goods.
"""


# how near a producer is to making a good, least to most
REACH = {"mature": 0, "gated": 1, "solved": 2}


class IncumbentPricesMixin:

    def _price_tables(self):
        """(labour-hour price of each good, provenance of each), for the incumbents' techniques plus the
        baseline for goods only a producer's own technique reaches."""
        projects = self.state.projects
        in_use = self.techniques_in_use()
        cached = getattr(self, "_price_tables_cache", None)
        if (cached is not None and cached[0] is projects.granted and cached[1] is in_use
                and cached[3] == len(projects.granted)):
            return cached[2]
        granted = frozenset(projects.granted)
        from .data import calculated_goods_table
        civ = dict(civilization_id=self.civ.get("id"), civilization=self.civ)
        incumbent = getattr(self, "_incumbent_table_cache", None)
        if incumbent is None or incumbent[0] != granted:
            incumbent = self._incumbent_table_cache = (granted, *calculated_goods_table(granted, **civ))
        hours, basis = dict(incumbent[1]), dict(incumbent[2])
        if in_use != granted:
            run_hours, run_basis = calculated_goods_table(in_use, **civ)
            for material, source in run_basis.items():
                if REACH.get(source, -1) > REACH.get(basis.get(material), -1):
                    hours[material], basis[material] = run_hours[material], source
        tables = (hours, basis)
        self._price_tables_cache = (projects.granted, in_use, tables, len(projects.granted))
        return tables

    def _material_prices(self):
        """{material: money per unit}: the incumbents' cost in this coin. The market's price is this
        times `market_price_ratio`."""
        hours = self._price_tables()[0]
        per_hour = self.labour.money_per_labour_hour()
        cached = getattr(self, "_material_prices_cache", None)
        if cached is not None and cached[0] is hours and cached[1] == per_hour:
            return cached[2]
        prices = {material: price * per_hour for material, price in hours.items()}
        self._material_prices_cache = (hours, per_hour, prices)
        return prices

    def material_price_basis(self, material):
        """"solved" (a technique some producer runs), "gated" (one nobody runs yet), "mature" (nothing in
        reach makes it) or None (not priced by the solver)."""
        return self._price_tables()[1].get(material)

    def _coin_metal_price(self, material):
        """Money per unit of the coin metal at the mint's standard: a unit of coin is a fixed weight of
        metal, so the metal's price in coin does not follow the price level of the goods."""
        price = self._material_prices().get(material)
        return None if price is None else price / self.home_price_level()
