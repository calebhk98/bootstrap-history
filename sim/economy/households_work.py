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


def hours_per_person_per_year(data: Mapping[str, Any], has_hearth: bool = True) -> float:
    """Hours of household work one person's share takes a year. A household with no hearth does no
    cooking of its own (its cooking task is left out: it buys cooked food, see `without_hearth_basket`)."""
    days = float(data["days_per_year"])
    total = 0.0
    for task in data["tasks"].values():
        if task.get("needs_hearth") and not has_hearth:
            continue
        if "hours_per_person_per_day" in task:
            total += float(task["hours_per_person_per_day"]) * days
        else:
            total += float(task["hours_per_adult_woman_per_day"]) * float(task["adult_women_per_person"]) * days
    return total


def hours_needed(people: float, data: Mapping[str, Any], has_hearth: bool = True) -> float:
    """Hours of household work a cohort's people need done in the year."""
    return max(0.0, people) * hours_per_person_per_year(data, has_hearth)


def hired_hours(needed_hours: float, surplus_income: float, service_price_per_hour: float,
                budget_share: float) -> float:
    """Hours of the work a household hires: what its surplus spending on the need buys at the service's price
    (the need's share of the money it has above its floors), never more than the work there is. A household with
    no surplus hires none."""
    if needed_hours <= 0.0 or service_price_per_hour <= 0.0 or surplus_income <= 0.0:
        return 0.0
    return min(needed_hours, surplus_income * budget_share / service_price_per_hour)


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

