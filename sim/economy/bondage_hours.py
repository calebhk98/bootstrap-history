"""Bonded hours leave the labour market (Complaint 538): a bonded cohort owes its creditor a share of its working
hours (bondage.BONDED_HOURS_OWED_SHARE), and the owed hours are worked in the creditor's own works, not sold.

Before the market clears, the owed share of each bonded cohort's offered hours (no more than the debt left is worth at
the cohort's reservation wage) is placed with the creditor's producers that bid for that trade in that area: the
hours come off the cohort's offer and off the producer's bid, and the producer is credited them as hired. Owed hours
no work of the creditor wants stay in the market, where the creditor takes its share of the wages instead
(bondage.service). The credited hours come off the debt at the reservation wage, the value of the hour to the cohort.
"""
import dataclasses
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from . import titles
from .types import AgentId, LabourBid, LabourOffer


@dataclasses.dataclass
class Placement:
    offers: List[LabourOffer]
    bids: List[LabourBid]
    hired: Dict[AgentId, Dict[str, float]]          # employer -> trade -> hours worked for the creditor
    hours_placed: Dict[AgentId, float]              # cohort -> hours it worked for its creditor
    value_placed: Dict[AgentId, float]              # cohort -> those hours at its reservation wage
    cash_share: Dict[AgentId, float]                # cohort -> share of its market wages still owed in cash


def place(bonds: Mapping[AgentId, Mapping], offers: Sequence[LabourOffer], bids: Sequence[LabourBid],
          works_of: Callable[[AgentId], Optional[AgentId]], owed_share: float) -> Placement:
    """Place bonded cohorts' owed hours with their creditors' works. `works_of(employer)` is the owner of the
    employer's works (the employer itself for an actor that is its own owner), or None."""
    new_offers = list(offers)
    new_bids = list(bids)
    hired: Dict[AgentId, Dict[str, float]] = {}
    placed_hours: Dict[AgentId, float] = {}
    placed_value: Dict[AgentId, float] = {}
    cash_share: Dict[AgentId, float] = {}
    for cohort_id, bond in sorted(bonds.items()):
        creditor, debt_left = bond["creditor"], bond["debt"]
        total_hours = sum(offer.hours for offer in offers if offer.worker == cohort_id)
        if total_hours <= 0.0:
            continue
        owed = owed_share * total_hours
        for index, offer in enumerate(new_offers):
            if offer.worker != cohort_id or offer.hours <= 0.0 or owed <= 1e-12 or debt_left <= titles.EPSILON:
                continue
            want = min(owed_share * offer.hours, owed, debt_left / offer.reservation_wage if offer.reservation_wage > 0.0 else owed)
            for slot, bid in enumerate(new_bids):
                if want <= 1e-12:
                    break
                if bid.trade != offer.trade or bid.area != offer.area or bid.hours <= 0.0 or works_of(bid.employer) != creditor:
                    continue
                taken = min(want, bid.hours)
                new_bids[slot] = dataclasses.replace(bid, hours=bid.hours - taken)
                new_offers[index] = dataclasses.replace(new_offers[index], hours=new_offers[index].hours - taken)
                rows = hired.setdefault(bid.employer, {})
                rows[bid.trade] = rows.get(bid.trade, 0.0) + taken
                placed_hours[cohort_id] = placed_hours.get(cohort_id, 0.0) + taken
                value = taken * offer.reservation_wage
                placed_value[cohort_id] = placed_value.get(cohort_id, 0.0) + value
                debt_left -= value
                owed -= taken
                want -= taken
        placed = placed_hours.get(cohort_id, 0.0)
        left_in_market = total_hours - placed
        cash_share[cohort_id] = max(0.0, owed_share * total_hours - placed) / left_in_market if left_in_market > 0.0 else 0.0
    return Placement(new_offers, new_bids, hired, placed_hours, placed_value, cash_share)


def deliver(hours_hired: Dict[AgentId, Dict[str, float]], placement: Placement) -> None:
    """Book the hours worked for creditors as hired hours of the creditors' works."""
    for employer, by_trade in placement.hired.items():
        rows = hours_hired.setdefault(employer, {})
        for trade, hours in by_trade.items():
            rows[trade] = rows.get(trade, 0.0) + hours


def works_of_producers(record) -> Callable[[AgentId], Optional[AgentId]]:
    """Employer -> the owner of its works: a producer's owner, or the employer itself when it is no producer."""
    return lambda employer: record.producers[employer].owner if employer in record.producers else employer
