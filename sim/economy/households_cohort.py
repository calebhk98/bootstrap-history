"""Household cohorts: the agents that stand for a tile's people, one per income class.

A cohort is plain data (it saves as it is). What it holds of goods and money lives in the book, not
here. Its income class follows the opening income distribution; after the opening its income is what
it earns (wages for the hours its workers sell) and owns (a share of the tile's rent and profit).

Functions here: `cohorts_for_tile`, `distribute_property_income`, `labour_offers`.
"""
import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional

from sim.constants import declare
from sim.world import demand

from . import labour
from .protocols import MarketView
from .types import AgentId, LabourOffer, TileId, TradeId

DEFAULT_INCOME_CLASS_COUNT = declare(
    "DEFAULT_INCOME_CLASS_COUNT", 3, kind="temporary_heuristic",
    unit="income classes per tile", source=None, confidence="D",
    why="Households of one tile are split into a few equal-population classes so that rich and poor "
        "can buy different baskets. Few classes keep the year loop fast; the real count is a trade "
        "between detail and run time, not a fact about the world.")
VALUE_OF_LIFE_YEARS_OF_INCOME = declare(
    "VALUE_OF_LIFE_YEARS_OF_INCOME", 20.0, kind="temporary_heuristic",
    unit="years of subsistence income", source=None, confidence="D",
    why="How many years of subsistence income a worker values his life at, which sets the pay he asks "
        "for a risky trade. Revealed-preference estimates of the value of a life differ widely; one "
        "number stands in until workers' risk attitudes are modelled.")


@dataclass
class Cohort:
    agent_id: AgentId
    tile: TileId
    income_class: int                  # 0 is the poorest
    people: float
    working_people: float
    ownership_share: float             # share of the tile's rent and profit this class receives
    expected_inflation: float = 0.0
    cash_target: float = 0.0           # 0 until the first close; goods_orders then computes it
    last_price_level: float = 1.0
    last_year_income: float = 0.0
    last_year_spending: float = 0.0
    unmet_floor_by_need: Dict[str, float] = field(default_factory=dict)   # need units short of the floor


def cohort_id(tile: TileId, income_class: int) -> AgentId:
    return "household:%s:%d" % (tile, income_class)


def cohorts_for_tile(tile: TileId, people: float, working_share: float, gini: float,
                     class_count: Optional[int] = None,
                     opening_income_per_capita: float = 0.0) -> List[Cohort]:
    """Equal-population classes from poorest to richest. The class's share of the tile's income at
    the opening is the Gini split (a Pareto distribution with that Gini); it becomes the class's
    ownership share and, with `opening_income_per_capita`, its first last-year income."""
    count = DEFAULT_INCOME_CLASS_COUNT if class_count is None else class_count
    if people <= 0.0:
        return []
    bins = sorted(demand.income_bins(people, 1.0, gini, count),
                  key=lambda income_bin: income_bin.income_per_capita_per_year)
    total_income = sum(income_bin.population * income_bin.income_per_capita_per_year for income_bin in bins)
    cohorts = []
    for index, income_bin in enumerate(bins):
        share = income_bin.population * income_bin.income_per_capita_per_year / total_income
        cohorts.append(Cohort(
            agent_id=cohort_id(tile, index), tile=tile, income_class=index, people=income_bin.population,
            working_people=income_bin.population * working_share, ownership_share=share,
            last_year_income=share * people * opening_income_per_capita))
    return cohorts


def distribute_property_income(cohorts: List[Cohort], amount: float) -> Dict[AgentId, float]:
    """A tile's rent and profit income split by what each class owns."""
    total = sum(cohort.ownership_share for cohort in cohorts)
    if total <= 0.0:
        return {cohort.agent_id: 0.0 for cohort in cohorts}
    return {cohort.agent_id: amount * cohort.ownership_share / total for cohort in cohorts}


def labour_offers(cohort: Cohort, workers_by_trade: Mapping[TradeId, float], view: MarketView,
                  subsistence_cost_per_year: float, working_hours_per_year: float,
                  danger_by_trade: Mapping[TradeId, float],
                  value_of_life_years_of_income: Optional[float] = None) -> List[LabourOffer]:
    """One offer per trade the cohort has workers in, at the reservation wage for that trade's danger."""
    value_of_life = (VALUE_OF_LIFE_YEARS_OF_INCOME if value_of_life_years_of_income is None
                     else value_of_life_years_of_income)
    offers = []
    for trade in sorted(workers_by_trade):
        workers = workers_by_trade[trade]
        if workers <= 0.0:
            continue
        reservation = labour.reservation_wage(subsistence_cost_per_year, working_hours_per_year,
                                              danger_by_trade.get(trade, 0.0), value_of_life)
        offers.append(LabourOffer(cohort.agent_id, trade, view.area_of(trade, cohort.tile),
                                  workers * working_hours_per_year, reservation))
    return offers


def renewed(cohort: Cohort, **changes) -> Cohort:
    return dataclasses.replace(cohort, **changes)
