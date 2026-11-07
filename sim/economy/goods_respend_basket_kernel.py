"""The households' respend bids as numba kernels: a need priced at the cheapest asks still offered (need_basket.priced_need
and price_ceilings) and the bids one rationed buyer places with the money it was rationed of (goods_respend.respend_bids).
Baskets are flattened to arrays (goods_respend_pack.py): needs of a basket in order, the goods of a need in order.
Every function takes and returns numpy arrays and numbers only.
"""
import numpy

from sim.jit import njit

from .goods_market_kernels import KERNEL

SHARE_LIMIT_TOLERANCE = 1e-12     # need_basket.limited_shares


@njit(**KERNEL)
def need_shares(first, last, has_limits, goods, effects, limits, limited, exponent, ask_of_good, shares, ceilings, priced,
                units, fixed_value, fixed_flag):
    """The spending shares and price ceilings of the goods of one need, rows `first` to `last` of the goods tables, priced at
    `ask_of_good` (NaN for a good not offered). A good is priced when its ask and effectiveness are positive; the shares of
    the priced rows follow the basket's constant-elasticity mix (`exponent` is one minus the substitution), limited by each
    good's largest share of the need's units when the need has limits. Fills `shares`, `ceilings` and `priced` at those rows
    (the other arrays are scratch of the same length) and returns how many goods are priced."""
    count = 0
    power = 0.0
    for row in range(first, last):
        price = ask_of_good[goods[row]]
        ok = price > 0.0 and effects[row] > 0.0
        priced[row] = ok
        shares[row] = 0.0
        if ok:
            count += 1
            weight = (price / effects[row]) ** exponent
            shares[row] = weight
            power += weight
    if count == 0:
        return 0
    units_per_money = 0.0
    for row in range(first, last):
        if priced[row]:
            shares[row] = shares[row] / power
            units_per_money += shares[row] * effects[row] / ask_of_good[goods[row]]
    if has_limits:
        binding = False
        for row in range(first, last):
            if priced[row]:
                units[row] = shares[row] * effects[row] / ask_of_good[goods[row]] / units_per_money
                if limited[row] and units[row] > limits[row] + SHARE_LIMIT_TOLERANCE:
                    binding = True
        if binding:
            for row in range(first, last):
                fixed_flag[row] = False
                fixed_value[row] = 0.0
            while True:
                free_total = 0.0
                fixed_total = 0.0
                free_count = 0
                for row in range(first, last):
                    if priced[row]:
                        if fixed_flag[row]:
                            fixed_total += fixed_value[row]
                        else:
                            free_total += units[row]
                            free_count += 1
                if free_count == 0 or free_total <= 0.0:
                    break
                scale = (1.0 - fixed_total) / free_total
                over = False
                for row in range(first, last):
                    if priced[row] and not fixed_flag[row] and limited[row] and \
                            units[row] * scale > limits[row] + SHARE_LIMIT_TOLERANCE:
                        over = True
                if not over:
                    for row in range(first, last):
                        if priced[row] and not fixed_flag[row]:
                            fixed_flag[row] = True
                            fixed_value[row] = units[row] * scale
                    break
                for row in range(first, last):
                    if priced[row] and not fixed_flag[row] and limited[row] and \
                            units[row] * scale > limits[row] + SHARE_LIMIT_TOLERANCE:
                        fixed_flag[row] = True
                        fixed_value[row] = limits[row]
            cost_per_unit = 0.0
            for row in range(first, last):
                if priced[row]:
                    cost_per_unit += fixed_value[row] * ask_of_good[goods[row]] / effects[row]
            for row in range(first, last):
                if priced[row]:
                    shares[row] = fixed_value[row] * ask_of_good[goods[row]] / effects[row] / cost_per_unit
    for row in range(first, last):
        ceilings[row] = numpy.inf
        if not priced[row]:
            continue
        cheapest_other = numpy.inf
        for other in range(first, last):
            if other != row and priced[other]:
                cost = ask_of_good[goods[other]] / effects[other]
                if cost < cheapest_other:
                    cheapest_other = cost
        if cheapest_other < numpy.inf:
            parity = cheapest_other * effects[row]
            if parity >= ask_of_good[goods[row]]:
                ceilings[row] = parity
    return count


@njit(**KERNEL)
def buyer_bids(basket, money, need_ptr, need_weight, need_has_limits, need_good_ptr, goods, effects, limits, limited,
               exponent, ask_of_good, shares, ceilings, priced, units, fixed_value, fixed_flag, spend, ceiling, touched,
               out_good, out_spend, out_ceiling):
    """The bids a buyer places with `money` (by need, indexed as the basket's needs: the money it was rationed of, zero where
    none), as goods_respend.respend_bids: a need's money goes to its goods still offered by the basket's choice rule; money of
    a need with none offered passes to the needs that have goods, by their budget weights. Writes the goods bid for in
    ascending order to `out_good`, with the money bid and the price ceiling, and returns how many. `spend`, `ceiling` and
    `touched` are scratch over goods; the others as `need_shares`."""
    first_need, last_need = need_ptr[basket], need_ptr[basket + 1]
    weight_total = 0.0
    passed = 0.0
    for need in range(first_need, last_need):
        count = need_shares(need_good_ptr[need], need_good_ptr[need + 1], need_has_limits[need], goods, effects, limits,
                            limited, exponent, ask_of_good, shares, ceilings, priced, units, fixed_value, fixed_flag)
        if count > 0:
            weight_total += need_weight[need]
        elif money[need - first_need] > 0.0:
            passed += money[need - first_need]
    spent = 0
    for need in range(first_need, last_need):
        first, last = need_good_ptr[need], need_good_ptr[need + 1]
        has_goods = False
        for row in range(first, last):
            if priced[row]:
                has_goods = True
        if not has_goods:
            continue
        amount = money[need - first_need]
        if amount < 0.0:
            amount = 0.0
        if passed > 0.0 and weight_total > 0.0:
            amount = amount + passed * need_weight[need] / weight_total
        if amount <= 0.0:
            continue
        for row in range(first, last):
            if priced[row] and shares[row] * amount > 0.0:
                good = goods[row]
                if not touched[good]:
                    touched[good] = True
                    spend[good] = 0.0
                    ceiling[good] = numpy.inf
                    out_good[spent] = good
                    spent += 1
                spend[good] += amount * shares[row]
                if ceilings[row] < ceiling[good]:
                    ceiling[good] = ceilings[row]
    for index in range(1, spent):             # the goods in ascending order, as respend_bids sorts them
        held = out_good[index]
        place = index - 1
        while place >= 0 and out_good[place] > held:
            out_good[place + 1] = out_good[place]
            place -= 1
        out_good[place + 1] = held
    for index in range(spent):
        good = out_good[index]
        out_spend[index] = spend[good]
        out_ceiling[index] = ceiling[good]
        touched[good] = False
    return spent
