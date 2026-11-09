"""Household cohorts: the agents that stand for a tile's people, one per income class.

A cohort is plain data (it saves as it is). What it holds of goods and money lives in the book, not
here. Its income class follows the opening income distribution; after the opening its income is what
it earns (wages for the hours its workers sell) and owns (a share of the tile's rent and profit).

Functions here: `cohorts_for_tile`, `distribute_property_income`, `labour_offers`.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

import numpy as np

from sim.constants import declare
from sim.world import demand

from sim.labour.api import reservation_wage_per_hour
from .protocols import MarketView
from .types import AgentId, LabourOffer, TileId, TradeId
from .replaced import replaced

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
    last_basket_price_level: float = 1.0
    last_year_income: float = 0.0
    share_wealth: Optional[float] = None   # what it owned of the firms at the last close (None before one)
    planned_spending: float = 0.0      # money placed in bids this year (set when the orders are made, read at the close)
    expected_spending: float = 0.0     # smoothed spending that sizes the stock of durables it wants
    expected_floor_cost: float = 0.0   # smoothed cost of the cohort's need floors; spending beyond it sizes durables
    unmet_floor_by_need: Dict[str, float] = field(default_factory=dict)   # need units short of the floor
    own_plan_by_need: Dict[str, float] = field(default_factory=dict)      # need units it grows with hours kept back
    hired_work_per_person: float = 0.0  # hours of household work a person's share hires this year (household_work_year.py)
    milled_grains: Tuple[str, ...] = ()  # grains it buys milled rather than grinds by hand this year (household_grinding.py)

    def __post_init__(self) -> None:
        self.milled_grains = tuple(self.milled_grains)  # a saved tuple reads back from JSON as a list


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
        reservation = reservation_wage_per_hour(subsistence_cost_per_year, working_hours_per_year,
                                                danger_by_trade.get(trade, 0.0), value_of_life)
        offers.append(LabourOffer(cohort.agent_id, trade, view.area_of(trade, cohort.tile),
                                  workers * working_hours_per_year, reservation))
    return offers


def renewed(cohort: Cohort, **changes) -> Cohort:
    return replaced(cohort, **changes)


# The cohort table (`record.cohorts`) is written only here and in `cohort_close_write.py` / `cohort_people.py`; every other module calls
# one of these. The table is a `CohortStore` (cohort_store.py); a plain mapping (a test's) is written as a dict.

def put_cohort(cohorts: Dict[AgentId, Cohort], cohort: Cohort) -> None:
    """`cohort` is the table's row for its id, new or replacing."""
    if hasattr(cohorts, "put"):
        cohorts.put(cohort)
    else:
        cohorts[cohort.agent_id] = cohort


def put_cohorts(cohorts: Dict[AgentId, Cohort], rows: Mapping[AgentId, Cohort]) -> None:
    for cohort in rows.values():
        put_cohort(cohorts, cohort)


def change_cohort(cohorts: Dict[AgentId, Cohort], cohort_id: AgentId, **changes) -> None:
    """The row for `cohort_id` with these fields changed."""
    if hasattr(cohorts, "set_fields"):
        cohorts.set_fields(cohort_id, **changes)
    else:
        cohorts[cohort_id] = replaced(cohorts[cohort_id], **changes)


def set_people(cohorts: Dict[AgentId, Cohort], cohort_id: AgentId, people: float, working_people: float) -> None:
    """The row for `cohort_id` with these people, of whom `working_people` work (never more than the people)."""
    change_cohort(cohorts, cohort_id, people=people, working_people=min(working_people, people))


def rebase_price_level(cohorts: Dict[AgentId, Cohort]) -> None:
    """Every cohort's last basket price level is one, the new base."""
    if hasattr(cohorts, "set_rows"):
        cohorts.set_rows("last_basket_price_level", np.arange(cohorts.count, dtype=np.int64), 1.0)
    else:
        cohorts.update({agent: renewed(cohort, last_basket_price_level=1.0) for agent, cohort in cohorts.items()})


def set_column(cohorts: Dict[AgentId, Cohort], name: str, values: Mapping[AgentId, float]) -> None:
    """One float field of the cohorts named takes the values."""
    if hasattr(cohorts, "set_column"):
        cohorts.set_column(name, values.keys(), values.values())
    else:
        for cohort_id, value in values.items():
            cohorts[cohort_id] = replaced(cohorts[cohort_id], **{name: value})


def set_work_plans(cohorts: Dict[AgentId, Cohort], plans: Mapping[AgentId, tuple]) -> None:
    """Each cohort's (hired hours a person, own hours, grains bought milled) is stored where it differs from what the cohort holds."""
    if hasattr(cohorts, "set_rows"):
        from .cohort_people import apply_work_plans      # the table's module imports this one
        apply_work_plans(cohorts, plans)
        return
    for cohort_id, (per_person, _own, milled) in plans.items():
        cohort = cohorts[cohort_id]
        if per_person != cohort.hired_work_per_person or tuple(milled) != tuple(cohort.milled_grains):
            change_cohort(cohorts, cohort_id, hired_work_per_person=per_person, milled_grains=milled)
