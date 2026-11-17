"""A producer's year end (producers_close.close_year with firm_year.settle_year and year_close's sales rules) over every
producer at once. `close_rows` walks the producers listed in `rows`, in that order, reading the year arrays and the packed
figures of `close_pack.py`, and fills the answer arrays; no record is touched. Each step is the rule of the same name in
the Python it replaces; the comments name it. A missing figure is NaN where the Python has None.

A producer whose plant would grow may need the price its own added output leaves (`price_share_after`, a walk of the
market's bids that stays in Python): such a row is marked in `needs_share` with the output it would add in
`added`, and is run again by the caller with `share` filled."""
import math

import numpy as np

from sim.jit import njit

from . import close_kernel_cost as cost
from .plan_wear import covered_input_bill

K_EXPECT, K_REGRESS, K_SPREAD, K_CHANGE, K_CLEARING, K_MONTHS, K_ASK_STEP, K_CLOSED, K_WORKING_YEARS = range(9)
K_INERTIA, K_DIVIDEND, K_FULL_PAYOUT, K_RESCALE, K_BANKRUPT_IDLE, K_BUFFER, K_EPSILON, K_KEEP, K_SOLD_OUT = range(9, 18)

STATE_OK, STATE_CRISIS, STATE_ILLIQUID, STATE_INSOLVENT = 0, 1, 2, 3
REQUEST_NONE, REQUEST_EXPAND, REQUEST_WORKING_CAPITAL = 0, 1, 2


@njit
def append_history(old, count, value, keep, out):
    kept = min(count, keep)
    for position in range(kept):
        out[position] = old[count - kept + position]
    out[kept] = value
    return kept + 1


@njit
def mean_of(values, count):
    total = 0.0
    for position in range(count):
        total += values[position]
    return total / count if count > 0 else 0.0


@njit
def shed_share(earnings, revenues, count, change_share):
    """producer_losses.shed_share."""
    if count == 0:
        return 0.0
    average_earnings = mean_of(earnings, count)
    average_revenue = mean_of(revenues, count)
    outlay = average_revenue - average_earnings
    if average_earnings >= 0.0 or outlay <= 0.0:
        return 0.0
    return min(change_share, -average_earnings / outlay)


@njit
def market_capacity_of(slot_goods, outputs, area_of, recipe_row, tile_row, capacity, yield_factor, idle_years, rows_count, count_goods, count_areas):
    """expected_sales.market_capacities over the producers not idle: output a year the plants allow, by (good, area)."""
    total = np.zeros((count_goods, count_areas))
    for row in range(rows_count):
        if idle_years[row] > 0:
            continue
        recipe = recipe_row[row]
        for good in range(count_goods):
            per_run = outputs[recipe, good]
            if per_run != 0.0:
                column = area_of[good, tile_row[row]]
                if column >= 0:
                    total[good, column] += per_run * (capacity[row] * yield_factor[row])
    return total


@njit
def fallback_prices(recipe, tile, width, tools, price, area_of, prices):
    """Fills the places of `prices` after the recipe's `width` slots with the price on `tile` of the goods a tool's wear may be covered
    with that the recipe does not use (NaN: none), as `plan_wear.covered_input_bill` reads them."""
    for place in range(width, prices.shape[0]):
        fallback = tools.bid_goods[recipe, place]
        prices[place] = cost.price_at(price, area_of, fallback, tile) if fallback >= 0 else np.nan


@njit
def close_rows(rows, constants,
               slot_goods, slot_trades, slot_is_input, slot_is_output, slot_is_plant, inputs, outputs, revenue_outputs, plant_goods, labour,
               plant_labour, plant_life, idle_wear,
               recipe_row, tile_row, capacity, yield_factor, years_of_loss, cash_target, expected_sales, last_runs,
               land_rent, earnings_history, revenue_history, history_count, expected, ask_multiple,
               area_of, price, offered, cleared, bare_quote, wage, clearing, unmet, market_capacity, spoilage, ground,
               rate_of, cash_in_currency, cash_in_money, revenue, running_costs, stock, sold, made, hours_hired,
               interest, commitments, arrears, debt, held_start, held_good, held_quantity, share,
               new_capacity, new_losses, new_target, new_expected, written, exited, dividend, request_kind, request_amount,
               request_rate, request_term, request_collateral, expansion_runs, replacement_runs, new_earnings, new_revenues,
               new_count, state, write_off, new_idle, new_expected_sales, new_last_runs, new_staffed, demand_runs,
               needs_share, added, tools):
    width = slot_goods.shape[1]
    places = tools.bid_goods.shape[1]       # the recipe's slots, then the fallback goods that are not inputs (year_arrays_tools.py)
    unscaled = np.ones((1, labour.shape[1]))
    trade_width = slot_trades.shape[1]
    q_in, q_out, q_plant = np.zeros(width), np.zeros(width), np.zeros(width)
    q_val = np.zeros(width)      # q_out as it fetches after the state's harvest share: what the runs are valued at
    live, exp, old_exp, latest = np.zeros(places), np.zeros(width), np.zeros(width), np.zeros(width)
    inputs_be, cover, prices, scratch = np.zeros(places), np.zeros(width), np.zeros(width), np.zeros(width)
    here = np.zeros(width)
    q_lab, q_pl, wages = np.zeros(trade_width), np.zeros(trade_width), np.zeros(trade_width)
    has_latest = np.zeros(width, dtype=np.bool_)
    for index in range(rows.shape[0]):
        row = rows[index]
        recipe = recipe_row[row]
        tile = tile_row[row]
        cap_old = capacity[row]
        yield_ = yield_factor[row]
        count = 0
        for slot in range(width):
            good = slot_goods[recipe, slot]
            if good < 0:
                break
            count = slot + 1
            q_in[slot] = inputs[recipe, good] if slot_is_input[recipe, slot] else 0.0
            q_out[slot] = outputs[recipe, good] if slot_is_output[recipe, slot] else 0.0
            q_val[slot] = revenue_outputs[recipe, good] if slot_is_output[recipe, slot] else 0.0
            q_plant[slot] = plant_goods[recipe, good] if slot_is_plant[recipe, slot] else 0.0
            live[slot] = (cost.price_at(price, area_of, good, tile)
                          if slot_is_input[recipe, slot] or slot_is_plant[recipe, slot] else np.nan)
            here[slot] = cost.price_at(price, area_of, good, tile)
            old_exp[slot] = expected[row, slot]
            exp[slot] = expected[row, slot]
            has_latest[slot] = False
            written[row, slot] = False
        fallback_prices(recipe, tile, width, tools, price, area_of, live)
        inputs_be[width:] = live[width:]
        trades = 0
        for slot in range(trade_width):
            trade = slot_trades[recipe, slot]
            if trade < 0:
                break
            trades = slot + 1
            q_lab[slot] = labour[recipe, trade]
            q_pl[slot] = plant_labour[recipe, trade]
            wages[slot] = wage[trade, tile]
        rate = rate_of[row]
        no_rate = np.isnan(rate)
        life = plant_life[recipe]
        has_plant = life > 0.0
        rent = land_rent[row]
        sales_expected = expected_sales[row]
        target_cover = max(0.0, sales_expected) * max(0.0, constants[K_MONTHS]) / 12.0

        # next_expectations
        for slot in range(count):
            if not slot_is_output[recipe, slot]:
                continue
            seen = here[slot]
            if np.isnan(seen):
                continue
            has_latest[slot] = True
            latest[slot] = seen
            previous = exp[slot]
            exp[slot] = seen if np.isnan(previous) else previous + constants[K_EXPECT] * (seen - previous)
            written[row, slot] = True
        for slot in range(count):
            if not slot_is_input[recipe, slot]:
                continue
            good = slot_goods[recipe, slot]
            paid = live[slot]
            cleared_price = cost.price_at(cleared, area_of, good, tile)
            if not np.isnan(cleared_price) and not np.isnan(paid) and cleared_price > paid:
                paid = cleared_price
            if not np.isnan(paid) and not slot_is_output[recipe, slot]:
                previous = exp[slot]
                exp[slot] = paid if np.isnan(previous) else previous + constants[K_EXPECT] * (paid - previous)
                written[row, slot] = True
        # _break_even_scale
        for slot in range(count):
            inputs_be[slot] = live[slot]
            if slot_is_input[recipe, slot] and not np.isnan(live[slot]) and not np.isnan(exp[slot]):
                inputs_be[slot] = exp[slot]
        break_even = np.nan
        input_share = 0.0
        if not no_rate:
            expected_revenue = cost.revenue_per_run(q_val, exp, count) * yield_
            input_bill = covered_input_bill(recipe, 0, tile, slot_goods, inputs, tools, labour, unscaled, wage, inputs_be)
            variable = input_bill + cost.bill(q_lab, wages, trades) + rent
            plant_value = cost.bill(q_plant, inputs_be, count) + cost.bill(q_pl, wages, trades)
            full = variable + cost.capital_charge(plant_value, life, rate)
            if expected_revenue > 0.0 and math.isfinite(full) and full > 0.0:
                break_even = full / expected_revenue
                input_share = input_bill / full
        worked_last = last_runs[row] > 0.0
        if not np.isnan(break_even):
            for slot in range(count):
                cover[slot] = exp[slot] * break_even if has_latest[slot] else np.nan
            for slot in range(count):
                if not has_latest[slot]:
                    continue
                gap = 0.0
                if worked_last:
                    unsold = stock[row, slot] - q_in[slot] * cap_old
                    gap = cost.stock_gap(unsold, target_cover * q_out[slot])
                weight = constants[K_REGRESS] * (1.0 - max(0.0, min(1.0, gap)))
                exp[slot] += weight * (exp[slot] * break_even - exp[slot])
            for slot in range(count):
                if has_latest[slot] and cost.flag_at(bare_quote, area_of, slot_goods[recipe, slot], tile):
                    exp[slot] = cost.held_to_band(exp[slot], old_exp[slot], cover[slot], input_share, ask_multiple[row, slot])
        else:
            for slot in range(count):
                cover[slot] = np.nan
        if worked_last:
            for slot in range(count):
                if has_latest[slot]:
                    unsold = stock[row, slot] - q_in[slot] * cap_old
                    exp[slot] = cost.adjusted_within_band(exp[slot], cover[slot], unsold, target_cover * q_out[slot],
                                                          ask_multiple[row, slot], input_share, constants[K_ASK_STEP])
        for slot in range(count):
            new_expected[row, slot] = exp[slot]

        # close_year
        currency_cash = max(0.0, cash_in_currency[row])
        paying = -1
        best = -np.inf
        for slot in range(count):       # prices_here, paying_output
            if not slot_is_output[recipe, slot]:
                continue
            here_price = cost.price_at(clearing, area_of, slot_goods[recipe, slot], tile)
            scratch[slot] = here_price
            if not np.isnan(here_price) and (paying < 0 or q_out[slot] * here_price > best):
                paying = slot
                best = q_out[slot] * here_price
        if paying < 0:
            for slot in range(count):
                if slot_is_output[recipe, slot]:
                    paying = slot
                    break
        run_of_paying = q_out[paying] * yield_ if paying >= 0 else 0.0
        worked_now = made[row, paying] / run_of_paying if run_of_paying > 0.0 else 0.0
        worked = min(max(0.0, worked_now), cap_old)
        # runs_sold
        if yield_ <= 0.0:
            sold_runs = sales_expected
        else:
            seen_value = 0.0
            run_value = 0.0
            best_ratio = -np.inf
            for slot in range(count):
                if not slot_is_output[recipe, slot]:
                    continue
                good = slot_goods[recipe, slot]
                column = area_of[good, tile]
                per_run = q_out[slot] * yield_
                market_capacity_here = market_capacity[good, column] if column >= 0 else 0.0
                unmet_here = unmet[good, column] if column >= 0 else 0.0
                seen = cost.demand_seen(sold[row, slot], stock[row, slot], per_run * cap_old, market_capacity_here, unmet_here,
                                        constants[K_SOLD_OUT])
                scratch_price = scratch[slot]
                if not np.isnan(scratch_price):
                    run_value += per_run * scratch_price
                    seen_value += seen * scratch_price
                ratio = seen / per_run if per_run != 0.0 else np.inf
                if ratio > best_ratio:
                    best_ratio = ratio
            sold_runs = seen_value / run_value if run_value > 0.0 else best_ratio
        demand_runs[row] = sold_runs

        input_now = covered_input_bill(recipe, 0, tile, slot_goods, inputs, tools, labour, unscaled, wage, live)
        variable_now = input_now + cost.bill(q_lab, wages, trades)
        plant_now = cost.bill(q_plant, live, count) + cost.bill(q_pl, wages, trades)
        charge = np.nan if no_rate else cost.capital_charge(plant_now, life, rate) * worked
        loss = worked <= 0.0 or revenue[row] < running_costs[row] + (charge if not np.isnan(charge) and math.isfinite(charge) else 0.0)
        losses = years_of_loss[row] + 1 if loss else 0
        # _expected_run
        missing = False
        for slot in range(count):
            prices[slot] = np.nan
            if not slot_is_output[recipe, slot]:
                continue
            chosen = exp[slot] if not np.isnan(exp[slot]) else here[slot]
            prices[slot] = chosen
            if np.isnan(chosen):
                missing = True
        revenue_run = 0.0
        cost_run = np.inf
        if not missing:
            if sales_expected > 0.0 and not no_rate:
                for slot in range(count):
                    if slot_is_output[recipe, slot] and not ground[slot_goods[recipe, slot]]:
                        held = max(0.0, stock[row, slot] - q_in[slot] * cap_old)
                        prices[slot] = cost.queued_holding_value(prices[slot], held, sales_expected * q_out[slot] * yield_, rate,
                                                                 spoilage[slot_goods[recipe, slot]])
            run_cost = variable_now + rent
            if math.isfinite(run_cost):
                revenue_run = cost.revenue_per_run(q_val, prices, count) * yield_
                cost_run = run_cost
        margin = revenue_run - cost_run
        pays = cost.share_working(revenue_run, cost_run, constants[K_SPREAD]) if math.isfinite(margin) else 0.0
        shedding = margin <= 0.0
        if shedding and pays < constants[K_CLOSED] and sales_expected <= constants[K_CLOSED] * cap_old:
            exited[row] = True
            dividend[row] = currency_cash
            continue
        exited[row] = False
        if has_plant:
            wear = cap_old / life
            new_cap = cap_old - wear
        else:
            wear = 0.0
            idle = cap_old - worked if margin <= 0.0 else 0.0
            new_cap = cap_old - idle_wear[recipe] * idle
        if shedding:
            shed = min(new_cap, max(pays * cap_old, (1.0 - constants[K_CHANGE]) * cap_old))
            needed = sales_expected / pays if pays > 0.0 else cap_old
            new_cap = max(shed, min(new_cap, needed))
        depreciation = wear * plant_now if has_plant else 0.0
        earnings = revenue[row] - running_costs[row] - interest[row] - (depreciation if math.isfinite(depreciation) else 0.0)
        keep = int(constants[K_KEEP])
        count_after = append_history(earnings_history[row], history_count[row], earnings, keep, new_earnings[row])
        append_history(revenue_history[row], history_count[row], revenue[row], keep, new_revenues[row])
        new_count[row] = count_after
        lost = shed_share(new_earnings[row], new_revenues[row], count_after, constants[K_CHANGE])
        new_cap = min(new_cap, cap_old * (1.0 - lost))
        if not has_plant and not shedding and lost <= 0.0:
            wanted_sales = sold_runs if sales_expected <= 0.0 else sales_expected + constants[K_EXPECT] * (sold_runs - sales_expected)
            if pays > 0.0 and new_cap > 0.0 and math.isfinite(wanted_sales) and math.isfinite(pays):
                new_cap = new_cap + min(max(0.0, wanted_sales / pays - new_cap), constants[K_CHANGE] * new_cap)
        working_cost = variable_now
        target = 0.0 if not math.isfinite(working_cost) else working_cost * new_cap * constants[K_WORKING_YEARS]
        # _investment, with the producer as it was before the close
        replacement = 0.0
        growth = 0.0
        if has_plant:
            for slot in range(count):       # expected_output_prices: the old expectation, else the price on offer
                if not slot_is_output[recipe, slot]:
                    scratch[slot] = np.nan
                    continue
                kept_price = old_exp[slot]
                scratch[slot] = kept_price if not np.isnan(kept_price) else cost.price_at(offered, area_of, slot_goods[recipe, slot], tile)
            wanted = plan_runs(q_out, q_val, scratch, stock, row, count, sales_expected, yield_, cost_run, constants[K_MONTHS],
                               constants[K_CLEARING], slot_is_output, recipe)
            planned = cost.within_a_years_change(worked, np.nan, cap_old, worked if math.isinf(wanted) else wanted, constants[K_CHANGE])
            gap = planned - new_cap
            investment = 0.0 if gap <= 0.0 else min(gap, constants[K_INERTIA] * max(0.0, wear))
            replacement = min(investment, max(0.0, wear))
            growth = investment - replacement
        # _expansion
        kind = REQUEST_NONE
        amount = 0.0
        max_rate = 0.0
        term = 0.0
        collateral = 0.0
        grown = 0.0
        needs_share[row] = False
        if not no_rate:
            value = plant_now
            if has_plant and value > 0.0 and math.isfinite(value) and growth > 0.0:
                for slot in range(count):
                    if not slot_is_output[recipe, slot]:
                        scratch[slot] = np.nan
                        continue
                    kept_price = old_exp[slot]
                    scratch[slot] = kept_price if not np.isnan(kept_price) else cost.price_at(offered, area_of, slot_goods[recipe, slot], tile)
                before = return_after_recovery(q_val, scratch, count, input_now, q_lab, trades, q_plant, q_pl, live, wages, life, rate)
                if not np.isnan(before) and before > rate:
                    for slot in range(count):
                        added[row, slot] = growth * q_out[slot] * yield_
                        if not np.isnan(scratch[slot]):
                            scratch[slot] = scratch[slot] * share[row, slot]
                    needs_share[row] = True
                    after = return_after_recovery(q_val, scratch, count, input_now, q_lab, trades, q_plant, q_pl, live, wages, life, rate)
                    yearly = return_on_capital(q_val, scratch, count, input_now, q_lab, trades, q_plant, q_pl, live, wages)
                    if not (np.isnan(yearly) or np.isnan(after) or after <= rate):
                        kind = REQUEST_EXPAND
                        amount = growth * value
                        max_rate = cost.earnable_rate(yearly, 1.0)
                        term = life
                        collateral = amount
                        grown = growth
        if kind == REQUEST_NONE:
            paid_now = variable_now
            if math.isfinite(paid_now) and paid_now > 0.0 and revenue_run > paid_now:
                smoothed = cost.within_a_years_change(worked, np.nan, new_cap, new_cap * pays, constants[K_CHANGE])
                cash_kept = min(currency_cash, target)
                short_runs = smoothed - cash_kept / paid_now
                if short_runs > 0.0:
                    amount = short_runs * paid_now
                    max_rate = cost.earnable_rate(revenue_run - paid_now, paid_now)
                    held = 0.0
                    for slot in range(count):
                        if slot_is_input[recipe, slot] or slot_is_output[recipe, slot]:
                            held_price = here[slot]
                            if not np.isnan(held_price) and held_price > 0.0 and stock[row, slot] > 0.0:
                                held += held_price * stock[row, slot]
                    plant_assets = new_cap * plant_now if has_plant else 0.0
                    assets = max(0.0, currency_cash) + held + max(0.0, plant_assets)
                    kind = REQUEST_WORKING_CAPITAL
                    term = 1.0
                    collateral = assets if assets > 0.0 else amount
        new_capacity[row] = new_cap
        new_losses[row] = losses
        new_target[row] = target
        # settle_year
        money_cash = max(0.0, cash_in_money[row])
        stock_value = 0.0
        for position in range(held_start[row], held_start[row + 1]):
            held_price = cost.price_at(price, area_of, held_good[position], tile)
            if not np.isnan(held_price) and held_price > 0.0:
                stock_value += held_price * held_quantity[position]
        plant_of_survivor = new_cap * plant_now if has_plant else 0.0
        assets_total = money_cash + plant_of_survivor + stock_value
        capital_and_cash = money_cash + plant_of_survivor
        wear_money = cap_old / life * plant_now if has_plant and cap_old > 0.0 else 0.0
        replacement_money = replacement * plant_now
        kept_cash = target + commitments[row] + replacement_money + constants[K_BUFFER] * max(0.0, running_costs[row])
        net = revenue[row] - running_costs[row] - interest[row] - wear_money
        count_settle = append_history(earnings_history[row], history_count[row], net, keep, new_earnings[row])
        append_history(revenue_history[row], history_count[row], revenue[row], keep, new_revenues[row])
        new_count[row] = count_settle
        average_revenue = mean_of(new_revenues[row], count_settle)
        average_earnings = max(0.0, mean_of(new_earnings[row], count_settle))
        if average_revenue < 1e-6 or money_cash < constants[K_FULL_PAYOUT] * average_revenue:
            pay = constants[K_DIVIDEND] * average_earnings
        else:
            pay = average_earnings
        needs_total = target + commitments[row] + pay
        if money_cash >= needs_total:
            status = STATE_OK
        elif money_cash >= arrears[row] - 1e-12:
            status = STATE_CRISIS
        else:
            status = STATE_ILLIQUID
        if arrears[row] > constants[K_EPSILON] and status != STATE_OK:
            status = STATE_ILLIQUID
        elif status == STATE_CRISIS:
            pay = max(0.0, money_cash - commitments[row] - target)
        else:
            pay = max(pay, max(0.0, money_cash - kept_cash))
        if status != STATE_ILLIQUID and assets_total - debt[row] < 0.0:
            status = STATE_INSOLVENT
        state[row] = status
        write_off[row] = 0.0
        new_idle[row] = 0
        if status == STATE_ILLIQUID or status == STATE_INSOLVENT:
            if debt[row] > constants[K_EPSILON]:
                goal = constants[K_RESCALE] * capital_and_cash
                if status == STATE_ILLIQUID and goal > debt[row]:
                    goal = constants[K_RESCALE] * debt[row]
                write_off[row] = min(1.0, max(0.0, (debt[row] - goal) / debt[row]))
            new_idle[row] = int(constants[K_BANKRUPT_IDLE])
            dividend[row] = 0.0
            request_kind[row] = REQUEST_NONE
            expansion_runs[row] = 0.0
        else:
            dividend[row] = max(0.0, min(pay, money_cash))
            request_kind[row] = kind
            expansion_runs[row] = grown
        request_amount[row] = amount
        request_rate[row] = max_rate
        request_term[row] = term
        request_collateral[row] = collateral
        replacement_runs[row] = replacement
        # year_close._with_sales
        new_last_runs[row] = worked_now
        new_expected_sales[row] = sold_runs if sales_expected <= 0.0 else sales_expected + constants[K_EXPECT] * (sold_runs - sales_expected)
        staffed_now = np.inf
        counted = False
        for slot in range(trades):
            if q_lab[slot] > 0.0:
                counted = True
                hired = hours_hired[row, slot] / q_lab[slot]
                if hired < staffed_now:
                    staffed_now = hired
        new_staffed[row] = min(staffed_now, new_cap) if counted else np.nan


@njit
def plan_runs(q_out, q_val, output_price, stock, row, count, sales, yield_, run_cost, months, clearing_years, slot_is_output, recipe):
    """producers.runs_for_stock with the prices the producer expects."""
    if sales <= 0.0:
        return np.inf
    target = max(0.0, sales) * max(0.0, months) / 12.0
    gaps = np.full(count, np.nan)
    any_gap = False
    for slot in range(count):
        made = q_out[slot] * yield_
        if slot_is_output[recipe, slot] and made > 0.0:
            gaps[slot] = target - stock[row, slot] / made
            any_gap = True
    if not any_gap:
        return sales
    counted = np.zeros(count, dtype=np.bool_)
    piling_any = False
    for slot in range(count):
        if not np.isnan(gaps[slot]):
            counted[slot] = True
            if gaps[slot] < 0.0:
                piling_any = True
    if piling_any:
        total = 0.0
        best = -np.inf
        paying = -1
        for slot in range(count):
            if slot_is_output[recipe, slot] and not np.isnan(output_price[slot]):
                value = q_val[slot] * output_price[slot]
                total += value
                if paying < 0 or value > best:
                    paying = slot
                    best = value
        if paying < 0:
            for slot in range(count):
                if slot_is_output[recipe, slot]:
                    paying = slot
                    break
        for slot in range(count):
            if not np.isnan(gaps[slot]) and gaps[slot] < 0.0:
                value = q_val[slot] * output_price[slot] if not np.isnan(output_price[slot]) else np.nan
                keeps = slot == paying or (not np.isnan(value) and value >= total - value)
                if not keeps:
                    counted[slot] = False
        sells = 0.0
        for slot in range(count):
            if slot_is_output[recipe, slot] and not np.isnan(output_price[slot]) and not (not np.isnan(gaps[slot]) and gaps[slot] < 0.0):
                sells += q_val[slot] * output_price[slot]
        sells *= yield_
        if sells > 0.0 and sells >= run_cost:
            for slot in range(count):
                counted[slot] = not np.isnan(gaps[slot]) and gaps[slot] >= 0.0
    smallest = np.inf
    found = False
    for slot in range(count):
        if counted[slot] and gaps[slot] < smallest:
            smallest = gaps[slot]
            found = True
    if not found:
        for slot in range(count):
            if not np.isnan(gaps[slot]) and gaps[slot] < smallest:
                smallest = gaps[slot]
    return max(0.0, sales + smallest / clearing_years)


@njit
def return_on_capital(q_out, output_price, count, input_bill, q_lab, trades, q_plant, q_pl, live, wages):
    """unit_cost.return_on_capital (rent not charged); NaN is None. Revenue is the per-run figure, as there. `input_bill` is the
    inputs with the tools covered the cheapest way (plan_wear.covered_input_bill)."""
    variable = input_bill + cost.bill(q_lab, wages, trades)
    employed = cost.bill(q_plant, live, count) + cost.bill(q_pl, wages, trades) + variable
    if not math.isfinite(employed) or employed <= 0.0:
        return np.nan
    return (cost.revenue_per_run(q_out, output_price, count) - variable) / employed


@njit
def return_after_recovery(q_out, output_price, count, input_bill, q_lab, trades, q_plant, q_pl, live, wages, life, rate):
    """unit_cost.return_after_recovery."""
    gross = return_on_capital(q_out, output_price, count, input_bill, q_lab, trades, q_plant, q_pl, live, wages)
    if np.isnan(gross):
        return np.nan
    plant = cost.bill(q_plant, live, count) + cost.bill(q_pl, wages, trades)
    employed = plant + input_bill + cost.bill(q_lab, wages, trades)
    wear = cost.capital_charge(plant, life, rate) - rate * plant
    return gross - wear / employed
