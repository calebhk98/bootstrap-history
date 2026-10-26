"""What is foreign to this society, what it must have before it can begin a thing, and what it finds dear to build.

Needs: tree, civilisation, techniques_held, stock_holds_met."""
from typing import Optional, Tuple

from . import civ_cost
from .institution_societies import belongs_to_other_society


class Foreign:

    def foreign_only(self, node_id: str) -> bool:
        """A legal or civic institution of a society that is not this one. The answer depends only on this
        civilisation and the node's own key and name, so it is kept for the life of the game."""
        value = self._foreign_only_memo.get(node_id)
        if value is None:
            haystack = (node_id + " " + self.tree_node(node_id).get("name", "")).lower()
            value = belongs_to_other_society(haystack, self.needs.civilisation(), "exclusive_markers")
            self._foreign_only_memo[node_id] = value
        return value

    def needs_first(self, node_id: str, about_stock: Optional[bool] = None) -> Tuple[Optional[str], Optional[str]]:
        """(node, why) this society must have before it can begin `node_id` at all.

        Some things are not dear but impossible: a society with no draught animals, no iron and no wheel in practical
        use cannot start horse_collar at any price. Data in the civilisation file, always liftable: every entry names
        the node that opens it. `about_stock` narrows to the gates that rest on held living stock (True) or on
        knowledge alone (False); left out, either."""
        spec = self.needs.civilisation().get("needs_first") or {}
        for key, entry in spec.items():
            if key.startswith("_") or not isinstance(entry, dict):
                continue
            if about_stock is not None and bool(entry.get("material")) != about_stock:
                continue
            if node_id in (entry.get("ids") or ()):
                node = entry.get("node")
                stock = {entry["material"]: entry.get("units", 0.0)} if entry.get("material") else None
                if stock and self.needs.stock_holds_met(stock):
                    continue
                if node and node not in self.needs.techniques_held():
                    return node, (entry.get("because") or "this society has no %s" % key)
        return None, None

    def civ_cost_factor(self, node_id: str) -> float:
        """What this society is unusually good or bad at building: above 1 it finds that domain harder than Rome
        does, below 1 easier. A small table in the civilisation file, so a new civilisation is data."""
        civilisation = self.needs.civilisation()
        if not civilisation.get("cost_multipliers"):
            return 1.0
        node = self.tree_node(node_id)
        return civ_cost.civ_cost_factor(civilisation.get("cost_multipliers"), civilisation.get("handicap_remedies"),
                                        self.needs.techniques_held(), node.get("cat"), node.get("traits") or ())
