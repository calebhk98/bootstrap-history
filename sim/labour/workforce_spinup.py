"""Each non-farm trade's share of the labour the society's demand puts on it.

Inputs are only what a civilisation already has: the techniques its known
technologies unlock and household demand. Labour need per trade comes from
the goods households consume and the recipes that make them, through the whole
recipe graph. The engine splits non-farm hours by these shares until the agent
economy has opened (labour_allocation.py); once it has, the labour core's people decide.

A need's budget is split among the available goods that satisfy it by the same constant-elasticity
mix households use (sim/world/need_basket.py), with a good's labour value per unit of need as its
price. An end good (one no available recipe consumes) that no need names has no demand of its own: it
is made only as far as the recipes that use it ask.

[temporary_heuristic] A material with several available producers is split equally among them, until
technique-choice costs exist to replace this; labour value stands for price until prices are known here.

Carriage is part of a good's chain: every tonne a recipe makes is carried by the crews of the carriage modes
the society's technologies unlock, as far as the tonne's value pays for and no farther than between the realm's
own tiles (workforce_carriage.py, from geography's rates and market reach).
Farm hours count in a chain's total, so a farm-heavy good gives the other trades only their own slice.

Farm labour is not decided here; the engine pins it from the farm-labour
logic in sim.world.agriculture and this module splits the remaining hours.
"""
import collections
import os
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import demand, need_demand
from sim.labour import labour_market, legacy_trade_defaults, workforce_carriage

FARM_TRADE = legacy_trade_defaults.FARM_TRADE

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _needs() -> Dict[str, Any]:
    return need_demand.load_needs(_REPOSITORY_ROOT)


def _dominant_output(entry: Mapping[str, Any]) -> Optional[str]:
    outputs = entry.get("outputs") or {}
    if not outputs:
        return None
    return labour_market._dominant_output_key(entry)


# Recipe fields that draw an energy carrier; the carrier is the material of the same name that the
# energy techniques (thermal_mj_charcoal, mechanical_mj_waterwheel, ...) output.
ENERGY_CARRIER_FIELDS = ("thermal_mj", "mechanical_mj", "electrical_mj")


def _input_coefficients(recipe_id: str, production: Mapping[str, Any]) -> Dict[str, float]:
    """Materials consumed per unit of the recipe's dominant output: its inputs and amortised capital, plus the
    energy it draws, which the techniques that supply that carrier must make."""
    coefficients = demand.input_coefficients_per_unit_output(recipe_id, dict(production))
    entry = production[recipe_id]
    basis_quantity = entry["outputs"][_dominant_output(entry)]
    for carrier in ENERGY_CARRIER_FIELDS:
        drawn = entry.get(carrier)
        if drawn:
            coefficients[carrier] = coefficients.get(carrier, 0.0) + drawn / basis_quantity
    return coefficients


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
                         carriage: Optional[workforce_carriage.Carriage] = None,
                         civ_values: Optional[Mapping[str, Any]] = None) -> Dict[str, float]:
    """Share of non-farm labour each trade is needed for, from the goods
    households consume and the available recipes that make them. Trades with
    no available recipe, or whose goods nothing demands, are absent. `techniques_available_to(production, reached)` is the engine's
    filter, returning (available, unreached, unclassified). `carriage` (workforce_carriage) says what a
    tonne costs to carry; every tonne a recipe in a good's chain makes is carried as far as its value pays
    for, so the carriers take their share of the good's labour."""
    carriage = carriage or workforce_carriage.Carriage()
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

    def chain_hours_per_unit(material: str) -> float:
        levels = _solve_levels({material: 1.0}, producers, input_coefficients)
        return sum(level * per_unit for recipe_id, level in levels.items()
                   for per_unit in labour[recipe_id].values())

    carriage_cache: Dict[str, Dict[str, float]] = {}

    def carriage_hours_per_tonne(recipe_id: str) -> Dict[str, float]:
        # Crew hours to carry a tonne this recipe makes: as far as its value (the labour of its whole chain
        # per tonne) pays for, unless the recipe states a distance (water drawn where it is used states none).
        if recipe_id not in carriage_cache:
            tonnes = tonnes_per_unit_output[recipe_id]
            value = chain_hours_per_unit(dominant[recipe_id]) / tonnes if tonnes > 0.0 else 0.0
            carriage_cache[recipe_id] = carriage.hours_per_tonne_by_trade(
                value, available[recipe_id].get("carriage_km"))
        return carriage_cache[recipe_id]

    def trade_hours_per_unit(material: str) -> Dict[str, float]:
        levels = _solve_levels({material: 1.0}, producers, input_coefficients)
        hours: Dict[str, float] = collections.defaultdict(float)
        for recipe_id, level in levels.items():
            for trade, per_unit in labour[recipe_id].items():
                hours[trade] += level * per_unit
            tonnes = level * tonnes_per_unit_output[recipe_id]
            if tonnes > 0.0:
                for trade, per_tonne in carriage_hours_per_tonne(recipe_id).items():
                    hours[trade] += tonnes * per_tonne
        return hours

    # Household demand: each need's budget goes to the available goods that satisfy it, split by what
    # a unit of need costs in labour. An end good no need names has no budget of its own.
    needs = _needs()
    demanded_goods = need_demand.budget_weights_by_good(needs, available, set(producers), civ_values=civ_values)
    labour_value = {material: sum(trade_hours_per_unit(material).values()) for material in demanded_goods}
    budget = need_demand.budget_weights_by_good(needs, available, set(producers), labour_value, civ_values)

    total_by_trade: Dict[str, float] = collections.defaultdict(float)

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

    for material, weight in budget.items():
        add_budget(material, weight)

    total_by_trade.pop(FARM_TRADE, None)
    total = sum(total_by_trade.values())
    if total <= 0.0:
        return {}
    return {trade: hours / total for trade, hours in sorted(total_by_trade.items())
            if hours > 0.0}
