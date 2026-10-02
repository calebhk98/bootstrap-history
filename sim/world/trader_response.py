"""What merchants charge and how fast they move goods between two markets.

`trade_between` moves the whole price gap above freight at once. Merchants
also pay agents, earn a markup, carry a risk of loss, and tie up money in the goods while
they travel and wait to be sold (interest at the market rate); and they do
not re-route a whole market's supply in a year. Here the cost over freight is
a share of the price paid at the origin and a sum per tonne, the flow adjusts a
share of the way each year from last year's flow toward the arbitrage volume
that cost leaves, and the flow is also limited by what carriers lift and merchants can finance.
The terms themselves are worked out in `sim/world/merchant_terms.py`.

Standalone: tonnes and money in, tonnes out.
"""
import dataclasses
import math
from dataclasses import dataclass

from . import trade_between


@dataclass(frozen=True)
class TraderTerms:
    """`cost_share_of_price` is the merchants' cost over freight, as a share of the exporter's price
    per tonne. `adjustment_share` is the share of the distance from last year's flow to the
    arbitrage volume closed in a year. `agent_cost_per_tonne` is money for the agents at the two
    ends. The capital limits are tonnes a year each way."""
    cost_share_of_price: float
    adjustment_share: float
    capital_tonnes_in: float = math.inf
    capital_tonnes_out: float = math.inf
    agent_cost_per_tonne: float = 0.0


def cost_share_of_price(margin_share, loss_share, market_rate, cycle_years):
    """Merchants' cost as a share of the price paid: margin, the expected loss of cargo (a share
    lost, grossed up to what must be bought to deliver one), and interest on the money tied up for
    a cycle of travel and waiting."""
    return margin_share + loss_share / (1.0 - loss_share) + market_rate * cycle_years


def clear_with_traders(home, foreign, home_price_per_tonne, foreign_price_per_tonne,
                       freight_per_tonne, terms, previous_flow_tonnes,
                       lift_into_home_tonnes=math.inf, lift_out_of_home_tonnes=math.inf):
    """`trade_between.clear_trading_markets` with merchants' costs and a partial adjustment from
    `previous_flow_tonnes` (positive into home)."""
    limit_in = min(lift_into_home_tonnes, terms.capital_tonnes_in)
    limit_out = min(lift_out_of_home_tonnes, terms.capital_tonnes_out)
    target = 0.0
    if (home_price_per_tonne > 0.0 and foreign_price_per_tonne > 0.0
            and math.isfinite(freight_per_tonne)):
        for direction in (1.0, -1.0):
            exporter_price = foreign_price_per_tonne if direction > 0 else home_price_per_tonne
            cost = (freight_per_tonne + terms.agent_cost_per_tonne
                    + terms.cost_share_of_price * exporter_price)
            target = trade_between.arbitrage_flow(
                home, foreign, home_price_per_tonne, foreign_price_per_tonne, cost, direction,
                limit_in if direction > 0 else limit_out)
            if target != 0.0:
                break
    flow = previous_flow_tonnes + terms.adjustment_share * (target - previous_flow_tonnes)
    # A faded flow, and last year's flow when markets have since shrunk, stay inside the limits.
    if flow > 0.0:
        flow = min(flow, limit_in, trade_between.offerable_tonnes(foreign))
    elif flow < 0.0:
        flow = -min(-flow, limit_out, trade_between.offerable_tonnes(home))
    if abs(flow) < 1e-9:
        flow = 0.0
    home_after, foreign_after = trade_between.with_flow(home, foreign, flow)
    return trade_between.TradeOutcome(
        flow, trade_between.clear_market(home_after), trade_between.clear_market(foreign_after),
        home_after, foreign_after)
