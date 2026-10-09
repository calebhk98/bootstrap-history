"""Each non-farm trade's share of the labour the society's demand puts on it.

Inputs are only what a civilisation already has: the techniques its known
technologies unlock and household demand. Labour need per trade comes from
the goods households consume and the recipes that make them, through the whole
recipe graph. The engine splits non-farm hours by these shares when the agent
economy is off (labour_allocation.py); with it on, the labour core's people decide.

[temporary_heuristic] A need's budget is split equally by labour value across
the available goods that satisfy it, an end good (one no available recipe
consumes) that no need names takes an equal generic weight, and a material
with several available producers is split equally among them, until
price-responsive shares and technique-choice costs exist to replace these.

Farm labour is not decided here; the engine pins it from the farm-labour
logic in sim.world.agriculture and this module splits the remaining hours.
"""
import collections
import os
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Set

from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import demand, need_demand
from sim.labour import labour_market, legacy_trade_defaults

FARM_TRADE = legacy_trade_defaults.FARM_TRADE

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _needs() -> Dict[str, Any]:
    return need_demand.load_needs(_REPOSITORY_ROOT)


def _dominant_output(entry: Mapping[str, Any]) -> Optional[str]:
    outputs = entry.get("outputs") or {}
    if not outputs:
        return None
    return labour_market._dominant_output_key(entry)


def _input_coefficients(recipe_id: str, production: Mapping[str, Any]) -> Dict[str, float]:
    return demand.input_coefficients_per_unit_output(recipe_id, dict(production))


def _labour_coefficients(recipe_id: str, production: Mapping[str, Any]) -> Dict[str, float]:
    return labour_market.labour_hours_coefficients_per_unit_output(recipe_id, dict(production))


def _solve_levels(final_demand: Mapping[str, float], producers: Mapping[str, list],
                  input_coefficients: Mapping[str, Mapping[str, float]]) -> Dict[str, float]:
    """Recipe levels (units of each recipe's dominant output) meeting the
    final demand plus the inputs the running recipes consume."""
    levels: Dict[str, float] = collections.defaultdict(float)
    pending = dict(final_demand)
    # Leontief series: each round meets the last round's input demand.
    for _round in range(200):
        next_pending: Dict[str, float] = collections.defaultdict(float)
        for material, quantity in pending.items():
            makers = producers.get(material)
            if not makers or quantity <= 0.0:
                continue
            share = quantity / len(makers)
            for recipe_id in makers:
                levels[recipe_id] += share
                for consumed, per_unit in input_coefficients[recipe_id].items():
                    next_pending[consumed] += share * per_unit
        if sum(next_pending.values()) <= 1e-12 * max(1.0, sum(pending.values())):
            break
        pending = next_pending
    return levels


def need_shares_by_trade(production: Mapping[str, Any], reached_nodes: Iterable[str],
                         techniques_available_to: Callable,
                         carriage_hours_per_tonne: Optional[Mapping[str, float]] = None) -> Dict[str, float]:
    """Share of non-farm labour each trade is needed for, from the goods
    households consume and the available recipes that make them. Trades with
    no available recipe are absent. `techniques_available_to(production, reached)` is the engine's
    filter, returning (available, unreached, unclassified). `carriage_hours_per_tonne` is {trade: hours
    to carry a tonne a typical haul} (workforce_carriage); every tonne a recipe in a good's chain makes
    is carried that far, so the carriers take their share of the good's labour."""
    carriage = dict(carriage_hours_per_tonne or {})
    available, _unreached, _unclassified = techniques_available_to(
        production, set(reached_nodes))
    dominant = {recipe_id: _dominant_output(entry) for recipe_id, entry in available.items()}
    dominant = {recipe_id: material for recipe_id, material in dominant.items() if material}
    producers: Dict[str, list] = collections.defaultdict(list)
    for recipe_id in sorted(dominant):
        producers[dominant[recipe_id]].append(recipe_id)
    input_coefficients = {recipe_id: _input_coefficients(recipe_id, available)
                          for recipe_id in dominant}
    labour = {recipe_id: _labour_coefficients(recipe_id, available) for recipe_id in dominant}

    # A recipe's dominant output as tonnes; a unit that is not a mass is not carried here.
    tonnes_per_unit_output = {
        recipe_id: (demand.mass_in_kg_or_none(material, 1.0) or 0.0) / KILOGRAMS_PER_TONNE
        for recipe_id, material in dominant.items()}

    consumed = set()
    for coefficients in input_coefficients.values():
        consumed.update(coefficients)
    end_goods = {material for material in producers if material not in consumed}

    def trade_hours_per_unit(material: str) -> Dict[str, float]:
        levels = _solve_levels({material: 1.0}, producers, input_coefficients)
        hours: Dict[str, float] = collections.defaultdict(float)
        for recipe_id, level in levels.items():
            for trade, per_unit in labour[recipe_id].items():
                hours[trade] += level * per_unit
            tonnes = level * tonnes_per_unit_output[recipe_id]
            for trade, per_tonne in carriage.items():
                hours[trade] += tonnes * per_tonne
        return hours

    # Household demand: each need's budget goes to the available goods that
    # satisfy it; an end good no need names takes the mean declared weight.
    declared_weight = need_demand.budget_weights_by_good(
        _needs(), available, set(producers))
    # TEMPORARY HEURISTIC: undeclared end goods share equal weight.
    generic_weight = (sum(declared_weight.values()) / len(declared_weight)
                      if declared_weight else 1.0)
    budget: Dict[str, float] = dict(declared_weight)
    for material in sorted(end_goods - set(declared_weight)):
        budget[material] = generic_weight

    total_by_trade: Dict[str, float] = collections.defaultdict(float)
    served_recipes: Set[str] = set()

    def add_budget(material: str, weight: float) -> None:
        # A unit of labour value: weight is spread over the good's trades, farm labour included, in
        # proportion to the hours its whole supply chain uses; the farm slice is dropped at the end,
        # so a farm-heavy good gives the other trades little rather than all of its weight.
        hours = trade_hours_per_unit(material)
        all_hours = sum(hours.values())
        if all_hours <= 0.0:
            return
        for trade, trade_hours in hours.items():
            total_by_trade[trade] += weight * trade_hours / all_hours
        levels = _solve_levels({material: 1.0}, producers, input_coefficients)
        served_recipes.update(recipe_id for recipe_id, level in levels.items() if level > 0.0)

    for material, weight in budget.items():
        add_budget(material, weight)
    # A recipe nothing reaches (a cycle with no end good, or output nobody
    # consumes) still runs for its own output, at the generic good weight.
    for recipe_id in sorted(dominant):
        if recipe_id not in served_recipes:
            add_budget(dominant[recipe_id], generic_weight)

    total_by_trade.pop(FARM_TRADE, None)
    total = sum(total_by_trade.values())
    if total <= 0.0:
        return {}
    return {trade: hours / total for trade, hours in sorted(total_by_trade.items())
            if hours > 0.0}
