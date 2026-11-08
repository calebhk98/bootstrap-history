"""A basket's needs priced on a tile, over the tables of `priced_need_tables`: `need_basket.priced_need` for every need at once.

Each sum the Python took with `math.fsum` is taken here with the exact sum of `opening_demand_kernel` (`_add`, `_total`), so the shares, the
price indexes and the ceilings equal the Python's to the last bit. `limit_shares` (the share limits' search, `need_basket.limited_shares`)
and `mix_shares` are written over plain arrays so the orders kernel's quality re-mix (`households_orders_kernel`) calls the same code."""
import numpy as np

from sim.jit import njit

from .opening_demand_kernel import PARTIALS, _add, _total

SHARE_LIMIT_TOLERANCE = 1e-12      # need_basket.limited_shares


@njit
def units_per_money(first, last, prices, effects, priced, share, partials):
    """The exact sum, over the priced rows `first` to `last`, of share times effect over price: need units one unit of money buys
    at the mix `share`."""
    count = 0
    for row in range(first, last):
        if priced[row]:
            count = _add(partials, count, share[row] * effects[row] / prices[row])
    return _total(partials, count)


@njit
def mix_shares(first, last, prices, effects, valued, exponent, priced, share, partials):
    """The constant-elasticity mix of the priced rows: each takes its weight, price over what it is valued at (effect, times its quality
    to the power the buyer pays for quality), to the `exponent`, over the exact sum of the weights. Fills `share`; returns the number of
    priced rows."""
    count = 0
    present = 0
    for row in range(first, last):
        share[row] = 0.0
        if priced[row]:
            present += 1
            share[row] = (prices[row] / valued[row]) ** exponent
            count = _add(partials, count, share[row])
    if present == 0:
        return 0
    power = _total(partials, count)
    for row in range(first, last):
        if priced[row]:
            share[row] = share[row] / power
    return present


@njit
def limit_shares(first, last, prices, effects, limits, priced, share, per_money, units, fixed_value, fixed_flag, partials, others):
    """`need_basket.limited_shares` over the rows `first` to `last`: each priced row with a limit (NaN means none) meets no more than its
    share of the need's units; the excess goes to the other goods in the proportions they were bought in. `per_money` is
    `units_per_money` at the shares as they come in. Unchanged when no limit binds. `units`, `fixed_value`, `fixed_flag` (1.0 once a
    row's share is fixed) are float scratch of the rows' length, `partials` and `others` two exact-sum scratch arrays."""
    binding = False
    for row in range(first, last):
        if priced[row]:
            units[row] = share[row] * effects[row] / prices[row] / per_money
            if limits[row] == limits[row] and units[row] > limits[row] + SHARE_LIMIT_TOLERANCE:
                binding = True
    if not binding:
        return
    for row in range(first, last):
        fixed_flag[row] = 0.0
        fixed_value[row] = 0.0
    while True:
        free_count = 0
        count = 0
        fixed_count = 0
        for row in range(first, last):
            if priced[row]:
                if fixed_flag[row] > 0.0:
                    fixed_count = _add(others, fixed_count, fixed_value[row])
                else:
                    free_count += 1
                    count = _add(partials, count, units[row])
        free_total = _total(partials, count)
        if free_count == 0 or free_total <= 0.0:
            break
        scale = (1.0 - _total(others, fixed_count)) / free_total
        over = False
        for row in range(first, last):
            if priced[row] and fixed_flag[row] <= 0.0 and limits[row] == limits[row] and units[row] * scale > limits[row] + SHARE_LIMIT_TOLERANCE:
                over = True
        if not over:
            for row in range(first, last):
                if priced[row] and fixed_flag[row] <= 0.0:
                    fixed_flag[row] = 1.0
                    fixed_value[row] = units[row] * scale
            break
        for row in range(first, last):
            if priced[row] and fixed_flag[row] <= 0.0 and limits[row] == limits[row] and units[row] * scale > limits[row] + SHARE_LIMIT_TOLERANCE:
                fixed_flag[row] = 1.0
                fixed_value[row] = limits[row]
    count = 0
    for row in range(first, last):
        if priced[row]:
            count = _add(partials, count, fixed_value[row] * prices[row] / effects[row])
    cost_per_unit = _total(partials, count)
    for row in range(first, last):
        if priced[row]:
            share[row] = fixed_value[row] * prices[row] / effects[row] / cost_per_unit


@njit
def price_ceilings(first, last, prices, effects, priced, ceiling):
    """`need_basket.price_ceilings`: the cheapest way to meet a need is bought up to the cost of the next cheapest per need unit, and
    a dearer good has no ceiling (inf). Fills `ceiling` at the priced rows."""
    for row in range(first, last):
        ceiling[row] = np.inf
        if not priced[row]:
            continue
        cheapest = np.inf
        for other in range(first, last):
            if other != row and priced[other]:
                cost = prices[other] / effects[other]
                if cost < cheapest:
                    cheapest = cost
        parity = cheapest * effects[row] if cheapest < np.inf else np.inf
        ceiling[row] = parity if parity >= prices[row] else np.inf


@njit
def price_needs(needs, rows, price_matrix, quality_reach, with_limits):
    """Every need priced: `need_basket.priced_need` for each need row, at the offered prices of its tile (`price_matrix[tile, good]`, NaN
    for none). Writes `price` and `priced` (a good with a positive price that gives need units), `share`, `ceiling` at the good rows and
    `need_priced` and `price_index` at the need rows. `quality_reach` (0 to 1) is how far the buyer pays for quality; `with_limits` says
    whether any good has a share limit (else the search is skipped)."""
    row_count = rows.row_count[0]
    units = np.zeros(row_count)
    fixed_value = np.zeros(row_count)
    fixed_flag = np.zeros(row_count)
    valued = np.zeros(row_count)
    partials = np.zeros(PARTIALS)
    others = np.zeros(PARTIALS)
    for need in range(needs.row_count[0]):
        first = needs.first_row[need]
        last = needs.end_row[need]
        for row in range(first, last):
            price = price_matrix[needs.tile[need], rows.good[row]]
            rows.price[row] = price
            rows.priced[row] = 1 if (price > 0.0 and rows.effect[row] > 0.0) else 0
            valued[row] = rows.effect[row] * rows.quality[row] ** quality_reach
        if mix_shares(first, last, rows.price, rows.effect, valued, needs.exponent[need], rows.priced, rows.share, partials) == 0:
            continue
        per_money = units_per_money(first, last, rows.price, rows.effect, rows.priced, rows.share, partials)
        if with_limits:
            limit_shares(first, last, rows.price, rows.effect, rows.limit, rows.priced, rows.share, per_money, units, fixed_value, fixed_flag,
                         partials, others)
            per_money = units_per_money(first, last, rows.price, rows.effect, rows.priced, rows.share, partials)
        price_ceilings(first, last, rows.price, rows.effect, rows.priced, rows.ceiling)
        needs.need_priced[need] = 1
        needs.price_index[need] = 1.0 / per_money
