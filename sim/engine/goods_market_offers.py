"""Who offers a good, and what households are asked to pay for it.

A good is offered by a modelled seller or it cannot be had, and a good no one offers has no price. The
sellers are the home society (a technique it holds, or one within reach of what it holds, in the price
table) and a trading partner that makes it (priced at what it costs the partner, the freight and the
merchants' terms, over a route that joins the two). A good neither offers is unavailable: it has no
price, cannot be bought, and anything that needs it cannot start until a seller appears (a technique is
reached, a route opens, a partner gains it).

The offers are worked out once a year (and again when the technologies held or the partners change),
from figures held to a few decimals, so the table is a function of its key and not of the moment it
was first asked for.
"""
import math

from sim.world import trader_response

from .goods_market_imports import HOME_SELLER, GoodsImports


RATE_DECIMALS = 3
LEVEL_DECIMALS = 4


class GoodsOffers(GoodsImports):
    """Mixin of `GoodsMarket`: reads of who sells what."""

    def merchants_cost_share(self, route, material=None, civilization_id=None):
        """Merchants' costs over freight as a share of the price at the origin: margin, loss
        (at sea, and spoilage of a named material) and interest, the terms the traders' flows are
        cleared with, at the market rate to a few decimals."""
        sim = self._sim
        return trader_response.cost_share_of_price(
            sim._trader_margin_share(civilization_id, route),
            sim._cargo_lost_share(route, material, civilization_id),
            round(sim.market_rate(), RATE_DECIMALS), sim._trader_cycle_years(route, civilization_id))

    def partner_price_level(self, civilization_id):
        return round(self._sim.partner_price_level(civilization_id), LEVEL_DECIMALS)

    def _route_from(self, civilization_id):
        from .data import load_civ
        return self._sim._foreign_route(load_civ(civilization_id))

    def landed_price(self, material, civilization_id, route=None):
        """Money per unit of a material delivered from a trading partner: its cost to the partner,
        the merchants' costs as a share of that, and the freight. None when the partner does not
        make it, it may not cross a border, or no route joins the two."""
        from .foreign_economies import not_traded_materials
        from .project_materials import tonnes_per_unit
        facts = self._sim._foreign_economy_facts(civilization_id)
        route = route or self._route_from(civilization_id)
        if (route is None or material not in facts["solved_materials"]
                or material in not_traded_materials()):
            return None
        partner_price = facts["prices_in_home_money"].get(material)
        if not partner_price:
            return None
        cost = partner_price * self.partner_price_level(civilization_id)
        return (cost * (1.0 + self.merchants_cost_share(route, material, civilization_id))
                + (route.cost_per_tonne + self._sim._agent_cost_per_tonne(civilization_id, route))
                * tonnes_per_unit(material))

    def _worked_out_offers(self):
        """(household prices, seller of each material) as of the key they were worked out for."""
        sim = self._sim
        prices = sim._material_prices()
        partners = tuple(sim.foreign_economies())
        key = (partners, len(sim.state.projects.done), sim.state.scenario.year,
               round(sim.market_rate(), RATE_DECIMALS),
               tuple(self.partner_price_level(partner) for partner in partners))
        cache = getattr(sim.household, "_goods_offers_cache", None)
        if cache is not None and cache[0] is prices and cache[1] == key:
            return cache[2], cache[3]
        routes = {partner: self._route_from(partner) for partner in partners}
        household = {material: price for material, price in prices.items()}
        sellers = {material: HOME_SELLER for material in prices}
        # A technique the home society holds no producer of yet (priced as within reach) is a home seller
        # only until a partner sells the same good cheaper: the cheapest seller in reach sells.
        in_reach = {material for material in prices if self._home_basis(material) == "gated"}
        for material in sorted((self._partner_made_materials(partners) - set(prices)) | in_reach):
            offers = [(landed, partner) for partner in partners
                      for landed in (self.landed_price(material, partner, routes[partner]),)
                      if landed is not None and math.isfinite(landed)
                      and sim.foreign_supply_tonnes(partner, material) > 0.0]
            if offers and min(offers)[0] < household.get(material, math.inf):
                household[material], sellers[material] = min(offers)[0], min(offers)[1]
        sim.household._goods_offers_cache = (prices, key, household, sellers)
        return household, sellers

    def _home_basis(self, material):
        """How the home price table reaches a material ("solved", "gated"), None when it does not."""
        return self._sim._price_tables()[1].get(material)

    def _partner_made_materials(self, partners):
        """Materials some trading partner makes with its own technologies."""
        made = set()
        for partner in partners:
            made |= self._sim._foreign_economy_facts(partner)["solved_materials"]
        return made

    def household_prices(self):
        """{material: money per unit} households are asked to pay: the solver's price where the
        home society makes it, the landed price where only a partner offers it, nothing where no
        one does. The same object while nothing it reads has changed."""
        return self._worked_out_offers()[0]

    def unit_price(self, material):
        """Money per unit to buy a material from the cheapest seller in reach (the home price
        table, else a partner's landed price), or None when no one in reach sells it."""
        if self.offered_by(material) not in (None, HOME_SELLER):
            return self.household_prices()[material]
        price = self._sim._material_price_per_kg(material)
        return price if price is not None else self.household_prices().get(material)

    def can_be_bought(self, material):
        return self.unit_price(material) is not None

    def offered_by(self, material):
        """HOME_SELLER when a technique the society holds or can reach makes the material, the
        trading partner's id when only a partner offers it, None when nothing does."""
        return self._worked_out_offers()[1].get(material)

    def commodity_is_unsourced(self, commodity):
        """Whether no material filed under this commodity has a seller in reach."""
        sellers = self._worked_out_offers()[1]
        return not any(material in sellers for material in self._sim._commodity_materials(commodity))
