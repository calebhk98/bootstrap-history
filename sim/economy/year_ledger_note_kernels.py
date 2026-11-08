"""Kernels that note a year's events in the ledger's tables: rows of settlements, rows of labour fills, cleared rounds, and the
totals of a market's rounds. They add one input row after another with the primitives of year_ledger_kernels.py, so many events in one
call give the sums and the entry order that noting them one at a time gave."""
import numpy

from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.economy.year_ledger_kernels import add_pair, add_to_figure
from sim.economy.year_ledger_tables import (DELIVERED, HOURS_SOLD, MONEY_OUT, PLANT_SPEND, SALES_IN, SALES_PURPOSE, WAGES_IN,
                                            WAGES_PURPOSE)
from sim.jit import njit


# ---- settlements, row by row ---------------------------------------------------------------------------------------------
# A row is one agent in one settlement. A call may hold many settlements one after another; adding row by row in order is the
# same sum, in the same order, as settling them one at a time.

@njit
def note_settlement_money(figures, counters, agents, paid, received, plant_bought, purpose_kind):
    """Money of settlement rows, in order: what an agent paid goes to `money_out` (and to `plant_spend` where `plant_bought` says
    it bought goods its plant is built from); what it received goes to `wages_in` (row purpose kind WAGES_PURPOSE) or `sales_in`
    (SALES_PURPOSE) and nowhere for any other purpose."""
    for i in range(len(agents)):
        agent = agents[i]
        if paid[i] > 0.0:
            add_to_figure(figures.money_out, figures.order_money_out, counters, MONEY_OUT, agent, paid[i])
            if plant_bought[i]:
                add_to_figure(figures.plant_spend, figures.order_plant_spend, counters, PLANT_SPEND, agent, paid[i])
        if received[i] > 0.0:
            if purpose_kind[i] == WAGES_PURPOSE:
                add_to_figure(figures.wages_in, figures.order_wages_in, counters, WAGES_IN, agent, received[i])
            elif purpose_kind[i] == SALES_PURPOSE:
                add_to_figure(figures.sales_in, figures.order_sales_in, counters, SALES_IN, agent, received[i])


@njit
def note_settlement_goods(received_target, sold_target, agents, got_goods, goods_in, goods_out, good, purpose_kind):
    """Goods of the sale rows (purpose kind SALES_PURPOSE), in order: an agent that got goods adds `goods_in` to `received`
    under the row's good, and one that gave some adds `goods_out` to `sold`."""
    for i in range(len(agents)):
        if purpose_kind[i] != SALES_PURPOSE:
            continue
        if got_goods[i]:
            add_pair(received_target, agents[i], good[i], 0, goods_in[i], 0.0)
        if goods_out[i] > 0.0:
            add_pair(sold_target, agents[i], good[i], 0, goods_out[i], 0.0)


@njit
def note_settlement_foreign(imports_target, exports_target, agents, imports, exports, template, reference):
    """Money across the border in settlement rows: positive `imports` and `exports` are added to the agent's row for the row's
    purpose (template, reference)."""
    for i in range(len(agents)):
        if imports[i] > 0.0:
            add_pair(imports_target, agents[i], template[i], reference[i], imports[i], 0.0)
        if exports[i] > 0.0:
            add_pair(exports_target, agents[i], template[i], reference[i], exports[i], 0.0)


# ---- the hours of labour markets ------------------------------------------------------------------------------------------

@njit
def paid_hours(quantity, wage, paid, slot):
    """The hours of a fill the wages actually paid cover (at most the fill), taking the wages used from the slot's purse."""
    covered = min(quantity, paid[slot] / wage)
    paid[slot] = paid[slot] - covered * wage
    return covered


@njit
def note_labour_fills(figures, counters, hired_target, by_market_target, fill_agent, fill_slot, fill_quantity, fill_price,
                      fill_is_buy, fill_trade, fill_market, fill_wage, fill_settled, paid_by_slot, paid_to_slot):
    """The hours of labour fills, in order (one labour market's fills after another's). A fill counts in full, or when its row
    says `fill_settled` for as many hours as the wages paid for it cover at the market's `fill_wage`: `paid_by_slot` is what each
    employer paid and `paid_to_slot` what each worker was paid, indexed by `fill_slot` (one slot per distinct agent of a market)
    and used up as they cover fills. A buy adds to `hours_hired` by trade and to `hours_hired_by_market` (hours and money); a
    sell adds to the worker's `hours_sold`."""
    for i in range(len(fill_agent)):
        agent = fill_agent[i]
        quantity = fill_quantity[i]
        if fill_settled[i]:
            if fill_is_buy[i]:
                quantity = paid_hours(quantity, fill_wage[i], paid_by_slot, fill_slot[i])
            else:
                quantity = paid_hours(quantity, fill_wage[i], paid_to_slot, fill_slot[i])
        if fill_is_buy[i]:
            add_pair(hired_target, agent, fill_trade[i], 0, quantity, 0.0)
            add_pair(by_market_target, agent, fill_market[i], 0, quantity, quantity * fill_price[i])
        else:
            add_to_figure(figures.hours_sold, figures.order_hours_sold, counters, HOURS_SOLD, agent, quantity)


@njit
def add_rounds(rounds, delivered, order_delivered, market_counters, markets, quantities, prices, moved):
    """Note cleared rounds in order: each is a row of `rounds`, and the goods its settlement moved (`moved`, which may be less
    than the round matched) are added to the market's delivered figure. The caller has reserved a row per round."""
    for i in range(len(markets)):
        row = claim_row(rounds)
        if row == NO_ROOM:
            return -1
        rounds.market[row] = markets[i]
        rounds.quantity[row] = quantities[i]
        rounds.price[row] = prices[i]
        add_to_figure(delivered, order_delivered, market_counters, DELIVERED, markets[i], moved[i])
    return 0


# ---- a market's rounds ------------------------------------------------------------------------------------------------------

@njit
def exact_sum(values, count):
    """The sum of the first `count` values correctly rounded, as `math.fsum` gives it (Shewchuk's partial sums, with
    the final rounding of CPython's `math.fsum`): the same figure whatever order the values are in."""
    partials = numpy.empty(count + 1)
    used = 0
    for position in range(count):
        x = values[position]
        slot = 0
        for j in range(used):
            y = partials[j]
            if abs(x) < abs(y):
                x, y = y, x
            high = x + y
            low = y - (high - x)
            if low != 0.0:
                partials[slot] = low
                slot += 1
            x = high
        partials[slot] = x
        used = slot + 1
    if used == 0:
        return 0.0
    used -= 1
    high = partials[used]
    low = 0.0
    while used > 0:
        x = high
        used -= 1
        y = partials[used]
        high = x + y
        low = y - (high - x)
        if low != 0.0:
            break
    if used > 0 and ((low < 0.0 and partials[used - 1] < 0.0) or (low > 0.0 and partials[used - 1] > 0.0)):
        y = low * 2.0
        x = high + y
        if y == x - high:
            high = x
    return high


@njit
def round_totals(round_market, round_quantity, round_price, round_count, delivered, order_delivered, market_count):
    """Per market that had a round, in the order its first round was noted: the market, the quantity delivered (0 where
    nothing was delivered), the price (rounds' prices weighted by the quantity each cleared, exactly rounded; the last round's
    price, NaN if it had none, when nothing was cleared or delivered).

    Returns (markets, quantity, price) as arrays, one entry per market that had a round."""
    first_seen = numpy.full(market_count, -1, dtype=numpy.int64)
    members = numpy.empty(market_count, dtype=numpy.int64)
    member_count = 0
    for round_row in range(round_count):
        market = round_market[round_row]
        if first_seen[market] < 0:
            first_seen[market] = member_count
            members[member_count] = market
            member_count += 1
    starts = numpy.zeros(member_count + 1, dtype=numpy.int64)
    for round_row in range(round_count):
        starts[first_seen[round_market[round_row]] + 1] += 1
    for member in range(member_count):
        starts[member + 1] += starts[member]
    next_slot = starts[:-1].copy()
    order = numpy.empty(round_count, dtype=numpy.int64)
    for round_row in range(round_count):
        member = first_seen[round_market[round_row]]
        order[next_slot[member]] = round_row
        next_slot[member] += 1
    quantity = numpy.zeros(member_count)
    price = numpy.full(member_count, numpy.nan)
    widest = 0
    for member in range(member_count):
        widest = max(widest, starts[member + 1] - starts[member])
    quantities = numpy.empty(widest)
    weighted = numpy.empty(widest)
    for member in range(member_count):
        market = members[member]
        if order_delivered[market] != 0:
            quantity[member] = delivered[market]
        count = 0
        weighted_count = 0
        for slot in range(starts[member], starts[member + 1]):
            round_row = order[slot]
            quantities[count] = round_quantity[round_row]
            count += 1
            if round_quantity[round_row] > 0.0:
                weighted[weighted_count] = round_quantity[round_row] * round_price[round_row]
                weighted_count += 1
        cleared = exact_sum(quantities, count)
        if quantity[member] > 0.0 and cleared > 0.0:
            price[member] = exact_sum(weighted, weighted_count) / cleared
        else:
            price[member] = round_price[order[starts[member + 1] - 1]]
    return members[:member_count].copy(), quantity, price
