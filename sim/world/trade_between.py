"""Two economies' markets for one material, linked by freight.

Each economy has its own market (`sim/world/market.py`) with its own
long-run cost. Goods move from the cheaper market to the dearer while the
price gap exceeds the freight over the route: arrivals are supply that cannot
idle in the importing market, and the same tonnes are demand in the exporting
one. Imports therefore cap a shortage at the importer and exports lift the
price at the exporter, until the gap shrinks to the freight cost. Prices are
compared in one money per tonne.

Standalone: tonnes and money in, tonnes out. A caller supplies the figures.
"""
import dataclasses
import math
from dataclasses import dataclass

from .market import MarketConditions, MarketOutcome, clear_market

FLOW_BISECTION_STEPS = 50


@dataclass(frozen=True)
class TradeOutcome:
    """`flow_tonnes` is what the home market receives from the foreign one;
    negative when it sends. The outcomes are each market's year with it."""
    flow_tonnes: float
    home: MarketOutcome
    foreign: MarketOutcome
    home_conditions: MarketConditions
    foreign_conditions: MarketConditions


def with_flow(home, foreign, flow_tonnes):
    """Both markets' conditions once `flow_tonnes` has moved from the foreign
    market to the home one (negative: from home to foreign)."""
    if flow_tonnes >= 0.0:
        return (dataclasses.replace(home, actor_supply_tonnes=home.actor_supply_tonnes + flow_tonnes),
                dataclasses.replace(foreign, committed_demand_tonnes=(
                    foreign.committed_demand_tonnes + flow_tonnes)))
    return (dataclasses.replace(home, committed_demand_tonnes=(
                home.committed_demand_tonnes - flow_tonnes)),
            dataclasses.replace(foreign, actor_supply_tonnes=(
                foreign.actor_supply_tonnes - flow_tonnes)))


def _offerable(conditions):
    """The most a market can send in a year: its capacity and stock."""
    return conditions.society_capacity_tonnes + conditions.stock_tonnes


def _price_gap(home, foreign, home_price, foreign_price, flow_tonnes):
    """Home price over foreign price (money per tonne) at a given flow."""
    home_at, foreign_at = with_flow(home, foreign, flow_tonnes)
    return (clear_market(home_at).price_ratio * home_price
            - clear_market(foreign_at).price_ratio * foreign_price)


def _solve_flow(home, foreign, home_price, foreign_price, freight, direction):
    """Largest flow (in `direction`, +1 into home, -1 out of it) whose price
    gap still exceeds freight; signed."""
    limit = _offerable(foreign if direction > 0 else home)
    if limit <= 0.0:
        return 0.0

    def margin(flow):
        return direction * _price_gap(home, foreign, home_price, foreign_price,
                                      direction * flow) - freight

    if margin(0.0) <= 0.0:
        return 0.0
    if margin(limit) > 0.0:
        return direction * limit
    low, high = 0.0, limit
    for _step in range(FLOW_BISECTION_STEPS):
        middle = 0.5 * (low + high)
        if margin(middle) > 0.0:
            low = middle
        else:
            high = middle
    return direction * 0.5 * (low + high)


def clear_trading_markets(home, foreign, home_price_per_tonne, foreign_price_per_tonne,
                          freight_per_tonne):
    """Clear two markets joined by a route that costs `freight_per_tonne`;
    prices are long-run costs in one money per tonne. A good one side cannot
    price is not traded."""
    flow = 0.0
    if (home_price_per_tonne > 0.0 and foreign_price_per_tonne > 0.0
            and math.isfinite(freight_per_tonne)):
        for direction in (1.0, -1.0):
            flow = _solve_flow(home, foreign, home_price_per_tonne, foreign_price_per_tonne,
                               freight_per_tonne, direction)
            if flow != 0.0:
                break
    home_after, foreign_after = with_flow(home, foreign, flow)
    return TradeOutcome(flow, clear_market(home_after), clear_market(foreign_after),
                        home_after, foreign_after)
