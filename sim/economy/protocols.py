"""The contracts between the economy's modules: what each one offers and what the year loop calls.

A module implements its contract with plain functions over the records in `types.py` and its own
state dataclass. `economy.py` is the only module that calls across them, in the order below.

The year (`economy.Economy.step`), one civilisation's economy:

    1. view      a read-only `MarketView` of last year's prices, wages, rates and this year's holdings
    2. labour    households offer hours, producers and other employers bid for them; the labour core
                 (`sim.labour.api`) clears each (trade, area), then trains, moves and replaces people;
                 wages are paid (settlement)
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

Every movement of money or goods is a `Transfer` or `GoodsMove` booked through `book.Book`.
An agent's purse never goes below zero except an edge account's (types.EDGE_*).
"""
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol, Tuple

from sim.labour.api import School

from .types import (AgentId, AreaId, Bid, CurrencyId, FundsOffer, GoodId, LabourBid, LabourOffer,
                    LoanRequest, Offer, SiteLimit, TileId, TradeId)


@dataclass(frozen=True)
class AgentOrders:
    """Everything one agent puts on the markets in one year."""
    bids: Tuple[Bid, ...] = ()
    offers: Tuple[Offer, ...] = ()
    labour_bids: Tuple[LabourBid, ...] = ()
    labour_offers: Tuple[LabourOffer, ...] = ()
    funds_offers: Tuple[FundsOffer, ...] = ()


class MarketView(Protocol):
    """What an agent may know when it plans: last year's market outcomes and its own holdings."""
    year: int

    def price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The planning price: last year's traded price or, where nothing traded, the market's quote (see
        `price_kind`); None if the market never posted anything."""

    def cleared_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The price the market cleared at last year, as paid, not as remembered (the remembered price moves
        part of the way when little traded); None when nothing traded."""

    def offered_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """What a buyer can buy at: a price the market traded at or an ask still posted; None where nothing is on
        offer (a bid ceiling, a cost quote or a price remembered from an old trade)."""

    def price_kind(self, good: GoodId, area: AreaId) -> Optional[str]:
        """What `price` is: PRICE_SMOOTHED_TRADE, or the kind of quote or estimate; None when the market has no price."""

    def prices_across(self, good: GoodId, areas) -> list:
        """`price(good, area.area_id)` for each of `areas` (the good's areas), in order."""

    setup: Any
    """The trades and opening wages (`trade_wages.wage_in_view` prices a trade from them)."""

    def present_prices_at(self, names: tuple, tile: TileId) -> Mapping[str, float]:
        """`price` of each of `names` (goods) in its area on `tile`, those with a price only."""

    def usual_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """A slow average of the clearing price, which holders of durable goods compare today's with.
        A view may omit it; holders then expect no reversion."""

    def wage(self, trade: TradeId, area: AreaId) -> Optional[float]:
        """Last year's wage per hour."""

    def wage_held_anywhere(self, trade: TradeId) -> bool:
        """Whether any labour area has a remembered wage for the trade (`trade_wages` prices a trade none has on its opening wage)."""

    def interest_rate(self, currency: CurrencyId) -> Optional[float]:
        """Last year's base lending rate."""

    def area_of(self, good: GoodId, tile: TileId) -> AreaId:
        """The market area a good bought or sold on this tile trades in."""

    def currency_of(self, area: AreaId) -> CurrencyId:
        """The money prices in this area are counted in."""

    def basket_price_level(self, currency: CurrencyId) -> float:
        """Last year's price level against the opening year (1.0 at the opening)."""

    def opening_wage_level(self, currency: CurrencyId) -> float:
        """Today's money per opening-year money for the wages the setup opened with (see `MarketMemory.opening_wage_level`)."""

    def observed_inflation(self, currency: CurrencyId) -> Optional[float]:
        """Last year's rise in prices, the weighted median of the goods' changes; None before there is one."""

    def cash(self, agent: AgentId, currency: CurrencyId) -> float:
        """The agent's money now."""

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        """The agent's holding of a good on a tile now."""

    def equity(self, agent: AgentId) -> float:
        """What the agent owns of the firms (net worth by ownership share), in money; zero where the view has no firms."""

    def claims(self, agent: AgentId, currency: CurrencyId) -> float:
        """What the agent expects to collect on loans it has made; zero where the view has no loans."""

    def loss_rate(self, agent: AgentId, currency: CurrencyId) -> float:
        """The loss the agent expects per year of credit exposure; zero where the view has no loans."""


@dataclass(frozen=True)
class EconomyYearInputs:
    """What the engine hands the economy each year, through the port. Physical facts only."""
    year: int
    population_by_tile: Mapping[TileId, float]
    yield_factor_by_producer: Mapping[AgentId, float]       # weather, depletion, technique: 1.0 is the opening
    engine_orders: Mapping[AgentId, AgentOrders]            # the founder, firms, the state: orders the engine decides
    legacy_transfers: Tuple = ()                            # one-sided engine postings, booked against EDGE_LEGACY
    harvest_factor: float = 1.0                             # this year's growing weather on households' own plots
    site_limits: Tuple[SiteLimit, ...] = ()                 # the sites' limits now; empty keeps the last declared
    import_accounts: Tuple = ()                             # accounts that sell goods landed from abroad: their sales are imports
    export_accounts: Tuple = ()                             # accounts that buy goods for abroad: their purchases are exports
    labour_levy_hours_per_worker: float = 0.0               # hours of each working person's year the state takes (a corvee, conscripts)
    debt_relief_tiles: Tuple[TileId, ...] = ()              # tiles whose households' debts the state cancels this year (debt_relief.py)
    title_moves: Tuple[Tuple[TileId, str, str, float], ...] = ()    # (tile, giver, receiver, share) the state decrees: confiscation, land reform (titles_moves.py)
    farmed_forms: Tuple[str, ...] = ()                      # money revenue forms the state lets to the best bidder this year (tax_farming.py)
    tax_rates: Tuple[Tuple[str, float], ...] = ()           # (form, rate) the state holds this year; a form not named keeps its rate (taxes.with_rates)
    land_tax_share_of_rent: float = 0.0                     # share of a rent the state's land forms take from the owner (land_market.settle_year)
    taxed_share_by_tile: Mapping[TileId, float] = field(default_factory=dict)   # share of a stayer's income the state takes on each tile, liability rule included (flight_routes.py)
    state_reach_by_tile: Mapping[TileId, float] = field(default_factory=dict)   # share of the people on each tile the state's officials reach: the chance a leaver is recaptured there
    amnesty_share: float = 0.0                              # share of a fugitive's arrears the state waives (government_levers_tax.amnesty_share)
    immunity_years: float = 0.0                             # years a taker-up of deserted land owes nothing (government_levers_tax.immunity_years)
    institutions: Tuple[str, ...] = ()                      # the credit institutions the society holds (banks.DEPOSIT_BANKING): without one its households found none
    durable_users: Tuple[AgentId, ...] = ()                 # outside actors' asset accounts whose durables are in use
    bondage_tiles: Tuple[TileId, ...] = ()                  # tiles whose society recognises bondage: bonded people may be bought there (Complaint 644)
    schools: Tuple[School, ...] = ()                        # trade schools the engine's seats hold, by trade and area: the labour core trains through them
    bonded_for_sale: Mapping[TileId, Mapping[str, float]] = None   # bonded people of a trade on offer per tile; None is none
    credit_asks: Tuple[LoanRequest, ...] = ()               # credit lines the engine's seats ask for: they join the year's clearing and are granted a room (credit_lines.py)
    standing_bids: Tuple[Bid, ...] = ()                     # demand settled outside the book (the founder's draws): entry reads it as bids, nothing clears
    state_capacity: float = 1.0                             # share of what the state assesses its officials collect this year (0..1); follows the officials (taxes.assess)
    working_people_by_tile: Mapping[TileId, float] = field(default_factory=dict)   # demography's working-age people on each tile; a tile it names sets its cohorts' working people (the working-age share follows demography)
