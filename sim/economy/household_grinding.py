"""Grinding grain is a way of making flour, so a household weighs it as it weighs cooking (Complaint 645): it grinds
a grain by hand when its hours cost less than the milling is worth to it, and buys the milled good otherwise. Hours
fall only on the food it grinds itself. Plain functions of the priced food need."""
import dataclasses
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

from .households_basket import Basket

PricedRow = Tuple[str, float, float, float]    # (good, price, need units one unit gives, share of spending)


def milled_as_map(need_data: Mapping[str, Any]) -> Dict[str, str]:
    """Per grain the needs file marks `milled_as`, the good it is milled into."""
    return {good: attributes["milled_as"] for good, attributes in sorted((need_data.get("goods") or {}).items())
            if attributes.get("milled_as")}


def unit_shares(rows: Sequence[PricedRow]) -> Dict[str, float]:
    """The share of the need's units each good meets in the household's mix (spending share over cost per unit)."""
    units = {good: share * effect / price for good, price, effect, share in rows if price > 0.0}
    total = sum(units.values())
    return {good: value / total for good, value in units.items()} if total > 0.0 else {}


def bought_milled(rows: Sequence[PricedRow], milled_as: Mapping[str, str], hours_per_unit: float,
                  hour_value: float) -> Tuple[str, ...]:
    """The grains the household buys milled: those whose milled good costs less per need unit than the grain plus
    the worth of the hours of grinding it. A grain with no priced milled good (no mill in reach) is ground by hand."""
    priced = {good: (price, effect) for good, price, effect, _share in rows if price > 0.0 and effect > 0.0}
    bought = []
    for grain, milled in sorted(milled_as.items()):
        if grain in priced and milled in priced:
            grind_cost = priced[grain][0] / priced[grain][1] + max(0.0, hours_per_unit) * max(0.0, hour_value)
            if priced[milled][0] / priced[milled][1] < grind_cost:
                bought.append(grain)
    return tuple(bought)


def ground_share(rows: Sequence[PricedRow], milled_as: Mapping[str, str], bought: Iterable[str]) -> float:
    """The share of the need's units met by grain the household grinds itself."""
    skipped = set(bought)
    shares = unit_shares(rows)
    return sum(share for good, share in shares.items() if good in milled_as and good not in skipped)


def without_goods(basket: Basket, goods: Iterable[str], food_need: str = "food") -> Basket:
    """The basket with the named goods dropped from the food need. The need keeps its goods when dropping
    them would leave it with nothing to buy."""
    dropped = set(goods)
    if not dropped:
        return basket
    needs = []
    for need in basket.needs:
        if need.need_id == food_need:
            kept = tuple((good, effect) for good, effect in need.goods if good not in dropped)
            if kept:
                need = dataclasses.replace(
                    need, goods=kept, share_limits=tuple(row for row in need.share_limits if row[0] not in dropped),
                    qualities=tuple(row for row in need.qualities if row[0] not in dropped))
        needs.append(need)
    return dataclasses.replace(basket, needs=tuple(needs))
