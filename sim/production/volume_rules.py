"""What a concern turns out and earns from the techniques its society runs, against its opening.

A node gates production entries (`node_output`); the concern running it has a staff and a plant. Its
lines of product are the sets of outputs those entries make. For each line the concern runs the best
entry among those held (the node's own, or a node a producer has run long enough to be copied that makes the
same outputs; see technique_spread.py), so a technique that cuts an entry's labour or plant per unit raises what the same
staff turn out once it is run, and a technique nobody runs changes nothing.

Two ratios against the opening, both from baskets worked out in labour hours:
- `concern_volume_ratio`: the quantity made, at the opening's prices, over the opening's quantity.
- `concern_value_ratio`: net sales (outputs less purchases) at the incumbents' prices, over the opening's.
  Takings multiply the loaded figure by it, then by the market's spot-over-incumbent ratio, so they are the
  volume times the price the market clears at; what a cheaper entry saves shows as fewer purchases and hours
  per unit, and its seller's cost (sim/prices/cost_books.py) is what it will not sell below.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): energy a line draws or makes is valued at the pool price, and
every line is run whatever the wage, in both baskets alike (the loaded figure applies a wage test).
"""
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from sim.prices.api import energy_prices
from . import node_output

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
