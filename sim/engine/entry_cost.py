"""What a unit of a good costs a producer that runs one production entry, at the prices the economy shows.

The calculator (`making_cost.cost_of_making`) costs one entry with its inputs, labour, plant and land priced by
the functions handed in: the economy's input prices, its wages, the lending rate and the land rent it lets at.
The market receives the result as a reservation price (producer_costs.py).
"""
from typing import Any, Callable, FrozenSet, Mapping, Optional

from . import making_cost
from . import prices as price_solver


class CostBook:
    """One set of prices, wages, rate and rent that entries are costed against."""

    def __init__(self, input_price_of: Callable[[str], Optional[float]], wage_of: Callable[[str], float],
                 rate: float, rent_of: Optional[Callable[[str], float]] = None,
                 civilization: Optional[Mapping[str, Any]] = None,
                 production: Optional[Mapping[str, Any]] = None) -> None:
        self.production = production if production is not None else price_solver.default_production_entries()
        self.input_price_of = input_price_of
        self.wage_of = wage_of
        self.rate = rate
        self.rent_of = rent_of
        self.civilization = civilization

    def _cost(self, good: str, techniques, include_plant: bool) -> Optional[making_cost.MakingCost]:
        return making_cost.cost_of_making(
            good, techniques, self.input_price_of, self.wage_of, self.rate, rent_of=self.rent_of,
            reference_price_of=self.input_price_of,   # a joint run is split by its outputs' worth at these prices
            include_plant=include_plant, production=self.production, civilization=self.civilization)

    def unit_cost(self, entry_key: str, material: str, include_plant: bool = True) -> Optional[float]:
        """Money one unit of `material` costs when made by this entry with every input bought at the book's
        prices; None where the entry does not make it or an input has no price. Without `include_plant` the
        plant's repayment is left out: the running cost of a built plant."""
        entry = self.production.get(entry_key)
        if entry is None or material not in (entry.get("outputs") or {}):
            return None
        made = self._cost(material, entry_key, include_plant)
        return None if made is None else made.unit_cost

    def running_unit_cost(self, entry_key: str, material: str) -> Optional[float]:
        """What a unit costs a producer whose plant is built: the full cost without the plant's repayment."""
        return self.unit_cost(entry_key, material, include_plant=False)

    def running_share(self, entry_key: str, material: str) -> Optional[float]:
        """Running cost over full cost of a unit of `material` by this entry (one where it has no plant);
        None where it cannot be costed."""
        full = self.unit_cost(entry_key, material)
        running = self.running_unit_cost(entry_key, material)
        if full is None or running is None or not full > 0.0:
            return None
        return min(1.0, max(0.0, running / full))

    def cheapest_entry(self, material: str, techniques: FrozenSet[str]) -> Optional[str]:
        """The entry the held techniques make `material` cheapest by at the book's prices, or None."""
        made = self._cost(material, techniques, True)
        return None if made is None else made.recipe_id
