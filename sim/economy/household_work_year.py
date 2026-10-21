"""A cohort's household work in a year (Complaint 645): which hours it hires and which it does itself, and the
basket that follows. Its own hours are kept back from the labour it offers (`labour_supply.HourSupply`); the hours
it hires become its floor of the `household_work` need, bought from domestic servants like any floor."""
import dataclasses
from typing import Dict, Mapping, Sequence, Tuple

from . import households_work, titles_worked
from .households_cohort import Cohort
from .setup import labour_area
from .types import AgentId, LabourOffer

WORK_NEED = "household_work"
HEARTH_EPSILON = 1e-9


def has_hearth(record, cohort: Cohort) -> bool:
    """A cohort cooks at a hearth of its own when it works land: it holds a title or a tenancy on its tile.
    (No urban marker exists yet; a landless townsman is a cohort with no title or tenancy.)"""
    return titles_worked.worked_share(record, cohort.tile, cohort.agent_id) > HEARTH_EPSILON


def cohort_basket(setup, record, cohort: Cohort):
    """The basket of a cohort: the tile's, with food bought only as ready to eat when it has no hearth (else cooking fuel on its warmth floor), and
    this year's hired household work as the floor of that need."""
    basket = setup.basket_for(cohort.tile)
    if not has_hearth(record, cohort):
        basket = households_work.without_hearth_basket(basket, setup.ready_to_eat, setup.hunger_need)
    else:
        basket = households_work.with_cooking_fuel(
            basket, households_work.cooking_fuel_per_person_per_year(setup.household_work), setup.fuel_need)
    if cohort.hired_work_per_person > 0.0:
        basket = dataclasses.replace(basket, needs=tuple(
            dataclasses.replace(need, subsistence_per_person=cohort.hired_work_per_person)
            if need.need_id == WORK_NEED else need for need in basket.needs))
    return basket


def cohort_split(setup, record, view, cohort: Cohort, offers: Sequence[LabourOffer],
                 servant_price_fallback_per_hour: float) -> Tuple[float, float]:
    """(hours hired, hours done itself) for one cohort: an hour of its own labour at the wage it faces against the
    servant's price (the servant trade's wage last year, else the fallback)."""
    if not setup.household_work:
        return 0.0, 0.0
    needed = households_work.hours_needed(cohort.people, setup.household_work, has_hearth(record, cohort))
    mine = [offer for offer in offers if offer.worker == cohort.agent_id]
    value = households_work.hour_value(
        [(offer.hours, view.wage(offer.trade, offer.area) or offer.reservation_wage) for offer in mine])
    price = view.wage(setup.servant_trade, labour_area(cohort.tile)) or servant_price_fallback_per_hour
    hired = households_work.hired_hours(needed, value, price)
    return hired, households_work.own_hours(needed, hired)


def decide(setup, record, view, offers: Sequence[LabourOffer], outside_option_by_tile: Mapping[str, float]
           ) -> Dict[AgentId, float]:
    """Settle the year's split for every cohort: store the hired hours a person's share (the cohort's floor) and
    return the own hours of each cohort, which it keeps back from the market."""
    own: Dict[AgentId, float] = {}
    for cohort_id, cohort in sorted(record.cohorts.items()):
        fallback = outside_option_by_tile.get(cohort.tile, 0.0) / max(setup.working_hours_per_year, 1e-9)
        hired, own[cohort_id] = cohort_split(setup, record, view, cohort, offers, fallback)
        per_person = hired / cohort.people if cohort.people > 0.0 else 0.0
        if per_person != cohort.hired_work_per_person:
            record.cohorts[cohort_id] = dataclasses.replace(cohort, hired_work_per_person=per_person)
    return own


def basket_key(record, cohort: Cohort):
    """What distinguishes one cohort's basket from another's on the same tile, for caching priced needs."""
    return (cohort.tile, has_hearth(record, cohort), cohort.hired_work_per_person)
