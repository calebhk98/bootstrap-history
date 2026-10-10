"""Living stock as a possession: held in the ledger, needed by nodes, granted, bought.

A node's `holds` ({material: units}) is a start gate beside `pre`: the stock must be in
the ledger now, however it came there. A civilisation's `opening_stock` is what it held at its
date; a node's `grants` is the stock a completed venture brings back; a partner that makes the
material and does not refuse sells it (living_stock_trade.py), and held stock breeds and dies by
the rates in data/world/living_stock.json (living_stock_yearly.py). Which materials are stock is
data; nothing here names one.
"""
from sim.world import living_stock

from .blockers import blocker_kind
from .data import load_civ
from .material_units import tonnes_per_unit


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

    def stock_gates(self, node_id):
        """The living stock a node rests on, held beside needed, whichever way the data says it:
        its own `holds`, or a civilisation's `needs_first` gate on a material."""
        gates = [{"material": material, "needed": units, "held": round(self.stock_held(material), 3),
                  "brought_by": None}
                 for material, units in sorted((self.nodes[node_id].get("holds") or {}).items())]
        for key, entry in (self.civ.get("needs_first") or {}).items():
            if (not key.startswith("_") and isinstance(entry, dict) and entry.get("material")
                    and node_id in (entry.get("ids") or ())):
                gates.append({"material": entry["material"], "needed": entry.get("units", 0.0),
                              "held": round(self.stock_held(entry["material"]), 3),
                              "brought_by": entry.get("node")})
        return gates

    def grant_stock(self, material, units):
        """Add units of a material to the held stock (a gift, a founding herd, an opening holding)."""
        self.change_stock(material, units)

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
        route = self._material_route(load_civ(civilization_id), material, facts["route"])
        if route is None:
            return None
        per_tonne = price / tonnes_per_unit(material) * self.partner_price_level(civilization_id)
        return (per_tonne * (1.0 + self._trader_cost_share(route, material, civilization_id))
                + self._agent_cost_per_tonne(civilization_id, route) + route.cost_per_tonne)
