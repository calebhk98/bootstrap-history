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



@dataclass(frozen=True)
class TraderTerms:
    """`cost_share_of_price` is the merchants' cost over freight, as a share of the exporter's price
    per tonne. `adjustment_share` is the share of the distance from last year's flow to the
    arbitrage volume closed in a year. `agent_cost_per_tonne` is money for the agents at the two
    ends. The capital limits are tonnes a year each way. `margin_share` and `cycle_years` are the
    markup and the cycle the cost share was worked from, kept for the merchants' return."""
    cost_share_of_price: float
    adjustment_share: float
    capital_tonnes_in: float = math.inf
    capital_tonnes_out: float = math.inf
    agent_cost_per_tonne: float = 0.0
    margin_share: float = 0.0
    cycle_years: float = 0.0


def cost_share_of_price(margin_share, loss_share, market_rate, cycle_years):
    """Merchants' cost as a share of the price paid: margin, the expected loss of cargo (a share
    lost, grossed up to what must be bought to deliver one), and interest on the money tied up for
    a cycle of travel and waiting."""
    return margin_share + loss_share / (1.0 - loss_share) + market_rate * cycle_years

