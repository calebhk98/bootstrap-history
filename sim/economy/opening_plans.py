"""The household plan the opening is solved for: which grains a cohort buys milled and which hours of household work it
hires. A year's households decide both from the prices and wages of the year (`household_work_year.plans`), and their
bids follow; an opening sized to final demand that ignored the decision would size the producers of a grain for
households that then buy it milled, and no labour for the work they hire (Complaint 473). The opening is therefore
solved again with the plans its own solve implies, until they stop changing.

Domestic service is a good made from hours, so the hours a tile's households hire are one more use of its hands. Where
they would take more than the tile's other producers leave, the tile's service price rises until hiring falls
(`households_work.service_price_that_fits`), and the opening posts that price. Plain functions over built inputs."""
import dataclasses
import math
from typing import Callable, Dict, Mapping, Optional, Tuple

from . import household_work_year, households_work, labour_state, year_labour
from .households_cohort import Cohort
from .market_memory import YearView, market_key
from .setup import labour_area
from .types import AgentId, TileId

CohortPlan = Tuple[float, float, Tuple[str, ...]]   # (hours hired a person, hours done itself, grains bought milled)
PLAN_TOLERANCE = 1e-6   # a numerical bound: hours hired a person are a share of the work, so a plan agrees within it
PLAN_FLOOR_HOURS = 1e-3 # a numerical floor under that tolerance (hours a person) so a plan of nothing can agree
PLAN_PASSES = 6          # a numerical bound on solving the opening against the plans it implies (a cycle of the choice ends here)


@dataclasses.dataclass(frozen=True)
class HouseholdPlans:
    by_cohort: Mapping[AgentId, CohortPlan]
    service_price_by_tile: Mapping[TileId, float] = dataclasses.field(default_factory=dict)   # an hour hired costs at least this, where servants are scarce
    margin_by_cohort: Mapping[AgentId, float] = dataclasses.field(default_factory=dict)       # worth of an hour hired less its price: who hires first


def hands_left_by_tile(setup, record) -> Dict[TileId, float]:
    """Hours a year each tile's workers have beyond what its producers hire for the runs they expect to sell."""
    hired = labour_state.producers_hours_needed(setup, record)
    return {tile: max(0.0, people * setup.working_share * setup.working_hours_per_year
                      - math.fsum(hired.get(labour_area(tile), {}).values()))
            for tile, people in setup.opening_population_by_tile.items()}


def service_goods(setup, tile: TileId) -> Dict[str, float]:
    """{good: hours of household work one unit does} for the goods that serve the tile's household-work need."""
    return {good: effect for need in setup.basket_for(tile).needs if need.need_id == household_work_year.WORK_NEED
            for good, effect in need.goods if effect > 0.0}


def household_plans(setup, record, area_map, room_by_tile: Optional[Mapping[TileId, float]] = None) -> HouseholdPlans:
    """What the cohorts of an opened record would plan for the first year, at its prices and wages. `room_by_tile` is
    the hours of hired work a tile's hands leave room for (None: no limit). Hours hired are bought in the market area
    of the service, so the households of an area whose servants the hands of its tiles together cannot supply find
    hiring dearer: the area posts the price at which hiring fits."""
    view = YearView(record.memory, record.book, area_map, setup.currency_id, labour_area)
    outside = year_labour.outside_option_by_tile(setup, record, view)
    offers = year_labour.labour_offers(setup, record, view, outside)
    floors: Dict[TileId, float] = {}
    margins: Dict[AgentId, float] = {}
    if room_by_tile is not None and setup.household_work:
        rows: Dict[str, list] = {}
        tiles_of: Dict[str, set] = {}
        for _cohort_id, cohort in sorted(record.cohorts.items()):
            fallback = outside.get(cohort.tile, 0.0) / max(setup.working_hours_per_year, 1e-9)
            value, needed, price, _milled = household_work_year.work_terms(setup, record, view, cohort, offers, fallback)
            market = _service_market(setup, area_map, cohort.tile)
            margins[_cohort_id] = value - price
            rows.setdefault(market, []).append((value, needed, price))
            tiles_of.setdefault(market, set()).add(cohort.tile)
        for market, market_rows in sorted(rows.items()):
            floor = households_work.service_price_that_fits(
                market_rows, math.fsum(room_by_tile.get(tile, 0.0) for tile in tiles_of[market]))
            if floor > 0.0:
                floors.update({tile: floor for tile in tiles_of[market]})
    return HouseholdPlans(household_work_year.plans(setup, record, view, offers, outside, floors), floors, margins)


def _service_market(setup, area_map, tile: TileId) -> str:
    """The market area in which the tile's households buy hours of household work."""
    goods = sorted(service_goods(setup, tile))
    return area_map.area_of(goods[0], tile) if goods else tile


def post_service_prices(memory, area_map, setup, floors: Mapping[TileId, float]) -> None:
    """The service goods' price in each tile whose households found hiring dearer: what an hour hired costs there."""
    for tile, floor in sorted(floors.items()):
        for good, effect in service_goods(setup, tile).items():
            key = market_key(good, area_map.area_of(good, tile))
            if key in memory.prices and memory.prices[key] < floor * effect:
                memory.prices[key] = floor * effect
                memory.note_usual_price(key)


def with_plans(cohorts: Mapping[AgentId, Cohort], plans: HouseholdPlans) -> Dict[AgentId, Cohort]:
    """The cohorts holding what they plan to hire and buy milled; a cohort with no plan is left as it is."""
    return {cohort_id: (dataclasses.replace(cohort, hired_work_per_person=plans.by_cohort[cohort_id][0],
                                            milled_grains=plans.by_cohort[cohort_id][2])
                        if cohort_id in plans.by_cohort and _differs(cohort, plans.by_cohort[cohort_id]) else cohort)
            for cohort_id, cohort in cohorts.items()}


def _differs(cohort: Cohort, plan: CohortPlan) -> bool:
    return (abs(cohort.hired_work_per_person - plan[0]) > PLAN_TOLERANCE * max(abs(plan[0]), PLAN_FLOOR_HOURS)
            or tuple(cohort.milled_grains) != tuple(plan[2]))


def agree(cohorts: Mapping[AgentId, Cohort], plans: HouseholdPlans) -> bool:
    """Whether every cohort holds what it plans (hours hired, grains milled)."""
    return not any(_differs(cohort, plans.by_cohort[cohort_id]) for cohort_id, cohort in cohorts.items()
                   if cohort_id in plans.by_cohort)


def settle(open_with: Callable[[Optional[HouseholdPlans]], object], choose: Callable[[object], HouseholdPlans],
           cohorts_of: Callable[[object], Mapping[AgentId, Cohort]], passes: int = PLAN_PASSES):
    """The opening solved for the plans its own solve implies: `open_with(plans)` opens the economy with its cohorts
    holding `plans` (None: none), `choose(opened)` is what its households then plan. Stops at the first opening that
    holds what its households then plan; after `passes` solves, at the last (a choice that cycles has no fixed point)."""
    opened = open_with(None)
    tried, seen = [], set()
    for _pass in range(passes):
        chosen = choose(opened)
        if agree(cohorts_of(opened), chosen):
            return opened
        pattern = tuple(sorted((cohort_id, plan[0] > 0.0) for cohort_id, plan in chosen.by_cohort.items()))
        if chosen.margin_by_cohort and pattern in seen:
            break       # the choice has come back to a hiring pattern it had: it cycles
        seen.add(pattern)
        tried.append(chosen)
        opened = open_with(chosen)
    widest = max(tried, key=lambda plans: sum(plan[0] for plan in plans.by_cohort.values()), default=None)
    if widest is None or not widest.margin_by_cohort:
        return opened
    return _by_margin(open_with, choose, widest)


def _only_the_first(plans: HouseholdPlans, ranked, count: int) -> HouseholdPlans:
    """The plans with only the first `count` of the ranked cohorts hiring."""
    dropped = set(ranked[count:])
    return HouseholdPlans({cohort_id: ((0.0,) + tuple(plan[1:]) if cohort_id in dropped else plan)
                           for cohort_id, plan in plans.by_cohort.items()})


def _by_margin(open_with, choose, widest: HouseholdPlans):
    """A choice that cycles (everyone hires, which makes hiring dear, so none does) has its fixed point in between: the
    households that gain most from hiring hire, as many as still gain at the prices that many hiring brings. Bisects
    on how many of the households, ranked by what an hour hired gains them, hire (hiring more raises the price, so
    the household that gains least is the first to find it no longer pays)."""
    ranked = sorted((cohort_id for cohort_id, plan in widest.by_cohort.items() if plan[0] > 0.0),
                    key=lambda cohort_id: (-widest.margin_by_cohort.get(cohort_id, 0.0), cohort_id))
    low, high = 0, len(ranked)
    opened_with = {}
    while low < high:
        middle = (low + high + 1) // 2
        trial = _only_the_first(widest, ranked, middle)
        opened = opened_with[middle] = open_with(trial)
        chosen = choose(opened)
        if any(chosen.by_cohort[cohort_id][0] <= 0.0 for cohort_id in ranked[:middle] if cohort_id in chosen.by_cohort):
            high = middle - 1
        else:
            low = middle
    return opened_with[low] if low in opened_with else open_with(_only_the_first(widest, ranked, low))
