"""What being a merchant costs, from the route's own fleet, the labour market and the capital market.

A merchant owns carriers, posts agents at both ends, ties money up in cargo while it waits for a
sailing and travels, and competes with the others on the route. Each term here follows from that:
the wait from the sailings the fleet offers, the agents' cost from the carriers' lift and the going
wage, the markup above cost from the number of merchants, the speed of change from how often a
carrier can change its cargo, and the capital from the merchants' own and borrowed money.

Standalone: counts, years and money in; shares, years and money out.
"""
import math

from sim.constants import declare

MONOPOLY_MARKUP_SHARE = declare(
    "MONOPOLY_MARKUP_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the price paid at the origin", source=None, confidence="D",
    why="The markup a lone merchant on a route could hold, which falls as 1 over the number of "
        "merchants (equal merchants choosing quantities). It is the inverse of the destination "
        "market's price elasticity of demand for the good, which no model yet supplies per route.")
AGENTS_PER_CARRIER = declare(
    "AGENTS_PER_CARRIER", 2.0, kind="engineering_estimate",
    unit="agents kept per carrier", confidence="D",
    source="A factor at each end of the route, to buy and load and to receive and sell, as in the "
           "commenda and societas partnerships of Mediterranean trade.",
    why="Agents' hours are charged per tonne the carrier lifts over a year; a route with a "
        "better-organised house needing fewer agents would lower it.")
BORROWING_PER_OWN_CAPITAL = declare(
    "BORROWING_PER_OWN_CAPITAL", 2.0, kind="engineering_estimate",
    unit="money borrowed per money of merchants' own", confidence="C",
    source="In the Genoese commenda an investing partner put up two thirds of the capital and the "
           "travelling partner one third (Lopez and Raymond, Medieval Trade in the Mediterranean "
           "World).",
    why="How far merchants' own capital stretches in borrowed money, before lenders' room limits it.")


def competition_markup_share(merchants):
    """Markup over cost, as a share of the price, when `merchants` equal merchants compete on a
    route: the lone merchant's markup divided by their number."""
    return MONOPOLY_MARKUP_SHARE / max(1.0, merchants)


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
