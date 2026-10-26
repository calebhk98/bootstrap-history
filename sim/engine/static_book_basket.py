"""The static market book's household basket: what households bought of each material at the opening, by the
engine's demand model, valued at the price table's opening prices. Only the static book (market_demand.py,
partner_demand.py) reads it; real output is the economy's (sim/reporting/output.py). Goes with the static book in
Complaint 507 stage 6."""

def opening_prices_in_hours(held, civ, opening_farmed_hectares):
    """{material: opening price in labour hours}: the solved prices at the opening's banded farmed area, less goods
    with no calculated price."""
    from .data import calculated_goods_table
    from sim.prices.api import prices as price_solver
    in_hours, _basis = calculated_goods_table(
        held, civilization_id=civ.get("id"), civilization=civ,
        farmed_hectares=price_solver.band_farmed_hectares(opening_farmed_hectares))
    return {material: price for material, price in sorted(in_hours.items())
            if price > 0.0}


class StaticBookBasketMixin:

    def static_book_basket(self):
        """{"prices": {material: opening price in labour hours}, "units": {material: units a year households bought
        at the opening}, "commodity": {material: its commodity}}. A function of the starting techniques and the
        civilisation only, so kept for the run."""
        from . import market_demand
        cached = getattr(self.household, "_static_book_basket_cache", None)
        if cached is not None:
            return cached
        prices = opening_prices_in_hours(
            frozenset(self.state.projects.granted), self.civ, self._opening_farmed_hectares)
        units = market_demand.household_demand_by_material(
            prices, self._opening_population(), market_demand.MEAN_INCOME_HOURS_PER_CAPITA,
            self.civ, self.world_map)
        units = {material: wanted for material, wanted in sorted(units.items())
                 if wanted > 0.0 and material in prices}
        basket = {"prices": prices, "units": units,
                  "commodity": {material: self._material_tag(material)[0] for material in units}}
        self.household._static_book_basket_cache = basket
        return basket
