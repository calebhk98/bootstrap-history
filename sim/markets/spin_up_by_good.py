"""Which goods the spin-up's settle gaps are made of, for `spin-up-trace --stages`: pure arithmetic over the per-year
states of spin_up_gap.py (a replayed row also carries "mix", sim/economy/spin_up_mix.py). The settle test does not read
this; it says where to look when the test fails."""
from .spin_up_gap import price_gaps, state_gaps


def worst_pair(states, name):
    """(before, after): the consecutive pair of `states` with the largest gap in the quantity `name` (`state_gaps`),
    which is the pair the window's gap is read from; the earliest of equals; None when fewer than two states."""
    pairs = list(zip(states, states[1:]))
    if not pairs:
        return None
    return max(pairs, key=lambda pair: state_gaps(pair[0], pair[1]).get(name, 0.0))


def price_parts(before, after):
    """[(good, its share of the watched spending, its change, its part of the pair's "prices" gap)], largest part first.
    The parts add up to `spin_up_gap.price_gap` of the pair: a share is the earlier state's "price_weights" over all
    the watched goods, or one over the goods priced when the state carries none."""
    gaps = price_gaps(after["prices"], before["prices"])
    weights = before.get("price_weights")
    total = sum(weights.values()) if weights else 0.0
    if weights:
        shares = {good: weights.get(good, 0.0) / total if total > 0.0 else 0.0 for good in gaps}
    else:
        shares = {good: 1.0 / len(gaps) for good in gaps}
    return sorted(((good, shares[good], gap, shares[good] * gap) for good, gap in gaps.items()), key=lambda part: (-part[3], part[0]))


def largest_moves(states):
    """{good: the largest change of its watched price between consecutive `states`}."""
    largest = {}
    for before, after in zip(states, states[1:]):
        for good, gap in price_gaps(after["prices"], before["prices"]).items():
            largest[good] = max(gap, largest.get(good, 0.0))
    return largest


def trend_and_saw(series):
    """(trend, saw) of a quantity's values over consecutive years: the trend is the mean yearly change, each as a share of
    the year before, and the saw the mean size of a year's change about that trend. A trend with little saw is a quantity
    still adjusting; a saw with little trend is one that overshoots back and forth. A year with no value, or a year
    before at nothing, breaks the chain there; None when no pair of years is left."""
    moves = [(after - before) / before for before, after in zip(series, series[1:])
             if before is not None and after is not None and before > 0.0]
    if not moves:
        return None
    trend = sum(moves) / len(moves)
    return trend, sum(abs(move - trend) for move in moves) / len(moves)


def price_trends(rows):
    """{good: `trend_and_saw` of its watched price over `rows`} for the goods with at least one pair of priced years."""
    goods = sorted({good for row in rows for good in row["prices"]})
    found = {good: trend_and_saw([row["prices"].get(good) for row in rows]) for good in goods}
    return {good: figures for good, figures in found.items() if figures is not None}


def value_parts(before, after, base):
    """[(good, the change of its value from `before` to `after` ({good: value}) as a share of `base`)], largest in size
    first; a good in only one of the two changed by its whole value. Nothing when `base` is not positive."""
    if not base > 0.0:
        return []
    parts = [(good, (after.get(good, 0.0) - before.get(good, 0.0)) / base) for good in sorted(set(before) | set(after))]
    return sorted((part for part in parts if part[1] != 0.0), key=lambda part: (-abs(part[1]), part[0]))


def mix_parts(states, quantity, mix_name):
    """`value_parts` of the mix values `mix_name` ("stock_by_good" or "output_by_good") over the pair of `states` with
    the largest gap in `quantity`, as shares of the earlier year's real output (what `state_gaps` reads stock against;
    for output itself the parts then add up to its change). Nothing when fewer than two states or no mix is carried."""
    pair = worst_pair(states, quantity)
    if pair is None or "mix" not in pair[0] or "mix" not in pair[1]:
        return []
    return value_parts(pair[0]["mix"][mix_name], pair[1]["mix"][mix_name], pair[0].get("real_output") or 0.0)


def by_good(rows, measured_years):
    """{good: {"share", "move" (largest over the measured years), "part" (of the "prices" gap, in the pair of measured
    years where that gap is largest), "trend", "saw" (over all the trimmed rows)}} for the watched goods priced in the
    trimmed stage of `rows`; a figure the rows do not give is None."""
    trimmed = [row for row in rows if row["stage"] == "trimmed"]
    measured = trimmed[-measured_years:]
    pair = worst_pair(measured, "prices")
    parts = {good: (share, part) for good, share, _gap, part in (price_parts(*pair) if pair else [])}
    moves = largest_moves(measured)
    trends = price_trends(trimmed)
    table = {}
    for good in sorted(set(parts) | set(moves) | set(trends)):
        share, part = parts.get(good, (None, None))
        trend, saw = trends.get(good, (None, None))
        table[good] = {"share": share, "move": moves.get(good), "part": part, "trend": trend, "saw": saw}
    return table
