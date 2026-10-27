"""The rules of the price tables and cost books as plain functions of plain values."""
from typing import Any, Dict, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple

# how near a producer is to making a good, least to most
REACH = {"gated": 1, "solved": 2}

# the seller id the goods market gives the home society (sim/markets/goods_imports.py HOME_SELLER)
HOME_SELLER = "home"


def merge_by_reach(incumbent_hours: Mapping[str, float], incumbent_basis: Mapping[str, str],
                   run_hours: Mapping[str, float], run_basis: Mapping[str, str]) -> Tuple[Dict[str, float], Dict[str, str]]:
    """The incumbents' table, with every good the techniques in use reach nearer (or that the incumbents do not reach)
    taken from the run table."""
    hours, basis = dict(incumbent_hours), dict(incumbent_basis)
    for material, source in run_basis.items():
        if REACH.get(source, -1) > REACH.get(basis.get(material), -1):
            hours[material], basis[material] = run_hours[material], source
    return hours, basis


def money_prices(hours: Mapping[str, float], money_per_hour: float) -> Dict[str, float]:
    """Money per unit of every good from its labour-hour price."""
    return {material: price * money_per_hour for material, price in hours.items()}


def priced_key(tag: str, prices: Mapping[str, Any], commodity: Mapping[str, Any]) -> Optional[str]:
    """The key of `prices` that prices a raw material key or a curated commodity id (the material its `price_material`
    names), given the commodity's record; None if `prices` cannot price it."""
    if tag in prices:
        return tag
    if commodity and prices.get(commodity.get("price_material")):
        return commodity["price_material"]
    return None


def basis_with_imports(basis: Optional[str], seller: Optional[str]) -> Optional[str]:
    """"imported" where a trading partner sells what no home producer in reach makes (or sells it though one is), else the
    solver's basis."""
    if seller is not None and (basis is None or seller != HOME_SELLER):
        return "imported"
    return basis


def commodity_map(commodities: Mapping[str, Mapping[str, Any]]) -> Dict[str, str]:
    """material key -> curated commodity id, from each commodity's own material_keys list."""
    mapping: Dict[str, str] = {}
    for commodity_id, commodity in sorted(commodities.items()):
        for material_key in commodity.get("material_keys", []):
            mapping[material_key] = commodity_id
    return mapping


def materials_of(commodity_of_material: Mapping[str, str], commodity: str) -> List[str]:
    """The material keys that trade as one commodity, sorted."""
    return sorted(material for material, group in commodity_of_material.items() if group == commodity)


def entry_indexes(production: Mapping[str, Any]) -> Tuple[Dict[str, List[str]], Dict[FrozenSet[str], List[str]]]:
    """({gate node: keys of the entries it gates}, {outputs: keys of entries making them}), keys in sorted order."""
    by_gate: Dict[str, List[str]] = {}
    by_outputs: Dict[FrozenSet[str], List[str]] = {}
    for key in sorted(production):
        entry = production[key]
        if entry.get("requires_node"):
            by_gate.setdefault(entry["requires_node"], []).append(key)
        if entry.get("outputs"):
            by_outputs.setdefault(frozenset(entry["outputs"]), []).append(key)
    return by_gate, by_outputs


# (production table, its indexes); the table is kept so a hit is confirmed with `is`
_INDEX: List[Any] = [None, None, None]


def entry_keys_held_for(node_id: str, production: Mapping[str, Any], held: Iterable[str]) -> List[str]:
    """Keys of the node's own entries and of every entry a held node gates that makes one of its lines."""
    if _INDEX[0] is not production:
        _INDEX[:] = [production, *entry_indexes(production)]
    by_gate, by_outputs = _INDEX[1], _INDEX[2]
    own = by_gate.get(node_id, [])
    keys = list(own)
    for line in sorted({frozenset(production[key]["outputs"]) for key in own if production[key].get("outputs")},
                       key=sorted):
        for key in by_outputs.get(line, []):
            if production[key].get("requires_node") in held and key not in own:
                keys.append(key)
    return keys


def cost_ratio(own: Optional[float], reference: Optional[float]) -> float:
    """A unit made by an entry over the same made by the reference entry; one where either cannot be costed."""
    return own / reference if own is not None and reference else 1.0


def mean_share(shares: Sequence[float]) -> Optional[float]:
    """The mean of the shares, None where there are none."""
    return sum(shares) / len(shares) if shares else None


def cheapest_ratio(ratios: Sequence[float]) -> float:
    """The least of the ratios; one where a concern holds no entry that makes the good."""
    return min(ratios) if ratios else 1.0
