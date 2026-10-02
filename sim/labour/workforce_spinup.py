"""Starting non-farm workforce per trade, produced by a labour-market spin-up.

Inputs are only what a civilisation already has: the techniques its known
technologies unlock and household demand. Labour need per trade comes from
the goods households consume and the recipes that make them, through the whole
recipe graph. A neutral (equal) split of the workforce is then stepped through
sim.labour.labour_market until the trade split stops moving.

[temporary_heuristic] A need's budget is split equally by labour value across
the available goods that satisfy it, an end good (one no available recipe
consumes) that no need names takes an equal generic weight, and a material
with several available producers is split equally among them, until
price-responsive shares and technique-choice costs exist to replace these.

Farm labour is not decided here; the engine pins it from the farm-labour
logic in sim.world.agriculture and this module splits the remaining hours.
"""
import collections
import hashlib
import json
import os
import tempfile
from typing import Any, Dict, Iterable, Mapping, Optional, Set

from sim.constants import declare
from sim.solve_prices_core import techniques_available_to
from sim.world import demand, need_demand
from sim.labour import labour_market

# Trade whose hours the farm-labour logic owns; its recipe hours are not part
# of the non-farm split.
FARM_TRADE = "labourer"

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CACHE_DIRECTORY = os.path.join(_REPOSITORY_ROOT, ".cache", "workforce_spinup")

SPIN_UP_MAX_YEARS = declare(
    "SPIN_UP_MAX_YEARS", 5000,
    kind="temporary_heuristic",
    unit="years of labour-market stepping before the spin-up gives up",
    why="A bound so a demand structure the mobility friction cannot settle "
        "reports non-convergence instead of looping. Generous against the "
        "occupational mobility rate so that a normal start converges well "
        "inside it; it is not a target and no start depends on reaching it.")

SPIN_UP_SHARE_TOLERANCE = declare(
    "SPIN_UP_SHARE_TOLERANCE", 1e-6,
    kind="temporary_heuristic",
    unit="largest change in any trade's share of non-farm hours between two "
         "consecutive years, as a fraction of non-farm hours",
    why="Convergence criterion: the split has stabilised when no trade's "
        "share moves by more than this in a year. Tight enough that a later "
        "year's reallocation starts from a rest state, loose enough to be "
        "reached in floating point.")


def _needs() -> Dict[str, Any]:
    from sim.engine import need_data
    return need_data.load_needs(_REPOSITORY_ROOT)


def _dominant_output(entry: Mapping[str, Any]) -> Optional[str]:
    outputs = entry.get("outputs") or {}
    if not outputs:
        return None
    return labour_market._dominant_output_key(entry)


def _input_coefficients(recipe_id: str, production: Mapping[str, Any]) -> Dict[str, float]:
    return demand.input_coefficients_per_unit_output(recipe_id, dict(production))


def _labour_coefficients(recipe_id: str, production: Mapping[str, Any]) -> Dict[str, float]:
    coefficients = labour_market.labour_hours_coefficients_per_unit_output(
        recipe_id, dict(production))
    coefficients.pop(FARM_TRADE, None)
    return coefficients


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


def need_shares_by_trade(production: Mapping[str, Any],
                         reached_nodes: Iterable[str]) -> Dict[str, float]:
    """Share of non-farm labour each trade is needed for, from the goods
    households consume and the available recipes that make them. Trades with
    no available recipe are absent."""
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
        # A unit of labour value: weight is spread over the good's trades in
        # proportion to the hours its whole supply chain uses.
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


SpinUpResult = collections.namedtuple(
    "SpinUpResult", ["shares_by_trade", "years", "converged", "final_share_change"])


def spin_up(production: Mapping[str, Any], reached_nodes: Iterable[str],
            max_years: int = SPIN_UP_MAX_YEARS,
            tolerance: float = SPIN_UP_SHARE_TOLERANCE) -> SpinUpResult:
    """Step an equal (neutral) split of one unit of non-farm hours toward
    the need, through labour_market.Workforce, until it stops moving."""
    reached = set(reached_nodes)
    need = need_shares_by_trade(production, reached)
    if not need:
        return SpinUpResult({}, 0, True, 0.0)
    trades = sorted(need)
    workforce = labour_market.Workforce({trade: 1.0 / len(trades) for trade in trades})
    walkable = labour_market.trades_reachable_given_technology(reached, dict(production))
    change = float("inf")
    years = 0
    while years < max_years:
        before = dict(workforce.hours_by_trade)
        workforce.step(need, walkable_trades=walkable)
        years += 1
        change = max(abs(workforce.hours_by_trade[trade] - before[trade]) for trade in trades)
        if change <= tolerance:
            break
    total = workforce.total_hours()
    shares = {trade: workforce.hours_by_trade[trade] / total for trade in trades}
    return SpinUpResult(shares, years, change <= tolerance, change)


_in_process_cache: Dict[str, SpinUpResult] = {}


def forget_in_process_cache() -> None:
    _in_process_cache.clear()


def _cache_key(production: Mapping[str, Any], reached_nodes: Set[str]) -> str:
    available, _unreached, _unclassified = techniques_available_to(production, reached_nodes)
    payload = json.dumps(
        {"recipes": available, "reached": sorted(reached_nodes),
         "needs": _needs(),
         "parameters": [SPIN_UP_MAX_YEARS, SPIN_UP_SHARE_TOLERANCE,
                        labour_market.OCCUPATIONAL_MOBILITY_RATE_PER_YEAR,
                        labour_market.OCCUPATIONAL_MOBILITY_GAP_RESPONSE_GAIN,
                        labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR]},
        sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def cached_spin_up(production: Mapping[str, Any], reached_nodes: Iterable[str],
                   cache_dir: Optional[str] = None) -> SpinUpResult:
    """spin_up, remembered per input set: the key hashes the available
    recipes and known technologies, so a different mod set or civilisation
    is a different entry. A cache that cannot be read or written is skipped."""
    reached = set(reached_nodes)
    key = _cache_key(production, reached)
    directory = cache_dir or DEFAULT_CACHE_DIRECTORY
    memo_key = directory + "|" + key
    if memo_key in _in_process_cache:
        return _in_process_cache[memo_key]
    path = os.path.join(directory, key + ".json")
    result = None
    try:
        with open(path, encoding="utf-8") as handle:
            result = SpinUpResult(**json.load(handle))
    except (OSError, ValueError, TypeError):
        result = None
    if result is None:
        result = spin_up(production, reached)
        try:
            os.makedirs(directory, exist_ok=True)
            handle_fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                json.dump(result._asdict(), handle, sort_keys=True)
            os.replace(temporary, path)
        except OSError:
            pass
    _in_process_cache[memo_key] = result
    return result
