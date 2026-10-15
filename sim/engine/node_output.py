"""What a node physically makes in a year: the adapter from a node to the plant kernel.

A node gates production entries (`requires_node`); this finds them and hands them, with the node's staff
(`sch` + `art` people) and declared output (`annual_output_t`), to `sim.world.plant_figures`, which holds the
arithmetic. Nothing here reads a revenue or upkeep figure.
"""
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional

from sim.world import plant_figures
from sim.world.plant_figures import Baskets, ENERGY_CARRIERS  # noqa: F401  (re-exported for callers)

from . import energy_prices

# (production table, {node id: entries run}); the table is kept so a hit is confirmed with `is`
_ENTRIES_BY_NODE: List[Any] = [None, None]


def entries_gated_by(node_id: str, production: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Production entries a node's concern runs, in key order: those that become available with it
    (`requires_node`) and those that name it in `operated_by`."""
    index = _ENTRIES_BY_NODE[1] if _ENTRIES_BY_NODE[0] is production else None
    if index is None:
        index = defaultdict(list)
        for key in sorted(production):
            entry = production[key]
            for operator in dict.fromkeys([entry.get("requires_node"), *(entry.get("operated_by") or [])]):
                if operator:
                    index[operator].append(entry)
        _ENTRIES_BY_NODE[:] = [production, index]
    return index.get(node_id, [])


def output_baskets(node: Mapping[str, Any], production: Mapping[str, Any], goods: Mapping[str, float],
                   energy: Optional[energy_prices.EnergyPrices] = None,
                   wages: Optional[Mapping[str, float]] = None,
                   entries: Optional[List[Dict[str, Any]]] = None) -> Optional[Baskets]:
    """The node's yearly baskets, or None when the data gives it no physical output to derive. `entries` replace
    the ones the node gates (the techniques a society holds for its lines)."""
    energy = energy or energy_prices.pool_only(goods)
    return plant_figures.yearly_baskets(
        entries if entries is not None else entries_gated_by(node["id"], production), goods, energy, wages,
        node.get("sch", 0.0) + node.get("art", 0.0), node.get("annual_output_t") or 0.0)
