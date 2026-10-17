"""Carriage as hired labour: the crew hours a merchant's shipments need are bid for in the year's labour
market before the goods move, and what is hired limits what is carried.

The hours come from geography's physical crew hours per tonne-km of the land mode with the lowest money
rate, over that rate: crew hours per unit of carriage money. A shipment's hours are its carriage fee times
that. Carts, ships and animals as capital, and the feed they eat, are not yet modelled here: the part of a
fee that is not crew pay still goes to the households of the tile the goods leave (year_close).
Sea and river hauls are counted at the land mode's hours until a haul's mode is known per route.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sim.constants import declare

from .market_memory import market_key
from .merchants import Merchant
from .producers_close import WORKING_CAPITAL_PURPOSE
from .setup import labour_area
from .types import LabourBid, LoanRequest

CARRIAGE_CREW_UNSKILLED_SHARE = declare(
    "CARRIAGE_CREW_UNSKILLED_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the crew hours bid in the setup's unskilled trade", source=None, confidence="D",
    retire="Complaints/556: one workforce owner whose opening places people in the trades the opening's flows need",
    why="The opening places people by the runs producers expect, not by the goods merchants carry, so no "
        "carters exist when merchants first ship and a specialist trade left to train its own would stop "
        "carriage for years. The crew hours are bid in the unskilled trade (porters and drovers on foot are "
        "labourers in the trade data) instead of the mode's carter or sailor trade.")


@dataclass(frozen=True)
class Crew:
    trades: Tuple[Tuple[str, float], ...]     # (trade, share of the crew hours), shares adding to one
    hours_per_money: float                    # crew hours inside one unit of carriage money


def crew_of(setup) -> Optional[Crew]:
    """The crew the setup's carriage hires, or None when its modes name no crew hours."""
    usable = [(setup.carriage_rates[mode], mode) for mode in setup.carriage_crew
              if setup.carriage_rates.get(mode, 0.0) > 0.0]
    if not usable:
        return None
    rate, mode = min(usable)
    trade, hours_per_tonne_km = setup.carriage_crew[mode]
    if hours_per_tonne_km <= 0.0:
        return None
    unskilled = min(1.0, max(0.0, CARRIAGE_CREW_UNSKILLED_SHARE))
    shares = ((setup.unskilled_trade, unskilled), (trade, 1.0 - unskilled))
    merged: Dict[str, float] = {}
    for each, share in shares:
        merged[each] = merged.get(each, 0.0) + share
    return Crew(tuple((each, share) for each, share in sorted(merged.items()) if share > 0.0),
                hours_per_tonne_km / rate)


def planned(merchant: Merchant) -> bool:
    """Whether the merchant has a carriage plan: it shipped something last year."""
    return bool(merchant.carriage_hours_wanted) and sum(merchant.carriage_hours_wanted.values()) > 0.0


def bids(setup, record) -> List[LabourBid]:
    """Each merchant's bid for carriers on the tiles its goods left last year. The merchants' plan is last
    year's shipments (what they wanted to carry, before any cut), because this year's purchases are not
    known until the goods markets clear, after the labour market. The most a hour of crew can be worth to
    a merchant is all of the carriage money its hours stand for."""
    crew = crew_of(setup)
    if crew is None:
        return []
    populated = {cohort.tile for cohort in record.cohorts.values()}
    return [LabourBid(merchant.agent_id, trade, labour_area(tile if tile in populated else merchant.home_tile),
                      hours * share, 1.0 / crew.hours_per_money)      # nobody lives where goods left: carriers come from home
            for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id)
            for tile, hours in sorted((merchant.carriage_hours_wanted or {}).items()) if hours > 0.0
            for trade, share in crew.trades]


def hired(ledger, merchant_id: str, trades) -> Dict[str, float]:
    """{"hours": hours this merchant's carriers worked, "wage": their average pay an hour}, over `trades`."""
    hours = sum(ledger.hours_hired.get(merchant_id, {}).get(trade, 0.0) for trade in trades)
    paid = 0.0
    quantity = 0.0
    for result in ledger.labour_results:
        if result.trade not in trades:
            continue
        for fill in result.fills:
            if fill.agent == merchant_id and fill.side == "buy":
                paid += fill.quantity * fill.price
                quantity += fill.quantity
    return {"hours": hours, "wage": paid / quantity if quantity > 0.0 else 0.0}


def wage_loans(setup, record, crew: Crew) -> List[LoanRequest]:
    """A one-year loan to each merchant whose carriers' wages for next year's plan its cash will not cover:
    carriers are paid at the labour market, before the year's lenders meet, so the merchant needs the cash
    in hand. It offers up to what the hours are worth to it above their wage, as a share of the wage."""
    money = setup.currency_id
    ceiling = 1.0 / crew.hours_per_money
    requests = []
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        bill, hours = 0.0, 0.0
        for tile, wanted in (merchant.carriage_hours_wanted or {}).items():
            for trade, share in crew.trades:
                bill += wanted * share * record.memory.wages.get(market_key(trade, labour_area(tile)), 0.0)
            hours += wanted
        short = bill - max(0.0, record.book.balance(merchant.agent_id, money))
        if short > 0.0 and bill > 0.0 and ceiling * hours > bill:
            requests.append(LoanRequest(merchant.agent_id, money, short, (ceiling * hours - bill) / bill, 1.0, short,
                                        WORKING_CAPITAL_PURPOSE))
    return requests
