"""What one household of a cohort can pay for one unit of a good.

A cohort stands for many households of one income class. A household cannot pay more for a unit of a
good than it spends on the need that good serves, so the cohort's bid for that good stops at that price
however large the cohort's total budget is. Goods a household cannot afford get no bid; the need's
spending moves to the goods it can.
"""
import math
from typing import Dict, Mapping, Sequence, Tuple

from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD

from .price_setting import LOGIT_INTENSITY


def household_budget_for_need(need_units: float, price_index: float, people: float) -> float:
    """Money one household plans to spend on a need in the year: its share of the cohort's need units
    at the need's price index."""
    if people <= 0.0:
        return 0.0
    return need_units * price_index * PERSONS_PER_HOUSEHOLD / people


def affordability(price: float, household_budget: float, service_life_years: float = 0.0) -> float:
    """Share of households of a cohort that can pay `price` for a unit, from 1 (far below what they spend on the
    need) to 0 (far above). A cohort has households with spread budgets, so the share falls smoothly with the log
    of the price over the budget (a logistic whose steepness is the buyers' price sensitivity `LOGIT_INTENSITY`).
    A unit of a durable serves its service life, so it is compared with the budget over that life."""
    if household_budget <= 0.0:
        return 0.0
    cost = price / service_life_years if service_life_years > 1.0 else price
    exponent = LOGIT_INTENSITY * math.log(cost / household_budget) if cost > 0.0 else -math.inf
    if exponent > 700.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(exponent))


def affordable_goods(goods: Sequence[Tuple[str, float, float, float]],
                     household_budget: float, has_floor: bool,
                     service_lives: Mapping[str, float] = None) -> Tuple[Dict[str, float], float, float]:
    """The share of households that can pay for one unit of each good of a need (`affordability`; a durable's
    `service_lives` entry spreads its price over its life), the share of the need's spending the goods carry
    (to scale up so the spending is all placed), and the price cap to put on a bid (infinite if no good is
    affordable and the need has a floor: every good then stays uncapped, so that a need's floor is never
    dropped; a need without a floor is not bought at all that year)."""
    lives = service_lives or {}
    affordable = {good: affordability(price, household_budget, lives.get(good, 0.0)) for good, price, _effect, _share in goods}
    share = math.fsum(row[3] * affordable[row[0]] for row in goods)
    if share <= 0.0:
        if not has_floor:
            return affordable, 1.0, household_budget
        return {good: 1.0 for good in affordable}, 1.0, math.inf
    return affordable, share, household_budget


def service_lives_of(goods: Sequence[Tuple[str, float, float, float]], specs) -> Dict[str, float]:
    """Service life in years of each durable among the goods of a need."""
    return {row[0]: specs[row[0]].service_life_years for row in goods
            if row[0] in specs and specs[row[0]].service_life_years > 0.0}


def bid_cap(household_cap: float, service_life_years: float) -> float:
    """Most one household bids for a unit: its need budget, or over the service life for a durable."""
    return household_cap * service_life_years if service_life_years > 1.0 else household_cap


def quantity_per_need_unit(goods: Sequence[Tuple[str, float, float, float]], price_index: float,
                           affordable: Mapping[str, float]) -> Dict[str, float]:
    """Units of each affordable good one household bids per need unit. The spending shares, weighted by
    affordability, are renormalised over the affordable goods, and so is what a need unit costs: the money a household
    plans for a need unit (`price_index`) is spent on them, but never beyond what meets the unit, so a
    cheap, weak good (many units to a need unit) does not take the whole mix's money in units it cannot
    use. When the affordable goods are dearer per need unit than the mix, the budget buys less than the
    unit and the rest stays unmet."""
    share = math.fsum(row[3] * affordable[row[0]] for row in goods)
    if share <= 0.0:
        return {}
    units_per_money = math.fsum(row[3] * affordable[row[0]] / share * row[2] / row[1] for row in goods if affordable[row[0]] > 0.0)
    money_per_unit = min(price_index, 1.0 / units_per_money)
    return {good: money_per_unit * row_share * affordable[good] / share / price
            for good, price, _effect, row_share in goods if affordable[good] > 0.0}
