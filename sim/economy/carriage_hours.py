"""Carriage as hired labour: the crew hours a merchant's shipments need are bid for in the year's labour
market before the goods move, and what is hired limits what is carried.

A haul's hours come from the route itself: each mode it travels spends geography's physical crew hours per
tonne-km on the tonne-km its legs cost, in that mode's trade (a sailor on water, a carter with animals, a porter on foot),
and each change to a mode the setup prices handling for (a port) spends handling hours of the unskilled trade.
The hours are bid at the tile the goods leave and paid that area's wage. The carriers and the feed
the animals eat are bought in the goods market (carriage_wear), and year_close keeps what is left of a fee with the
merchant that owns the carriers.
"""
import math
from typing import Dict, List, Optional, Tuple

from . import carriage_funding, credit, trade_wages
from .cohort_reads import populated_tiles
from .market_memory import KEY_SEPARATOR as MARKET_KEY_SEPARATOR, market_key
from .merchants import Merchant
from .producers_working_capital import WORKING_CAPITAL_PURPOSE
from .setup import labour_area
from .labour_bid_sink import BidFigures, bid_objects, put_bids
from .types import LabourBid, LoanRequest

CrewRows = Tuple[Tuple[str, float], ...]      # ((crew key, crew hours),): a crew key is market_key(trade, tile hired at)


def hires(setup) -> bool:
    """Whether the setup's carriage hires any crew hours."""
    return any(hours > 0.0 for _trade, hours in setup.carriage_crew.values())


def crew_trades(setup, mode_trade: str) -> Tuple[Tuple[str, float], ...]:
    """The trades a mode's crew hours are bid in, as (trade, share): the mode's own trade whole (a sailor on
    water, a carter with animals, a porter on foot), the unskilled trade where the mode names none. The labour
    core holds those trades from the opening (labour_state.seeded_hours), so they answer the bids."""
    return ((mode_trade or setup.unskilled_trade, 1.0),)


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
                trade = setup.carriage_handling_trade.get(mode) or setup.unskilled_trade
                hours[trade] = hours.get(trade, 0.0) + count * per_handling
        return hours

    def hours_per_tonne(self, source: str, destination: str) -> CrewRows:
        """((crew key, hours)) a tonne needs: the hours of each trade, hired where the goods leave."""
        found = self._rows.get((source, destination))
        if found is None:
            found = self._rows[(source, destination)] = tuple(
                (market_key(trade, source), hours)
                for trade, hours in sorted(self.hours_by_trade(source, destination).items()) if hours > 0.0)
        return found


def crew_for(setup, carriage_record, carriage) -> Optional[Crew]:
    """The year's crew over `carriage`, or None when the setup's modes name no crew hours."""
    return Crew(setup, carriage, carriage_record.area_imbalance) if hires(setup) else None


def wage_scale(setup, record, carriage) -> float:
    """The multiplier on the carriage table for the year: the rates were priced at `carriage_wage`, and their
    labour part (each hauled route's crew hours, handling included, over both legs of the round trip the
    emptiness of the returns leaves, at that wage) follows the wage of the area the goods left instead, as last
    year's labour market cleared it. The routes are last year's carried flows, so the mix of modes is the one
    used. The multiplier is the change in the labour part over the whole fee, so the table's fee as a whole moves
    by the labour change, spread over all its parts; route dues are paid apart from it (route_dues.py). Carriers are priced in the area they
    are hired in (`hiring_area`: the first merchant, by id, that wanted carriage from the tile gives it its home where nobody lives).
    The rates and `carriage_wage` are opening-year money, so the whole table is carried to today's money by the memory's
    `opening_wage_level` and the labour part then follows the wage against `carriage_wage` at that level. 1 where nothing has
    changed since the opening or nothing is carried; never below 0."""
    carried = record.carriage.carried
    if not carried or setup.carriage_wage <= 0.0 or not hires(setup):
        return record.memory.opening_wage_level(setup.currency_id)
    crew = Crew(setup, carriage, record.carriage.area_imbalance)
    populated = populated_tiles(record.cohorts)
    hired_in: Dict[str, str] = {}
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        for key in sorted(merchant.carriage_hours_wanted or {}):
            tile = _split(key)[1]
            hired_in.setdefault(tile, hiring_area(record, merchant, tile, populated))
    level = record.memory.opening_wage_level(setup.currency_id)
    money = 0.0
    labour_change = 0.0
    for source, row in sorted(carried.items()):
        for destination, tonnes in sorted(row.items()):
            cost = carriage.unscaled_cost_per_tonne(source, destination)
            if tonnes <= 0.0 or not math.isfinite(cost):
                continue
            money += tonnes * cost
            for trade, hours in crew.hours_by_trade(source, destination).items():
                wage = trade_wages.wage_in_area(setup, record.memory, trade, hired_in.get(source) or labour_area(source))
                labour_change += tonnes * hours * (wage - setup.carriage_wage * level)
    return max(0.0, level + labour_change / money) if money > 0.0 else level     # a fee never pays the shipper


def planned(merchant: Merchant) -> bool:
    """Whether the merchant has a carriage plan: it shipped something last year."""
    return bool(merchant.carriage_hours_wanted) and sum(merchant.carriage_hours_wanted.values()) > 0.0


def hiring_area(record, merchant: Merchant, tile: str, populated=None) -> str:
    """The labour area carriers for goods leaving `tile` are hired in: the tile's own, or the merchant's home
    where nobody lives (carriers come from home)."""
    if populated is None:
        populated = populated_tiles(record.cohorts)
    return labour_area(tile if tile in populated else merchant.home_tile)


def _split(key: str) -> Tuple[str, str]:
    trade, tile = key.split(MARKET_KEY_SEPARATOR, 1)
    return trade, tile


def bids(setup, record) -> List[LabourBid]:
    """`bid_figures` as records (an edge: the workforce's figures, tests)."""
    return bid_objects(bid_figures(setup, record))


def write_bids(sink, setup, record) -> List[BidFigures]:
    """Add every merchant's bid for carriers to the year's labour bids (a `LabourBidTable`, or a list of records), each merchant's bounded by
    what its cash pays at the area wages (`carriage_funding.fund_bids`); the bids written are returned."""
    wages: Dict[Tuple[str, str], float] = {}

    def wage_of(trade: str, area: str) -> float:
        if (trade, area) not in wages:
            wages[(trade, area)] = trade_wages.wage_in_area(setup, record.memory, trade, area)
        return wages[(trade, area)]
    figures = carriage_funding.fund_bids(bid_figures(setup, record), wage_of, lambda employer: record.book.balance(employer, setup.currency_id))
    put_bids(sink, figures)
    return figures


def bid_figures(setup, record) -> List[BidFigures]:
    """Each merchant's bid for carriers on the tiles its goods left last year, in the trades the hauls need: (employer, trade, area,
    hours, maximum wage) each. The merchants' plan is last year's shipments (what they wanted to carry, before any cut), because
    this year's purchases are not known until the goods markets clear, after the labour market. The most an hour of crew can be
    worth to a merchant is all of the carriage money its hours stand for."""
    if not hires(setup):
        return []
    populated = populated_tiles(record.cohorts)
    found = []
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        for key, hours in sorted((merchant.carriage_hours_wanted or {}).items()):
            if hours > 0.0:
                trade, tile = _split(key)
                found.append((merchant.agent_id, trade, hiring_area(record, merchant, tile, populated), hours,
                              merchant.carriage_money_wanted.get(key, 0.0) / hours))
    return found


def crew_wage(setup, record, merchant: Merchant, key: str, populated, kept=None) -> float:
    """The wage an hour of the crew `key` is priced at (`trade_wages.wage_in_area` of the area the merchant hires it in).
    `kept`, a dict the caller shares between merchants, holds the wage by (trade, area) once it is read."""
    trade, tile = _split(key)
    area = hiring_area(record, merchant, tile, populated)
    if kept is None:
        return trade_wages.wage_in_area(setup, record.memory, trade, area)
    if (trade, area) not in kept:
        kept[(trade, area)] = trade_wages.wage_in_area(setup, record.memory, trade, area)
    return kept[(trade, area)]


def _markets_of_plan(record, merchant: Merchant, populated):
    """({crew key: (trade, area it is hired in)}, {(trade, area): hours the plan wants there}) of the merchant's carriage plan."""
    market_of = {}
    markets: Dict[Tuple[str, str], float] = {}
    for key, hours in (merchant.carriage_hours_wanted or {}).items():
        trade, tile = _split(key)
        market_of[key] = (trade, hiring_area(record, merchant, tile, populated))
        markets[market_of[key]] = markets.get(market_of[key], 0.0) + hours
    return market_of, markets


def bought_in_plan_markets(record, merchant: Merchant, index, populated=None) -> Dict[Tuple[str, str], float]:
    """{(trade, area): hours bought} in the labour markets of the merchant's plan where `index` (`YearLedger.hours_hired_by_market`)
    holds a row for it; a merchant bids only in the markets of its plan, so these are all it bought."""
    if populated is None:
        populated = populated_tiles(record.cohorts)
    bought = {}
    for trade, area in _markets_of_plan(record, merchant, populated)[1]:
        row = index.get((merchant.agent_id, trade, area))
        if row is not None:
            bought[(trade, area)] = row[0]
    return bought


def engaged(record, merchant: Merchant, index, populated=None) -> Tuple[Dict[str, float], Dict[str, Optional[float]]]:
    """({crew key: hours hired}, {crew key: average wage, None where nothing was hired}) for the merchant's plan, from `YearLedger.hours_hired_by_market` (hours the employer paid for, not hours matched). Keys
    that share a labour market (goods leaving unpopulated tiles are bid for at home) share what was hired in
    proportion to their hours. `populated` is the populated tiles when the caller has them."""
    if populated is None:
        populated = populated_tiles(record.cohorts)
    plan = merchant.carriage_hours_wanted or {}
    market_of, markets = _markets_of_plan(record, merchant, populated)
    hours_by_key: Dict[str, float] = {}
    wage_by_key: Dict[str, Optional[float]] = {}
    for key, hours in plan.items():
        trade, area = market_of[key]
        bought, paid = index.get((merchant.agent_id, trade, area), (0.0, 0.0))
        hours_by_key[key] = bought * hours / markets[market_of[key]] if markets[market_of[key]] > 0.0 else 0.0
        wage_by_key[key] = paid / bought if bought > 0.0 else None
    return hours_by_key, wage_by_key


def wage_loans(setup, record) -> List[LoanRequest]:
    """A one-year loan to each merchant whose carriers' wages for next year's plan its cash will not cover: carriers are paid at the labour
    market, before the year's lenders meet, so the merchant needs the cash in hand. The request is the wage bill of the hours the plan wants
    that the cash does not pay (`carriage_funding.loan_wanted`), at the wage of the area each is hired in; the credit market's own cap
    rations it. It offers up to what the hours are worth to it above their wage, as a share of the wage."""
    money = setup.currency_id
    populated = populated_tiles(record.cohorts)
    requests = []
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        wanted_by_key = merchant.carriage_hours_wanted or {}
        pairs = [(hours, crew_wage(setup, record, merchant, key, populated)) for key, hours in wanted_by_key.items()]
        bill = carriage_funding.wage_bill(pairs)
        worth = sum(merchant.carriage_money_wanted.get(key, 0.0) for key in wanted_by_key)
        short = carriage_funding.loan_wanted(bill, worth, record.book.balance(merchant.agent_id, money))
        if short is not None:
            requests.append(LoanRequest(merchant.agent_id, money, short, credit.earnable_rate(worth - bill, bill), 1.0, short,
                                        WORKING_CAPITAL_PURPOSE))
    return requests
