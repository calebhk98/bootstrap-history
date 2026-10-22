"""Household work as a need: cooking, water and fuel, cleaning, grinding and childcare take hours every household
spends (data/world/household_work.json). A household meets them with its own hours or hires them, the same choice
as own-plot growing (households_own.py): hours it hires are the domestic servant's (the `household_work` need,
met by the `domestic_service_hour` good), the rest are its own and come out of the hours it could sell. Cooking
needs a hearth and fuel; a household without a hearth buys cooked food instead, which is what cooks and eating
houses supply. Everything here is a plain function of the cohort's figures.
"""
import dataclasses
import json
import os
from typing import Any, Dict, Mapping

from .households_basket import Basket

_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "world", "household_work.json")


def load_household_work(path: str = _DATA_PATH) -> Dict[str, Any]:
    """The household-work data file (tasks and the figures behind them)."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def hours_per_person_per_year(data: Mapping[str, Any], has_hearth: bool = True, ground_share: float = 1.0,
                              only_grinding: bool = False) -> float:
    """Hours of household work one person's share takes a year. A household with no hearth does no
    cooking of its own (its cooking task is left out: it buys cooked food, see `without_hearth_basket`). A task
    that scales with ground grain (grinding) takes the sourced hours times the share of its food the household
    grinds itself. `only_grinding` counts that task alone."""
    days = float(data["days_per_year"])
    total = 0.0
    for task in data["tasks"].values():
        if task.get("needs_hearth") and not has_hearth:
            continue
        grinding = bool(task.get("scales_with_ground_grain"))
        if only_grinding and not grinding:
            continue
        scale = max(0.0, ground_share) if grinding else 1.0
        if "hours_per_person_per_day" in task:
            total += float(task["hours_per_person_per_day"]) * days * scale
        else:
            total += float(task["hours_per_adult_woman_per_day"]) * float(task["adult_women_per_person"]) * days * scale
    return total


def cooking_fuel_per_person_per_year(data: Mapping[str, Any], has_hearth: bool = True) -> float:
    """Megajoules of fuel heat a person's share of the cooking burns a year, in the units of the warmth need. A
    household with no hearth burns none (it buys cooked food); data with no figure adds none."""
    if not has_hearth:
        return 0.0
    per_day = float(data.get("cooking_fuel_mj_per_person_per_day", 0.0))
    return per_day * float(data["days_per_year"]) if per_day else 0.0


def with_cooking_fuel(basket: Basket, fuel_per_person: float, fuel_need: str = "warmth") -> Basket:
    """The basket with a cooking fuel floor added to the fuel need's floor (the climate floor heats the dwelling;
    cooking burns fuel beyond it). Left whole when there is none to add."""
    if fuel_per_person <= 0.0:
        return basket
    return dataclasses.replace(basket, needs=tuple(
        dataclasses.replace(need, subsistence_per_person=need.subsistence_per_person + fuel_per_person)
        if need.need_id == fuel_need else need for need in basket.needs))


def hours_needed(people: float, data: Mapping[str, Any], has_hearth: bool = True, ground_share: float = 1.0) -> float:
    """Hours of household work a cohort's people need done in the year."""
    return max(0.0, people) * hours_per_person_per_year(data, has_hearth, ground_share)


def hour_value(hours_and_wages) -> float:
    """What an hour of the household's own labour is worth at the market: the wage per hour it faces, averaged
    over the hours it would sell, as (hours, wage per hour) rows. Zero when it would sell none."""
    rows = [(max(0.0, hours), wage) for hours, wage in hours_and_wages if hours > 0.0]
    total = sum(hours for hours, _wage in rows)
    return sum(hours * wage for hours, wage in rows) / total if total > 0.0 else 0.0


def supervision_share(data: Mapping[str, Any]) -> float:
    """Hours of the household's own that each hour of hired work takes to direct (data file; none when it gives no figure)."""
    return max(0.0, float(data.get("supervision_hours_per_hired_hour", 0.0)))


def net_hour_value(own_hour_value: float, supervision: float) -> float:
    """What an hour hired is worth to the household for the hours it frees: of every hour hired the household
    spends `supervision` hours directing it, so only the rest are freed to sell at the worth of its hour."""
    return own_hour_value * max(0.0, 1.0 - supervision)


def sold_share(hours_hired: float, hours_idle: float) -> float:
    """Share of the hours offered in a labour market that found a buyer last year; all of them when none were offered
    (no history is no evidence that hours go unsold)."""
    offered = max(0.0, hours_hired) + max(0.0, hours_idle)
    return max(0.0, hours_hired) / offered if offered > 0.0 else 1.0


def hired_hours(needed_hours: float, own_hour_value: float, service_price_per_hour: float) -> float:
    """Hours of the work a household hires: all of it when an hour of its own labour is worth more at the market
    than the servant's price (it would rather sell the hour and pay), none otherwise. Never more than the work
    there is. Cohorts differ in what their hours earn, so the aggregate hired rises step by step with the wage."""
    if needed_hours <= 0.0 or service_price_per_hour <= 0.0:
        return 0.0
    return needed_hours if own_hour_value > service_price_per_hour else 0.0


def service_price_that_fits(households, room_hours: float) -> float:
    """The price of an hour hired at which the households that still hire need no more hours than `room_hours`: the
    servants there are not more than that, so where households would hire more the price rises until hiring falls
    (the one whose hour is worth least of those hiring drops out first). `households` are (worth of an hour, hours
    it would hire, price an hour costs it) rows; the price is the worth of the dearest hour that no longer hires,
    zero where every household that hires fits."""
    hiring = sorted(((value, hours) for value, hours, price in households if hours > 0.0 and value > price),
                    key=lambda row: -row[0])
    total = 0.0
    for value, hours in hiring:
        total += hours
        if total > room_hours:
            return value
    return 0.0


def own_hours(needed_hours: float, hired: float) -> float:
    """Hours the household does itself: the work less what it hired. These come out of the hours it could sell."""
    return max(0.0, needed_hours - hired)


def ready_to_eat_goods(need_data: Mapping[str, Any]) -> frozenset:
    """Goods the needs file marks `ready_to_eat`: a household with no hearth can eat them as bought."""
    return frozenset(good for good, attributes in (need_data.get("goods") or {}).items()
                     if attributes.get("ready_to_eat"))


def without_hearth_basket(basket: Basket, ready_goods: frozenset, food_need: str = "food") -> Basket:
    """The basket for a household with no hearth: the goods that serve the food need are only those eaten as
    bought (cooked meals, bread, cheese), since it cannot cook raw grain or meat. Left whole when none of
    them is in the basket (it would go hungry for want of a seller, not of a hearth)."""
    needs = []
    for need in basket.needs:
        if need.need_id == food_need:
            kept = tuple((good, effect) for good, effect in need.goods if good in ready_goods)
            if kept:
                need = dataclasses.replace(
                    need, goods=kept,
                    share_limits=tuple(row for row in need.share_limits if row[0] in ready_goods),
                    qualities=tuple(row for row in need.qualities if row[0] in ready_goods))
        needs.append(need)
    return dataclasses.replace(basket, needs=tuple(needs))


def cooked_food_units(people: float, food_floor_per_person: float, has_hearth: bool) -> float:
    """Food need units a cohort must buy ready to eat: its whole floor when it has no hearth, none otherwise."""
    return 0.0 if has_hearth else max(0.0, people) * max(0.0, food_floor_per_person)

