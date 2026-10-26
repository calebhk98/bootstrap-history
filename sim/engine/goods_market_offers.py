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

from . import trade_duty
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
        return self._sim._foreign_route(self._sim.partner_civ(civilization_id))

    def landed_price(self, material, civilization_id, route=None, with_duty=True):
        """Money per unit of a material delivered from a trading partner: its cost to the partner,
        the merchants' costs as a share of that, the freight and the home state's tariff on the partner's
        goods (`with_duty` False leaves it out). None when the partner does not make it, it may not cross
        a border, no route joins the two, or the home state embargoes the partner."""
        from .foreign_economy_data import not_traded_materials
        from .material_units import tonnes_per_unit
        facts = self._sim._foreign_economy_facts(civilization_id)
        route = route or self._route_from(civilization_id)
        if (route is None or material not in facts["solved_materials"]
                or material in not_traded_materials()):
            return None
        partner_price = facts["prices_in_home_money"].get(material)
        if not partner_price:
            return None
        tariff, embargoed = trade_duty.import_terms(self._sim, civilization_id)
        if embargoed:
            return None
        cost = partner_price * self.partner_price_level(civilization_id)
        return (cost * (1.0 + self.merchants_cost_share(route, material, civilization_id) + (tariff if with_duty else 0.0))
                + (route.cost_per_tonne + self._sim._agent_cost_per_tonne(civilization_id, route))
                * tonnes_per_unit(material))

    def _home_prices(self, at_cost=False):
        """{material: money per unit} the home society's sellers ask at the acting tile: the economy's price
        where it has a market for the good, the cost of making it (the cost table) where it has none or while
        it opens. The same object while neither has changed. `at_cost` gives the cost table itself."""
        sim = self._sim
        table = sim._material_prices()
        if at_cost:
            return table
        paid = sim.economy.agent_prices_at()
        if paid is None:
            return table
        held = getattr(sim.household, "_home_prices_cache", None)
        if held is not None and held[0] is table and held[1] is paid:
            return held[2]
        merged = {material: paid.get(material, cost) for material, cost in table.items()}
        sim.household._home_prices_cache = (table, paid, merged)
        return merged

    def home_unit_price(self, material):
        """Money per unit the home society's sellers ask for a material (or a curated commodity, by the material
        it is priced as) at the acting tile; None when no home seller offers it. The one price of the coin metal
        in the mint and in cargo."""
        prices = self._home_prices()
        key = self._sim._priced_key(material, prices)
        return None if key is None else prices[key]

    def _worked_out_offers(self, at_cost=False):
        """(household prices, seller of each material) as of the key they were worked out for; with `at_cost`
        the home sellers' prices are what a technique makes the goods for (the cost table)."""
        sim = self._sim
        prices = self._home_prices(at_cost)
        partners = tuple(sim.foreign_economies())
        key = (partners, len(sim.state.projects.done), sim.state.scenario.year,
               round(sim.market_rate(), RATE_DECIMALS),
               tuple(self.partner_price_level(partner) for partner in partners),
               trade_duty.signature(sim, partners))
        cache_name = "_goods_offers_cost_cache" if at_cost else "_goods_offers_cache"
        cache = getattr(sim.household, cache_name, None)
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
        setattr(sim.household, cache_name, (prices, key, household, sellers))
        return household, sellers

    def _home_basis(self, material):
        """How the home price table reaches a material ("solved", "gated"), None when it does not."""
        return self._sim.view("material_reach")[material]

    def _partner_made_materials(self, partners):
        """Materials some trading partner makes with its own technologies."""
        made = set()
        for partner in partners:
            made |= self._sim._foreign_economy_facts(partner)["solved_materials"]
        return made

    def household_cost_prices(self):
        """`household_prices` with the home sellers' prices at what a technique makes the goods for, not what
        the economy shows: the prices the household demand model and the opening basket are measured at."""
        return self._worked_out_offers(at_cost=True)[0]

    def household_prices(self):
        """{material: money per unit} households are asked to pay: the economy's price on the acting tile where the
        home society makes it (its cost of making while the economy opens or has no market for the good), the
        landed price where only a partner offers it, nothing where no one does. The same object while nothing it
        reads has changed."""
        return self._worked_out_offers()[0]

    def unit_price(self, material):
        """Money per unit to buy a material from the cheapest seller in reach (the home sellers' price on the
        acting tile, else a partner's landed price), or None when no one in reach sells it."""
        if self.offered_by(material) not in (None, HOME_SELLER):
            return self.household_prices()[material]
        price = self.home_unit_price(material)
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
