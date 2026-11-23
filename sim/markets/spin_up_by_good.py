"""Which goods the spin-up's settle gaps are made of, for `spin-up-trace --stages`: pure arithmetic over the per-year
states of spin_up_gap.py (a replayed row also carries "mix", sim/economy/spin_up_mix.py). The settle test does not read
this; it says where to look when the test fails."""
from .spin_up_gap import price_gaps, state_gaps, value_at, window_gaps


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


MIX_OF_VALUED = {"stock_by_good": "stock", "output_by_good": "output"}      # the valued figure each mix value stands for


def valued_parts(before, after, kind):
    """`value_parts` of what is made ("output") or held ("stock") between two years' "valued" figures
    (sim/economy/spin_up_valued.py), every quantity at the earlier year's price (a good that year did not price at the
    later year's), as shares of the earlier year's output at those prices: what `spin_up_gap.valued_gaps` adds up."""
    prices, later = before["prices"], after["prices"]

    def values(quantities):
        return {good: quantity * prices.get(good, later.get(good, 0.0)) for good, quantity in quantities.items()}
    return value_parts(values(before[kind]), values(after[kind]), value_at(before["output"], prices, later))


def mix_parts(states, quantity, mix_name):
    """`value_parts` of the mix values `mix_name` ("stock_by_good" or "output_by_good") over the pair of `states` with
    the largest gap in `quantity`, as shares of the earlier year's real output (what `state_gaps` reads stock against;
    for output itself the parts then add up to its change). Where the pair carries a year's prices and quantities
    ("valued") the parts are read from them (`valued_parts`), as the gap is. Nothing when fewer than two states or
    neither is carried."""
    pair = worst_pair(states, quantity)
    if pair is not None and pair[0].get("valued") and pair[1].get("valued"):
        return valued_parts(pair[0]["valued"], pair[1]["valued"], MIX_OF_VALUED[mix_name])
    if pair is None or "mix" not in pair[0] or "mix" not in pair[1]:
        return []
    return value_parts(pair[0]["mix"][mix_name], pair[1]["mix"][mix_name], pair[0].get("real_output") or 0.0)


def level_of(costs):
    """The fixed-basket price level of {good: (its basket cost now, at the base prices)}: the first sum over the second;
    one where nothing is counted."""
    base = sum(at_base for _now, at_base in costs.values())
    return sum(now for now, _at_base in costs.values()) / base if base > 0.0 else 1.0


def level_parts(before, after):
    """[(good, "moved" or "entered" or "left", its effect on the price level)] between two years' basket costs
    (`spin_up_mix.basket_costs`), largest in size first. A good's effect is the later year's level less what that level
    would be had the good stayed as it was the year before (its earlier cost for one that moved, out of the count for
    one that entered, still in it for one that left), the others as they are in the later year; the effects need not
    add up to the change, since the level is a ratio."""
    level = level_of(after)
    parts = []
    for good in sorted(set(before) | set(after)):
        held = dict(after)
        if good in before and good in after:
            if before[good] == after[good]:
                continue
            kind = "moved"
            held[good] = before[good]
        elif good in after:
            kind = "entered"
            del held[good]
        else:
            kind = "left"
            held[good] = before[good]
        effect = level - level_of(held)
        if effect != 0.0:
            parts.append((good, kind, effect))
    return sorted(parts, key=lambda part: (-abs(part[2]), part[0]))


def price_level_parts(states):
    """`level_parts` over the pair of `states` with the largest gap in the price level, as shares of the earlier year's
    level; nothing when fewer than two states or no mix is carried."""
    pair = worst_pair(states, "price_level")
    if pair is None or "mix" not in pair[0] or "mix" not in pair[1]:
        return []
    earlier = level_of(pair[0]["mix"]["basket_costs"])
    return [(good, kind, effect / earlier) for good, kind, effect in level_parts(pair[0]["mix"]["basket_costs"], pair[1]["mix"]["basket_costs"])]


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


def misses(states, tolerance):
    """[(quantity, its gap, the good that moved it most or None, that good's part or None)] for the settle quantities whose
    gap over `states` (the measured years) is at or over `tolerance`, the largest gap first. The good is read where the
    quantity is made of goods: the watched prices (`price_parts`), the price level (`price_level_parts`), stock and
    output (`mix_parts`); hours, the rate and unmet need name none. Nothing when fewer than two states."""
    gaps = window_gaps(states)
    if gaps is None:
        return []
    found = []
    for quantity, gap in sorted(gaps.items(), key=lambda item: (-item[1], item[0])):
        if gap < tolerance:
            continue
        good, part = None, None
        if quantity == "prices":
            parts = price_parts(*worst_pair(states, "prices"))
            if parts:
                good, part = parts[0][0], parts[0][3]
        elif quantity == "price_level":
            parts = price_level_parts(states)
            if parts:
                good, part = parts[0][0], parts[0][2]
        elif quantity in ("inventory_value", "real_output"):
            parts = mix_parts(states, quantity, "stock_by_good" if quantity == "inventory_value" else "output_by_good")
            if parts:
                good, part = parts[0]
        found.append((quantity, gap, good, part))
    return found
