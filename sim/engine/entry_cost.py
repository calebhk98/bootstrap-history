"""What a unit of a good costs a producer that runs one production entry, at the input prices it faces.

This is the price solver's remaining job in the market: not "the price of the good" but the cost of one
entry, with its inputs, labour, plant and land priced at the prices handed in (the market's, not a
re-solved cheapest route). The market receives the result as a reservation price.
"""
from typing import Any, Dict, FrozenSet, Mapping, Optional

from sim.engine import rent_standin, solve_prices, solve_prices_core

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
    rent = rent_standin.stand_in_rent(
        available, wage_by_trade, civilization_id=civilization["id"],
        civilizations={civilization["id"]: civilization})
    _CONTEXTS[key] = (production, wage_by_trade, rent)
    return wage_by_trade, rent


class CostBook:
    """The wages and rent one price table is costed against, worked out once."""

    def __init__(self, prices_in_hours: Mapping[str, float], wage_document: Mapping[str, Any],
                 civilization: Mapping[str, Any], held: FrozenSet[str],
                 production: Optional[Mapping[str, Any]] = None) -> None:
        self.production = production if production is not None else price_solver.default_production_entries()
        self.prices = prices_in_hours
        self.civilization = civilization
        gates = frozenset(price_solver.all_gate_nodes(self.production) & held)
        self.wages, self.rent = _context(self.production, gates, civilization,
                                         solve_prices.wage_ratios_by_trade(wage_document))
        self.interest = float(civilization["starting_interest_rate"])

    def unit_cost_hours(self, entry_key: str, material: str, include_capital: bool = True) -> Optional[float]:
        """Labour hours one unit of `material` costs when made by this entry with every input bought at
        the table's prices; None where the entry does not make it or an input has no price. Without
        `include_capital` the plant's repayment is left out: the running cost of a built plant."""
        entry = self.production.get(entry_key)
        if entry is None or material not in (entry.get("outputs") or {}):
            return None
        result = solve_prices_core.recipe_cost_and_allocation(
            entry_key, entry, self.prices, self.wages, rent_hours_per_kg_by_material=self.rent,
            reference_price_by_material=self.prices,    # a joint run is split by the outputs' worth in the table
            interest_rate=self.interest, include_capital=include_capital)
        return None if result is None else result[1].get(material)

    def running_unit_cost_hours(self, entry_key: str, material: str) -> Optional[float]:
        """What a unit costs a producer whose plant is built: the full cost without the plant's repayment."""
        return self.unit_cost_hours(entry_key, material, include_capital=False)

    def running_share(self, entry_key: str, material: str) -> Optional[float]:
        """Running cost over full cost of a unit of `material` by this entry (one where it has no plant);
        None where it cannot be costed."""
        full = self.unit_cost_hours(entry_key, material)
        running = self.running_unit_cost_hours(entry_key, material)
        if full is None or running is None or not full > 0.0:
            return None
        return min(1.0, max(0.0, running / full))
