"""A cohort's hours kept for its own plot rather than offered (Complaints 473, 608): the choice of
`households_hours_offered` against the wage it faced and what its plot yields at the prices of what it grows. The
hours kept are added to those the own-plot plan and the household work already keep back (`labour_supply.HourSupply`)."""
from typing import Callable, Dict, Mapping, Optional, Sequence

from . import households_hours_offered
from .households_basket import need_prices
from .households_own import Option, own_production
from .labour_ask_floor import hectares_per_hour_by_recipe, plot_return_per_hour
from .types import AgentId, LabourOffer

SPARE_HOURS = 1e18        # more hours than any plot takes, to ask how many it could use


def wage_faced_per_hour(view, offers: Sequence[LabourOffer]) -> float:
    """The wage per hour a cohort's offers face: last year's clearing wage in each market, else the reservation wage,
    averaged over the hours offered (the same reading household work takes, household_work_year.cohort_split)."""
    rows = [(offer.hours, view.wage(offer.trade, offer.area) or offer.reservation_wage) for offer in offers if offer.hours > 0.0]
    total = sum(hours for hours, _wage in rows)
    return sum(hours * wage for hours, wage in rows) / total if total > 0.0 else 0.0


def usable_plot_hours(setup, cohort, options: Mapping[str, Sequence[Option]], held: float) -> float:
    """Hours of a cohort's work its plot can take: the floors of the needs its land grows, on the land it holds."""
    tile = setup.tiles.get(cohort.tile)
    if tile is None or held <= 0.0 or tile.fertility <= 0.0:
        return 0.0
    used: Dict[str, float] = {}
    own_production(cohort, SPARE_HOURS, options, setup.recipes, tile.fertility, setup.basket_for(cohort.tile),
                   setup.land_per_run, held, used)
    return sum(used.values())


def plot_schedules(setup, record, view, offers: Sequence[LabourOffer], options: Mapping[str, Sequence[Option]],
                   hectares_held: Mapping[AgentId, float], usable_out: Optional[Dict[AgentId, float]] = None
                   ) -> Dict[AgentId, Callable[[float], float]]:
    """For each cohort with a plot, the hours it keeps for the plot at a wage an hour (a function of the wage); a
    cohort with no land held, or none that grows a need's floor, has none. `usable_out`, if given, is filled with
    the hours each plot could use in all."""
    schedules: Dict[AgentId, Callable[[float], float]] = {}
    hectares_per_hour = hectares_per_hour_by_recipe(setup.recipes, setup.land_per_run)
    for cohort_id, cohort in sorted(record.cohorts.items()):
        available = sum(offer.hours for offer in offers if offer.worker == cohort_id)
        tile = setup.tiles.get(cohort.tile)
        held = hectares_held.get(cohort_id, 0.0)
        if available <= 0.0 or tile is None or held <= 0.0 or tile.fertility <= 0.0 or cohort.working_people <= 0.0:
            continue
        basket = setup.basket_for(cohort.tile)
        usable = usable_plot_hours(setup, cohort, options, held)
        if usable_out is not None:
            usable_out[cohort_id] = usable
        per_worker_hours = available / cohort.working_people
        marginal = plot_return_per_hour(need_prices(basket, view, cohort.tile), options, tile.fertility, per_worker_hours,
                                        cohort.people / cohort.working_people, hectares_per_hour,
                                        held / cohort.working_people)
        schedules[cohort_id] = plot_schedule(per_worker_hours, marginal, usable / cohort.working_people, cohort.working_people)
    return schedules


def plot_schedule(per_worker_hours: float, marginal: float, usable_per_worker: float, workers: float) -> Callable[[float], float]:
    """Hours a cohort keeps for its plot at a wage (`households_hours_offered.plot_hours_kept` times its workers),
    with what does not depend on the wage worked out once: it is asked at many wages."""
    if per_worker_hours <= 0.0 or usable_per_worker <= 0.0 or marginal <= 0.0:
        return lambda wage_per_hour: 0.0 * workers
    usable = min(per_worker_hours, usable_per_worker)
    exponent = 1.0 / (1.0 - households_hours_offered.LABOUR_OUTPUT_ELASTICITY)

    def kept(wage_per_hour: float) -> float:
        if wage_per_hour <= 0.0:
            return usable * workers
        return min(usable, per_worker_hours * (marginal / wage_per_hour) ** exponent) * workers
    return kept


def decide(setup, record, view, offers: Sequence[LabourOffer], options: Mapping[str, Sequence[Option]],
           hectares_held: Mapping[AgentId, float]) -> Dict[AgentId, float]:
    """Hours each cohort keeps for its plot at the wage it faces (last year's, from the view); a cohort with no
    land held, or none that grows a need's floor, keeps none."""
    kept: Dict[AgentId, float] = {}
    for cohort_id, schedule in plot_schedules(setup, record, view, offers, options, hectares_held).items():
        hours = schedule(wage_faced_per_hour(view, [offer for offer in offers if offer.worker == cohort_id]))
        if hours > 0.0:
            kept[cohort_id] = hours
    return kept

