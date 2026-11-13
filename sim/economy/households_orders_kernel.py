"""The year's goods orders of every cohort at once, over arrays (`households_orders_pack.py` packs and unpacks).

The rules are `households_orders.goods_orders` (the cohort's budget, its needs' units, the goods' affordability, the
durables' replacement, the surplus scaled to the spending, the store's bids and the store value outside the durables kept in
use; the floors the own plot grew are met first: not bought, not charged to the spending), written once over the packed cohorts.
The needs, goods and store goods of a basket are packed once per basket (a template); a cohort names its template and
carries its own holdings, plot units and cash. The helpers are the opening kernel's (`opening_demand_kernel`), which makes the
same orders at the opening's incomes; this one adds the held durables in use, the year's incomes and cash, the smoothing flag and the
savings left after the store. A sum the old code made with `math.fsum` is made exactly here (`_add`, `_total`)."""
import numpy as np

from sim.jit import njit

from .opening_demand_kernel import (K_BAND, K_CASH_SHARE, K_CUT, K_DRAWDOWN, K_FLOOR_MARGIN, K_HOUSEHOLD_SIZE, K_SAFETY,
                                    K_WEALTH_TARGET, NF_HAS_FLOOR, NF_LIMIT, NF_PIDX, NF_QUALITIES, NF_SUB, NI_ROW0, NI_ROW1, RF_CEIL, RF_LIFE, RF_PRICE,
                                    RF_SHARE, RI_GOOD, RI_UNIT, SF_LIFE, SF_PRICE, SF_WEIGHT, V_FLOORS, V_PIDX, V_SFLOORS, V_STOTALS, V_TOTALS, W_AFF,
                                    W_BUDGET, W_CAP, W_CEIL, W_COUNT, W_FLEX, W_FLOOR, W_ON, W_QTY, W_SHARE, _add, _affordable, _need_units,
                                    _resting_purse, _store_value_target, _total)
from .opening_demand_kernel import RF_EFFECT, RF_LIMIT, RF_QUALITY, _remix as _remix_unlimited
from .satiated_demand import is_satiated
from .store_spend import store_spend
from .priced_need_kernel import limit_shares, price_ceilings, units_per_money

# template ints (one row per basket)
TM_NEED0 = 0
TM_NEED1 = 1
TM_ROW0 = 2
TM_ROW1 = 3
TM_STORE0 = 4
TM_STORE1 = 5
TM_UNIT0 = 6
TM_HAS_RATE = 7
TM_COUNT = 8
# template floats
TF_RATE = 0
TF_SUBSTITUTION = 1
TF_COUNT = 2
# cohort floats
CO_PEOPLE = 0
CO_EXPECTED_SPENDING = 1
CO_EXPECTED_FLOOR = 2
CO_INFLATION = 3
CO_CASH_TARGET = 4
CO_OWNED = 5
CO_CLAIMS = 6
CO_CASH = 7
CO_INCOME = 8
CO_LAST_INCOME = 9
CO_COUNT = 10
# cohort ints
CT_TEMPLATE = 0
CT_ROW_OUT = 1        # first row of this cohort in the holdings and row answers
CT_STORE_OUT = 2      # first row of this cohort in the store holdings and store answers
CT_GROWN0 = 3         # first of this cohort's plot units
CT_COUNT = 4
# row answers
RO_ON = 0
RO_FLOOR = 1
RO_FLEX = 2
RO_BUDGET = 3
RO_CAP = 4
RO_SATIATED = 5        # 1.0 when the row's need sits at its satiation limit: its bid does not respond to a fall in price
RO_COUNT = 6
# store answers
SO_BUDGET = 0
SO_FLEX = 1
SO_HELD = 2           # what is held beyond the durables kept in use
SO_COUNT = 3
# cohort answers
CA_SAVINGS = 0
CA_ABOVE_BUFFER = 1
CA_REAL_RATE = 2
CA_PLAN = 3           # 1.0 when the cohort has a store plan (store goods and a rate)
CA_FLOOR_COST = 4
CA_COUNT = 5
# row scratch of the share-limit search, after the opening kernel's columns
X_PRICED = W_COUNT          # 1.0 on every packed row (a packed row is a priced good)
X_UNITS = W_COUNT + 1       # need units each good meets at the mix
X_FIXED = W_COUNT + 2       # the units a good is fixed at once limited
X_FLAGGED = W_COUNT + 3     # 1.0 once a good is fixed
X_COUNT = W_COUNT + 4
# per good
G_FLOW = 0
G_SMOOTH = 1
G_COUNT = 2


@njit
def _remix(n, r0, r1, reach, exponent, row_floats, row_scratch, pidx, partials):
    """need_basket.with_quality_reach for one need: the opening kernel's re-mix, then the share limits' search
    (need_basket.limited_shares) when a good of the need has a limit; the mix is left in `row_scratch[:, W_SHARE]` and
    `[:, W_CEIL]` and the need's price index in `pidx`."""
    share = row_scratch[:, W_SHARE]
    limited = False
    for r in range(r0, r1):
        if row_floats[r, RF_LIMIT] == row_floats[r, RF_LIMIT]:
            limited = True
    if not limited:
        _remix_unlimited(n, r0, r1, reach, exponent, row_floats, share, row_scratch[:, W_CEIL], pidx, partials[0])
        return
    count = 0
    for r in range(r0, r1):
        row_scratch[r, X_PRICED] = 1.0
        valued = row_floats[r, RF_EFFECT] * row_floats[r, RF_QUALITY] ** reach
        share[r] = (row_floats[r, RF_PRICE] / valued) ** exponent
        count = _add(partials[0], count, share[r])
    power = _total(partials[0], count)
    for r in range(r0, r1):
        share[r] = share[r] / power
    prices, effects, priced = row_floats[:, RF_PRICE], row_floats[:, RF_EFFECT], row_scratch[:, X_PRICED]
    per_money = units_per_money(r0, r1, prices, effects, priced, share, partials[0])
    limit_shares(r0, r1, prices, effects, row_floats[:, RF_LIMIT], priced, share, per_money, row_scratch[:, X_UNITS], row_scratch[:, X_FIXED],
                 row_scratch[:, X_FLAGGED], partials[0], partials[1])
    pidx[n] = 1.0 / units_per_money(r0, r1, prices, effects, priced, share, partials[0])
    price_ceilings(r0, r1, prices, effects, priced, row_scratch[:, W_CEIL])


@njit
def _smoothed(n0, n1, people, spending, floor_cost, constants, need_floats, need_ints, row_floats, row_ints, row_scratch, need_scratch, good_scratch, partials):
    """households_orders._smoothed_flow_by_good for one cohort: into good_scratch[:, G_SMOOTH] the yearly flow of each good
    the surplus of `spending` over `floor_cost` buys (the goods the cohort could afford on it)."""
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
def _reset_mix(n0, n1, r0, r1, need_floats, row_floats, row_ints, row_scratch, need_scratch, good_scratch):
    """The needs' mix as packed (before any quality re-mix), and no flow counted for any good of the cohort."""
    for n in range(n0, n1):
        need_scratch[n, V_PIDX] = need_floats[n, NF_PIDX]
    for r in range(r0, r1):
        row_scratch[r, W_SHARE] = row_floats[r, RF_SHARE]
        row_scratch[r, W_CEIL] = row_floats[r, RF_CEIL]
        good_scratch[row_ints[r, RI_GOOD], G_FLOW] = 0.0
        good_scratch[row_ints[r, RI_GOOD], G_SMOOTH] = 0.0


@njit
def _met(unit, unit0, grown0, people, unit_floor_per_person, grown):
    """The share of a floor unit the cohort's own plot grew (none for a row with no unit)."""
    if unit < 0:
        return 0.0
    unit_floor = unit_floor_per_person[unit0 + unit] * people
    if unit_floor <= 0.0:
        return 0.0
    return min(1.0, grown[grown0 + unit] / unit_floor)


@njit
def _cohort(c, smooth_rise, constants, cohort_floats, cohort_ints, template_ints, template_floats, need_floats, need_ints, row_floats, row_ints,
            store_floats, store_ints, unit_floor_per_person, order, held_rows, held_stores, grown, row_scratch, need_scratch, good_scratch, partials,
            row_out, store_out, cohort_out):
    template = cohort_ints[c, CT_TEMPLATE]
    n0 = template_ints[template, TM_NEED0]
    n1 = template_ints[template, TM_NEED1]
    r0 = template_ints[template, TM_ROW0]
    r1 = template_ints[template, TM_ROW1]
    s0 = template_ints[template, TM_STORE0]
    s1 = template_ints[template, TM_STORE1]
    unit0 = template_ints[template, TM_UNIT0]
    row_base = cohort_ints[c, CT_ROW_OUT] - r0
    store_base = cohort_ints[c, CT_STORE_OUT] - s0
    grown0 = cohort_ints[c, CT_GROWN0]
    people = cohort_floats[c, CO_PEOPLE]
    for r in range(r0, r1):
        row_scratch[r, W_ON] = 0.0
        row_scratch[r, W_BUDGET] = 0.0
        for column in range(RO_COUNT):
            row_out[row_base + r, column] = 0.0
    for s in range(s0, s1):
        store_out[store_base + s, SO_BUDGET] = 0.0
        store_out[store_base + s, SO_FLEX] = 0.0
        store_out[store_base + s, SO_HELD] = held_stores[store_base + s]
    for column in range(5):
        cohort_out[c, column] = 0.0
    cash = max(0.0, cohort_floats[c, CO_CASH])
    if n1 == n0 or people <= 0.0:
        return
    income = cohort_floats[c, CO_INCOME]
    last_income = cohort_floats[c, CO_LAST_INCOME]
    claims = cohort_floats[c, CO_CLAIMS]
    owned = cohort_floats[c, CO_OWNED]
    expected = cohort_floats[c, CO_EXPECTED_SPENDING]
    inflation = cohort_floats[c, CO_INFLATION]
    exponent = 1.0 - template_floats[template, TF_SUBSTITUTION]
    count = 0
    for n in range(n0, n1):
        met = 0.0
        if need_ints[n, NI_ROW1] > need_ints[n, NI_ROW0]:
            met = _met(row_ints[need_ints[n, NI_ROW0], RI_UNIT], unit0, grown0, people, unit_floor_per_person, grown)
        count = _add(partials[0], count, need_floats[n, NF_PIDX] * need_floats[n, NF_SUB] * people * (1.0 - met))
    floor_cost = _total(partials[0], count)
    cohort_out[c, CA_FLOOR_COST] = floor_cost
    mean_income = income if last_income <= 0.0 else 0.5 * (income + last_income)

    # what it holds of the store goods that is wealth to spend from: a durable kept in use serves a need and is not
    count = 0
    durable_in_use = False
    for s in range(s0, s1):
        held = held_stores[store_base + s]
        if held > 0.0 and store_floats[s, SF_LIFE] > 0.0:
            durable_in_use = True
        else:
            count = _add(partials[0], count, held * store_floats[s, SF_PRICE])
    store_value = _total(partials[0], count)
    if durable_in_use:
        provisional = mean_income + constants[K_CASH_SHARE] * cash
        if owned > 0.0:
            provisional += constants[K_CASH_SHARE] * (owned - constants[K_WEALTH_TARGET] * mean_income)
        provisional = max(0.0, min(cash, provisional))
        _reset_mix(n0, n1, r0, r1, need_floats, row_floats, row_ints, row_scratch, need_scratch, good_scratch)
        for s in range(s0, s1):
            good_scratch[store_ints[s], G_FLOW] = 0.0
            good_scratch[store_ints[s], G_SMOOTH] = 0.0
        if provisional > 0.0 and floor_cost > 0.0:
            reach = max(0.0, min(1.0, (provisional - floor_cost) / provisional))
            if reach > 0.0:
                for n in range(n0, n1):
                    if need_floats[n, NF_QUALITIES] > 0.0:
                        _remix(n, need_ints[n, NI_ROW0], need_ints[n, NI_ROW1], reach, exponent, row_floats, row_scratch, need_scratch[:, V_PIDX], partials)
            _smoothed(n0, n1, people, provisional, floor_cost, constants, need_floats, need_ints, row_floats, row_ints, row_scratch, need_scratch,
                      good_scratch, partials[0])
        count = 0
        for s in range(s0, s1):
            held = held_stores[store_base + s]
            if held > 0.0 and store_floats[s, SF_LIFE] > 0.0:
                flow = good_scratch[store_ints[s], G_SMOOTH]
                in_use = 0.0
                if flow > 0.0:
                    in_use = flow * store_floats[s, SF_LIFE] * (1.0 + constants[K_BAND])
                count = _add(partials[1], count, max(0.0, held - in_use) * store_floats[s, SF_PRICE])
        store_value = store_value + _total(partials[1], count)

    budget = mean_income + constants[K_CASH_SHARE] * (cash + claims)
    if owned > 0.0:
        budget += constants[K_CASH_SHARE] * (owned - constants[K_WEALTH_TARGET] * mean_income)
    budget = max(0.0, min(cash, budget))
    target = cohort_floats[c, CO_CASH_TARGET]
    if target == 0.0:
        target = _resting_purse(mean_income, owned, claims, 0.0, constants)
    drawdown = min(budget - income, constants[K_DRAWDOWN] * max(0.0, max(income, last_income)))
    spending = max(0.0, min(cash, income + drawdown))
    if expected > 0.0:
        if smooth_rise:
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
    _reset_mix(n0, n1, r0, r1, need_floats, row_floats, row_ints, row_scratch, need_scratch, good_scratch)
    for s in range(s0, s1):
        good_scratch[store_ints[s], G_FLOW] = 0.0
        good_scratch[store_ints[s], G_SMOOTH] = 0.0
    if reach > 0.0:
        for n in range(n0, n1):
            if need_floats[n, NF_QUALITIES] > 0.0:
                _remix(n, need_ints[n, NI_ROW0], need_ints[n, NI_ROW1], reach, exponent, row_floats, row_scratch, pidx, partials)
    _need_units(n0, n1, people, spending - floor_cost, need_floats, pidx, floors, totals, partials[0])
    scale = 1.0
    if expected > 0.0 and spending > 0.0:
        scale = expected / spending
    if expected > 0.0 and cohort_floats[c, CO_EXPECTED_FLOOR] > 0.0:
        _smoothed(n0, n1, people, expected, cohort_floats[c, CO_EXPECTED_FLOOR], constants, need_floats, need_ints, row_floats, row_ints, row_scratch,
                  need_scratch, good_scratch, partials[0])
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
            if is_satiated(totals[n], need_floats[n, NF_LIMIT], people):
                row_out[row_base + r, RO_SATIATED] = 1.0
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
                    ratio = max(0.0, flow * (stock_flow / flow) * life - held_rows[row_base + r]) / flow
            if ratio > 0.0 and floor_quantity + flexible_quantity > 0.0:
                met = _met(row_ints[r, RI_UNIT], unit0, grown0, people, unit_floor_per_person, grown)
                row_scratch[r, W_FLOOR] = floor_quantity * (1.0 - met) * ratio
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
    left = min(usable, max(spending, floor_wanted * floor_scale)) - floor_wanted * floor_scale
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
    if s1 > s0 and template_ints[template, TM_HAS_RATE] > 0:
        cohort_out[c, CA_PLAN] = 1.0
        pot = min(savings, usable - budget_total)
        real_rate = template_floats[template, TF_RATE] - inflation
        above_buffer = cash + claims + store_value - target
        count = 0
        for s in range(s0, s1):
            held = held_stores[store_base + s]
            stock_flow = max(good_scratch[store_ints[s], G_FLOW] * scale, good_scratch[store_ints[s], G_SMOOTH])
            in_use = 0.0
            if store_floats[s, SF_LIFE] > 0.0 and stock_flow > 0.0:
                in_use = stock_flow * store_floats[s, SF_LIFE] * (1.0 + constants[K_BAND])
            held = max(0.0, held - in_use)
            store_out[store_base + s, SO_HELD] = held
            count = _add(partials[0], count, held * store_floats[s, SF_PRICE])
        held_value = _total(partials[0], count)
        cohort_out[c, CA_ABOVE_BUFFER] = above_buffer
        cohort_out[c, CA_REAL_RATE] = real_rate
        wanted = _store_value_target(above_buffer, inflation, real_rate, constants)
        count = 0
        for s in range(s0, s1):
            if store_floats[s, SF_LIFE] > 0.0:
                count = _add(partials[0], count, store_floats[s, SF_WEIGHT] * min(1.0, 1.0 / store_floats[s, SF_LIFE]))
        spend = 0.0
        if pot > 0.0:
            spend = store_spend(wanted, held_value, _total(partials[0], count), pot, constants[K_BAND])
        if spend > 0.0:
            count = 0
            for s in range(s0, s1):
                store_budget = spend * store_floats[s, SF_WEIGHT]
                if store_budget > 0.0:
                    store_out[store_base + s, SO_BUDGET] = store_budget
                    store_out[store_base + s, SO_FLEX] = store_budget / store_floats[s, SF_PRICE]
                    count = _add(partials[0], count, store_budget)
            savings -= _total(partials[0], count)
    cohort_out[c, CA_SAVINGS] = savings
    for r in range(r0, r1):
        if row_scratch[r, W_ON] <= 0.0:
            continue
        row_out[row_base + r, RO_ON] = 1.0
        row_out[row_base + r, RO_FLOOR] = row_scratch[r, W_FLOOR]
        row_out[row_base + r, RO_FLEX] = row_scratch[r, W_FLEX]
        row_out[row_base + r, RO_BUDGET] = row_scratch[r, W_BUDGET]
        row_out[row_base + r, RO_CAP] = row_scratch[r, W_CAP]


@njit
def year_orders(smooth_rise, constants, cohort_floats, cohort_ints, template_ints, template_floats, need_floats, need_ints, row_floats, row_ints,
                store_floats, store_ints, unit_floor_per_person, order, held_rows, held_stores, grown, good_count, row_out, store_out, cohort_out):
    """Every cohort's goods orders for the year as arrays: `row_out` (a bid on each need-good row: on, floor, flexible quantity,
    budget after the plot's cut, price cap), `store_out` (each store good's bid budget and flexible quantity, and what is held
    beyond the durables in use), `cohort_out` (the savings left to lend, the wealth the store is judged on, the real rate)."""
    row_scratch = np.zeros((row_floats.shape[0], X_COUNT))
    need_scratch = np.zeros((need_floats.shape[0], 5))
    good_scratch = np.zeros((good_count, G_COUNT))
    partials = np.zeros((4, 64))
    for c in range(cohort_ints.shape[0]):
        _cohort(c, smooth_rise, constants, cohort_floats, cohort_ints, template_ints, template_floats, need_floats, need_ints, row_floats, row_ints,
                store_floats, store_ints, unit_floor_per_person, order, held_rows, held_stores, grown, row_scratch, need_scratch, good_scratch, partials,
                row_out, store_out, cohort_out)
