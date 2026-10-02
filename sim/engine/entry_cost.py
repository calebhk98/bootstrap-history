"""What a unit of a good costs a producer that runs one production entry, at the input prices it faces.

This is the price solver's remaining job in the market: not "the price of the good" but the cost of one
entry, with its inputs, labour, plant and land priced at the prices handed in (the market's, not a
re-solved cheapest route). The market receives the result as a reservation price.
"""
from typing import Any, Dict, FrozenSet, Mapping, Optional

from sim import joint_allocation, solve_prices, solve_prices_core

from . import prices as price_solver

# {(gate nodes, civilisation, wage ratios, territory): (production table, wages, rent)}
_CONTEXTS: Dict[Any, Any] = {}


def _context(production: Mapping[str, Any], gates: FrozenSet[str], civilization: Mapping[str, Any],
             document_ratios: Dict[str, float]):
    key = (gates, civilization["id"], tuple(sorted(document_ratios.items())),
           price_solver.territory_fingerprint(civilization))
    cached = _CONTEXTS.get(key)
    if cached is not None and cached[0] is production:
        return cached[1], cached[2]
    available, _unreached, _unclassified = solve_prices.techniques_available_to(production, gates)
    wage_by_trade = price_solver.solver_wage_ratios(production, document_ratios)
    rent = solve_prices.rent_hours_per_kg_by_ore_material(available, wage_by_trade)
    rent.update(solve_prices.land_rent_hours_per_hectare(
        available, wage_by_trade, civilization_id=civilization["id"],
        civilizations={civilization["id"]: civilization}))
    _CONTEXTS[key] = (production, wage_by_trade, rent)
    return wage_by_trade, rent


def unit_cost_hours(entry_key: str, material: str, prices_in_hours: Mapping[str, float],
                    wage_document: Mapping[str, Any], civilization: Mapping[str, Any],
                    held: FrozenSet[str], production: Optional[Mapping[str, Any]] = None
                    ) -> Optional[float]:
    """Labour hours one unit of `material` costs when made by this entry with every input bought at
    `prices_in_hours`; None where the entry does not make it or an input has no price."""
    production = production if production is not None else price_solver.default_production_entries()
    entry = production.get(entry_key)
    if entry is None or material not in (entry.get("outputs") or {}):
        return None
    gates = frozenset(price_solver.all_gate_nodes(production) & held)
    wage_by_trade, rent = _context(production, gates, civilization,
                                   solve_prices.wage_ratios_by_trade(wage_document))
    anchors = joint_allocation.build_demand_anchors(civilization["id"], civilization=civilization)
    result = solve_prices_core.recipe_cost_and_allocation(
        entry_key, entry, prices_in_hours, wage_by_trade, rent_hours_per_kg_by_material=rent,
        demand_anchor_price_by_material=anchors.prices(prices_in_hours) if anchors else None,
        interest_rate=float(civilization["starting_interest_rate"]))
    return None if result is None else result[1].get(material)
