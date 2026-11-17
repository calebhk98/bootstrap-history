"""Grinding grain is a way of making flour, so a household weighs it as it weighs cooking (Complaint 645): it grinds
a grain by hand when its hours cost less than the milling is worth to it, and buys the milled good otherwise. A
cohort is many households, so the share of a grain bought milled is a logit on the two costs per need unit, and moves
a small step for a small change in a price or in the worth of an hour. Hours fall only on the food it grinds itself.
Plain functions of the priced food need."""
import dataclasses
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from sim.constants import declare
from sim.world.need_basket import Basket

from .households_work import WORK_CHOICE_INTENSITY
from .price_setting import choice_shares

HandGround = Tuple[Tuple[str, float], ...]       # (grain, share of the need's units it still meets by hand), sorted by grain
PricedRow = Tuple[str, float, float, float]    # (good, price, need units one unit gives, share of spending)

GRINDING_ADJUSTMENT_SHARE_PER_YEAR = declare(
    "GRINDING_ADJUSTMENT_SHARE_PER_YEAR", 0.2, kind="temporary_heuristic",
    unit="share of the gap between the share of a grain a cohort ground by hand last year and the share its choice asks for closed each year",
    source=None, confidence="D", retire="Complaints/645-household-work-is-not-a-need-so-there-are-no-servants-cooks-or-taverns.md",
    why="Households change how they get their flour over years, not all at once on one year's prices; without it the choice, "
        "made on last year's prices, swings the hours households grind and so the hours they sell, and the wage, with a period "
        "of two years (Complaint 473). No source found for the speed.")


def milled_as_map(need_data: Mapping[str, Any]) -> Dict[str, str]:
    """Per grain the needs file marks `milled_as`, the good it is milled into."""
    return {good: attributes["milled_as"] for good, attributes in sorted((need_data.get("goods") or {}).items())
            if attributes.get("milled_as")}


def unit_shares(rows: Sequence[PricedRow]) -> Dict[str, float]:
    """The share of the need's units each good meets in the household's mix (spending share over cost per unit)."""
    units = {good: share * effect / price for good, price, effect, share in rows if price > 0.0}
    total = sum(units.values())
    return {good: value / total for good, value in units.items()} if total > 0.0 else {}


def bought_shares(rows: Sequence[PricedRow], milled_as: Mapping[str, str], hours_per_unit: float,
                  hour_value: float) -> Dict[str, float]:
    """Per grain with a priced milled good, the share of it the households buy milled: a logit on the milled good's cost
    per need unit against the grain's plus the worth of the hours of grinding it. A grain with no priced milled good
    (no mill in reach) is absent: it is ground by hand."""
    priced = {good: (price, effect) for good, price, effect, _share in rows if price > 0.0 and effect > 0.0}
    bought = {}
    for grain, milled in sorted(milled_as.items()):
        if grain in priced and milled in priced:
            grind_cost = priced[grain][0] / priced[grain][1] + max(0.0, hours_per_unit) * max(0.0, hour_value)
            bought[grain] = choice_shares([priced[milled][0] / priced[milled][1], grind_cost], WORK_CHOICE_INTENSITY)[0]
    return bought


def ground_by_hand(rows: Sequence[PricedRow], milled_as: Mapping[str, str],
                   bought: Mapping[str, float]) -> HandGround:
    """Per grain with a bought share, (grain, share of the need's units it still meets by hand): its share of the units
    less what is bought milled. This is what a cohort holds and what its basket caps the grain at."""
    shares = unit_shares(rows)
    return tuple((grain, shares[grain] * (1.0 - share)) for grain, share in sorted(bought.items()) if grain in shares)


def ground_share(rows: Sequence[PricedRow], milled_as: Mapping[str, str], ground: HandGround) -> float:
    """The share of the need's units met by grain the household grinds itself: each grain's share of the units, or the
    part of it the household holds as ground by hand when that is less."""
    held = dict(ground)
    shares = unit_shares(rows)
    return sum(min(share, held.get(good, share)) for good, share in shares.items() if good in milled_as)


def with_hand_ground(basket: Basket, ground: HandGround, food_need: str) -> Basket:
    """The basket with each grain in `ground` capped, in the food need, at the share of the need's units the household
    grinds of it by hand (below any limit it had); the milled good takes up what the grain no longer meets. A grain
    wholly bought milled is capped at nothing. The need is left whole when every one of its goods would be capped at nothing."""
    caps = {grain: max(0.0, share) for grain, share in ground}
    if not caps:
        return basket
    needs = []
    for need in basket.needs:
        if need.need_id == food_need and any(good not in caps or caps[good] > 0.0 for good, _effect in need.goods):
            limits = dict(need.share_limits)
            for grain, cap in caps.items():
                if any(good == grain for good, _effect in need.goods):
                    limits[grain] = min(cap, limits.get(grain, cap))
            need = dataclasses.replace(need, share_limits=tuple(sorted(limits.items())))
        needs.append(need)
    return dataclasses.replace(basket, needs=tuple(needs))


def stepped_overall_share(held: Optional[float], chosen: float, share: float = GRINDING_ADJUSTMENT_SHARE_PER_YEAR) -> float:
    """The share of its food a cohort counts as ground by hand when it counts its housework hours this year: the share it counted last
    year moved `share` of the way to this year's computed one. With none held (the opening, or a cohort no year has counted) the
    computed one is taken whole."""
    if held is None:
        return chosen
    return max(0.0, min(1.0, held + share * (chosen - held)))


def stepped_ground(rows: Sequence[PricedRow], previous: HandGround, chosen: HandGround,
                   share: float = GRINDING_ADJUSTMENT_SHARE_PER_YEAR) -> HandGround:
    """The share of each grain's units a cohort grinds by hand this year: the share it held last year moved `share` of the way
    to the share its choice asks for. A grain it held no share of (no year has set it) was wholly ground by hand."""
    held = dict(previous)
    units = unit_shares(rows)
    stepped = []
    for grain, wanted in chosen:
        before = held.get(grain, units.get(grain, wanted))
        stepped.append((grain, max(0.0, before + share * (wanted - before))))
    return tuple(stepped)
