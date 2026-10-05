"""The contracts between the economy's modules: what each one offers and what the year loop calls.

A module implements its contract with plain functions over the records in `types.py` and its own
state dataclass. `economy.py` is the only module that calls across them, in the order below.

The year (`economy.Economy.step`), one civilisation's economy:

    1. view      a read-only `MarketView` of last year's prices, wages, rates and this year's holdings
    2. labour    households offer hours, producers and other employers bid for them; `labour.clear`
                 per (trade, area); wages are paid (settlement)
    3. credit    `credit.clear` matches loan requests (producers' from last close, households' and
                 merchants' from now) with savings, so the money reaches borrowers before they order
    4. goods     every agent posts bids and offers planned on the view; markets clear one good at a
                 time in input-depth order, so a good clears after the goods it is made from: before
                 a good clears, its producers `produce` from the inputs and hours they obtained and
                 offer the output; cycles in the recipe graph draw their inputs from stock
    5. money     `credit.service` collects interest and principal from the year's sales, ahead of
                 carriage, taxes and dividends, and books defaults (a lender's loss, in credit_claims);
                 the mint (mint.py) has bought metal and sold what it holds in the goods markets; coin wear and metal loss
                 take their share of the money and metal held
    6. close     each agent closes its year (consumes, records unmet need, updates expectations,
                 idles or exits); `inventory.carry` applies spoilage to every held stock

Every movement of money or goods is a `Transfer` or `GoodsMove` booked through `accounts.Book`.
An agent's purse never goes below zero except an edge account's (types.EDGE_*).
"""
from dataclasses import dataclass
from typing import Mapping, Optional, Protocol, Sequence, Tuple

from .types import (AgentId, AreaId, Bid, CurrencyId, FundsOffer, GoodId, LabourBid, LabourOffer,
                    LoanRequest, Offer, SiteLimit, TileId, TradeId)


@dataclass(frozen=True)
class AgentOrders:
    """Everything one agent puts on the markets in one year."""
    bids: Tuple[Bid, ...] = ()
    offers: Tuple[Offer, ...] = ()
    labour_bids: Tuple[LabourBid, ...] = ()
    labour_offers: Tuple[LabourOffer, ...] = ()
    loan_requests: Tuple[LoanRequest, ...] = ()
    funds_offers: Tuple[FundsOffer, ...] = ()


class MarketView(Protocol):
    """What an agent may know when it plans: last year's market outcomes and its own holdings."""
    year: int

    def price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """Last year's clearing price; None if the market never cleared."""

    def wage(self, trade: TradeId, area: AreaId) -> Optional[float]:
        """Last year's wage per hour."""

    def interest_rate(self, currency: CurrencyId) -> float:
        """Last year's base lending rate."""

    def area_of(self, good: GoodId, tile: TileId) -> AreaId:
        """The market area a good bought or sold on this tile trades in."""

    def currency_of(self, area: AreaId) -> CurrencyId:
        """The money prices in this area are counted in."""

    def price_level(self, currency: CurrencyId) -> float:
        """Last year's price level against the opening year (1.0 at the opening)."""

    def expected_inflation(self, currency: CurrencyId) -> float:
        """Adaptive expectation of next year's rise in the price level, as a share."""

    def cash(self, agent: AgentId, currency: CurrencyId) -> float:
        """The agent's money now."""

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        """The agent's holding of a good on a tile now."""


class Clearing(Protocol):
    """goods_market.clear and labour.clear share this shape."""

    def __call__(self, bids: Sequence, offers: Sequence, key: str, area: AreaId,
                 currency: CurrencyId, last_price: Optional[float]) -> object:
        """Clear one market for one year; deterministic in the order of its inputs."""


@dataclass(frozen=True)
class YearInputs:
    """What the engine hands the economy each year, through the port. Physical facts only."""
    year: int
    population_by_tile: Mapping[TileId, float]
    working_age_share: float
    yield_factor_by_producer: Mapping[AgentId, float]       # weather, depletion, technique: 1.0 is the opening
    engine_orders: Mapping[AgentId, AgentOrders]            # the founder, firms, the state: orders the engine decides
    legacy_transfers: Tuple = ()                            # one-sided engine postings, booked against EDGE_LEGACY
    harvest_factor: float = 1.0                             # this year's growing weather on households' own plots
    site_limits: Tuple[SiteLimit, ...] = ()                 # the sites' limits now; empty keeps the last declared
