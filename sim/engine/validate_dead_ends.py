"""Produced goods that nothing consumes (Complaints/533).

A good is a dead end when it is made by a recipe but no recipe or capital build takes it as input, no need
lists it, no trade keeps it as a tool, no carriage or navy rule wears it, no durable life holds it and no
state or army budget line buys it. Report only: a dead end is a missing consumer to author, not a fault.
A good that only tech-tree nodes consume is listed apart, since a node's materials are a one-off build cost
and not a flow of demand.
"""
from typing import Any, Iterable, List, Mapping, Set, Tuple


def produced_goods(production: Mapping[str, Mapping[str, Any]]) -> Set[str]:
    """Every good some recipe outputs."""
    goods: Set[str] = set()
    for key, entry in production.items():
        outputs = entry.get("outputs") or {}
        goods.update(outputs if outputs else [key])
    return goods


def consumed_goods(production: Mapping[str, Mapping[str, Any]], need_goods: Mapping[str, Any],
                   service_lives: Mapping[str, Any], trade_registry: Mapping[str, Mapping[str, Any]],
                   state_goods: Iterable[str] = ()) -> Set[str]:
    """Every good some consumer takes: recipe inputs and capital builds, needs, tool baskets, carriage and navy
    wear, held durables, and the goods the state and army budgets name."""
    consumed: Set[str] = set(state_goods)
    for key, entry in production.items():
        consumed.update(entry.get("inputs") or {})
        if any(entry.get(field) for field in ("thermal_mj", "mechanical_mj", "electrical_mj")):
            consumed.update(("thermal_mj",) if entry.get("thermal_mj") else ())
            consumed.update(("mechanical_mj",) if entry.get("mechanical_mj") else ())
            consumed.update(("electrical_mj",) if entry.get("electrical_mj") else ())
        for capital in entry.get("capital") or []:
            consumed.update(capital.get("build_materials") or {})
        if entry.get("carrier_use") or entry.get("naval_crew") or entry.get("capital_asset"):
            consumed.update((entry.get("outputs") or {key: 1}))
        if entry.get("satisfies"):
            consumed.update(entry.get("outputs") or {key: 1})
    consumed.update(good for good, attributes in need_goods.items() if attributes.get("satisfies"))
    consumed.update(service_lives)
    for fields in trade_registry.values():
        consumed.update(fields.get("tool_basket") or ())
        consumed.update(fields.get("tool_stock_per_worker") or ())
    return consumed


def dead_end_goods(production: Mapping[str, Mapping[str, Any]], need_goods: Mapping[str, Any],
                   service_lives: Mapping[str, Any], trade_registry: Mapping[str, Mapping[str, Any]],
                   state_goods: Iterable[str] = (),
                   tree_materials: Iterable[str] = ()) -> Tuple[List[str], List[str]]:
    """(goods nothing consumes, goods only tree nodes consume), each sorted."""
    consumed = consumed_goods(production, need_goods, service_lives, trade_registry, state_goods)
    unconsumed = sorted(produced_goods(production) - consumed)
    tree = set(tree_materials)
    return ([good for good in unconsumed if good not in tree], [good for good in unconsumed if good in tree])


def report_lines(production, need_goods, service_lives, trade_registry, state_goods, tree_materials) -> List[str]:
    nothing, only_nodes = dead_end_goods(production, need_goods, service_lives, trade_registry, state_goods, tree_materials)
    lines = ["produced goods nothing consumes: %d; consumed only by tech-tree nodes: %d" % (len(nothing), len(only_nodes))]
    lines.append("  no consumer: " + (", ".join(nothing) or "(none)"))
    return lines


def state_goods() -> Set[str]:
    """The goods the state and army budget lines name in code (the dole and the army's equipment)."""
    from sim.agents.api import DOLE_MATERIAL, EQUIPMENT_MATERIAL
    return {DOLE_MATERIAL, EQUIPMENT_MATERIAL}
