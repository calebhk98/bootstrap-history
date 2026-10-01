"""Living stock as a possession: held in the ledger, needed by nodes, granted, bought.

A node's `holds` ({material: units}) is a start gate beside `pre`: the stock must be in
the ledger now, however it came there. A civilisation's `opening_stock` is what it held at its
date; a node's `grants` is the stock a completed venture brings back; a partner that makes the
material and does not refuse sells it at its price plus the route's freight and the merchants'
cost. Which materials are stock is data; nothing here names one.
"""
from sim.world import living_stock

from .blockers import blocker_kind
from .project_materials import tonnes_per_unit


@blocker_kind("supply")
def check_unheld_stock(self, node_id, node, ignore_trade, _memo, _why):
    """Refuse a node whose `holds` the actor does not hold; the refusal names what is short."""
    short = self.stock_missing(node_id)
    if not short:
        return None
    if not _why:
        return False, None
    return False, ("it needs living stock you do not hold: %s. Get it by trade, gift or "
                   "expedition; it is not something you can research"
                   % ", ".join("%s (%.3g more)" % pair for pair in short))


class LivingStockMixin:

    def _stock_key(self, material):
        return self._material_tag(material)[0]

    def stock_held(self, material):
        """Units of `material` held now."""
        return self.material_stock_t(self._stock_key(material)) / tonnes_per_unit(material)

    def stock_missing(self, node_id):
        """[(material, units short)] of what the node's `holds` asks and is not held."""
        holds = self.nodes[node_id].get("holds")
        if not holds:
            return []
        return living_stock.unheld(
            lambda material: self.material_stock_t(self._stock_key(material)), holds, tonnes_per_unit)

    def grant_stock(self, material, units):
        """Add units of a material to the held stock (a gift, a founding herd, an opening holding)."""
        tonnes = float(units) * tonnes_per_unit(material)
        key = self._stock_key(material)
        self._material_stock()[key] += tonnes
        opening = self._material_opening_stock()
        opening[key] = opening.get(key, 0.0) + tonnes
        self.state.household._stock_throttle_sig = None

    def grant_opening_stock(self):
        """Credit what the civilisation held at its date."""
        for material, units in sorted((self.civ.get("opening_stock") or {}).items()):
            if not material.startswith("_"):
                self.grant_stock(material, units)

    def stock_holds_met(self, holds):
        """Whether every {material: units} in `holds` is held."""
        return not living_stock.unheld(
            lambda material: self.material_stock_t(self._stock_key(material)), holds, tonnes_per_unit)

    def partner_quote_per_tonne(self, material, civilization_id):
        """Home money per tonne delivered from a partner, or None when it cannot supply it."""
        if civilization_id not in self.foreign_economies() or self.partner_refusal(civilization_id, material):
            return None
        facts = self._foreign_economy_facts(civilization_id)
        price = facts["prices_in_home_money"].get(material)
        if material not in facts["solved_materials"] or not price:
            return None
        per_tonne = price / tonnes_per_unit(material) * self.partner_price_level(civilization_id)
        return per_tonne * (1.0 + self._trader_cost_share(facts["route"])) + facts["freight_per_tonne"]

    def buy_stock_from_partner(self, material, units, civilization_id):
        """Buy units of a material from a partner economy; returns the units bought (0 when the
        partner refuses, cannot make it, or the buyer cannot pay)."""
        from . import purchase_rule
        from .data import load_civ
        quote = self.partner_quote_per_tonne(material, civilization_id)
        units = float(units)
        if quote is None or units <= 0.0:
            return 0.0
        tonnes = units * tonnes_per_unit(material)
        cost = quote * tonnes
        if not purchase_rule.can_pay(self, cost):
            return 0.0
        self.state.household.debit(cost, "stock bought abroad")
        coin = load_civ(civilization_id)["coin_standard"]
        coin_price = self._material_prices().get(coin["material"])
        if coin_price:
            self._settle_flow(civilization_id, tonnes, cost, coin["kg_per_unit"] * coin_price)
        self.grant_stock(material, units)
        return units
