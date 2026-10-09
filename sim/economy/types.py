"""Plain records the economy's modules pass to one another.

Every module in `sim/economy/` speaks these types and nothing else, so each can be written and
tested alone. Quantities are in the good's own unit (a `*_kg` good is counted in kg); money is in
the currency named beside it. Nothing here names a particular good, trade, place or currency.
"""
import math
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple

from sim.book import (EDGE_PREFIX, AgentId, CurrencyId, GoodId, GoodsMove, TileId, Transfer,  # noqa: F401
                      is_edge)

AreaId = str
TradeId = str

# Accounts that are the edge of the model: money and goods enter or leave the economy only through
# one of these, so every other agent's holdings change only by a transfer with a counterparty.
EDGE_MINT = "edge:mint"                  # coin struck from metal, or melted back into it
EDGE_ISSUE = "edge:issue"                # money an issuer creates or retires (fiat, notes)
EDGE_WEAR = "edge:wear"                  # coin and metal lost to wear, loss and burial
EDGE_EXTERNAL = "edge:external"          # foreign economies not modelled as agents here
EDGE_PRODUCTION = "edge:production"      # goods made: the counterparty of output
EDGE_CONSUMPTION = "edge:consumption"    # goods used up by households, inputs used in production
EDGE_SPOILAGE = "edge:spoilage"          # goods lost while held
EDGE_DEFAULT = "edge:default"            # debt written off
EDGE_LEGACY = "edge:legacy"              # engine postings that do not yet name a counterparty
EDGE_CARGO = "edge:cargo"                # money between a trader's purse (outside the book) and its cargo account


def external_edge(partner: str) -> AgentId:
    """The edge one partner's cargo arrives from and leaves to; it holds no money of its own, so the partner's
    payment goes through the foreign coin ledger, not the book."""
    return EDGE_EXTERNAL + ":" + partner


# ---- what exists -------------------------------------------------------------------------------

@dataclass(frozen=True)
class GoodSpec:
    good_id: GoodId
    unit_mass_kg: float              # mass of one unit, for freight
    spoilage_per_year: float         # share of a held stock lost in a year
    service_life_years: float        # 0: used up within the year; above 0: a durable that serves
    category: str                    # a data label (food, fuel, ...); code never branches on a good id

    @property
    def portable(self) -> bool:
        """False for a unit with no mass to carry (ground, a flow of energy): infinite unit mass."""
        return math.isfinite(self.unit_mass_kg)


@dataclass(frozen=True)
class CurrencySpec:
    currency_id: CurrencyId
    regime: str                      # "struck_coin", "weighed_metal", "commodity" or "fiat"
    backing_good: Optional[GoodId]   # the metal or commodity; None for fiat
    backing_per_unit: float          # units of backing_good in one unit of money; 0 for fiat
    issuer: Optional[AgentId]        # who strikes or prints it; None for weighed metal
    mint_charge_share: float = 0.0   # share of the metal the mint keeps when striking
    fineness: float = 1.0            # share of a struck coin's mass that is the backing metal


@dataclass(frozen=True)
class TileSpec:
    tile_id: TileId
    latitude: float
    longitude: float
    land_area_km2: float
    coastal: bool
    borders: Tuple[TileId, ...]
    arable_fraction: float
    fertility: float
    climate_class: str = ""          # a climate label from data (Koppen); empty when not known
    country: str = ""                # the civilisation whose people live and hold techniques here; empty is the home one


@dataclass(frozen=True)
class MarketArea:
    """Tiles close enough, for one good, that its price differs between them by less than carriage."""
    area_id: AreaId
    good_id: GoodId
    tiles: Tuple[TileId, ...]
    anchor_tile: TileId              # where the market sits; carriage within the area is counted to it


@dataclass(frozen=True)
class Recipe:
    """One way to make goods: per run, what goes in and what comes out. Data, never engine nodes."""
    recipe_id: str
    outputs: Mapping[GoodId, float]
    inputs: Mapping[GoodId, float]
    labour_hours: Mapping[TradeId, float]
    plant_goods: Mapping[GoodId, float] = field(default_factory=dict)        # tied up per run a year of capacity
    plant_labour_hours: Mapping[TradeId, float] = field(default_factory=dict)  # building that capacity
    plant_life_years: float = 0.0
    climate_classes: Tuple[str, ...] = ()   # climates it can be worked in, from data; empty: any
    site_bound: bool = False         # runs only where a site is declared (sites.py); the economy knows nothing else of it


@dataclass(frozen=True)
class SiteLimit:
    """What a site imposes on a recipe, declared from outside the economy (geography owns deposits)."""
    recipe_id: str
    tile: TileId
    capacity_runs_per_year: float    # most runs a year the site allows
    yield_factor: float = 1.0        # output per run against the recipe's own, at this site


# ---- moving money and goods --------------------------------------------------------------------

# ---- orders ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Bid:
    """A buyer's demand for one good in one market area, as a schedule.

    quantity_at(price) = min(floor_quantity + flexible_quantity * (price / reference_price) ** -elasticity,
                             budget / price)
    The floor is what the buyer needs whatever the price (subsistence, a recipe's fixed input);
    the budget caps it, so a buyer who cannot pay goes without and the shortfall is recorded.
    Above `maximum_price` the buyer takes nothing: a producer will not pay more for an input than
    the run it goes into is worth.
    """
    buyer: AgentId
    good: GoodId
    area: AreaId
    tile: TileId                     # where the goods are delivered
    floor_quantity: float
    flexible_quantity: float
    reference_price: float
    elasticity: float
    budget: float
    priority: int = 0                # lower clears first when rationed at the same price (need tiers)
    maximum_price: float = float("inf")   # above it the buyer takes nothing (what the good is worth to it)


@dataclass(frozen=True)
class Offer:
    """A seller's stock or output put on one market at the lowest price it will take.

    The reservation can sit below cost (a distressed seller, a perishable) and below zero
    (a waste product that costs money to be rid of).
    """
    seller: AgentId
    good: GoodId
    area: AreaId
    tile: TileId                     # where the goods are
    quantity: float
    reservation_price: float


@dataclass(frozen=True)
class Fill:
    agent: AgentId
    good: GoodId
    area: AreaId
    tile: TileId
    quantity: float                  # bought (buyer fill) or sold (seller fill), never negative
    price: float
    side: str                        # "buy" or "sell"


@dataclass(frozen=True)
class ClearingResult:
    good: GoodId
    area: AreaId
    currency: CurrencyId
    price: float
    quantity: float
    demand_at_price: float
    offered_at_price: float
    unmet_floor: float               # floor quantity buyers could not get or pay for
    fills: Tuple[Fill, ...]


@dataclass(frozen=True)
class LabourOffer:
    worker: AgentId                  # a household cohort
    trade: TradeId
    area: AreaId
    hours: float
    reservation_wage: float          # per hour: the outside option


@dataclass(frozen=True)
class LabourBid:
    employer: AgentId
    trade: TradeId
    area: AreaId
    hours: float
    maximum_wage: float              # per hour: what the hours are worth to the employer


@dataclass(frozen=True)
class LabourResult:
    trade: TradeId
    area: AreaId
    currency: CurrencyId
    wage: float                      # per hour
    hours_hired: float
    vacant_hours: float
    idle_hours: float
    fills: Tuple[Fill, ...]          # good = trade id, quantity = hours


@dataclass(frozen=True)
class LoanRequest:
    borrower: AgentId
    currency: CurrencyId
    amount: float
    maximum_rate: float
    years: float
    collateral_value: float
    purpose: str


@dataclass(frozen=True)
class FundsOffer:
    lender: AgentId
    currency: CurrencyId
    amount: float
    minimum_rate: float


@dataclass
class Loan:
    loan_id: str
    lender: AgentId
    borrower: AgentId
    currency: CurrencyId
    principal: float
    rate: float
    years_left: float
    collateral_value: float
    arrears: float = 0.0
    issued_year: int = 0
