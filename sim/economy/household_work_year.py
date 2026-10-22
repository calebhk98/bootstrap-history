"""A cohort's household work in a year (Complaint 645): which hours it hires and which it does itself, and the
basket that follows. Its own hours are kept back from the labour it offers (`labour_supply.HourSupply`); the hours
it hires become its floor of the `household_work` need, bought from domestic servants like any floor."""
import dataclasses
from typing import Dict, Mapping, Sequence, Tuple

from . import household_grinding, households_work, titles_worked
from .households_basket import need_prices
from .households_cohort import Cohort
from .setup import labour_area
from .types import AgentId, LabourOffer

WORK_NEED = "household_work"
HEARTH_EPSILON = 1e-9


def has_hearth(record, cohort: Cohort) -> bool:
    """A cohort cooks at a hearth of its own when it works land: it holds a title or a tenancy on its tile.
    (No urban marker exists yet; a landless townsman is a cohort with no title or tenancy.)"""
    return titles_worked.worked_share(record, cohort.tile, cohort.agent_id) > HEARTH_EPSILON


def food_basket(setup, record, cohort: Cohort):
    """The tile's basket, with food only as ready to eat when the cohort has no hearth."""
    basket = setup.basket_for(cohort.tile)
    if not has_hearth(record, cohort):
        basket = households_work.without_hearth_basket(basket, setup.ready_to_eat, setup.hunger_need)
    return basket


def grinding_plan(setup, record, view, cohort: Cohort, hour_value: float) -> Tuple[Tuple[str, ...], float]:
    """(grains the cohort buys milled, share of its food it grinds by hand): a grain is bought milled when the
    milled good costs less per need unit than the grain plus the worth of its hours of grinding. With no grain
    marked as milled, or no priced food, the whole sourced load is its own."""
    if not setup.milled_as:
        return (), 1.0
    food = next((need for need in need_prices(food_basket(setup, record, cohort), view, cohort.tile)
                 if need.spec.need_id == setup.hunger_need), None)
    if food is None:
        return (), 1.0
    floor = food.spec.subsistence_per_person
    hours_per_unit = households_work.hours_per_person_per_year(setup.household_work, True, 1.0, True) / floor if floor > 0.0 else 0.0
    bought = household_grinding.bought_milled(food.goods, setup.milled_as, hours_per_unit, hour_value)
    return bought, household_grinding.ground_share(food.goods, setup.milled_as, bought)


def cohort_basket(setup, record, cohort: Cohort, buying: bool = True):
    """The basket of a cohort: the tile's, with food bought only as ready to eat when it has no hearth (else cooking fuel on its warmth floor), and
    this year's hired household work as the floor of that need. `buying` leaves out the grains it buys milled, which
    it does not bid for; the basket that counts what it ate (`buying` False) keeps them, since a grain it grew on
    its own plot is eaten whatever it buys."""
    basket = food_basket(setup, record, cohort)
    if buying and cohort.milled_grains:
        basket = household_grinding.without_goods(basket, cohort.milled_grains, setup.hunger_need)
    if has_hearth(record, cohort):
        basket = households_work.with_cooking_fuel(
            basket, households_work.cooking_fuel_per_person_per_year(setup.household_work), setup.fuel_need)
    if cohort.hired_work_per_person > 0.0:
        basket = dataclasses.replace(basket, needs=tuple(
            dataclasses.replace(need, subsistence_per_person=cohort.hired_work_per_person)
            if need.need_id == WORK_NEED else need for need in basket.needs))
    return basket


def service_price_per_hour(setup, view, tile, wage_price: float) -> float:
    """What an hour of household work costs a household that hires it: the market price of the goods that serve the
    household-work need per need unit (the cheapest posted), else the servant's wage. The wage is only what the
    servant is paid; the household pays the service's price, which departs from it where servants are scarce."""
    area = view.area_of
    prices = []
    for need in setup.basket_for(tile).needs:
        if need.need_id != WORK_NEED:
            continue
        for good, effect in need.goods:
            posted = view.price(good, area(good, tile))
            if posted is not None and posted > 0.0 and effect > 0.0:
                prices.append(posted / effect)
    return min(prices) if prices else wage_price


def cohort_split(setup, record, view, cohort: Cohort, offers: Sequence[LabourOffer],
                 servant_price_fallback_per_hour: float) -> Tuple[float, float]:
    """(hours hired, hours done itself) for one cohort: an hour of its own labour at the wage it faces against the
    servant's price (the servant trade's wage last year, else the fallback)."""
    hired, own, _milled = cohort_plan(setup, record, view, cohort, offers, servant_price_fallback_per_hour)
    return hired, own


def work_terms(setup, record, view, cohort: Cohort, offers: Sequence[LabourOffer],
               servant_price_fallback_per_hour: float) -> Tuple[float, float, float, Tuple[str, ...]]:
    """(worth of the cohort's hour, hours of household work it needs, price of an hour hired, grains bought milled):
    what its choice between hiring and doing the work is read from. Grinding falls only on the food it grinds by
    hand, decided at the worth of its hour (the water and fuel are a fixed load either way)."""
    mine = [offer for offer in offers if offer.worker == cohort.agent_id]
    value = households_work.hour_value(
        [(offer.hours, view.wage(offer.trade, offer.area) or offer.reservation_wage) for offer in mine])
    milled, ground = grinding_plan(setup, record, view, cohort, value)
    needed = households_work.hours_needed(cohort.people, setup.household_work, has_hearth(record, cohort), ground)
    wage_price = view.wage(setup.servant_trade, labour_area(cohort.tile)) or servant_price_fallback_per_hour
    return value, needed, service_price_per_hour(setup, view, cohort.tile, wage_price), milled


def cohort_plan(setup, record, view, cohort: Cohort, offers: Sequence[LabourOffer],
                servant_price_fallback_per_hour: float, service_price_floor: float = 0.0
                ) -> Tuple[float, float, Tuple[str, ...]]:
    """(hours hired, hours done itself, grains bought milled) for one cohort. `service_price_floor` is a price an hour
    hired is not below (the opening's, where servants are scarce)."""
    if not setup.household_work:
        return 0.0, 0.0, ()
    value, needed, price, milled = work_terms(setup, record, view, cohort, offers, servant_price_fallback_per_hour)
    hired = households_work.hired_hours(needed, value, max(price, service_price_floor))
    return hired, households_work.own_hours(needed, hired), milled


def plans(setup, record, view, offers: Sequence[LabourOffer], outside_option_by_tile: Mapping[str, float],
          service_price_floor_by_tile: Mapping[str, float] = None) -> Dict[AgentId, Tuple[float, float, Tuple[str, ...]]]:
    """Each cohort's (hours hired a person, hours done itself, grains bought milled) for the year; changes nothing."""
    floors = service_price_floor_by_tile or {}
    result: Dict[AgentId, Tuple[float, float, Tuple[str, ...]]] = {}
    for cohort_id, cohort in sorted(record.cohorts.items()):
        fallback = outside_option_by_tile.get(cohort.tile, 0.0) / max(setup.working_hours_per_year, 1e-9)
        hired, own, milled = cohort_plan(setup, record, view, cohort, offers, fallback, floors.get(cohort.tile, 0.0))
        result[cohort_id] = (hired / cohort.people if cohort.people > 0.0 else 0.0, own, milled)
    return result


def decide(setup, record, view, offers: Sequence[LabourOffer], outside_option_by_tile: Mapping[str, float]
           ) -> Dict[AgentId, float]:
    """Settle the year's split for every cohort: store the hired hours a person's share (the cohort's floor) and
    return the own hours of each cohort, which it keeps back from the market."""
    own: Dict[AgentId, float] = {}
    for cohort_id, (per_person, own[cohort_id], milled) in plans(setup, record, view, offers, outside_option_by_tile).items():
        cohort = record.cohorts[cohort_id]
        if per_person != cohort.hired_work_per_person or milled != tuple(cohort.milled_grains):
            record.cohorts[cohort_id] = dataclasses.replace(cohort, hired_work_per_person=per_person, milled_grains=milled)
    return own


def basket_key(record, cohort: Cohort):
    """What distinguishes one cohort's basket from another's on the same tile, for caching priced needs."""
    return (cohort.tile, has_hearth(record, cohort), cohort.hired_work_per_person, tuple(cohort.milled_grains))
