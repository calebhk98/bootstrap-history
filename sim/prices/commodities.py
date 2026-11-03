"""The curated commodity records of `commodities.json`, loaded through `shared_ledger` in `sim/prices/memos.py`:
the tonnes a year the society brings to market of a catalogued commodity, with the multipliers its built works
raise it by. The live material price and availability rules are in `sim/materials/`, not here."""
import json
import os
from typing import Any, Dict, Iterable, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMMODITIES_FILE = os.path.join(ROOT, "data", "world", "commodities.json")

Commodities = Dict[str, Dict[str, Any]]


def load_commodities() -> Commodities:
    """The commodities table, keyed by commodity id."""
    with open(COMMODITIES_FILE) as handle:
        return json.load(handle)["commodities"]


class CommodityLedger:
    """The curated commodities and how much of each the country produces."""

    def __init__(self, commodities: Optional[Commodities] = None) -> None:
        self.commodities: Commodities = commodities if commodities is not None else load_commodities()

    def best_multiplier(self, commodity_id: str, built: Iterable[str]) -> float:
        """The output multiplier the commodity's production runs at given the built node ids: the best route times every
        multiplier entry built; 1.0 if nothing built changes it."""
        commodity = self.commodities[commodity_id]
        route_best = 1.0
        boost = 1.0
        built = set(built)
        for entry in commodity.get("produced_by", []):
            node = entry.get("node", "")
            is_built = node.startswith("mine:") or node in built
            if not is_built:
                continue
            multiplier = float(entry.get("output_multiplier", 1.0))
            if entry.get("kind") == "multiplier":
                boost *= multiplier
            else:
                route_best = max(route_best, multiplier)
        return route_best * boost

    def country_output(self, commodity_id: str, built: Iterable[str] = ()) -> float:
        """Tonnes a year the whole country produces of the commodity; a manufactured one (with a `recipe`) is capped by
        what its inputs can supply."""
        commodity = self.commodities[commodity_id]
        if commodity.get("recipe"):
            return self._manufactured_output(commodity_id, built)
        base = commodity.get("national_output_t_per_yr")
        if base is None:
            base = commodity.get("import_capacity_t_per_yr", 0.0)
        return base * self.best_multiplier(commodity_id, built)

    def _manufactured_output(self, commodity_id: str, built: Iterable[str]) -> float:
        commodity = self.commodities[commodity_id]
        base = float(commodity.get("national_manufacturing_capacity_t_per_yr", 0.0))
        capacity = base * self.best_multiplier(commodity_id, built)
        limits = [self.country_output(input_id, built) / ratio
                  for input_id, ratio in (commodity.get("recipe") or {}).items() if ratio > 0]
        return min([capacity] + limits)
