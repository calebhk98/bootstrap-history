"""What a concern turns out and earns from the techniques its society runs, against its opening.

A node gates production entries (`node_output`); the concern running it has a staff and a plant. Its
lines of product are the sets of outputs those entries make. For each line the concern runs the best
entry among those some producer runs (the node's own, or a running node's that makes the same outputs; see
techniques_in_use.py), so a technique that cuts an entry's labour or plant per unit raises what the same
staff turn out once it is run, and a technique nobody runs changes nothing.

Two ratios against the opening, both from baskets worked out in labour hours:
- `concern_volume_ratio`: the quantity made, at the opening's prices, over the opening's quantity.
- `concern_value_ratio`: net sales (outputs less purchases) at the prices the solver gives the
  techniques in use now, over the opening's. Takings multiply the loaded figure by it, then by the market's
  spot-over-solved ratio, so they are the volume times the price the market clears at.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): energy a line draws or makes is valued at the pool price, and
every line is run whatever the wage, in both baskets alike (the loaded figure applies a wage test).
"""
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from . import energy_prices, node_output

# (production table, {outputs: entries}); the table is kept so a hit is confirmed with `is`
_ENTRIES_BY_OUTPUTS: List[Any] = [None, None]


def _entries_by_outputs(production: Dict[str, Any]) -> Dict[FrozenSet[str], List[Dict[str, Any]]]:
    if _ENTRIES_BY_OUTPUTS[0] is not production:
        index: Dict[FrozenSet[str], List[Dict[str, Any]]] = {}
        for key in sorted(production):
            entry = production[key]
            if entry.get("outputs"):
                index.setdefault(frozenset(entry["outputs"]), []).append(entry)
        _ENTRIES_BY_OUTPUTS[:] = [production, index]
    return _ENTRIES_BY_OUTPUTS[1]


def entries_held_for(node_id: str, production: Dict[str, Any], held: FrozenSet[str]) -> List[Dict[str, Any]]:
    """The node's own entries and every entry a held node gates that makes one of the node's lines,
    in production key order."""
    own = node_output.entries_gated_by(node_id, production)
    by_outputs = _entries_by_outputs(production)
    entries = list(own)
    for line in sorted({frozenset(entry["outputs"]) for entry in own if entry.get("outputs")}, key=sorted):
        for entry in by_outputs.get(line, []):
            if entry.get("requires_node") in held and not any(entry is gated for gated in own):
                entries.append(entry)
    return entries


def _net_value(baskets: node_output.Baskets, goods: Dict[str, float]) -> float:
    sold = sum(quantity * goods.get(material, 0.0) for material, quantity in baskets.outputs.items())
    sold += sum(basket["value"] for basket in baskets.energy_sold.values())
    bought = sum(quantity * goods.get(material, 0.0) for material, quantity in baskets.purchases.items())
    bought += sum(basket["value"] for basket in baskets.energy_bought.values())
    return sold - bought


def baskets_for(node: Dict[str, Any], production: Dict[str, Any], held: FrozenSet[str],
                goods: Dict[str, float]) -> Optional[node_output.Baskets]:
    """The node's yearly baskets with the techniques `held` in use, at its own staff and plant."""
    return node_output.output_baskets(node, production, goods, energy_prices.pool_only(goods),
                                      entries=entries_held_for(node["id"], production, held))


def ratios(node: Dict[str, Any], production: Dict[str, Any], opening: Tuple[FrozenSet[str], Dict[str, float]],
           now: Tuple[FrozenSet[str], Dict[str, float]]) -> Tuple[float, float, Optional[node_output.Baskets]]:
    """(volume ratio, value ratio, baskets now) of a node's concern; ones for a node with no baskets."""
    before = baskets_for(node, production, *opening)
    after = baskets_for(node, production, *now)
    if before is None or after is None:
        return 1.0, 1.0, None
    prices = opening[1]
    quantity_before = sum(made * prices.get(material, 0.0) for material, made in before.outputs.items())
    quantity_after = sum(made * prices.get(material, 0.0) for material, made in after.outputs.items())
    volume = quantity_after / quantity_before if quantity_before > 0.0 else 1.0
    value_before = _net_value(before, prices)
    value = max(0.0, _net_value(after, now[1])) / value_before if value_before > 0.0 else 1.0
    return volume, value, after


class ConcernVolumeMixin:
    """Per-concern volume and value ratios, remembered while the techniques held are unchanged."""

    def _concern_prices_in_hours(self, held):
        from .data import calculated_goods_prices
        return {material: price for material, price in sorted(calculated_goods_prices(
            held, civilization_id=self.civ.get("id"), civilization=self.civ, money_per_labour_hour=1.0).items())
            if price > 0.0}

    def _concern_ratios(self, node_id):
        node = self.nodes[node_id]
        if node.get("_revenue_basis") != "output":
            return 1.0, 1.0, None

        def work_out():
            from . import prices as price_solver
            granted = frozenset(self.state.projects.granted)
            held = self.techniques_in_use()
            opening = (granted, self._done_memo("concern_opening_prices", granted,
                                                lambda: self._concern_prices_in_hours(granted)))
            now = (held, self._done_memo("concern_prices", held, lambda: self._concern_prices_in_hours(held)))
            return ratios(node, price_solver.default_production_entries(), opening, now)
        return self._done_memo("concern_ratios", node_id, work_out)

    def concern_volume_ratio(self, node_id):
        """What the concern turns out now over what it turned out at the opening, from the same staff."""
        return self._concern_ratios(node_id)[0]

    def concern_value_ratio(self, node_id):
        """The concern's net sales at the solved prices of the techniques held now, over the opening's."""
        return self._concern_ratios(node_id)[1]

    def concern_baskets_now(self, node_id):
        """What the concern makes and buys in a year with the techniques held now; None for a node
        whose revenue is not derived from output."""
        return self._concern_ratios(node_id)[2]
