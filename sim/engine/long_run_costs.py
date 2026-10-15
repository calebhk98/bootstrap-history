"""The long-run cost of making every good a technology set can make (Complaints/507).

`making_cost.cost_of_making` costs one good at prices handed in. This closes it over the recipe graph: every
good costed at the cost of its inputs, the cheapest technique for each, a plant charged at the rate, rent as
given. It is the reference a cost comparison reads, and what the economy's opening is seeded from. It reads no
population, income or demand; the same wages, rate and rent give the same table.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from sim.engine import prices as price_engine
from sim.engine import rent_standin, solve_prices
from sim.engine.making_cost import LAND_MATERIAL


@dataclass(frozen=True)
class LongRunCost:
    """What a unit of a good costs in the long run, the recipe that makes it, and how it is known:
    "solved" under the held techniques, "gated" at a technique one step away."""
    cost: float
    recipe_id: str
    provenance: str


def _trades(production: Mapping[str, Any]) -> Iterable[str]:
    trades = set()
    for entry in production.values():
        trades.update((entry.get("labour_hours") or {}))
        for plant in entry.get("capital") or ():
            trades.update((plant.get("build_labour_hours") or {}))
    trades.add(solve_prices.NUMERAIRE_TRADE)
    return sorted(trades)


def long_run_costs(techniques: Iterable[str],
                   wage_of: Callable[[str], float],
                   rate: float,
                   rent_of: Optional[Callable[[str], float]] = None,
                   civilization: Optional[Mapping[str, Any]] = None,
                   production: Optional[Mapping[str, Any]] = None) -> Dict[str, LongRunCost]:
    """{good: LongRunCost} for the goods the held techniques (or one step beyond them) can make.

    `wage_of(trade)` is money an hour; costs come back in the same money. `rent_of(key)` is money per unit of
    an extracted good (and per hectare of land); None charges none. `civilization` supplies the territory
    whose climate decides which crops are made and the state's waste-dumping rule; the cost reads neither its
    population nor its income.
    """
    production = production if production is not None else price_engine.default_production_entries()
    numeraire = wage_of(solve_prices.NUMERAIRE_TRADE)
    ratios = {trade: wage_of(trade) / numeraire for trade in _trades(production)}
    rent_hours = {}
    if rent_of is not None:
        for key in sorted({material for entry in production.values() for material in entry.get("outputs") or ()}
                          | {LAND_MATERIAL}):
            rent = rent_of(key)
            if rent:
                rent_hours[key] = rent / numeraire
    hours, provenance, recipe = price_engine.priced_goods_in_hours(
        techniques, ratios, production_entries=production, interest_rate=rate, civilization=civilization,
        civilization_id=None if civilization is None else civilization["id"], rent_hours_per_kg_by_material=rent_hours)
    return {good: LongRunCost(cost * numeraire, recipe[good], provenance[good]) for good, cost in hours.items()}


def opening_rent_of(techniques: Iterable[str], wage_of: Callable[[str], float],
                    civilization: Optional[Mapping[str, Any]] = None,
                    production: Optional[Mapping[str, Any]] = None) -> Callable[[str], float]:
    """`rent_of` for `long_run_costs` at the opening: the labelled stand-in (`rent_standin.py`), money an hour of
    the numeraire trade buys times the hours of rent per unit. Ore and land rent are Ricardian margins that need a
    quantity demanded; until the economy's own rent replaces them (ONE_PRICE_OWNER_PLAN.md stage 5) the opening
    fixes it from physical figures and no price."""
    production = production if production is not None else price_engine.default_production_entries()
    numeraire = wage_of(solve_prices.NUMERAIRE_TRADE)
    ratios = price_engine.solver_wage_ratios(
        production, {trade: wage_of(trade) / numeraire for trade in _trades(production)})
    available, _unreached, _unclassified = solve_prices.techniques_available_to(production, frozenset(techniques))
    hours = rent_standin.stand_in_rent(
        available, ratios, civilization_id=None if civilization is None else civilization["id"],
        civilizations=None if civilization is None else {civilization["id"]: civilization})
    return lambda key: hours.get(key, 0.0) * numeraire
