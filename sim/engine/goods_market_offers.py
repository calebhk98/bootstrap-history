"""Who offers a good, and what households are asked to pay for it.

A good is offered by a modelled seller or it cannot be had. The sellers are the home society (a
technique it holds, or one within reach of what it holds) and a trading partner (priced at what it
costs the partner, the freight and the merchants' terms). A good neither offers is priced by the
solver only "as if every technology were held" (`sim/engine/prices.py`, provenance "mature"); the
founder's own quote and the cost of a project that needs it still read that figure, but households
are given no price for it, so the need it served draws no spending on it.
"""
import math

HOME_SELLER = "home"


class GoodsOffers:
    """Mixin of `GoodsMarket`: reads of who sells what."""

    def landed_price(self, material, civilization_id):
        """Money per unit of a material delivered from a trading partner: its cost to the partner,
        the merchants' costs as a share of that, and the freight. None when the partner does not
        make it, it may not cross a border, or no route joins the two."""
        from .foreign_economies import not_traded_materials
        from .project_materials import tonnes_per_unit
        sim = self._sim
        facts = sim._foreign_economy_facts(civilization_id)
        if (material not in facts["solved_materials"] or material in not_traded_materials()
                or not math.isfinite(facts["freight_per_tonne"])):
            return None
        partner_price = facts["prices_in_home_money"].get(material)
        if not partner_price:
            return None
        cost = partner_price * sim.partner_price_level(civilization_id)
        return (cost * (1.0 + sim._trader_cost_share(facts["route"]))
                + facts["freight_per_tonne"] * tonnes_per_unit(material))

    def _cheapest_partner(self, material):
        """(partner id, landed price) of the partner that delivers it cheapest; None when none does."""
        offers = []
        for civilization_id in self._sim.foreign_economies():
            landed = self.landed_price(material, civilization_id)
            if landed is not None:
                offers.append((landed, civilization_id))
        if not offers:
            return None
        landed, civilization_id = min(offers)
        return civilization_id, landed

    def offered_by(self, material):
        """HOME_SELLER when a technique the society holds or can reach makes the material, the
        trading partner's id when only a partner offers it, None when nothing does."""
        basis = self._sim.material_price_basis(material)
        if basis != "mature":
            return HOME_SELLER if basis is not None else None
        partner = self._cheapest_partner(material)
        return None if partner is None else partner[0]

    def commodity_is_unsourced(self, commodity):
        """Whether every material the solver prices under this commodity is one nothing offers."""
        sim = self._sim
        prices = sim._material_prices()
        priced = [material for material in sim._commodity_materials(commodity) if material in prices]
        return bool(priced) and all(self.offered_by(material) is None for material in priced)

    def household_prices(self):
        """{material: money per unit} households are asked to pay: the solver's price where the
        home society makes it, the landed price where only a partner offers it, nothing where no
        one does. Remembered while the price table, the partners and the technologies are the same."""
        sim = self._sim
        prices = sim._material_prices()
        key = (tuple(sim.foreign_economies()), len(sim.state.projects.done))
        cache = getattr(sim.household, "_household_prices_cache", None)
        if cache is not None and cache[0] is prices and cache[1] == key:
            return cache[2]
        offered = {}
        for material, price in prices.items():
            if sim.material_price_basis(material) != "mature":
                offered[material] = price
                continue
            partner = self._cheapest_partner(material)
            if partner is not None:
                offered[material] = partner[1]
        sim.household._household_prices_cache = (prices, key, offered)
        return offered
