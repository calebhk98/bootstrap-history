"""The year's market for one material: price moves with scarcity around cost.

Producers who put goods on the market name a reservation price (producer_market.py): the cost of
making a unit by the technique each runs. One that cannot cover it at the clearing price sells nothing
that year. The market holds no technology: it takes tonnes and prices.

A price solver gives a long-run cost, the price at which building and running
capacity pays for itself. In any one year the price is set by what is on offer
against what is wanted, with capacity already built treated as sunk:

    supply  = the society's capacity + actors' output + sales into the market
              + stock held over from earlier years
    demand  = households (falls as price rises) + purchases that do not wait
              for a price (the founder's and projects')

The price ratio (price over long-run cost) is the one that clears the two.
It is held between a ceiling and two floors. Producers' floor: what running built capacity costs
without paying its capital back; below it society producers idle. Stock's floor: stock and price takers
(the founder's sales, actors' output) sell below any producer's cost, down to a holder's reservation
(stock_reservation_ratio: the producers' floor less the cost of carrying it a year); below that they hold. Above the
producers' floor everything on offer sells; at it the surplus goes unsold, society producers (who can
idle) take the unsold part and idle: only goods that exist are carried as stock. Capacity then follows the price:
it grows while the price sits above cost and shrinks while below.

Standalone: it takes tonnes and returns tonnes. `sim/engine/market_clearing.py`
supplies the figures.
"""
import math
from dataclasses import dataclass, replace
from typing import Optional, Tuple

from sim.constants import declare

from .producer_market import Offer, offered_tonnes

DEFAULT_DEMAND_PRICE_ELASTICITY = declare(
    "DEFAULT_DEMAND_PRICE_ELASTICITY", 0.5, kind="temporary_heuristic",
    unit="dimensionless (fall in quantity demanded per rise in price, in logs)",
    source=None, confidence="D",
    why="Short-run household and derived demand for a material is inelastic: "
        "recipes and habits do not change within a year. One value for every "
        "material; the need model's own substitution between goods "
        "(NEED_SUBSTITUTION_ELASTICITY) would give a per-material figure.")

SHORT_RUN_SUPPLY_PRICE_ELASTICITY = declare(
    "SHORT_RUN_SUPPLY_PRICE_ELASTICITY", 0.3, kind="temporary_heuristic",
    unit="dimensionless (rise in output per rise in price, in logs)",
    source=None, confidence="D",
    why="With capacity fixed, output still rises with price as dearer "
        "workings (a poorer seam, an older furnace) come in, and falls when "
        "they stop paying. One value for every material; the spread of "
        "deposit costs in sim/world/deposits.py would give a per-material "
        "curve.")

CLEARING_BISECTION_STEPS = 34

UNSPLIT_FLOOR_RATIO = 1.0   # a producer whose cost has no running part to idle on sells at no less than its cost

CARRYING_RATE_PER_YEAR = declare(
    "CARRYING_RATE_PER_YEAR", 0.1, kind="temporary_heuristic",
    unit="fraction of a held good's value per year (storage and interest)", source=None, confidence="D",
    retire="the agent economy's seller reservation search (sim/economy) reading storage cost and the interest rate",
    why="A holder of stock keeps it while selling now fetches less than selling later net of what holding "
        "costs. One figure for every material; a per-material storage cost and the economy's own interest "
        "rate would replace it. Spoilage is STOCK_RETENTION.")

DEFAULT_CEILING_RATIO = declare(
    "DEFAULT_CEILING_RATIO", 6.0, kind="temporary_heuristic",
    unit="price over long-run cost (maximum)", source=None, confidence="D",
    why="Where demand switches to substitutes or does without, so a shortage "
        "cannot raise the price without bound. Taken from the default price "
        "ceiling commodities.json already uses.")

CAPACITY_ADJUSTMENT_RATE = declare(
    "CAPACITY_ADJUSTMENT_RATE", 0.15, kind="temporary_heuristic",
    unit="fractional change in capacity per year per unit of price gap",
    source=None, confidence="D",
    why="How quickly society's producers open capacity when the price is above "
        "cost and idle it when below. Real lags depend on build time of the "
        "good's own plant, which the recipe data does not yet give.")

CAPACITY_MAXIMUM_STEP = declare(
    "CAPACITY_MAXIMUM_STEP", 0.3, kind="temporary_heuristic",
    unit="fraction of capacity per year (largest change)", source=None,
    confidence="D",
    why="Capacity cannot more than this fraction in a year however large the "
        "price gap, since building and closing both take time.")

STOCK_RETENTION = declare(
    "STOCK_RETENTION", 0.9, kind="temporary_heuristic",
    unit="fraction of unsold stock still there a year later", source=None,
    confidence="D",
    why="Unsold goods are carried to next year but spoil, leak or are written "
        "off at some rate. One figure for every material; a per-material "
        "storage loss from its physical properties would replace it.")


@dataclass(frozen=True)
class MarketConditions:
    """Everything the year's clearing depends on, in tonnes (a year's flow)."""
    household_demand_at_anchor_tonnes: float
    committed_demand_tonnes: float
    society_capacity_tonnes: float
    actor_supply_tonnes: float
    founder_sales_tonnes: float
    stock_tonnes: float
    actor_demand_tonnes: float = 0.0
    offers: Tuple[Offer, ...] = ()
    imports: Tuple[Offer, ...] = ()   # foreign cargo at its landed cost, as a ratio to the long-run cost
    demand_price_elasticity: float = DEFAULT_DEMAND_PRICE_ELASTICITY
    supply_price_elasticity: float = SHORT_RUN_SUPPLY_PRICE_ELASTICITY
    floor_ratio: float = UNSPLIT_FLOOR_RATIO
    stock_floor_ratio: Optional[float] = None   # a holder's reservation override; None reads the carrying cost
    carrying_rate: float = CARRYING_RATE_PER_YEAR
    ceiling_ratio: float = DEFAULT_CEILING_RATIO


@dataclass(frozen=True)
class MarketOutcome:
    price_ratio: float
    quantity_traded_tonnes: float
    society_sales_tonnes: float
    unsold_tonnes: float
    unmet_demand_tonnes: float
    offers_sold_tonnes: float = 0.0
    held_over_tonnes: float = 0.0   # goods that exist and did not sell: the stock carried on
    imports_sold_tonnes: float = 0.0


def _demand_at(conditions: MarketConditions, price_ratio: float) -> float:
    household = conditions.household_demand_at_anchor_tonnes * (
        price_ratio ** -conditions.demand_price_elasticity)
    return max(0.0, household + conditions.committed_demand_tonnes + conditions.actor_demand_tonnes)


def _society_output_at(conditions: MarketConditions, price_ratio: float) -> float:
    """What the society's producers bring to market at this price: their
    dearest working only pays above the cost it is already priced at, and
    below their floor they idle."""
    if price_ratio < conditions.floor_ratio:
        return 0.0
    return conditions.society_capacity_tonnes * (
        price_ratio ** conditions.supply_price_elasticity)


def stock_reservation_ratio(conditions: MarketConditions) -> float:
    """The price over long-run cost below which a holder keeps stock: what the market returns to once the
    stock is gone (the producers' floor), brought back a year at the cost of carrying it (spoilage, storage,
    interest)."""
    if conditions.stock_floor_ratio is not None:
        return conditions.stock_floor_ratio
    return conditions.floor_ratio * STOCK_RETENTION / (1.0 + conditions.carrying_rate)


def _stock_on_offer(conditions: MarketConditions, price_ratio: float) -> float:
    return conditions.stock_tonnes if price_ratio >= stock_reservation_ratio(conditions) else 0.0


def _supply_at(conditions: MarketConditions, price_ratio: float) -> float:
    return (_society_output_at(conditions, price_ratio) + conditions.actor_supply_tonnes
            + offered_tonnes(conditions.offers, price_ratio)
            + conditions.founder_sales_tonnes + _stock_on_offer(conditions, price_ratio))


def clearing_price_ratio(conditions: MarketConditions) -> float:
    """The price over long-run cost at which demand equals the supply on
    offer, held between the stock's floor and the ceiling."""
    low, high = min(stock_reservation_ratio(conditions), conditions.floor_ratio), conditions.ceiling_ratio
    if (conditions.committed_demand_tonnes == 0.0 and conditions.actor_demand_tonnes == 0.0
            and conditions.actor_supply_tonnes == 0.0 and not conditions.offers
            and conditions.founder_sales_tonnes == 0.0 and conditions.stock_tonnes == 0.0
            and conditions.society_capacity_tonnes > 0.0
            and conditions.household_demand_at_anchor_tonnes > 0.0):
        # Only households and society producers: demand = supply has a closed form.
        exponent = 1.0 / (conditions.demand_price_elasticity
                          + conditions.supply_price_elasticity)
        ratio = (conditions.household_demand_at_anchor_tonnes
                 / conditions.society_capacity_tonnes) ** exponent
        return min(high, max(conditions.floor_ratio, ratio))
    if _demand_at(conditions, low) <= _supply_at(conditions, low):
        return low
    if _demand_at(conditions, high) >= _supply_at(conditions, high):
        return high
    for _step in range(CLEARING_BISECTION_STEPS):
        middle = math.sqrt(low * high)
        if _demand_at(conditions, middle) > _supply_at(conditions, middle):
            low = middle
        else:
            high = middle
    return high     # the side where supply covers demand, so a producer pinned at its cost sells


def clear_market(conditions: MarketConditions) -> MarketOutcome:
    """The year's price ratio and who sells what at it. Cargo asking less than the producers' floor sells first,
    cheapest first, each lot at its own landed cost and only as far as demand at that price takes it; the rest
    of the market clears on what is left of demand, and the price ratio reported is the average the tonnes sold
    fetched. Cargo asking the floor or more is an ordinary offer."""
    cheap = sorted((offer for offer in conditions.imports if offer.reservation_ratio < conditions.floor_ratio),
                   key=lambda offer: offer.reservation_ratio)
    dearer = tuple(offer for offer in conditions.imports if offer.reservation_ratio >= conditions.floor_ratio)
    if not cheap:
        return _clear_at_one_price(replace(conditions, imports=(), offers=conditions.offers + dearer))
    sold_tonnes, takings, unsold_cargo = 0.0, 0.0, 0.0
    for offer in cheap:
        taken = min(offer.tonnes, max(0.0, _demand_at(conditions, offer.reservation_ratio) - sold_tonnes))
        sold_tonnes += taken
        takings += taken * offer.reservation_ratio
        unsold_cargo += offer.tonnes - taken
    rest = _clear_at_one_price(replace(
        conditions, imports=(), offers=conditions.offers + dearer,
        committed_demand_tonnes=conditions.committed_demand_tonnes - sold_tonnes))
    traded = sold_tonnes + rest.quantity_traded_tonnes
    price_ratio = (takings + rest.price_ratio * rest.quantity_traded_tonnes) / traded if traded > 0.0 else rest.price_ratio
    return replace(rest, price_ratio=price_ratio, quantity_traded_tonnes=traded, imports_sold_tonnes=sold_tonnes,
                   held_over_tonnes=rest.held_over_tonnes + unsold_cargo)


def _clear_at_one_price(conditions: MarketConditions) -> MarketOutcome:
    price_ratio = clearing_price_ratio(conditions)
    output = _society_output_at(conditions, price_ratio)
    supply = _supply_at(conditions, price_ratio)
    demand = _demand_at(conditions, price_ratio)
    traded = min(supply, demand)
    # Sellers who cannot idle sell first: the founder, actors, then stock;
    # the society's producers get what is left and carry what does not sell.
    offers_sold = min(offered_tonnes(conditions.offers, price_ratio), traded)
    after_outsiders = max(0.0, traded - conditions.founder_sales_tonnes
                          - conditions.actor_supply_tonnes - offers_sold)
    on_offer = _stock_on_offer(conditions, price_ratio)
    from_stock = min(on_offer, after_outsiders)
    # what exists and did not sell: stock held back or unsold, and outsiders' goods the market did not take
    outsiders = (conditions.founder_sales_tonnes + conditions.actor_supply_tonnes
                 + offered_tonnes(conditions.offers, price_ratio))
    held_over = outsiders + conditions.stock_tonnes - min(traded, outsiders + on_offer)
    society_sales = min(output, after_outsiders - from_stock)
    return MarketOutcome(
        price_ratio=price_ratio, quantity_traded_tonnes=traded,
        society_sales_tonnes=society_sales,
        unsold_tonnes=max(0.0, supply - traded),
        unmet_demand_tonnes=max(0.0, demand - supply), offers_sold_tonnes=offers_sold,
        held_over_tonnes=max(0.0, held_over))


def society_sales_displaced_by_founder(conditions: MarketConditions) -> float:
    """Tonnes the society's producers sell less because the founder sells."""
    if conditions.founder_sales_tonnes <= 0.0:
        return 0.0
    without = MarketConditions(**{**conditions.__dict__, "founder_sales_tonnes": 0.0})
    return max(0.0, clear_market(without).society_sales_tonnes
               - clear_market(conditions).society_sales_tonnes)


def adjusted_capacity(capacity_tonnes: float, price_ratio: float) -> float:
    """Next year's society capacity: it grows while the price is above the
    long-run cost, shrinks below, by a bounded step."""
    change = CAPACITY_ADJUSTMENT_RATE * (price_ratio - 1.0)
    change = max(-CAPACITY_MAXIMUM_STEP, min(CAPACITY_MAXIMUM_STEP, change))
    return capacity_tonnes * (1.0 + change)


def stock_after_year(outcome: MarketOutcome) -> float:
    """Stock carried into next year: goods that exist and did not sell, less what spoils. Idle capacity
    is not stock: a producer that cannot sell at its cost does not make the output."""
    return outcome.held_over_tonnes * STOCK_RETENTION
