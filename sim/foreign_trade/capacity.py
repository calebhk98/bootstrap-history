"""What a foreign economy produces and wants, from its own society.

Demand is its own households' purchases of final goods (its population and income at its own solved prices, held to the income
they have); goods bought only as inputs to other goods are not traded until an industrial demand model prices them. Capacity is
what its own tiles and recipes can supply: a mined commodity follows the shares of the deposits on its tiles; a made or grown one
follows its demand when the economy holds a technique for every step of the chain and every ore deposit on that chain lies on
its tiles; anything else has no capacity and is only bought.

(needs: partner_household_demand, material_commodity, national_output, tracked_materials, mineral_share_of_tiles,
tiles_listed_by)"""
from typing import Any, Dict, Optional, Tuple

from sim.world import demand as demand_model

from . import rules
from .constants import FOREIGN_OPENING_IN_BALANCE, FOREIGN_OUTPUT_PER_POPULATION_SHARE


class Capacity:

    def foreign_supply_tonnes(self, civilization_id: str, material: str) -> float:
        """Tonnes a year a partner can sell of a material: what its own techniques, inputs and regions make, and what it
        holds. Zero when it cannot make the material. A partner's book, once opened, carries its capacity and stock; before
        that the opening figures stand."""
        facts = self.partner_facts(civilization_id)
        commodity = self.needs.material_commodity[material]
        solved = facts["solved_materials"]
        if material not in solved or not self._can_make(civilization_id, material, solved):
            return 0.0
        entry = self.world.market_book.get(civilization_id, {}).get(commodity)
        if entry is not None:
            return entry["capacity_tonnes"] + entry["stock_tonnes"]
        capacity, _demand = self.foreign_opening(civilization_id, commodity, solved)
        if capacity > 0.0 or self._tracked_mineral(commodity):
            return capacity
        output, reference_population = self.needs.national_output[commodity]
        return rules.input_only_supply(output, float(self.partner_civ(civilization_id).get("population") or 0.0),
                                       reference_population, FOREIGN_OUTPUT_PER_POPULATION_SHARE)

    def _tracked_mineral(self, commodity: str) -> bool:
        """Whether some deposit shares out its output over tiles."""
        return commodity in self.needs.tracked_materials()

    def _mineral_share(self, civilization_id: str, commodity: str) -> float:
        """Share of a mined commodity on the tiles the partner holds."""
        tiles = self.needs.tiles_listed_by(self.partner_civ(civilization_id))
        return self.needs.mineral_share_of_tiles(tiles, commodity)

    def _can_make(self, civilization_id: str, material: str, solved: Any, _seen: Optional[frozenset] = None) -> bool:
        """Whether its techniques and regions supply the material: it holds a technique, every input can be had the same way,
        and an ore deposit on the chain is one its regions hold."""
        key = (civilization_id, material)
        if key in self._can_make_cache:
            return self._can_make_cache[key]
        if material not in solved:
            return False
        seen = _seen or frozenset()
        if material in seen:
            return True
        entry = demand_model.production_data().get(material) or {}
        if "deposit" in str(entry.get("extracted_from") or ""):
            commodity = self.needs.material_commodity[material]
            result = (self._tracked_mineral(commodity)
                      and self._mineral_share(civilization_id, commodity) > 0.0)
        else:
            result = all(self._can_make(civilization_id, input_material, solved, seen | {material})
                         for input_material in sorted(entry.get("inputs") or {}))
        if not seen:
            self._can_make_cache[key] = result
        return result

    def _demand_and_make(self, civilization_id: str, solved: Any) -> Dict[str, Tuple[float, float]]:
        """{commodity: (tonnes wanted, tonnes of that it can make)}."""
        cached = self._demand_cache.get(civilization_id)
        if cached is not None:
            return cached
        by_commodity: Dict[str, Tuple[float, float]] = {}
        for material, tonnes in sorted(self.needs.partner_household_demand[civilization_id].items()):
            commodity = self.needs.material_commodity[material]
            wanted, made = by_commodity.get(commodity, (0.0, 0.0))
            by_commodity[commodity] = (wanted + tonnes, made + (
                tonnes if self._can_make(civilization_id, material, solved) else 0.0))
        self._demand_cache[civilization_id] = by_commodity
        return by_commodity

    def foreign_opening(self, civilization_id: str, commodity: str, solved: Any) -> Tuple[float, float]:
        """(capacity tonnes, demand tonnes) a foreign economy opens a commodity with. A mined commodity is its regions' share
        of the national output and its own demand; one nothing can make has no capacity."""
        wanted, made = self._demand_and_make(civilization_id, solved).get(commodity, (0.0, 0.0))
        tracked = self._tracked_mineral(commodity)
        output = self.needs.national_output[commodity][0] if tracked else 0.0
        share = self._mineral_share(civilization_id, commodity) if tracked else 0.0
        return rules.opening_of_commodity(wanted, made, tracked, output, share, FOREIGN_OPENING_IN_BALANCE)

    def partner_entry(self, civilization_id: str, commodity: str, facts: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """The foreign economy's book entry for a commodity, opened from its own society on first use; None when it neither
        makes nor wants the good."""
        book = self.world.market_book.setdefault(civilization_id, {})
        entry = book.get(commodity)
        if entry is None:
            capacity, demand = self.foreign_opening(civilization_id, commodity, facts["solved_materials"])
            if not demand > 0.0:
                return None
            entry = book[commodity] = rules.new_entry(demand, capacity)
        return entry

    def partner_book_entry(self, civilization_id: str, commodity: str) -> Optional[Dict[str, float]]:
        return self.partner_entry(civilization_id, commodity, self.partner_facts(civilization_id))

    def partner_market_book(self, civilization_id: str) -> Dict[str, Dict[str, float]]:
        """The partner's market book by commodity (empty when it has none)."""
        return self.world.market_book.get(civilization_id, {})
