"""Households keep part of their savings in durable, non-spoiling goods of high value per kilogram.
Pure functions: which goods qualify and how the holding is split among them, and how much of savings
goes into the holding. Goods are chosen by their physical properties and price, never by id."""
import math
from typing import Dict, List, Mapping, Optional, Tuple

from sim.constants import declare

from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .inventory import holding_reservation
from .store_return import (STORE_SERVICE_UNLIMITED, STORE_STORAGE_COST_PER_KG_YEAR, carrying_return,
                           service_values_per_year, split_by_return)
from .types import Bid, GoodId, GoodSpec, Offer

STORE_MAX_SPOILAGE = declare(
    "STORE_MAX_SPOILAGE", 0.01, kind="temporary_heuristic", unit="share of a stock lost a year",
    source=None, confidence="D",
    why="A good is worth keeping as a store of wealth only if it barely spoils. The cut-off is a "
        "round figure, not measured for any society here.")
STORE_MIN_DENSITY_MULTIPLE = declare(
    "STORE_MIN_DENSITY_MULTIPLE", 20.0, kind="temporary_heuristic",
    unit="multiple of the staple's price per kg", source=None, confidence="D",
    why="Wealth kept as goods has to be small enough to hide, carry and guard, so only goods worth many "
        "times a staple's price per kg qualify. The multiple is an assumption, not measured.")
STORE_SAVINGS_SHARE = declare(
    "STORE_SAVINGS_SHARE", 0.1, kind="temporary_heuristic", unit="share of savings", source=None,
    confidence="D",
    why="The share of savings a household keeps in goods when it expects no inflation and lending pays "
        "its time preference. It is an assumption; hoard finds and probate inventories would bound it.")
STORE_SHARE_LIMIT = declare(
    "STORE_SHARE_LIMIT", 0.5, kind="temporary_heuristic", unit="share of savings", source=None,
    confidence="D",
    why="Even when inflation is expected a household keeps some savings as claims or cash; the bound is "
        "an assumption standing in for a portfolio choice that is not modelled.")
STORE_REBALANCE_BAND = declare(
    "STORE_REBALANCE_BAND", 0.2, kind="temporary_heuristic", unit="share of the target value",
    source=None, confidence="D",
    why="A household buys more of its store only when it holds this much less than it wants, and sells "
        "only when it holds this much more, so small price moves do not make it trade every year. "
        "Dealing costs and habit are not modelled; the width is an assumption.")
STORE_LIQUIDATION_RESERVATION_SHARE = declare(
    "STORE_LIQUIDATION_RESERVATION_SHARE", 0.7, kind="temporary_heuristic",
    unit="share of last year's price", source=None, confidence="D",
    why="A household short of cash for its food sells part of its store at a discount, as pawned plate "
        "fetched less than its worth. The discount is an assumption; pawnbrokers' margins would bound it.")
STORE_PRIORITY = 2          # after the need tiers (floors, then surplus)

def store_candidates(specs: Mapping[GoodId, GoodSpec], prices: Mapping[GoodId, float],
                     staple_price_per_kg: float,
                     usual_prices: Optional[Mapping[GoodId, float]] = None,
                     service_values: Optional[Mapping[GoodId, float]] = None) -> Dict[GoodId, float]:
    """Goods fit to hold as wealth, each with its share of the holding (sums to one; empty if none).
    The shares follow each good's expected carrying return (`store_return`), so a good whose price is
    high against its usual price draws less and the stock, not the year's flow, settles the price.
    `service_values` is what a unit saves a year by serving a need (`store_return.service_values_per_year`)."""
    returns = {}
    for good, spec in specs.items():
        price = prices.get(good, 0.0)
        if (spec.service_life_years <= 0.0 or spec.spoilage_per_year > STORE_MAX_SPOILAGE
                or not math.isfinite(spec.unit_mass_kg) or spec.unit_mass_kg <= 0.0 or price <= 0.0):
            continue
        if price / spec.unit_mass_kg < STORE_MIN_DENSITY_MULTIPLE * staple_price_per_kg:
            continue
        service = STORE_SERVICE_UNLIMITED * (service_values or {}).get(good, 0.0)
        returns[good] = carrying_return(spec, price, (usual_prices or {}).get(good), service)
    return split_by_return(returns)


def store_value_target(savings: float, expected_inflation: float, real_rate: float) -> float:
    """Value of savings to hold as goods: more when inflation is expected, less when lending pays
    more than the time preference, never above the limit."""
    inflation_pull = 1.0 + max(0.0, expected_inflation) / HOUSEHOLD_TIME_PREFERENCE
    lending_pull = 1.0 + max(0.0, real_rate - HOUSEHOLD_TIME_PREFERENCE) / HOUSEHOLD_TIME_PREFERENCE
    share = min(STORE_SHARE_LIMIT, STORE_SAVINGS_SHARE * inflation_pull / lending_pull)
    return share * max(0.0, savings)


def staple_price_per_kg(priced, specs: Mapping[GoodId, GoodSpec]) -> float:
    """Cheapest price per kg among the goods that meet a need with a subsistence floor (inf if none)."""
    cheapest = math.inf
    for need in priced:
        if need.spec.subsistence_per_person <= 0.0:
            continue
        for good, price, _effect, _share in need.goods:
            spec = specs.get(good)
            if spec is not None and math.isfinite(spec.unit_mass_kg) and spec.unit_mass_kg > 0.0 and price > 0.0:
                cheapest = min(cheapest, price / spec.unit_mass_kg)
    return cheapest


def store_holding(cohort, view, specs: Mapping[GoodId, GoodSpec], priced) -> Tuple[Dict[GoodId, float], Dict[GoodId, float], Dict[GoodId, float]]:
    """(weights, last prices, quantities held) of the store goods at this cohort's tile; empty if none."""
    staple = staple_price_per_kg(priced, specs)
    if not math.isfinite(staple):
        return {}, {}, {}
    prices, usual_prices = {}, {}
    for good in specs:
        area = view.area_of(good, cohort.tile)
        price = view.price(good, area)
        if price:
            prices[good] = price
            usual = getattr(view, "usual_price", None)      # a view that keeps no price memory has none
            if usual is not None and usual(good, area):
                usual_prices[good] = usual(good, area)
    weights = store_candidates(specs, prices, staple, usual_prices, service_values_per_year(priced, specs))
    return (weights, {good: prices[good] for good in weights},
            {good: view.stock(cohort.agent_id, good, cohort.tile) for good in weights})


def store_bids(cohort, view, specs, basket, weights, prices, held, wealth_above_buffer: float,
               real_rate: float, pot: float) -> Tuple[List[Bid], float]:
    """Bids for the store when its value is below the target less the band, paid from `pot` (money the
    household would otherwise lend); returns the bids and the money they may spend."""
    if not weights or pot <= 0.0:
        return [], 0.0
    held_value = math.fsum(held[good] * prices[good] for good in weights)
    target = store_value_target(wealth_above_buffer, cohort.expected_inflation, real_rate)
    if held_value >= target * (1.0 - STORE_REBALANCE_BAND):
        return [], 0.0
    spend = min(pot, target - held_value)
    bids = []
    for good, weight in weights.items():
        budget = spend * weight
        if budget > 0.0:
            bids.append(Bid(cohort.agent_id, good, view.area_of(good, cohort.tile), cohort.tile, 0.0,
                            budget / prices[good], prices[good], basket.substitution, budget, STORE_PRIORITY))
    return bids, math.fsum(bid.budget for bid in bids)


def store_offers(cohort, view, specs, weights, prices, held, wealth_above_buffer: float, real_rate: float,
                 cash: float, floor_cost: float) -> List[Offer]:
    """Offers of the store: the excess over the target plus the band at the holding reservation, and
    enough at a low reservation to cover a shortfall of cash against the floor cost."""
    held_value = math.fsum(held[good] * prices[good] for good in weights)
    if held_value <= 0.0:
        return []
    rate = view.interest_rate(view.currency_of(view.area_of(next(iter(weights)), cohort.tile)))
    target = store_value_target(wealth_above_buffer, cohort.expected_inflation, real_rate)
    excess = max(0.0, held_value - target * (1.0 + STORE_REBALANCE_BAND))
    shortfall = max(0.0, floor_cost - cash)
    offers = []
    for good in sorted(weights):
        share = held[good] * prices[good] / held_value
        spec = specs[good]
        low = prices[good] * STORE_LIQUIDATION_RESERVATION_SHARE
        urgent = min(held[good], shortfall * share / low) if shortfall > 0.0 else 0.0
        patient = min(held[good] - urgent, excess * share / prices[good])
        area = view.area_of(good, cohort.tile)
        if urgent > 0.0:
            offers.append(Offer(cohort.agent_id, good, area, cohort.tile, urgent, low))
        if patient > 0.0:
            reservation = holding_reservation(prices[good], rate, spec.spoilage_per_year,
                                              STORE_STORAGE_COST_PER_KG_YEAR * spec.unit_mass_kg)
            offers.append(Offer(cohort.agent_id, good, area, cohort.tile, patient, reservation))
    return offers
