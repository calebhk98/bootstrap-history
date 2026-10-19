"""What the opening's households own of the firms, before the firms exist.

The opening settles households' income (opening_income.py) from the demand it pays for, ahead of the producers
sized to that demand. A household counts what it owns of those producers among the wealth it wants to hold
(equity.py), so the settlement reads the same from the producers the runs imply: plant at replacement cost and
the working capital each keeps, shared across the cohorts by people and ownership share.
"""
import math
from typing import Dict, Mapping

from . import opening_income, unit_cost
from .market_memory import YearView
from .producers_close import working_capital_target
from .types import AgentId, GoodId, Recipe


class OpeningView(YearView):
    """The opening's market view; `owned` holds each cohort's equity once the settlement has set it."""

    def __init__(self, *arguments, **keywords) -> None:
        super().__init__(*arguments, **keywords)
        self.owned: Dict[AgentId, float] = {}

    def equity(self, agent: AgentId) -> float:
        return self.owned.get(agent, 0.0)


def firms_worth(runs: Mapping[str, float], recipes: Mapping[str, Recipe], prices: Mapping[GoodId, float],
                wages: Mapping[str, float]) -> float:
    """Worth of the producers that make `runs` at the opening prices: each recipe's plant at replacement cost
    (sized so the share of it that works makes the runs) and the working capital it keeps."""
    worth = 0.0
    for recipe_id, count in runs.items():
        recipe = recipes[recipe_id]
        capacity = count / opening_income.working_share(recipe, prices, wages) if recipe.plant_life_years > 0.0 else count
        plant = unit_cost.plant_value_per_run(recipe, prices, wages) * capacity if recipe.plant_life_years > 0.0 else 0.0
        capital = working_capital_target(recipe, count, prices, wages)
        worth += (plant if math.isfinite(plant) else 0.0) + capital
    return worth


def split(cohorts, worth: float) -> Dict[AgentId, float]:
    """`worth` shared over the cohorts by their people and the share of the tile's profit each class takes."""
    weights = {cohort.agent_id: cohort.people * cohort.ownership_share for cohort in cohorts}
    total = math.fsum(weights.values())
    return {agent: worth * weight / total for agent, weight in weights.items()} if total > 0.0 else {}
