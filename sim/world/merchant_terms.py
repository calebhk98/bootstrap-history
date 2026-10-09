"""What being a merchant costs, from the route's own fleet, the labour market and the capital market.

A merchant owns carriers, posts agents at both ends, ties money up in cargo while it waits for a
sailing and travels, and competes with the others on the route. Each term here follows from that:
the wait from the sailings the fleet offers, the sailing season and the time to sell into the
destination's demand, the agents' cost from the carriers' lift and the going wage, the markup above
cost from the destination's price response and the number of houses, the speed of change from how
often a carrier can change its cargo, and the capital from the merchants' own and borrowed money.

Standalone: counts, years and money in; shares, years and money out.
"""
import math

from sim.constants import declare

from . import market

BORROWING_PER_OWN_CAPITAL = declare(
    "BORROWING_PER_OWN_CAPITAL", 2.0, kind="engineering_estimate",
    unit="money borrowed per money of merchants' own", confidence="C",
    source="In the Genoese commenda an investing partner put up two thirds of the capital and the "
           "travelling partner one third (Lopez and Raymond, Medieval Trade in the Mediterranean "
           "World).",
    why="How far merchants' own capital stretches in borrowed money, before lenders' room limits it.")


def price_flexibility(price_factor, landed_share):
    """How far the destination's price falls per rise in the quantity on its market, in logs: the
    inverse of the price elasticity of demand. `price_factor` is the price after a cargo of
    `landed_share` of the market's quantity lands, over the price before. None of it moves, or a rise,
    is no flexibility."""
    if landed_share <= 0.0 or price_factor >= 1.0 or price_factor <= 0.0:
        return 0.0
    return -math.log(price_factor) / math.log1p(landed_share)


def price_flexibility_or_default(flexibility):
    """The flexibility measured, or where no response is known the inverse of the market's default
    demand elasticity."""
    return 1.0 / market.DEFAULT_DEMAND_PRICE_ELASTICITY if flexibility is None else flexibility


def monopoly_markup_share(flexibility):
    """Markup over cost, as a share of the price, of a lone merchant who sells into a market whose
    price falls with the quantity landed at `flexibility` where price meets cost. For a demand that
    falls in a straight line the profit-maximising markup is flexibility over two plus flexibility."""
    flexibility = max(0.0, flexibility)
    return flexibility / (2.0 + flexibility)


def competition_markup_share(houses, flexibility):
    """Markup over cost, as a share of the price, when `houses` equal houses compete on a route: the
    lone merchant's markup divided by their number."""
    return monopoly_markup_share(flexibility) / max(1.0, houses)


def retained_share(return_on_capital, market_rate):
    """Share of what merchants earn above cost that they put back into trade: the part of their
    whole return (the market's rate plus the return above it) that is above the market's rate."""
    excess = max(0.0, return_on_capital)
    if math.isinf(excess):
        return 1.0
    return excess / (excess + max(0.0, market_rate)) if excess > 0.0 else 0.0


def selling_years(cargo_tonnes, demand_tonnes_per_year, houses):
    """Years the average tonne of a cargo waits to be sold: the market takes its demand a year and
    the houses on the route share it, so a cargo sells over its size over the house's share of the
    demand, and half of that is the average wait. Endless demand sells at once."""
    if math.isinf(demand_tonnes_per_year):
        return 0.0
    if demand_tonnes_per_year <= 0.0:
        return math.inf
    return 0.5 * max(0.0, cargo_tonnes) * max(1.0, houses) / demand_tonnes_per_year


def season_wait_years(open_share):
    """Average years a cargo waits for sailing to open when it is ready at a random time of year and
    the hulls sail `open_share` of the year: the closed share of the year times half of it."""
    closed = 1.0 - min(1.0, max(0.0, open_share))
    return 0.5 * closed * closed


def wait_years(round_trip_years, carriers):
    """Years cargo waits for a sailing at the two ends together: a route with `carriers` carriers
    on round trips of `round_trip_years` offers a sailing every round trip over carriers, and cargo
    waits half of that at each end. None, or endless, carriers mean no wait."""
    if carriers <= 0.0:
        return math.inf
    return 0.0 if math.isinf(carriers) else round_trip_years / carriers


def redirect_share_per_year(round_trip_years):
    """Share of a route's flow that can change cargo or direction in a year: a carrier changes only
    when it is home, once a round trip."""
    return 1.0 if round_trip_years <= 1.0 else 1.0 / round_trip_years


def capital_to_finance(own_capital, credit_room):
    """Money merchants can put into goods: their own, and what they borrow against it up to the room
    lenders have left (`None`: not yet known, so only the borrowing their own capital supports)."""
    own = max(0.0, own_capital)
    borrowed = BORROWING_PER_OWN_CAPITAL * own
    if credit_room is not None:
        borrowed = min(borrowed, max(0.0, credit_room))
    return own + borrowed


def agent_cost_per_tonne(lift_years_per_tonne, hours_per_person_year, wage_per_hour, agents_per_carrier):
    """Money for the agents kept at the two ends per tonne a carrier lifts: their hours over the
    carrier-years one tonne a year of lift takes, at the going wage. A sale that needs no carrier
    (None) needs no agents; where goods cross places this is what finding and serving buyers costs."""
    if lift_years_per_tonne is None:
        return 0.0
    return agents_per_carrier * lift_years_per_tonne * hours_per_person_year * wage_per_hour
