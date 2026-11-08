"""The merchants' route search for one good as a compiled loop over arrays (the rule of `merchants._good_routes`).

Areas are positions in the order the good's areas are listed. `prices` holds the price in each area, 0.0 where the
merchant knows none (a missing price and a zero price both leave an area out, as they always have). `cost` is the
carriage per tonne from one area's anchor tile to another's (infinite where no path exists), `years` the whole years a
haul between the anchors is held (0: not yet looked up), `id_order` the positions sorted by area id (it breaks ties
between equally dear destinations) and `source_allowed` which areas may be a source.

The answer is the rows (source position, destination position, rank, price here, outlay, most it pays) and the
(source, destination) pairs whose holding years were needed but unknown: the caller fills them in and searches again.
"""
import numpy as np

from sim.jit import njit

MISSING_YEARS_PLACEHOLDER = 1        # years a pair counts for while its real figure is looked up


@njit
def lost_share(spoilage_per_year, years):
    """The share of a good that spoils over `years` of holding."""
    return 1.0 - np.power(1.0 - min(1.0, max(0.0, spoilage_per_year)), float(years))


@njit
def nearest_costs(cost):
    """For each area, the least carriage per tonne from it to another area (infinite where no path leaves it)."""
    count_areas = cost.shape[0]
    nearest = np.full(count_areas, np.inf)
    for source in range(count_areas):
        for other in range(count_areas):
            if other != source and cost[source, other] < nearest[source]:
                nearest[source] = cost[source, other]
    return nearest


@njit
def search_good(prices, cost, years, id_order, source_allowed, interest_rate, spoilage_per_year, unit_mass_kg,
                margin_share, kilograms_per_tonne):
    capacity = prices.shape[0] * prices.shape[0]
    rows_source = np.empty(capacity, np.int64)
    rows_destination = np.empty(capacity, np.int64)
    rows_rank = np.empty(capacity, np.float64)
    rows_price_here = np.empty(capacity, np.float64)
    rows_outlay = np.empty(capacity, np.float64)
    rows_ceiling = np.empty(capacity, np.float64)
    missing = np.zeros(capacity, np.bool_)
    flagged = np.zeros(1, np.int64)
    count = search_into(prices, cost, nearest_costs(cost), years, id_order, source_allowed, interest_rate, spoilage_per_year, unit_mass_kg,
                        margin_share, kilograms_per_tonne, rows_source, rows_destination, rows_rank, rows_price_here,
                        rows_outlay, rows_ceiling, missing, flagged)
    return count, rows_source, rows_destination, rows_rank, rows_price_here, rows_outlay, rows_ceiling, missing


@njit
def search_into(prices, cost, nearest_cost, years, id_order, source_allowed, interest_rate, spoilage_per_year, unit_mass_kg,
                margin_share, kilograms_per_tonne, rows_source, rows_destination, rows_rank, rows_price_here,
                rows_outlay, rows_ceiling, missing, flagged):
    """`search_good` writing its rows into buffers of at least areas squared places and flagging pairs in `missing`
    (indexed source * areas + destination), adding one to `flagged[0]` for each; returns the row count. `nearest_cost` is `nearest_costs(cost)`, which a caller
    searching many times over one cost matrix keeps."""
    count_areas = prices.shape[0]
    count = 0
    interest = max(0.0, interest_rate)
    spoilage = min(1.0, max(0.0, spoilage_per_year))
    keep = 1.0 - spoilage
    found_price = False
    dearest = 0.0
    found_cheapest = False
    cheapest = 0.0
    for area in range(count_areas):
        price = prices[area]
        if price != 0.0:
            if not found_price or price > dearest:
                dearest = price
            found_price = True
            if price > 0.0 and (not found_cheapest or price < cheapest):
                cheapest = price
                found_cheapest = True
    if not found_cheapest:
        return count
    cheapest_floor = cheapest * (1.0 + interest + margin_share)
    if dearest * keep - cheapest_floor <= 0.0:
        return count
    # destinations dearest first, equal prices in area id order, leaving out those that cannot cover the cheapest floor
    candidates = np.empty(count_areas, np.int64)
    candidate_keys = np.empty(count_areas, np.float64)
    count_candidates = 0
    for position in range(count_areas):
        area = id_order[position]
        price = prices[area]
        if price != 0.0 and not price * keep - cheapest_floor <= 0.0:
            candidates[count_candidates] = area
            candidate_keys[count_candidates] = -price
            count_candidates += 1
    ranked = np.argsort(candidate_keys[:count_candidates], kind="mergesort")
    dearest_first = candidates[:count_candidates][ranked]
    dearest_kept = prices[dearest_first[0]] * keep
    for source in range(count_areas):
        price_here = prices[source]
        if price_here == 0.0 or not source_allowed[source]:
            continue
        if price_here <= 0.0:
            continue
        floor_cost = price_here * (1.0 + interest + margin_share)
        if dearest_kept - floor_cost <= 0.0:
            continue
        interest_here = price_here * interest
        margin_here = margin_share * price_here
        nearest = nearest_cost[source]
        if nearest == np.inf:
            continue
        nearest_money = nearest * unit_mass_kg / kilograms_per_tonne
        for rank_position in range(count_candidates):
            destination = dearest_first[rank_position]
            price_there = prices[destination]
            kept_there = price_there * keep
            if kept_there - floor_cost <= 0.0:
                break
            if kept_there - floor_cost - nearest_money + 1e-9 * (price_there + price_here + nearest_money) <= 0.0:
                break
            per_tonne = cost[source, destination]
            net = price_there - price_here - (per_tonne * unit_mass_kg / kilograms_per_tonne + interest_here + price_there * spoilage
                                              + margin_here)
            if net > 0.0:
                held_years = years[source, destination]
                if held_years == 0:
                    missing[source * count_areas + destination] = True
                    flagged[0] += 1
                    held_years = MISSING_YEARS_PLACEHOLDER
                if held_years > 1:
                    net -= interest_here * (held_years - 1) + price_there * (
                        lost_share(spoilage_per_year, held_years) - spoilage)
                if net > 0.0:
                    carriage_per_unit = per_tonne * unit_mass_kg / kilograms_per_tonne
                    outlay = price_here + carriage_per_unit
                    kept = price_there * (1.0 - lost_share(spoilage_per_year, held_years)) - carriage_per_unit
                    rows_source[count] = source
                    rows_destination[count] = destination
                    rows_rank[count] = -net / outlay
                    rows_price_here[count] = price_here
                    rows_outlay[count] = outlay
                    rows_ceiling[count] = max(0.0, kept) / (1.0 + interest * held_years + margin_share)
                    count += 1
    return count
