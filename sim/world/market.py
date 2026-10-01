"""The year's market for one material: price moves with scarcity around cost.

A price solver gives a long-run cost, the price at which building and running
capacity pays for itself. In any one year the price is set by what is on offer
against what is wanted, with capacity already built treated as sunk:

    supply  = the society's capacity + actors' output + sales into the market
              + stock held over from earlier years
    demand  = households (falls as price rises) + purchases that do not wait
              for a price (the founder's and projects')

The price ratio (price over long-run cost) is the one that clears the two.
It is held between a floor, what running built capacity costs without paying
its capital back, and a ceiling. Above the floor everything on offer sells;
at the floor the surplus goes unsold, society producers (who can idle) take
the unsold part, and it is carried as stock. Capacity then follows the price:
it grows while the price sits above cost and shrinks while below.

Standalone: it takes tonnes and returns tonnes. `sim/engine/market_clearing.py`
supplies the figures.
"""
import math
from dataclasses import dataclass

from sim.constants import declare

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

CLEARING_BISECTION_STEPS = 40

DEFAULT_FLOOR_RATIO = declare(
    "DEFAULT_FLOOR_RATIO", 0.4, kind="temporary_heuristic",
    unit="price over long-run cost (minimum)", source=None, confidence="D",
    why="What running capacity that is already built costs, as a share of the "
        "long-run cost, which also repays the capital. Taken from the share "
        "commodities.json already uses as its default price floor; a split "
        "of each recipe's cost into running and capital parts would replace "
        "it.")

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
    demand_price_elasticity: float = DEFAULT_DEMAND_PRICE_ELASTICITY
    supply_price_elasticity: float = SHORT_RUN_SUPPLY_PRICE_ELASTICITY
    floor_ratio: float = DEFAULT_FLOOR_RATIO
    ceiling_ratio: float = DEFAULT_CEILING_RATIO


@dataclass(frozen=True)
class MarketOutcome:
    price_ratio: float
    quantity_traded_tonnes: float
    society_sales_tonnes: float
    unsold_tonnes: float
    unmet_demand_tonnes: float


def _demand_at(conditions: MarketConditions, price_ratio: float) -> float:
    household = conditions.household_demand_at_anchor_tonnes * (
        price_ratio ** -conditions.demand_price_elasticity)
    return household + conditions.committed_demand_tonnes + conditions.actor_demand_tonnes


def _society_output_at(conditions: MarketConditions, price_ratio: float) -> float:
    """What the society's producers bring to market at this price: their
    dearest working only pays above the cost it is already priced at."""
    return conditions.society_capacity_tonnes * (
        price_ratio ** conditions.supply_price_elasticity)


def _supply_at(conditions: MarketConditions, price_ratio: float) -> float:
    return (_society_output_at(conditions, price_ratio) + conditions.actor_supply_tonnes
            + conditions.founder_sales_tonnes + conditions.stock_tonnes)


def clearing_price_ratio(conditions: MarketConditions) -> float:
    """The price over long-run cost at which demand equals the supply on
    offer, held between the floor and the ceiling."""
    low, high = conditions.floor_ratio, conditions.ceiling_ratio
    if (conditions.committed_demand_tonnes == 0.0 and conditions.actor_demand_tonnes == 0.0
            and conditions.actor_supply_tonnes == 0.0
            and conditions.founder_sales_tonnes == 0.0 and conditions.stock_tonnes == 0.0
            and conditions.society_capacity_tonnes > 0.0
            and conditions.household_demand_at_anchor_tonnes > 0.0):
        # Only households and society producers: demand = supply has a closed form.
        exponent = 1.0 / (conditions.demand_price_elasticity
                          + conditions.supply_price_elasticity)
        ratio = (conditions.household_demand_at_anchor_tonnes
                 / conditions.society_capacity_tonnes) ** exponent
        return min(high, max(low, ratio))
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
    return math.sqrt(low * high)


def clear_market(conditions: MarketConditions) -> MarketOutcome:
    """The year's price ratio and who sells what at it."""
    price_ratio = clearing_price_ratio(conditions)
    output = _society_output_at(conditions, price_ratio)
    supply = _supply_at(conditions, price_ratio)
    demand = _demand_at(conditions, price_ratio)
    traded = min(supply, demand)
    # Sellers who cannot idle sell first: the founder, actors, then stock;
    # the society's producers get what is left and carry what does not sell.
    after_outsiders = max(0.0, traded - conditions.founder_sales_tonnes
                          - conditions.actor_supply_tonnes)
    from_stock = min(conditions.stock_tonnes, after_outsiders)
    society_sales = min(output, after_outsiders - from_stock)
    return MarketOutcome(
        price_ratio=price_ratio, quantity_traded_tonnes=traded,
        society_sales_tonnes=society_sales,
        unsold_tonnes=max(0.0, supply - traded),
        unmet_demand_tonnes=max(0.0, demand - supply))


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
    """Stock carried into next year: what went unsold, less what is lost."""
    return outcome.unsold_tonnes * STOCK_RETENTION
