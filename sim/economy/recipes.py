"""Production data read as `types.Recipe`: what one run takes in and puts out, with no engine or tree.

One run is one basis batch of a `data/production/` entry. Which entries are available is the caller's
choice (it knows the techniques; the economy never sees the tree), so every function takes the allowed
ids. Mapping, field by field:

    outputs, inputs, labour_hours   copied (joint outputs kept)
    thermal_mj, mechanical_mj,      become inputs of the same-named good: the energy-carrier entries
    electrical_mj                   output exactly those goods, so heat and shaft work are bought
    capital                         becomes plant: build materials and build hours per run of yearly
                                    capacity (build bill over the runs the plant turns out in a year);
                                    parts of different life are folded onto the longest life by scaling
                                    the shorter-lived parts by how often they are rebuilt in it

`extracted_from` only sets `site_bound`: the recipe runs only where a site is declared (sites.py); which
site, and its grade, come from outside as a `SiteLimit`. `grown_in_climate_classes` becomes
`climate_classes`: the recipe runs only on tiles of those climates (sites.climate_allows).

Not mapped, and why: `land_hectare_years` (a site's fertility is the producer's yield factor, so rent
appears as profit); `energy_mj` (the uncosted
residual); `requires_node`, `temperature_*` (gates the caller applies);
`disposal_value_hours` (a surplus by-product's value is whatever its market clears at); the prose
fields. `unmapped_field_counts` measures this.

`input_depth_order` puts each good after the goods its recipes consume, for the year loop.
"""
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from .types import GoodId, Recipe

ENERGY_CARRIER_FIELDS = ("thermal_mj", "mechanical_mj", "electrical_mj")
MAPPED_FIELDS = frozenset(("outputs", "inputs", "labour_hours", "capital", "extracted_from",
                           "grown_in_climate_classes") + ENERGY_CARRIER_FIELDS)


def _basis_output(recipe_id: str, outputs: Mapping[GoodId, float]) -> float:
    """The output the plant's yearly capacity is quoted in: the entry's own good, else the largest."""
    if recipe_id in outputs:
        return outputs[recipe_id]
    return max(outputs.values())


def _plant(recipe_id: str, entry: Mapping[str, Any], outputs: Mapping[GoodId, float]):
    items = [item for item in entry.get("capital") or ()
             if item.get("annual_output_at_basis", 0) > 0 and item.get("service_life_years", 0) > 0]
    if not items:
        return {}, {}, 0.0
    life = max(float(item["service_life_years"]) for item in items)
    goods: Dict[GoodId, float] = {}
    hours: Dict[str, float] = {}
    for item in items:
        runs_per_year = item["annual_output_at_basis"] / _basis_output(recipe_id, outputs)
        rebuilds = life / item["service_life_years"]
        for good, quantity in (item.get("build_materials") or {}).items():
            goods[good] = goods.get(good, 0.0) + quantity * rebuilds / runs_per_year
        for trade, trade_hours in (item.get("build_labour_hours") or {}).items():
            hours[trade] = hours.get(trade, 0.0) + trade_hours * rebuilds / runs_per_year
    return goods, hours, life


def recipe_from_entry(recipe_id: str, entry: Mapping[str, Any]) -> Recipe:
    outputs = {good: float(quantity) for good, quantity in entry["outputs"].items() if quantity > 0}
    inputs = {good: float(quantity) for good, quantity in (entry.get("inputs") or {}).items() if quantity > 0}
    for carrier in ENERGY_CARRIER_FIELDS:
        if entry.get(carrier, 0) > 0:
            inputs[carrier] = inputs.get(carrier, 0.0) + float(entry[carrier])
    labour = {trade: float(hours) for trade, hours in (entry.get("labour_hours") or {}).items() if hours > 0}
    plant_goods, plant_labour, plant_life = _plant(recipe_id, entry, outputs)
    return Recipe(recipe_id, outputs, inputs, labour, plant_goods, plant_labour, plant_life,
                  site_bound=bool(entry.get("extracted_from")),
                  climate_classes=tuple(entry.get("grown_in_climate_classes") or ()))


def recipes_from_production_data(data: Mapping[str, Mapping[str, Any]],
                                 allowed_entry_ids: Optional[Iterable[str]] = None) -> Dict[str, Recipe]:
    """Recipes keyed by entry id, for the allowed ids (all entries when None); unknown ids are ignored."""
    wanted = sorted(data) if allowed_entry_ids is None else sorted(set(allowed_entry_ids) & set(data))
    return {entry_id: recipe_from_entry(entry_id, data[entry_id]) for entry_id in wanted}


def unmapped_field_counts(data: Mapping[str, Mapping[str, Any]],
                          allowed_entry_ids: Optional[Iterable[str]] = None) -> Dict[str, int]:
    """How many allowed entries carry each field this module does not map."""
    wanted = data if allowed_entry_ids is None else {key: data[key] for key in allowed_entry_ids if key in data}
    counts: Counter = Counter()
    for entry in wanted.values():
        counts.update(field for field in entry if field not in MAPPED_FIELDS)
    return dict(sorted(counts.items()))


def _consumed_by(recipes: Mapping[str, Recipe]) -> Dict[GoodId, Set[GoodId]]:
    """For each good, the goods its recipes consume (plant is built, not consumed, so it is left out)."""
    needs: Dict[GoodId, Set[GoodId]] = {}
    for recipe in recipes.values():
        for output in recipe.outputs:
            needs.setdefault(output, set()).update(good for good in recipe.inputs if good != output)
        for good in recipe.inputs:
            needs.setdefault(good, set())
    return needs


def _components(needs: Mapping[GoodId, Set[GoodId]]) -> List[List[GoodId]]:
    """Tarjan's strongly connected components, iterative, in a fixed order; dependencies come first."""
    index_of: Dict[GoodId, int] = {}
    low: Dict[GoodId, int] = {}
    on_stack: Set[GoodId] = set()
    stack: List[GoodId] = []
    result: List[List[GoodId]] = []
    for root in sorted(needs):
        if root in index_of:
            continue
        work = [(root, iter(sorted(needs[root])))]
        index_of[root] = low[root] = len(index_of)
        stack.append(root)
        on_stack.add(root)
        while work:
            node, neighbours = work[-1]
            advanced = False
            for neighbour in neighbours:
                if neighbour not in index_of:
                    index_of[neighbour] = low[neighbour] = len(index_of)
                    stack.append(neighbour)
                    on_stack.add(neighbour)
                    work.append((neighbour, iter(sorted(needs[neighbour]))))
                    advanced = True
                    break
                if neighbour in on_stack:
                    low[node] = min(low[node], index_of[neighbour])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index_of[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                result.append(sorted(component))
    return result


def input_depth(recipes: Mapping[str, Recipe]) -> Dict[GoodId, int]:
    """Each good's depth: zero for goods nothing is consumed to make, else one more than the deepest
    good consumed. Goods in a cycle share one depth (the cycle counts as a single step)."""
    needs = _consumed_by(recipes)
    depth: Dict[GoodId, int] = {}
    for component in _components(needs):
        members = set(component)
        below = [depth[good] for member in component for good in needs[member]
                 if good not in members]
        level = 1 + max(below) if below else 0
        for member in component:
            depth[member] = level
    return depth


def input_depth_order(recipes: Mapping[str, Recipe]) -> List[GoodId]:
    """Goods ordered so each comes after every good its recipes consume. A cycle is broken by name
    order inside it, so the order is the same on every run. Cycle members then draw on stock."""
    depth = input_depth(recipes)
    return sorted(depth, key=lambda good: (depth[good], good))
