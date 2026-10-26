"""Choosing a route on rates that already carry the provisions.

A route search prices each mode per km. A carrier's own food and water take lift from the cargo, so
a mode's real rate per tonne delivered is its rate over the share of lift left for cargo. The share
depends on the legs the route ends up with, so the search is repeated on rates divided by the share
the last route left, and the cheapest route priced with provisions is kept.

Standalone: the search, the pricing and the share come in as functions.
"""
import math

ROUNDS = 3


def _provisioned(base_rates, share_of, route):
    rates = {}
    for mode, rate in base_rates.items():
        share = share_of(mode, route)
        rates[mode] = rate / share if share > 0.0 else math.inf
    return rates


def choose_route(search, price, base_rates, share_of, rounds=ROUNDS):
    """The cheapest route of those searched, priced by `price`. `search(rates)` finds a route on
    per-km rates (None when nothing joins); `share_of(mode, route)` is the share of a carrier's lift
    that arrives as cargo on that route's legs of the mode (`route` None before one is known)."""
    rates = _provisioned(base_rates, share_of, None)
    best, best_price = None, math.inf
    for _round in range(rounds):
        found = search(rates)
        if found is None:
            break
        found_price = price(found)
        if best is None or found_price < best_price:
            best, best_price = found, found_price
        revised = _provisioned(base_rates, share_of, found)
        if revised == rates:
            break
        rates = revised
    return best
