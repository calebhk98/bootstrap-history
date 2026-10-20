"""Carriage as hired labour: the crew hours a merchant's shipments need are bid for in the year's labour
market before the goods move, and what is hired limits what is carried.

A haul's hours come from the route itself: each mode it travels spends geography's physical crew hours per
tonne-km on the tonne-km its legs cost, in that mode's trade (a sailor on water, a carter with animals, a porter on foot),
and each change to a mode the setup prices handling for (a port) spends handling hours of the unskilled trade.
The hours are bid at the tile the goods leave and paid that area's wage. Carts, ships and animals as capital,
and the feed they eat, are not yet modelled here: the part of a fee that is not crew pay still goes to the
households of the tile the goods leave (year_close).
"""
import math
from typing import Dict, List, Optional, Tuple

from sim.constants import declare

from .market_memory import KEY_SEPARATOR as MARKET_KEY_SEPARATOR, market_key
from .merchants import Merchant
from .producers_close import WORKING_CAPITAL_PURPOSE
from .setup import labour_area
from .types import LabourBid, LoanRequest

CARRIAGE_CREW_UNSKILLED_SHARE = declare(
    "CARRIAGE_CREW_UNSKILLED_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the crew hours bid in the setup's unskilled trade", source=None, confidence="D",
    retire="Complaints/556: one workforce owner whose opening places people in the trades the opening's flows need",
    why="The opening places people by the runs producers expect, not by the goods merchants carry, so no "
        "carters or sailors exist when merchants first ship and a specialist trade left to train its own would "
        "stop carriage for years. The crew hours are bid in the unskilled trade (porters and drovers on foot "
        "are labourers in the trade data) instead of the mode's carter or sailor trade.")

CrewRows = Tuple[Tuple[str, float], ...]      # ((crew key, crew hours),): a crew key is market_key(trade, tile hired at)


def hires(setup) -> bool:
    """Whether the setup's carriage hires any crew hours."""
    return any(hours > 0.0 for _trade, hours in setup.carriage_crew.values())


def crew_trades(setup, mode_trade: str) -> Tuple[Tuple[str, float], ...]:
    """The trades a mode's crew hours are bid in, as (trade, share): the unskilled trade for the share
    CARRIAGE_CREW_UNSKILLED_SHARE names and the mode's own for the rest."""
    unskilled = min(1.0, max(0.0, CARRIAGE_CREW_UNSKILLED_SHARE))
    merged: Dict[str, float] = {}
    for trade, share in ((setup.unskilled_trade, unskilled), (mode_trade, 1.0 - unskilled)):
        merged[trade] = merged.get(trade, 0.0) + share
    return tuple((trade, share) for trade, share in sorted(merged.items()) if share > 0.0)


class Crew:
    """The crew hours a tonne needs on any haul of a carriage table, at the return-trip emptiness `imbalance`
    leaves (the carriers' empty legs home are crewed too)."""

    def __init__(self, setup, carriage, imbalance: float):
        self.setup, self.carriage, self.imbalance = setup, carriage, imbalance
        self.rates = setup.carriage_rates_at(imbalance)
        self._rows: Dict[Tuple[str, str], CrewRows] = {}

    def hours_by_trade(self, source: str, destination: str) -> Dict[str, float]:
        """{trade: crew hours} to carry a tonne from `source` to `destination` by the table's cheapest path. A
        mode's crew hours follow the money its legs cost: that money over the mode's rate is the tonne-km it
        stands for (grades and detours included), and each tonne-km spends the mode's crew hours. Each handling
        into a mode the setup prices spends its handling hours, of the unskilled trade, and its money is not a leg's."""
        haul = self.carriage.haul(source, destination)
        setup = self.setup
        handlings = dict(haul.handlings_by_mode)
        hours: Dict[str, float] = {}
        for mode, money in haul.money_by_mode:
            mode_trade, per_tonne_km = setup.carriage_crew.get(mode, ("", 0.0))
            rate = self.rates.get(mode, 0.0)
            leg_money = money - handlings.get(mode, 0) * setup.handling_rates.get(mode, 0.0)
            if per_tonne_km > 0.0 and rate > 0.0 and leg_money > 0.0:
                tonne_km = leg_money / rate
                for trade, share in crew_trades(setup, mode_trade):
                    hours[trade] = hours.get(trade, 0.0) + tonne_km * per_tonne_km * (1.0 + self.imbalance) * share
        for mode, count in haul.handlings_by_mode:
            per_handling = setup.carriage_handling.get(mode, 0.0)
            if per_handling > 0.0:
                hours[setup.unskilled_trade] = hours.get(setup.unskilled_trade, 0.0) + count * per_handling
        return hours

    def hours_per_tonne(self, source: str, destination: str) -> CrewRows:
        """((crew key, hours)) a tonne needs: the hours of each trade, hired where the goods leave."""
        found = self._rows.get((source, destination))
        if found is None:
            found = self._rows[(source, destination)] = tuple(
                (market_key(trade, source), hours)
                for trade, hours in sorted(self.hours_by_trade(source, destination).items()) if hours > 0.0)
        return found


def crew_for(setup, record, carriage) -> Optional[Crew]:
    """The year's crew over `carriage`, or None when the setup's modes name no crew hours."""
    return Crew(setup, carriage, record.area_imbalance) if hires(setup) else None


def wage_scale(setup, record, carriage) -> float:
    """The multiplier on the carriage table for the year: the rates were priced at `carriage_wage`, and their
    labour part (each hauled route's crew hours, handling included, over both legs of the round trip the
    emptiness of the returns leaves, at that wage) follows the wage of the area the goods left instead, as last
    year's labour market cleared it. The routes are last year's carried flows, so the mix of modes is the one
    used. The rest of a fee (feed, carts, animals) keeps its price. 1 where the wages are the one priced, or
    nothing is known of either; never below 0."""
    carried = getattr(record, "carried", None)
    if not carried or setup.carriage_wage <= 0.0 or not hires(setup):
        return 1.0
    crew = Crew(setup, carriage, record.area_imbalance)
    wages = record.memory.wages
    money = 0.0
    labour_change = 0.0
    for source, row in sorted(carried.items()):
        for destination, tonnes in sorted(row.items()):
            cost = carriage.unscaled_cost_per_tonne(source, destination)
            if tonnes <= 0.0 or not math.isfinite(cost):
                continue
            money += tonnes * cost
            for trade, hours in crew.hours_by_trade(source, destination).items():
                wage = wages.get(market_key(trade, labour_area(source)), 0.0)
                if wage > 0.0:
                    labour_change += tonnes * hours * (wage - setup.carriage_wage)
    return max(0.0, 1.0 + labour_change / money) if money > 0.0 else 1.0     # a fee never pays the shipper


def planned(merchant: Merchant) -> bool:
    """Whether the merchant has a carriage plan: it shipped something last year."""
    return bool(merchant.carriage_hours_wanted) and sum(merchant.carriage_hours_wanted.values()) > 0.0


def hiring_area(record, merchant: Merchant, tile: str, populated=None) -> str:
    """The labour area carriers for goods leaving `tile` are hired in: the tile's own, or the merchant's home
    where nobody lives (carriers come from home)."""
    if populated is None:
        populated = {cohort.tile for cohort in record.cohorts.values()}
    return labour_area(tile if tile in populated else merchant.home_tile)


def _split(key: str) -> Tuple[str, str]:
    trade, tile = key.split(MARKET_KEY_SEPARATOR, 1)
    return trade, tile


def bids(setup, record) -> List[LabourBid]:
    """Each merchant's bid for carriers on the tiles its goods left last year, in the trades the hauls need. The
    merchants' plan is last year's shipments (what they wanted to carry, before any cut), because this year's
    purchases are not known until the goods markets clear, after the labour market. The most an hour of crew
    can be worth to a merchant is all of the carriage money its hours stand for."""
    if not hires(setup):
        return []
    populated = {cohort.tile for cohort in record.cohorts.values()}
    found = []
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        for key, hours in sorted((merchant.carriage_hours_wanted or {}).items()):
            if hours > 0.0:
                trade, tile = _split(key)
                found.append(LabourBid(merchant.agent_id, trade, hiring_area(record, merchant, tile, populated), hours,
                                       merchant.carriage_money_wanted.get(key, 0.0) / hours))
    return found


def last_wage(record, key: str) -> float:
    """What an hour of the crew `key` (trade and tile it is hired at) was last paid in its labour market, 0 when unknown."""
    trade, tile = _split(key)
    return record.memory.wages.get(market_key(trade, labour_area(tile)), 0.0)


def hired_index(ledger) -> Dict[Tuple[str, str, str], Tuple[float, float]]:
    """{(employer, trade, area): (hours bought, money paid)} over the year's labour markets."""
    found: Dict[Tuple[str, str, str], Tuple[float, float]] = {}
    for result in ledger.labour_results:
        for fill in result.fills:
            if fill.side == "buy":
                bought, paid = found.get((fill.agent, result.trade, result.area), (0.0, 0.0))
                found[(fill.agent, result.trade, result.area)] = (bought + fill.quantity, paid + fill.quantity * fill.price)
    return found


def engaged(record, merchant: Merchant, index) -> Tuple[Dict[str, float], Dict[str, float]]:
    """({crew key: hours hired}, {crew key: average wage}) for the merchant's plan, from `hired_index`. Keys
    that share a labour market (goods leaving unpopulated tiles are bid for at home) share what was hired in
    proportion to their hours."""
    populated = {cohort.tile for cohort in record.cohorts.values()}
    plan = merchant.carriage_hours_wanted or {}
    markets: Dict[Tuple[str, str], float] = {}
    market_of = {}
    for key, hours in plan.items():
        trade, tile = _split(key)
        market_of[key] = (trade, hiring_area(record, merchant, tile, populated))
        markets[market_of[key]] = markets.get(market_of[key], 0.0) + hours
    hours_by_key: Dict[str, float] = {}
    wage_by_key: Dict[str, float] = {}
    for key, hours in plan.items():
        trade, area = market_of[key]
        bought, paid = index.get((merchant.agent_id, trade, area), (0.0, 0.0))
        hours_by_key[key] = bought * hours / markets[market_of[key]] if markets[market_of[key]] > 0.0 else 0.0
        wage_by_key[key] = paid / bought if bought > 0.0 else 0.0
    return hours_by_key, wage_by_key


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


def wage_loans(setup, record) -> List[LoanRequest]:
    """A one-year loan to each merchant whose carriers' wages for next year's plan its cash will not cover:
    carriers are paid at the labour market, before the year's lenders meet, so the merchant needs the cash
    in hand. It offers up to what the hours are worth to it above their wage, as a share of the wage."""
    money = setup.currency_id
    populated = {cohort.tile for cohort in record.cohorts.values()}
    requests = []
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        bill, worth = 0.0, 0.0
        for key, wanted in (merchant.carriage_hours_wanted or {}).items():
            trade, tile = _split(key)
            area = hiring_area(record, merchant, tile, populated)
            bill += wanted * record.memory.wages.get(market_key(trade, area), 0.0)
            worth += merchant.carriage_money_wanted.get(key, 0.0)
        short = bill - max(0.0, record.book.balance(merchant.agent_id, money))
        if short > 0.0 and bill > 0.0 and worth > bill:
            requests.append(LoanRequest(merchant.agent_id, money, short, (worth - bill) / bill, 1.0, short,
                                        WORKING_CAPITAL_PURPOSE))
    return requests
