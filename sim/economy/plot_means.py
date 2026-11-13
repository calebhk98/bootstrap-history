"""The hours a household's plot work takes given the means it holds: the tools its workers wear, and the team and
plant the recipe ties up. A short tool is drawn from by the next tool and then by hand (tool_fallback.draws); runs
beyond the plant held (a draught team, a plough) are worked by hand at the recipe's by-hand hours factor. A shortage
asks more hours and never stops the work. Plain functions of the recipe and the stock; any actor can use them."""
import math
from typing import FrozenSet, Mapping

from . import tool_fallback
from .types import GoodId, Recipe, TradeId

_BISECTION_STEPS = 60


def means_goods(recipe: Recipe) -> FrozenSet[GoodId]:
    """The goods whose stock changes the hours of a run: tools, their fallbacks and plant."""
    fallback_goods = {step.good for steps in recipe.tool_fallbacks.values() for step in steps if step.good}
    return frozenset(recipe.tool_wear) | fallback_goods | frozenset(recipe.plant_goods)


def by_hand_factor(recipe: Recipe, trade: TradeId) -> float:
    """The hours factor of working by hand for `trade` (the data's by-hand step of a tool fallback); 1.0 when the
    recipe states none."""
    factors = [step.hours_factor for steps in recipe.tool_fallbacks.values() for step in steps
               if not step.good and trade in step.trades]
    return max([1.0] + factors)


def plant_extra_hours(recipe: Recipe, held: Mapping[GoodId, float], runs: float) -> float:
    """Extra hours for the runs the plant held cannot cover: each run needs `plant_goods` of every plant good, and the
    runs beyond the scarcest one are worked by hand."""
    if runs <= 0.0 or not recipe.plant_goods:
        return 0.0
    covered = min([runs] + [held.get(good, 0.0) / per_run for good, per_run in recipe.plant_goods.items() if per_run > 0.0])
    per_run = math.fsum((by_hand_factor(recipe, trade) - 1.0) * hours for trade, hours in recipe.labour_hours.items())
    return (runs - covered) * per_run


def hours_for_runs(recipe: Recipe, held: Mapping[GoodId, float], runs: float) -> float:
    """Hours `runs` runs take with the stock `held`: the recipe's hours plus the extra a short tool or plant asks."""
    if runs <= 0.0:
        return 0.0
    _used, extra = tool_fallback.draws(recipe, held, runs)
    return runs * math.fsum(recipe.labour_hours.values()) + math.fsum(extra.values()) + plant_extra_hours(recipe, held, runs)


def runs_within(recipe: Recipe, held: Mapping[GoodId, float], hours: float) -> float:
    """The runs `hours` can work with the stock `held` (hours rise with runs, so it is found by halving)."""
    base = math.fsum(recipe.labour_hours.values())
    if hours <= 0.0:
        return 0.0
    if base <= 0.0:
        return math.inf
    low, high = 0.0, hours / base           # the means can only add hours, so `high` runs may be too many
    for _ in range(_BISECTION_STEPS):
        middle = (low + high) / 2.0
        if hours_for_runs(recipe, held, middle) <= hours:
            low = middle
        else:
            high = middle
    return low


def plot_goods(options, recipes: Mapping[str, Recipe]) -> FrozenSet[GoodId]:
    """The goods whose stock matters to the recipes own-plot options grow with (the first option of each need is the one grown)."""
    return frozenset().union(*(means_goods(recipes[rows[0][1]]) for rows in options.values() if rows))


def held_of(view, agent: str, tile: str, goods: FrozenSet[GoodId]) -> Mapping[GoodId, float]:
    """What `agent` holds on `tile` of `goods`."""
    return {good: view.stock(agent, good, tile) for good in sorted(goods)}
