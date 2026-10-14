"""What a unit of a good costs to make, at prices the caller hands in (Complaints/507).

`cost_of_making` costs one good through the cheapest technique a held technology set allows: inputs at
`input_price_of`, labour at `wage_of`, the plant's repayment at `rate`, energy by the capability grade the
recipe needs, rent as given. It reads no population, income or demand, so the same arguments give the same cost
for any actor: a firm judging an entry, a state, a founder, the long-run table (`long_run_costs.py`).

Money is whatever unit the prices and wages are in; the result is in that unit.
"""
import collections
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, Iterable, Mapping, Optional, Union

from sim.engine import disposal_cost, solve_prices_core as core, solve_prices_round
from sim.engine import prices as price_engine

LAND_MATERIAL = "hectare_land"

Techniques = Union[FrozenSet[str], Iterable[str], str]


@dataclass(frozen=True)
class MakingCost:
    """Unit cost of a good, the recipe that makes it cheapest, and where the cost comes from (each share is
    money per unit of the good; they add up to `unit_cost`)."""
    unit_cost: float
    recipe_id: str
    input_cost: Dict[str, float] = field(default_factory=dict)
    trade_cost: Dict[str, float] = field(default_factory=dict)
    plant_cost: float = 0.0
    rent_cost: float = 0.0
    energy_cost: float = 0.0
    holding_cost: float = 0.0


class _Prices:
    """A price lookup over a function; a good the function has no price for has none."""

    def __init__(self, input_price_of: Callable[[str], Optional[float]], rent_of: Optional[Callable[[str], float]]):
        self.input_price_of = input_price_of
        self.rent_of = rent_of

    def get(self, material: str, default: Optional[float] = None) -> Optional[float]:
        price = self.input_price_of(material)
        if price is None and material == LAND_MATERIAL:
            price = self.rent_of(material) if self.rent_of is not None else 0.0
        return default if price is None else price

    def __getitem__(self, material: str) -> float:
        price = self.get(material)
        if price is None:
            raise KeyError(material)
        return price

    def __contains__(self, material: str) -> bool:
        return self.get(material) is not None


class _Function:
    """A mapping read through a function, for the lookups the cost arithmetic does by key."""

    def __init__(self, function: Callable[[str], float]):
        self.function = function

    def get(self, key: str, default: float = 0.0) -> float:
        value = self.function(key)
        return default if value is None else value

    __getitem__ = get


@dataclass
class _Catalogue:
    """What a technology set allows: the recipes, who makes what, and the energy grades they need."""
    available: Dict[str, Any]
    producers_of: Dict[str, Any]
    floor_by_carrier: Dict[str, float]
    required_grades: Dict[str, Any]
    suppliers: Dict[str, Any]


_CATALOGUES: Dict[Any, Any] = {}


def _catalogue(production: Mapping[str, Any], techniques: Techniques) -> _Catalogue:
    if isinstance(techniques, str):
        entries = {techniques: production[techniques]} if techniques in production else {}
        key = ("recipe", techniques)
    else:
        gates = frozenset(price_engine.all_gate_nodes(production) & set(techniques))
        entries = None
        key = ("gates", gates)
    cached = _CATALOGUES.get(key)
    if cached is not None and cached[0] is production:
        return cached[1]
    if entries is None:
        entries, _unreached, _unclassified = core.techniques_available_to(production, gates)
    required = core.capability_required_grades(entries)
    built = _Catalogue(entries, core.build_producers_index(entries), core.capability_floor_by_carrier(entries),
                       required, solve_prices_round.band_suppliers(required, entries))
    _CATALOGUES[key] = (production, built)
    return built


def cost_of_making(good: str,
                   techniques: Techniques,
                   input_price_of: Callable[[str], Optional[float]],
                   wage_of: Callable[[str], float],
                   rate: float,
                   rent_of: Optional[Callable[[str], float]] = None,
                   reference_price_of: Optional[Callable[[str], Optional[float]]] = None,
                   include_plant: bool = True,
                   production: Optional[Mapping[str, Any]] = None,
                   civilization: Optional[Mapping[str, Any]] = None) -> Optional[MakingCost]:
    """The cheapest cost of one unit of `good`, or None when nothing the techniques allow can make it or an
    input has no price.

    `techniques` is the held gate nodes, or one recipe id to cost that recipe alone. `rent_of(key)` is money
    per unit of an extracted good (and per hectare-year of land); None charges none. `reference_price_of(good)`
    is what a joint run's outputs are worth, to split the run's cost by value; an output it gives none for is
    valued at what its cheapest sole-output route costs now, else by mass (sim/engine/joint_allocation.py).
    `include_plant` False is the running cost of a plant already built. `civilization` supplies the state's
    waste-dumping rule.
    """
    production = production if production is not None else price_engine.default_production_entries()
    catalogue = _catalogue(production, techniques)
    prices = _Prices(input_price_of, rent_of)
    wages = _Function(wage_of)
    rents = _Function(rent_of) if rent_of is not None else {}
    dump_distance = price_engine.waste_dump_minimum_distance(civilization)
    bands = solve_prices_round.band_prices(
        catalogue.required_grades, catalogue.suppliers, prices, wages, rents, rate)

    def bill(recipe_id: str) -> Optional[Dict[str, Any]]:
        return _bill(recipe_id, catalogue.available[recipe_id], prices, wages, rents, rate, bands, include_plant)

    best = None
    for recipe_id in catalogue.producers_of.get(good, ()):
        entry = catalogue.available[recipe_id]
        if not core._meets_capability_floor(good, entry, catalogue.floor_by_carrier):
            continue
        if civilization is not None and not price_engine.climate_allows_entry(entry, civilization):
            continue
        costed = bill(recipe_id)
        if costed is None:
            continue
        outputs = entry["outputs"]
        references = {}
        if len(outputs) > 1:
            references = _references(outputs, reference_price_of, catalogue, bill)
        disposal_costs = (disposal_cost.disposal_cost_by_material(outputs, prices, rate, dump_distance)
                          if len(outputs) > 1 else None)
        unit_cost = core._allocate_output_prices(
            outputs, prices, costed["total"], references, rate, disposal_costs)[good]
        if best is None or unit_cost < best[0]:
            best = (unit_cost, recipe_id, costed)
    if best is None:
        return None
    unit_cost, recipe_id, costed = best
    scale = unit_cost / costed["raw_total"] if costed["raw_total"] > 0.0 else 0.0
    return MakingCost(
        unit_cost=unit_cost, recipe_id=recipe_id,
        input_cost={material: cost * scale for material, cost in costed["inputs"].items()},
        trade_cost={trade: cost * scale for trade, cost in costed["trades"].items()},
        plant_cost=costed["plant"] * scale, rent_cost=costed["rent"] * scale,
        energy_cost=costed["energy"] * scale, holding_cost=costed["holding"] * scale)


def _references(outputs: Mapping[str, float], reference_price_of, catalogue: _Catalogue, bill) -> Dict[str, float]:
    """The worth of each output of a joint run: the caller's, else the cheapest sole-output route's."""
    references = {}
    for output in outputs:
        given = reference_price_of(output) if reference_price_of is not None else None
        if given is not None:
            references[output] = given
            continue
        direct = [costed["total"] / entry["outputs"][output]
                  for recipe_id in catalogue.producers_of.get(output, ())
                  for entry in (catalogue.available[recipe_id],)
                  if len(entry["outputs"]) == 1
                  for costed in (bill(recipe_id),) if costed is not None]
        if direct:
            references[output] = min(direct)
    return references


def _bill(recipe_id: str, entry: Mapping[str, Any], prices: _Prices, wages: _Function, rents, rate: float,
          bands, include_plant: bool) -> Optional[Dict[str, Any]]:
    """The cost of one batch of a recipe by source, or None when an input has no price."""
    inputs = entry.get("inputs") or {}
    waste_costs = None
    if any(prices.get(material, 0.0) < 0.0 for material in inputs):
        waste_costs = disposal_cost.disposal_cost_by_material(inputs, prices, rate)
    material_cost = core._material_cost_hours(inputs, prices, waste_costs)
    land_cost = core._land_cost_hours(entry, prices)
    capital_cost = core._capital_cost_hours_per_unit(
        (entry.get("capital") or []) if include_plant else [], prices, wages, rate)
    energy_cost = core._energy_cost_hours(entry, prices, bands)
    if None in (material_cost, land_cost, capital_cost, energy_cost):
        return None
    outputs = entry.get("outputs") or {}
    batch = max(outputs.values()) if outputs else 1.0
    per_input = collections.OrderedDict()
    for material, quantity in inputs.items():
        price = prices.get(material)
        if price < 0.0:
            price = max(price, -(waste_costs or {}).get(material, 0.0))
        per_input[material] = quantity * price
    trades = {trade: hours * wages[trade] for trade, hours in (entry.get("labour_hours") or {}).items()}
    rent = core._extraction_rent_cost_hours(outputs, rents) + land_cost
    holding = material_cost * rate * float(entry.get("holding_years") or 0.0)
    plant = capital_cost * batch
    raw_total = material_cost + sum(trades.values()) + rent + plant + energy_cost + holding
    return {"total": max(0.0, raw_total), "raw_total": raw_total, "inputs": per_input, "trades": trades,
            "plant": plant, "rent": rent, "energy": energy_cost, "holding": holding}
