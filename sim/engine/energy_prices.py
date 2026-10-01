"""What an energy carrier costs a given entry, and what a producer of one sells it for.

The goods table prices a carrier (`thermal_mj`, `mechanical_mj`, `electrical_mj`) once, at
the cheapest technique that clears the carrier's universal floor. An entry that states the
temperature it needs pays the cheapest technique that reaches that temperature instead
(`sim/solve_prices_core.py`, per-consumer grading). This module recomputes those graded
prices from the finished solve so a node's revenue values the energy it buys, and the
energy it sells, the way the solver charged the goods it makes.
"""
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from sim import solve_prices
from sim.solve_prices_core import CAPABILITY_CAP_FIELDS, capability_required_grades, recipe_cost_and_allocation

ENERGY_CARRIERS = ("thermal_mj", "mechanical_mj", "electrical_mj")

# {key: (production table, bands, own-cost function)}; `is` confirms a hit
_CACHE: Dict[Tuple[Any, ...], Tuple[Any, Dict[Tuple[str, float], float], Callable]] = {}


class EnergyPrices:
    """Money per megajoule of each carrier for an entry that buys it or sells it.

    `own_cost(entry)` is what the entry's own technique costs a unit of each carrier it makes; where
    given, a producer sells no dearer than that. TRANSITIONAL (CLAUDE.md 4.4): nothing yet says who
    buys the megajoules or how many, so a better engine earns what its technique costs rather than the
    dearer incumbent's price on unlimited volume. It goes when demand for energy is modelled."""

    def __init__(self, pool: Mapping[str, float], bands: Mapping[Tuple[str, float], float],
                 own_cost: Optional[Callable[[Mapping[str, Any]], Mapping[str, float]]] = None):
        self.pool = dict(pool)
        self.bands = dict(bands)
        self.own_cost = own_cost

    def bought(self, carrier: str, entry: Mapping[str, Any]) -> float:
        """The price the entry pays: the band of its own stated requirement, else the pool price."""
        capped = CAPABILITY_CAP_FIELDS.get(carrier)
        if capped:
            required = entry.get(capped[1])
            if required is not None and (carrier, required) in self.bands:
                return self.bands[(carrier, required)]
        return self.pool.get(carrier, 0.0)

    def sold(self, carrier: str, entry: Mapping[str, Any]) -> float:
        """The price a producer earns: the highest band its stated reach clears, else the pool price,
        and no more than its own technique costs."""
        market = self._market(carrier, entry)
        if self.own_cost is None:
            return market
        return min(market, self.own_cost(entry).get(carrier, market))

    def _market(self, carrier: str, entry: Mapping[str, Any]) -> float:
        capped = CAPABILITY_CAP_FIELDS.get(carrier)
        if capped:
            reached = entry.get(capped[0])
            if reached is not None:
                cleared = [required for (name, required) in self.bands
                           if name == carrier and required <= reached]
                if cleared:
                    return self.bands[(carrier, max(cleared))]
        return self.pool.get(carrier, 0.0)


def pool_only(goods: Mapping[str, float]) -> EnergyPrices:
    """Every consumer pays the pool price: what a caller without the solver's tables gets."""
    return EnergyPrices({carrier: goods[carrier] for carrier in ENERGY_CARRIERS if carrier in goods}, {})


def graded(held_technology_ids, prices_json: Dict[str, Any], goods: Mapping[str, float],
           civilization_id: Optional[str] = None, interest_rate: Optional[float] = None) -> EnergyPrices:
    """The graded carrier prices of a society holding these technologies, in the coin of `prices_json`."""
    from . import prices as price_solver
    entries = price_solver.default_production_entries()
    solved = price_solver.solved_prices(held_technology_ids, prices_json, civilization_id=civilization_id,
                                        interest_rate=interest_rate)
    ratios = solve_prices.wage_ratios_by_trade(prices_json)
    key = (solved.gate_nodes_held, solved.civilization_id, tuple(sorted(ratios.items())),
           prices_json["money_per_labour_hour"], solved.interest_rate)
    cached = _CACHE.get(key)
    pool = {carrier: goods[carrier] for carrier in ENERGY_CARRIERS if carrier in goods}
    if cached is not None and cached[0] is entries:
        return EnergyPrices(pool, cached[1], cached[2])
    mature = price_solver.solved_prices(price_solver.all_gate_nodes(entries), prices_json,
                                        civilization_id=civilization_id, interest_rate=interest_rate)
    wage_by_trade = price_solver.solver_wage_ratios(entries, ratios)
    money_per_hour = prices_json["money_per_labour_hour"]
    hour_prices = {material: price / money_per_hour for material, price in goods.items()}
    tables = []
    for table in (solved, mature):
        available, _unreached, _unclassified = solve_prices.techniques_available_to(entries, table.gate_nodes_held)
        tables.append((table, available))
    bands: Dict[Tuple[str, float], float] = {}
    hour_bands: Dict[str, Dict[float, Tuple[float, str]]] = {}
    for carrier, required_values in capability_required_grades(entries).items():
        for required in required_values:
            for table, available in tables:
                found = solve_prices.capability_price_for_requirement(
                    carrier, required, available, table.prices_in_labour_hours, wage_by_trade,
                    interest_rate=table.interest_rate)
                if found is not None:
                    bands[(carrier, required)] = found[0] * money_per_hour
                    hour_bands.setdefault(carrier, {})[required] = found
                    break
    # Keyed by address; the entry itself is kept and confirmed with `is`, so a recycled address cannot match.
    own: Dict[int, Tuple[Mapping[str, Any], Mapping[str, float]]] = {}

    def own_cost(entry: Mapping[str, Any]) -> Mapping[str, float]:
        hit = own.get(id(entry))
        if hit is not None and hit[0] is entry:
            return hit[1]
        result = recipe_cost_and_allocation("node-entry", entry, hour_prices, wage_by_trade,
                                            capability_band_price_by_carrier=hour_bands,
                                            interest_rate=solved.interest_rate)
        cost = {} if result is None else {
            material: price * money_per_hour for material, price in result[1].items()}
        own[id(entry)] = (entry, cost)
        return cost

    _CACHE[key] = (entries, bands, own_cost)
    return EnergyPrices(pool, bands, own_cost)
