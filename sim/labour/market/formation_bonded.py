"""Buying bonded people for the vacancies of a trade (Complaints 644 and 648), by the owners' ask and the buyers' bid
(bonded_worth.py). Used by formation.py for an empty trade after migration, and for any trade with vacancies left."""
from typing import Dict, Optional

import dataclasses

from . import aptitude, bonded_room, bonded_worth
from .records import Clearing, MarketState, YearInputs, YearReport


def _practised_wage(index: Dict, area: str, trade: str) -> Optional[float]:
    clearing = index.get((area, trade))
    if clearing is None or clearing.hours_hired <= 0.0:
        return None
    return clearing.average_wage


def _floor_per_hour(inputs: YearInputs, area: str) -> float:
    return inputs.ask_floor_per_worker_year.get(area, 0.0) / max(inputs.hours_per_worker_year, 1e-12)


def _training_years(inputs: YearInputs, trade: str) -> float:
    spec = inputs.trades.get(trade)
    return spec.training_years if spec is not None else 0.0


def worth_in(inputs: YearInputs, index: Dict, area: str, trade: str, trade_wage: Optional[float]) -> Optional[float]:
    """Present value of a trained person's hours in `area` over a career; None when neither the trade's wage nor the
    area's wage floor is known there, so no price can be named."""
    floor = _floor_per_hour(inputs, area)
    if floor <= 0.0 and (trade_wage is None or trade_wage <= 0.0):
        return None
    wage = bonded_worth.trained_wage_per_hour(trade_wage, floor, _training_years(inputs, trade),
                                              inputs.discount_rate, inputs.career_years)
    return bonded_worth.worth_of_hours(wage, inputs.hours_per_worker_year, inputs.career_years, inputs.discount_rate)


def untrained_worth_in(inputs: YearInputs, area: str) -> float:
    """Present value of an untrained person's hours: the area's wage floor over a career."""
    return bonded_worth.worth_of_hours(_floor_per_hour(inputs, area), inputs.hours_per_worker_year,
                                       inputs.career_years, inputs.discount_rate)


def buy(state: MarketState, inputs: YearInputs, index: Dict, area: str, trade: str, wanted: float,
        pool: Dict[str, Dict[str, float]], report: YearReport, unassigned: Dict[str, float]) -> float:
    """Buy up to `wanted` bonded people of `trade` for `area` out of `pool` (origin -> trade -> people left, drawn down);
    they join the area's workers and are recorded in `report.bonded_lots`. Returns the people bought. Nothing is bought
    in an area whose civilisation does not recognise bondage, or when the buyers' bid cannot be priced. Only the
    employers with a vacancy and room in their plans buy (bonded_room.py); `unassigned` (employer -> free cash) is
    drawn down by what they pay."""
    if wanted <= 0.0 or area not in inputs.bondage_allowed:
        return 0.0
    clearing: Optional[Clearing] = index.get((area, trade))
    bid = worth_in(inputs, index, area, trade, clearing.heading_wage if clearing is not None else None)
    if bid is None:
        return 0.0
    offers = {origin: by_trade[trade] for origin, by_trade in pool.items() if by_trade.get(trade, 0.0) > 0.0}
    ask, carriage = {}, {}
    for origin in offers:
        price = worth_in(inputs, index, origin, trade, _practised_wage(index, origin, trade))
        if price is not None:
            ask[origin] = price
            carriage[origin] = bonded_worth.cheapest_carriage(inputs.routes, origin, area)
    buyers = bonded_room.buyers_in(inputs.bids, clearing, unassigned) if clearing is not None else []
    shares, ceiling, vacant = bonded_room.shares_and_ceiling(buyers)
    if not shares:
        return 0.0
    left = dict(offers)
    lots = bonded_worth.buy_lots(area, trade, min(wanted, vacant / inputs.hours_per_worker_year), bid, left, ask, carriage)
    lots = _within(lots, ceiling, tuple(sorted(shares.items())))
    for lot in lots:
        offers[lot.origin] -= lot.people
    for origin, remaining in offers.items():
        pool[origin][trade] = remaining
    bonded_room.spend(buyers, shares, sum(lot.people * lot.price for lot in lots), unassigned)
    bought = sum(lot.people for lot in lots)
    if bought > 0.0:
        count = aptitude.band_count()
        destination = state.workers.setdefault(area, {}).setdefault(trade, [0.0] * count)
        for band in range(count):
            destination[band] += bought / count     # the bought are not picked for ability
        report.bonded_lots.extend(lots)
        by_route = report.formed.setdefault(area, {}).setdefault(trade, {})
        by_route["bonded"] = by_route.get("bonded", 0.0) + bought
    return bought


def _within(lots, ceiling: float, payers) -> list:
    """The lots, cheapest first, cut where their cost reaches `ceiling`, each naming who pays."""
    kept, spent = [], 0.0
    for lot in lots:
        people = min(lot.people, (ceiling - spent) / lot.price) if lot.price > 0.0 else lot.people
        if people <= 1e-12:
            break
        kept.append(dataclasses.replace(lot, people=people, payers=payers))
        spent += people * lot.price
    return kept
