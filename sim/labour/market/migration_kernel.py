"""Migration over the tables (the kernels behind `migration.migrate`): workers re-weigh their area against the routes out of it.

A route is a row of the routes arrays, grouped by origin area (`route_first`, `route_count`) and sorted by (destination, moving
cost). The flows of every (origin, trade, route) are worked out from the people at the start of the step, then applied together,
so the order of areas does not matter. Sums that the Python added with `sum` or `math.fsum` use `exact_sums`."""
import math
from typing import NamedTuple

import numpy as np

from sim.jit import njit

from .exact_sums import exact_sum, python_sum
from .income_kernel import expected_income


class Routes(NamedTuple):
    """The year's routes out of every area, grouped by origin."""
    first: np.ndarray               # per area: its first route
    count: np.ndarray               # per area: how many routes leave it
    destination: np.ndarray         # per route: the area it leads to
    moving_cost: np.ndarray         # per route: what moving a person costs
    expected_penalty: np.ndarray    # per route: what a leaver expects to pay if the state recaptures him
    taxed_share: np.ndarray         # per area: share of a worker's income the state takes from those who stay


class MigrationRules(NamedTuple):
    """The rule's constants (migration.py declares them)."""
    taste_scale: float              # spread of the unobserved tastes, in log real income
    cost_weight: float              # weight of a move's cost, in years of the origin's subsistence, against the log gain
    consideration_share: float      # share of a trade's workers who weigh moving in a year


@njit
def real_income(rates, results, caps, hours, people, present, routes, area, trade, scratch_caps, scratch_hours):
    """Expected income after the state's take over the area's subsistence; NaN where the area has no subsistence figure."""
    floor = rates.subsistence[area]
    if math.isnan(floor) or floor == 0.0:
        return np.nan
    kept = 1.0 - min(1.0, max(0.0, routes.taxed_share[area]))
    return kept * expected_income(rates, results, caps, hours, people, present, area, trade, scratch_caps, scratch_hours) / floor


@njit
def move_shares(real_origin, options_income, options_cost, count, rules, shares, weights):
    """`migration.move_shares`: the share of the people of one place who move along each option this year (`shares[option]`).
    An option is the real income at its end (NaN or not above zero: it cannot be weighed) and the moving cost in years of the
    origin's subsistence; staying scores zero."""
    log_origin = math.log(real_origin)
    best = 0.0
    weighed = False
    for option in range(count):
        shares[option] = np.nan
        if math.isnan(options_income[option]) or options_income[option] <= 0.0:
            continue
        shares[option] = math.log(options_income[option]) - log_origin - rules.cost_weight * options_cost[option]
        if not weighed or shares[option] > best:
            best = shares[option]
        weighed = True
    if not weighed:
        for option in range(count):
            shares[option] = 0.0
        return
    top = max(0.0, best)
    stay_weight = math.exp((0.0 - top) / rules.taste_scale)
    for option in range(count):
        weights[option] = 0.0 if math.isnan(shares[option]) else math.exp((shares[option] - top) / rules.taste_scale)
    total = exact_sum(weights, count) + stay_weight
    for option in range(count):
        shares[option] = weights[option] / total * rules.consideration_share


@njit
def find_flows(rates, rules, results, caps, hours, workers, routes, scratch_caps, scratch_hours, flow_origin, flow_route, flow_trade,
               flow_people):
    """The flows of the step, in the order the Python rule made them (origins ascending, trades ascending, routes in order): origin
    area, route row, trade and people per band. Returns how many flows there are."""
    trade_count = rates.risk.shape[0]
    band_count = workers.people.shape[1]
    most_routes = 1
    for area in range(routes.count.shape[0]):
        most_routes = max(most_routes, routes.count[area])
    options_income, options_cost = np.empty(most_routes), np.empty(most_routes)
    shares, weights = np.empty(most_routes), np.empty(most_routes)
    cached = np.zeros(workers.present.shape[0], np.bool_)
    cache = np.zeros(workers.present.shape[0])
    found = 0
    for origin in range(routes.count.shape[0]):
        floor = rates.subsistence[origin]
        if routes.count[origin] == 0 or math.isnan(floor) or floor <= 0.0:
            continue
        for trade in range(trade_count):
            row = origin * trade_count + trade
            if not workers.present[row] or python_sum(workers.people[row], band_count) <= 0.0:
                continue
            real_origin = _cached_income(rates, results, caps, hours, workers, routes, origin, trade, scratch_caps, scratch_hours, cached, cache)
            if math.isnan(real_origin) or real_origin <= 0.0:
                continue
            for slot in range(routes.count[origin]):
                route = routes.first[origin] + slot
                if routes.destination[route] == origin:
                    options_income[slot], options_cost[slot] = np.nan, 0.0
                else:
                    options_income[slot] = _cached_income(rates, results, caps, hours, workers, routes, routes.destination[route], trade,
                                                          scratch_caps, scratch_hours, cached, cache)
                    options_cost[slot] = (routes.moving_cost[route] + routes.expected_penalty[route]) / floor
            move_shares(real_origin, options_income, options_cost, routes.count[origin], rules, shares, weights)
            for slot in range(routes.count[origin]):
                if shares[slot] > 0.0:
                    flow_origin[found], flow_route[found], flow_trade[found] = origin, routes.first[origin] + slot, trade
                    for band in range(band_count):
                        flow_people[found, band] = workers.people[row, band] * shares[slot]
                    found += 1
    return found


@njit
def _cached_income(rates, results, caps, hours, workers, routes, area, trade, scratch_caps, scratch_hours, cached, cache):
    row = area * rates.risk.shape[0] + trade
    if not cached[row]:
        cache[row] = real_income(rates, results, caps, hours, workers.people, workers.present, routes, area, trade, scratch_caps, scratch_hours)
        cached[row] = True
    return cache[row]


@njit
def apply_flows(workers, areas, counter, routes, trade_count, flow_origin, flow_route, flow_trade, flow_people, found, migrated, migrated_seen,
                migrated_order):
    """Move the people: out of the origin's bands, into the destination's (the pair is made if it was not there), and add the net
    change to each area's total in the order the areas first appear (origin, then destination, flow by flow)."""
    band_count = workers.people.shape[1]
    for flow in range(found):
        origin, destination, trade = flow_origin[flow], routes.destination[flow_route[flow]], flow_trade[flow]
        from_row, to_row = origin * trade_count + trade, destination * trade_count + trade
        if not areas.workers_named[destination]:
            areas.workers_named[destination] = True
            counter[0] += 1
            areas.workers_order[destination] = counter[0]
        if not workers.present[to_row]:
            workers.present[to_row] = True
            counter[0] += 1
            workers.order[to_row] = counter[0]
            workers.length[to_row] = band_count
        for band in range(band_count):
            workers.people[from_row, band] -= flow_people[flow, band]
            workers.people[to_row, band] += flow_people[flow, band]
        total = python_sum(flow_people[flow], band_count)
        for area, sign in ((origin, -1.0), (destination, 1.0)):
            if not migrated_seen[area]:
                migrated_seen[area] = True
                counter[0] += 1
                migrated_order[area] = counter[0]
            migrated[area] = migrated[area] + sign * total
