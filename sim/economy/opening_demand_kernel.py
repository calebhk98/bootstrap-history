"""What every cohort of an opening buys at an income, in one pass over arrays (the kernel of `opening_demand.py`).

The rules are `households_orders.goods_orders` (the cohort's budget, its needs' units, the goods' affordability, the
durables' replacement, the surplus scaled to the spending, the store's bids), `opening_own.OwnPlots.resting_orders`
(the purse that matches the budget the plot frees), `year_goods.less_what_it_grew` (the floors the plot grew are not
bought) and `goods_market.quantity_at` (what a bid takes at the opening price), each written once over the packed
cohorts, needs, goods and store goods. The packed columns are named by the constants below; a cohort's needs, goods
and store goods are contiguous slices of the arrays. A bid exists when its budget is above nothing, and a cohort whose
spending only just covers its floors has a budget left for the rest of a few ulps or none, so the sums the old code made
with `math.fsum` (or the compensated `sum`) are made here exactly (`_add`, `_total`) and the answer is the old one."""
import numpy as np

from sim.jit import njit

# constants row (opening_demand.constants)
K_FLOOR_MARGIN = 0
K_SAFETY = 1
K_DRAWDOWN = 2
K_CUT = 3
K_CASH_SHARE = 4
K_WEALTH_TARGET = 5          # months of income held as share wealth, as a share of a year
K_STORE_LIMIT = 6
K_STORE_SHARE = 7
K_TIME_PREFERENCE = 8
K_BAND = 9
K_HOUSEHOLD_SIZE = 10
K_PURSE_TOLERANCE = 11
K_COUNT = 12

# cohort floats
CF_PEOPLE = 0
CF_EXPECTED_SPENDING = 1
CF_EXPECTED_FLOOR = 2
CF_INFLATION = 3
CF_CASH_TARGET = 4
CF_OWNED = 5
CF_CLAIMS = 6
CF_FLOOR_COST = 7
CF_RATE = 8
CF_SUBSTITUTION = 9
CF_COUNT = 10
# cohort ints
CI_NEED0 = 0
CI_NEED1 = 1
CI_ROW0 = 2
CI_ROW1 = 3
CI_STORE0 = 4
CI_STORE1 = 5
CI_TILE = 6
CI_HAS_RATE = 7
CI_COUNT = 8
# need floats
NF_PIDX = 0
NF_SUB = 1
NF_WEIGHT = 2
NF_LIMIT = 3
NF_HAS_FLOOR = 4
NF_QUALITIES = 5
NF_COUNT = 6
# need ints
NI_ROW0 = 0
NI_ROW1 = 1
NI_COUNT = 2
# row floats
RF_PRICE = 0
RF_EFFECT = 1
RF_SHARE = 2
RF_CEIL = 3
RF_QUALITY = 4
RF_HELD = 5
RF_LIFE = 6
RF_SPOIL = 7
RF_GPRICE = 8
RF_LIMIT = 9          # largest share of the need's units the good can meet (NaN: none); the opening kernel does not read it
RF_COUNT = 10
# row ints
RI_GOOD = 0
RI_UNIT = 1
RI_COUNT = 2
# store floats
SF_WEIGHT = 0
SF_PRICE = 1
SF_HELD = 2
SF_GPRICE = 3
SF_LIFE = 4
SF_COUNT = 5

PURSE_PASSES = 3
PARTIALS = 64        # room for the partial sums of an exact sum (an exact sum of doubles keeps a few dozen at most)


@njit
def flexible_budget_left(usable, spending, floor_wanted, floor_scale):
    """The cash left for flexible spending once the floors are paid: the spending beyond the floors, within the usable cash.
    When the floors take all the usable cash (wanted floors, `floor_scale` below one) nothing is left, exactly: the scaled floors
    differ from the usable cash by rounding, and that residue must not become bids. No floors wanted leaves the whole spending."""
    if floor_wanted > 0.0 and floor_scale < 1.0:
        return 0.0
    scaled = floor_wanted * floor_scale
    return min(usable, max(spending, scaled)) - scaled


@njit
def _add(partials, count, term):
    """One more term into the exact sum held in `partials[:count]` (the algorithm of `math.fsum`); returns the new count."""
    x = term
    kept = 0
    for index in range(count):
        y = partials[index]
        if abs(x) < abs(y):
            x, y = y, x
        high = x + y
        low = y - (high - x)
        if low != 0.0:
            partials[kept] = low
            kept += 1
        x = high
    partials[kept] = x
    return kept + 1


@njit
def _total(partials, count):
    """The correctly rounded value of the exact sum in `partials[:count]` (`math.fsum`'s answer)."""
    if count == 0:
        return 0.0
    index = count - 1
    high = partials[index]
    low = 0.0
    while index > 0:
        x = high
        index -= 1
        y = partials[index]
        high = x + y
        low = y - (high - x)
        if low != 0.0:
            break
    if index > 0 and ((low < 0.0 and partials[index - 1] < 0.0) or (low > 0.0 and partials[index - 1] > 0.0)):
        y = low * 2.0
        x = high + y
        if y == x - high:
            high = x
    return high


@njit
def _satiate(n0, n1, people, need_floats, pidx, totals):
    """need_satiation.apply_satiation over the needs n0..n1: cap each satiable need's units at its limit and move the
    freed spending to the needs still open, by their budget weights."""
    count = n1 - n0
    capped = np.zeros(count, dtype=np.bool_)
    newly = np.zeros(count, dtype=np.bool_)
    while True:
        found = False
        for index in range(count):
            n = n0 + index
            limit = need_floats[n, NF_LIMIT]
            newly[index] = (not capped[index]) and (not np.isnan(limit)) and totals[n] > limit * people
            found = found or newly[index]
        if not found:
            return
        freed = 0.0
        for index in range(count):
            if newly[index]:
                n = n0 + index
                limit = need_floats[n, NF_LIMIT] * people
                freed += (totals[n] - limit) * pidx[n]
                totals[n] = limit
                capped[index] = True
        weight_total = 0.0         # `sum` of floats, which compensates (Neumaier) from Python 3.12
        compensation = 0.0
        for index in range(count):
            if not capped[index]:
                x = need_floats[n0 + index, NF_WEIGHT]
                t = weight_total + x
                if abs(weight_total) >= abs(x):
                    compensation += (weight_total - t) + x
                else:
                    compensation += (x - t) + weight_total
                weight_total = t
        if compensation != 0.0 and np.isfinite(compensation):
            weight_total += compensation
        if weight_total <= 0.0:
            return
        for index in range(count):
            if not capped[index]:
                n = n0 + index
                totals[n] += freed * need_floats[n, NF_WEIGHT] / weight_total / pidx[n]


@njit
def _need_units(n0, n1, people, surplus, need_floats, pidx, floors, totals, partials):
    """need_basket.need_units (with satiation) for one cohort's needs n0..n1."""
    count = 0
    for n in range(n0, n1):
        count = _add(partials, count, need_floats[n, NF_WEIGHT])
        floors[n] = need_floats[n, NF_SUB] * people
        totals[n] = floors[n]
    weight_total = _total(partials, count)
    if surplus > 0.0 and weight_total > 0.0:
        for n in range(n0, n1):
            totals[n] += surplus * need_floats[n, NF_WEIGHT] / weight_total / pidx[n]
        _satiate(n0, n1, people, need_floats, pidx, totals)


@njit
def _ceilings(r0, r1, row_floats, share, ceil):
    """need_basket.price_ceilings for the goods r0..r1 of one need."""
    for r in range(r0, r1):
        cheapest = np.inf
        for other in range(r0, r1):
            if other != r:
                cost = row_floats[other, RF_PRICE] / row_floats[other, RF_EFFECT]
                if cost < cheapest:
                    cheapest = cost
        parity = cheapest * row_floats[r, RF_EFFECT]
        ceil[r] = parity if (r1 - r0 > 1 and parity >= row_floats[r, RF_PRICE]) else np.inf


@njit
def _remix(n, r0, r1, reach, exponent, row_floats, share, ceil, pidx, partials):
    """need_basket.with_quality_reach for one need: the mix weighs a good's quality factor to the power `reach`."""
    count = 0
    for r in range(r0, r1):
        valued = row_floats[r, RF_EFFECT] * row_floats[r, RF_QUALITY] ** reach
        share[r] = (row_floats[r, RF_PRICE] / valued) ** exponent
        count = _add(partials, count, share[r])
    power = _total(partials, count)
    count = 0
    for r in range(r0, r1):
        share[r] = share[r] / power
        count = _add(partials, count, share[r] * row_floats[r, RF_EFFECT] / row_floats[r, RF_PRICE])
    pidx[n] = 1.0 / _total(partials, count)
    _ceilings(r0, r1, row_floats, share, ceil)


@njit
def _affordable(r0, r1, household_budget, has_floor, pidx_of_need, row_floats, share, aff, qty, partials):
    """households_ability.affordable_goods and quantity_per_need_unit for one need: `aff` is 1.0 on the goods one
    household can pay a unit of, `qty` the units of each per need unit; returns the price cap to bid under."""
    count = 0
    for r in range(r0, r1):
        aff[r] = 1.0 if row_floats[r, RF_PRICE] <= household_budget else 0.0
        qty[r] = 0.0
        if aff[r] > 0.0:
            count = _add(partials, count, share[r])
    total = _total(partials, count)
    cap = household_budget
    if total <= 0.0:
        if not has_floor:
            return cap
        count = 0
        for r in range(r0, r1):
            aff[r] = 1.0
            count = _add(partials, count, share[r])
        total = _total(partials, count)
        cap = np.inf
    count = 0
    for r in range(r0, r1):
        if aff[r] > 0.0:
            count = _add(partials, count, share[r] / total * row_floats[r, RF_EFFECT] / row_floats[r, RF_PRICE])
    money_per_unit = min(pidx_of_need, 1.0 / _total(partials, count))
    for r in range(r0, r1):
        if aff[r] > 0.0:
            qty[r] = money_per_unit * share[r] / total / row_floats[r, RF_PRICE]
    return cap


@njit
def _resting_purse(mean_income, share_wealth, claims, extra, constants):
    """opening_resting.resting_household_purse."""
    extra = max(0.0, extra)
    if share_wealth <= 0.0 and extra <= 0.0:
        return 0.0
    share_term = 0.0
    if share_wealth > 0.0:
        share_term = constants[K_CASH_SHARE] * (share_wealth - constants[K_WEALTH_TARGET] * mean_income)
    cash = max(mean_income + extra, (extra - share_term) / constants[K_CASH_SHARE] - claims)
    return cash - mean_income




# scratch columns: per need-good row
W_SHARE = 0
W_CEIL = 1
W_AFF = 2
W_QTY = 3
W_FLOOR = 4
W_FLEX = 5
W_CAP = 6
W_BUDGET = 7
W_ON = 8
W_COUNT = 9
# per need
V_PIDX = 0
V_FLOORS = 1
V_TOTALS = 2
V_SFLOORS = 3
V_STOTALS = 4
V_COUNT = 5
# per good
G_FLOW = 0
G_SMOOTH = 1
G_COUNT = 2
# per store good
T_BUDGET = 0
T_FLEX = 1
T_COUNT = 2


@njit
def _smoothed_flows(c, spending, floor_cost, constants, cohort_floats, cohort_ints, need_floats, need_ints, row_floats, row_ints, row_scratch, need_scratch, good_scratch, partials):
    """households_orders._smoothed_flow_by_good: the yearly flow of each good that the smoothed surplus buys (and the cohort
    could afford), into good_scratch[:, G_SMOOTH]."""
    n0 = cohort_ints[c, CI_NEED0]
    n1 = cohort_ints[c, CI_NEED1]
    people = cohort_floats[c, CF_PEOPLE]
    floors = need_scratch[:, V_SFLOORS]
    totals = need_scratch[:, V_STOTALS]
    _need_units(n0, n1, people, spending - floor_cost, need_floats, need_scratch[:, V_PIDX], floors, totals, partials)
    for n in range(n0, n1):
        r0 = need_ints[n, NI_ROW0]
        r1 = need_ints[n, NI_ROW1]
        household_budget = totals[n] * need_scratch[n, V_PIDX] * constants[K_HOUSEHOLD_SIZE] / people
        _affordable(r0, r1, household_budget, need_floats[n, NF_HAS_FLOOR] > 0.0, need_scratch[n, V_PIDX], row_floats, row_scratch[:, W_SHARE],
                    row_scratch[:, W_AFF], row_scratch[:, W_QTY], partials)
        for r in range(r0, r1):
            if row_scratch[r, W_AFF] > 0.0:
                good_scratch[row_ints[r, RI_GOOD], G_SMOOTH] += (floors[n] + max(0.0, totals[n] - floors[n])) * row_scratch[r, W_QTY]


@njit
def _store_value_target(savings, inflation, real_rate, constants):
    """households_store.store_value_target."""
    inflation_pull = 1.0 + max(0.0, inflation) / constants[K_TIME_PREFERENCE]
    lending_pull = 1.0 + max(0.0, real_rate - constants[K_TIME_PREFERENCE]) / constants[K_TIME_PREFERENCE]
    share = min(constants[K_STORE_LIMIT], constants[K_STORE_SHARE] * inflation_pull / lending_pull)
    return share * max(0.0, savings)


@njit
def _orders(c, cash, income, last_income, stationary, constants, cohort_floats, cohort_ints, need_floats, need_ints, row_floats, row_ints, store_floats, store_ints, row_scratch, need_scratch, good_scratch, order, store_scratch, partials):
    """households_orders.goods_orders for cohort c holding `cash`, as arrays: per need-good row the floor and flexible
    quantity, the price cap and the budget (W_ON says a bid is made), and per store good the budget and flexible quantity."""
    n0 = cohort_ints[c, CI_NEED0]
    n1 = cohort_ints[c, CI_NEED1]
    r0 = cohort_ints[c, CI_ROW0]
    r1 = cohort_ints[c, CI_ROW1]
    s0 = cohort_ints[c, CI_STORE0]
    s1 = cohort_ints[c, CI_STORE1]
    people = cohort_floats[c, CF_PEOPLE]
    for r in range(r0, r1):
        row_scratch[r, W_ON] = 0.0
        row_scratch[r, W_BUDGET] = 0.0
    for s in range(s0, s1):
        store_scratch[s, T_BUDGET] = 0.0
        store_scratch[s, T_FLEX] = 0.0
    cash = max(0.0, cash)
    if n1 == n0 or people <= 0.0:
        return
    floor_cost = cohort_floats[c, CF_FLOOR_COST]
    claims = cohort_floats[c, CF_CLAIMS]
    owned = cohort_floats[c, CF_OWNED]
    expected = cohort_floats[c, CF_EXPECTED_SPENDING]
    inflation = cohort_floats[c, CF_INFLATION]
    count = 0
    for s in range(s0, s1):
        count = _add(partials[0], count, store_floats[s, SF_HELD] * store_floats[s, SF_PRICE])
    store_value = _total(partials[0], count)
    mean_income = income if last_income <= 0.0 else 0.5 * (income + last_income)
    budget = mean_income + constants[K_CASH_SHARE] * (cash + claims)
    if owned > 0.0:
        budget += constants[K_CASH_SHARE] * (owned - constants[K_WEALTH_TARGET] * mean_income)
    budget = max(0.0, min(cash, budget))
    target = cohort_floats[c, CF_CASH_TARGET]
    if target == 0.0:
        target = _resting_purse(mean_income, owned, claims, 0.0, constants)
    drawdown = min(budget - income, constants[K_DRAWDOWN] * max(0.0, max(income, last_income)))
    spending = max(0.0, min(cash, income + drawdown))
    if expected > 0.0:
        spending = min(spending, max(income, (1.0 + constants[K_CUT]) * expected))
        spending = max(spending, min(cash, (1.0 - constants[K_CUT]) * expected))
    reach = 0.0
    if spending > 0.0:
        reach = max(0.0, min(1.0, (spending - floor_cost) / spending))
    share = row_scratch[:, W_SHARE]
    ceil = row_scratch[:, W_CEIL]
    pidx = need_scratch[:, V_PIDX]
    floors = need_scratch[:, V_FLOORS]
    totals = need_scratch[:, V_TOTALS]
    for n in range(n0, n1):
        pidx[n] = need_floats[n, NF_PIDX]
    for r in range(r0, r1):
        share[r] = row_floats[r, RF_SHARE]
        ceil[r] = row_floats[r, RF_CEIL]
        good_scratch[row_ints[r, RI_GOOD], G_FLOW] = 0.0
        good_scratch[row_ints[r, RI_GOOD], G_SMOOTH] = 0.0
    for s in range(s0, s1):
        good_scratch[store_ints[s], G_FLOW] = 0.0
        good_scratch[store_ints[s], G_SMOOTH] = 0.0
    if reach > 0.0:
        exponent = 1.0 - cohort_floats[c, CF_SUBSTITUTION]
        for n in range(n0, n1):
            if need_floats[n, NF_QUALITIES] > 0.0:
                _remix(n, need_ints[n, NI_ROW0], need_ints[n, NI_ROW1], reach, exponent, row_floats, share, ceil, pidx, partials[0])
    _need_units(n0, n1, people, spending - floor_cost, need_floats, pidx, floors, totals, partials[0])
    scale = 1.0
    if expected > 0.0 and spending > 0.0:
        scale = expected / spending
    if expected > 0.0 and cohort_floats[c, CF_EXPECTED_FLOOR] > 0.0:
        _smoothed_flows(c, expected, cohort_floats[c, CF_EXPECTED_FLOOR], constants, cohort_floats, cohort_ints, need_floats, need_ints, row_floats, row_ints, row_scratch, need_scratch, good_scratch, partials[0])
    for n in range(n0, n1):
        rn0 = need_ints[n, NI_ROW0]
        rn1 = need_ints[n, NI_ROW1]
        household_budget = totals[n] * pidx[n] * constants[K_HOUSEHOLD_SIZE] / people
        household_cap = _affordable(rn0, rn1, household_budget, need_floats[n, NF_HAS_FLOOR] > 0.0, pidx[n], row_floats, share,
                                    row_scratch[:, W_AFF], row_scratch[:, W_QTY], partials[0])
        for r in range(rn0, rn1):
            if row_scratch[r, W_AFF] <= 0.0:
                continue
            per_unit = row_scratch[r, W_QTY]
            floor_quantity = floors[n] * per_unit
            flexible_quantity = max(0.0, totals[n] - floors[n]) * per_unit
            flow = floor_quantity + flexible_quantity
            good = row_ints[r, RI_GOOD]
            good_scratch[good, G_FLOW] += flow
            stock_flow = max(flow * scale, good_scratch[good, G_SMOOTH])
            life = row_floats[r, RF_LIFE]
            ratio = 1.0
            if life > 0.0:
                if flow <= 0.0:
                    ratio = 0.0
                else:
                    ratio = max(0.0, flow * (stock_flow / flow) * life - row_floats[r, RF_HELD]) / flow
                    if stationary:
                        serving = stock_flow * life
                        wear = min(1.0, 1.0 / life)
                        spoilage = min(1.0, max(0.0, row_floats[r, RF_SPOIL]))
                        ratio = (serving - max(0.0, serving * (1.0 - wear - spoilage))) / flow
            if ratio > 0.0 and floor_quantity + flexible_quantity > 0.0:
                row_scratch[r, W_FLOOR] = floor_quantity * ratio
                row_scratch[r, W_FLEX] = flexible_quantity * ratio
                row_scratch[r, W_CAP] = min(ceil[r], household_cap)
                row_scratch[r, W_ON] = 1.0
    count = 0
    other = 0
    for r in range(r0, r1):
        if row_scratch[r, W_ON] > 0.0:
            count = _add(partials[0], count, row_floats[r, RF_PRICE] * row_scratch[r, W_FLOOR])
            other = _add(partials[1], other, row_floats[r, RF_PRICE] * row_scratch[r, W_FLEX])
    floor_spend = _total(partials[0], count)
    flexible_spend = _total(partials[1], other)
    floor_wanted = floor_spend * (1.0 + constants[K_FLOOR_MARGIN])
    usable = cash * (1.0 - constants[K_SAFETY])
    floor_scale = min(1.0, usable / floor_wanted) if floor_wanted > 0.0 else 0.0
    left = flexible_budget_left(usable, spending, floor_wanted, floor_scale)
    flexible_scale = min(1.0, left / flexible_spend) if flexible_spend > 0.0 else 0.0
    budget_total = 0.0
    for index in range(r0, r1):
        r = order[index]
        if row_scratch[r, W_ON] <= 0.0:
            continue
        price = row_floats[r, RF_PRICE]
        bid_budget = (row_scratch[r, W_FLOOR] * price * (1.0 + constants[K_FLOOR_MARGIN]) * floor_scale
                      + row_scratch[r, W_FLEX] * price * flexible_scale)
        if bid_budget <= 0.0:
            row_scratch[r, W_ON] = 0.0
            continue
        row_scratch[r, W_BUDGET] = bid_budget
        budget_total += bid_budget
    savings = cash - budget_total - target
    if s1 > s0 and cohort_ints[c, CI_HAS_RATE] > 0:
        pot = min(savings, usable - budget_total)
        if pot > 0.0:
            real_rate = cohort_floats[c, CF_RATE] - inflation
            above_buffer = cash + claims + store_value - target
            count = 0
            for s in range(s0, s1):
                stock_flow = max(good_scratch[store_ints[s], G_FLOW] * scale, good_scratch[store_ints[s], G_SMOOTH])
                in_use = 0.0
                if store_floats[s, SF_LIFE] > 0.0 and stock_flow > 0.0:
                    in_use = stock_flow * store_floats[s, SF_LIFE] * (1.0 + constants[K_BAND])
                count = _add(partials[0], count, max(0.0, store_floats[s, SF_HELD] - in_use) * store_floats[s, SF_PRICE])
            held_value = _total(partials[0], count)
            wanted = _store_value_target(above_buffer, inflation, real_rate, constants)
            if held_value < wanted * (1.0 - constants[K_BAND]):
                spend = min(pot, wanted - held_value)
                for s in range(s0, s1):
                    store_budget = spend * store_floats[s, SF_WEIGHT]
                    if store_budget > 0.0:
                        store_scratch[s, T_BUDGET] = store_budget
                        store_scratch[s, T_FLEX] = store_budget / store_floats[s, SF_PRICE]


@njit
def demand(incomes, stationary, constants, cohort_floats, cohort_ints, need_floats, need_ints, row_floats, row_ints, store_floats, store_ints, row_scratch, need_scratch, good_scratch, order, store_scratch, unit_floor, unit_grown,
           memo, final, stamp, extra, freed_out, partials):
    """The opening's final demand at `incomes` (one per cohort): what each cohort buys after its plot, summed by tile and
    good into `final`, with the order each (tile, good) first appeared in `stamp`. `memo[c]` is (has, income, purse): the
    purse the cohort's orders were last made with, from which the purse search starts again at the same income. `extra[c]`
    is the spending beyond income its plot allows and `freed_out[c]` the budget the plot freed."""
    counter = 0
    for c in range(cohort_ints.shape[0]):
        income = incomes[c]
        r0 = cohort_ints[c, CI_ROW0]
        r1 = cohort_ints[c, CI_ROW1]
        s0 = cohort_ints[c, CI_STORE0]
        s1 = cohort_ints[c, CI_STORE1]
        purse = 0.0
        if memo[c, 0] > 0.0 and memo[c, 1] == income:
            purse = memo[c, 2]
        freed = 0.0
        extra_spending = 0.0
        for _pass in range(PURSE_PASSES):
            if not (memo[c, 0] > 0.0 and memo[c, 1] == income and memo[c, 2] == purse):
                memo[c, 0] = 1.0
                memo[c, 1] = income
                memo[c, 2] = purse
            _orders(c, income + purse, income, income, stationary, constants, cohort_floats, cohort_ints, need_floats, need_ints, row_floats, row_ints, store_floats, store_ints, row_scratch, need_scratch, good_scratch, order, store_scratch, partials)
            before = 0
            after = 0
            for r in range(r0, r1):
                if row_scratch[r, W_ON] <= 0.0:
                    continue
                before = _add(partials[2], before, row_scratch[r, W_BUDGET])
                unit = row_ints[r, RI_UNIT]
                met = 0.0
                if unit >= 0:
                    if unit_floor[unit] > 0.0:
                        met = min(1.0, unit_grown[unit] / unit_floor[unit])
                if met > 0.0 and row_scratch[r, W_FLOOR] > 0.0:
                    cut = row_scratch[r, W_FLOOR] * met
                    kept = 1.0 - cut / (row_scratch[r, W_FLOOR] + row_scratch[r, W_FLEX])
                    new_budget = row_scratch[r, W_BUDGET] * max(0.0, kept)
                    row_scratch[r, W_FLOOR] = row_scratch[r, W_FLOOR] - cut
                    row_scratch[r, W_BUDGET] = new_budget
                after = _add(partials[3], after, row_scratch[r, W_BUDGET])
            for s in range(s0, s1):      # the store's bids are in both sums, as in the old path
                before = _add(partials[2], before, store_scratch[s, T_BUDGET])
                after = _add(partials[3], after, store_scratch[s, T_BUDGET])
            freed = _total(partials[2], before) - _total(partials[3], after)
            extra_spending = min(freed, constants[K_DRAWDOWN] * income)
            wanted = _resting_purse(income, 0.0, 0.0, extra_spending, constants)
            if abs(wanted - purse) <= constants[K_PURSE_TOLERANCE] * max(income, 1e-9):
                break
            purse = wanted
        extra[c] = extra_spending
        freed_out[c] = freed
        tile = cohort_ints[c, CI_TILE]
        elasticity = cohort_floats[c, CF_SUBSTITUTION]
        for index in range(r0, r1):
            r = order[index]
            if row_scratch[r, W_ON] <= 0.0 or row_floats[r, RF_GPRICE] <= 0.0:
                continue
            price = row_floats[r, RF_GPRICE]
            quantity = 0.0
            if not (row_scratch[r, W_BUDGET] <= 0.0 or price > row_scratch[r, W_CAP]):
                wanted_quantity = row_scratch[r, W_FLOOR]
                if row_scratch[r, W_FLEX] > 0.0 and row_floats[r, RF_PRICE] > 0.0:
                    wanted_quantity += row_scratch[r, W_FLEX] * (price / row_floats[r, RF_PRICE]) ** -elasticity
                quantity = min(wanted_quantity, row_scratch[r, W_BUDGET] / price)
            good = row_ints[r, RI_GOOD]
            final[tile, good] += quantity
            if stamp[tile, good] < 0:
                stamp[tile, good] = counter
                counter += 1
        for s in range(s0, s1):
            if store_scratch[s, T_BUDGET] <= 0.0 or store_floats[s, SF_GPRICE] <= 0.0:
                continue
            price = store_floats[s, SF_GPRICE]
            wanted_quantity = 0.0
            if store_scratch[s, T_FLEX] > 0.0 and store_floats[s, SF_PRICE] > 0.0:
                wanted_quantity += store_scratch[s, T_FLEX] * (price / store_floats[s, SF_PRICE]) ** -elasticity
            quantity = min(wanted_quantity, store_scratch[s, T_BUDGET] / price)
            good = store_ints[s]
            final[tile, good] += quantity
            if stamp[tile, good] < 0:
                stamp[tile, good] = counter
                counter += 1


@njit
def uncut(incomes, stationary, constants, cohort_floats, cohort_ints, need_floats, need_ints, row_floats, row_ints, store_floats,
          store_ints, row_scratch, need_scratch, good_scratch, order, store_scratch, row_quantity, partials):
    """The quantity (floor plus flexible) of each need-good bid every cohort makes holding exactly its income, before any
    plot cut, into `row_quantity` (zero where no bid is made)."""
    for c in range(cohort_ints.shape[0]):
        _orders(c, incomes[c], incomes[c], incomes[c], stationary, constants, cohort_floats, cohort_ints, need_floats,
                need_ints, row_floats, row_ints, store_floats, store_ints, row_scratch, need_scratch, good_scratch, order,
                store_scratch, partials)
        for r in range(cohort_ints[c, CI_ROW0], cohort_ints[c, CI_ROW1]):
            row_quantity[r] = 0.0
            if row_scratch[r, W_ON] > 0.0:
                row_quantity[r] = row_scratch[r, W_FLOOR] + row_scratch[r, W_FLEX]
