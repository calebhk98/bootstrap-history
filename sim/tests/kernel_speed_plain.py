"""The versions of the market, book and ledger kernels before they were made cheaper to run (plain Python over the same compiled
helpers), kept so the kernels are tested against them: the rules and the order of every sum are these, to the last digit."""
import numpy

from sim.jit import njit
from sim.book_commit import add_flow, record_edge_goods
from sim.book_index import EMPTY, index_find, pack_key, start_position
from sim.book_tables import FREE, NEGATIVE_AMOUNT, NEGATIVE_QUANTITY
from sim.compiled_tables.causes import OK
from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.economy import goods_market_kernels as kernels
from sim.economy.goods_market_kernels import LOGIT_INTENSITY, ROUNDING_SHARE
from sim.economy.year_ledger_kernels import touch as touch_figure


# ---- goods_market_kernels ----------------------------------------------------------------------------------------------

@njit
def relative_weight(ask, cheapest):
    """The one transcendental step of a weight, compiled like the kernels' own (numpy's scalar exp can differ from it in the last bit)."""
    return numpy.exp(-LOGIT_INTENSITY * numpy.log(ask / cheapest))


def choice_weights(asks, stocked):
    count = len(asks)
    weights = numpy.zeros(count)
    running = numpy.zeros(count + 1)
    cheapest = 0.0
    found = False
    for offer in range(count):
        if stocked[offer] and not found:
            cheapest = asks[offer]
            found = True
    if found:
        for offer in range(count):
            if stocked[offer]:
                if cheapest > 0.0:
                    weights[offer] = relative_weight(asks[offer], cheapest)
                elif asks[offer] <= cheapest:
                    weights[offer] = 1.0
    for offer in range(count):
        running[offer + 1] = running[offer] + weights[offer]
    return weights, running


def requested_round_one(asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped):
    stocked = quantities > ROUNDING_SHARE * quantities
    weights, running = choice_weights(asks, stocked)
    requested = 0.0
    for bid in range(len(floors)):
        total = kernels.weight_sum(running, asks, maximums[bid])
        for offer in range(len(asks)):
            want = kernels.want_at(asks[offer], floors[bid], flexibles[bid], budgets[bid], references[bid], exponents[bid],
                                   maximums[bid], capped)
            requested += want * weights[offer] / total
    return requested


def allocate_arrays(asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped, tier_bounds):
    offers, bids = len(asks), len(floors)
    wants = numpy.zeros((offers, bids))
    for offer in range(offers):
        for bid in range(bids):
            wants[offer, bid] = kernels.want_at(asks[offer], floors[bid], flexibles[bid], budgets[bid], references[bid],
                                                exponents[bid], maximums[bid], capped)
    left = quantities.copy()
    stocked = left > ROUNDING_SHARE * quantities
    weights, running = choice_weights(asks, stocked)
    sums = numpy.zeros(bids)
    for bid in range(bids):
        sums[bid] = kernels.weight_sum(running, asks, maximums[bid])
    requests = numpy.zeros((offers, bids))
    requested = 0.0
    for offer in range(offers):
        for bid in range(bids):
            requests[offer, bid] = wants[offer, bid] * weights[offer] / sums[bid]
            requested += requests[offer, bid]
    served = numpy.zeros((offers, bids))
    short = numpy.zeros((offers, bids))
    kernels.serve(requests, left, tier_bounds, served, short)
    flow = served.copy()
    taken = numpy.zeros(bids)
    cost = numpy.zeros(bids)
    unmet = numpy.zeros(bids)
    for offer in range(offers):
        for bid in range(bids):
            taken[bid] += served[offer, bid]
            cost[bid] += asks[offer] * served[offer, bid]
            unmet[bid] += short[offer, bid]
    for _round in range(offers):
        stocked = left > ROUNDING_SHARE * quantities
        if not stocked.any() or not (unmet > 0.0).any():
            break
        weights, running = choice_weights(asks, stocked)
        for bid in range(bids):
            sums[bid] = kernels.weight_sum(running, asks, maximums[bid])
        for offer in range(offers):
            for bid in range(bids):
                again = 0.0
                if unmet[bid] > 0.0:
                    budget_left = max(budgets[bid] - cost[bid], 0.0)
                    affordable = kernels.affordable_units(asks[offer], budget_left)
                    again = unmet[bid] if unmet[bid] < affordable else affordable
                    room = max(wants[offer, bid] - taken[bid], 0.0)
                    if room < again:
                        again = room
                requests[offer, bid] = again * weights[offer] / sums[bid]
        kernels.serve(requests, left, tier_bounds, served, short)
        unmet[:] = 0.0
        for offer in range(offers):
            for bid in range(bids):
                flow[offer, bid] += served[offer, bid]
                taken[bid] += served[offer, bid]
                cost[bid] += asks[offer] * served[offer, bid]
                unmet[bid] += short[offer, bid]
    return taken, cost, quantities - left, requested, flow


# ---- book_plan and book_commit -------------------------------------------------------------------------------------------

def touch(plan, local_index, key, holder):
    position = start_position(key, len(local_index))
    mask = len(local_index) - 1
    while True:
        row = local_index[position]
        if row == EMPTY:
            row = plan.row_count[0]
            plan.row_count[0] = row + 1
            plan.key[row], plan.holder[row], plan.slot[row], plan.failing[row] = key, holder, FREE, 0
            plan.position[row] = position
            local_index[position] = row
            return row, True
        if plan.key[row] == key:
            return row, False
        position = (position + 1) & mask


def add_to_cell(plan, local_index, key, holder, held, amount, receives):
    row, is_new = touch(plan, local_index, key, holder)
    if is_new:
        plan.before[row] = held
        plan.after[row] = held
        plan.moved[row] = amount
    else:
        plan.moved[row] += amount
    if receives:
        plan.after[row] += amount
    else:
        plan.after[row] -= amount
    return row


def plan_transfers(transfers, first, last, balances, stride, plan, local_index):
    for row in range(first, last):
        amount = transfers.amount[row]
        if not amount >= 0.0:
            return NEGATIVE_AMOUNT, row
        payer, payee, currency = transfers.payer[row], transfers.payee[row], transfers.currency[row]
        cell = payer * stride + currency
        add_to_cell(plan, local_index, cell, payer, balances.amount[cell], amount, False)
        cell = payee * stride + currency
        add_to_cell(plan, local_index, cell, payee, balances.amount[cell], amount, True)
    return OK, 0


def add_to_stock(plan, local_index, stocks, stock_index, agent, good, tile, amount, receives):
    key = pack_key(agent, good, tile)
    row, is_new = touch(plan, local_index, key, agent)
    if is_new:
        slot = index_find(stocks.key, stock_index, key)
        plan.slot[row] = slot
        plan.before[row] = 0.0 if slot == FREE else stocks.quantity[slot]
        plan.after[row] = plan.before[row]
        plan.moved[row] = amount
    else:
        plan.moved[row] += amount
    if receives:
        plan.after[row] += amount
    else:
        plan.after[row] -= amount


def plan_moves(moves, first, last, stocks, stock_index, plan, local_index):
    for row in range(first, last):
        quantity = moves.quantity[row]
        if not quantity >= 0.0:
            return NEGATIVE_QUANTITY, row
        good = moves.good[row]
        add_to_stock(plan, local_index, stocks, stock_index, moves.giver[row], good, moves.tile[row], quantity, False)
        add_to_stock(plan, local_index, stocks, stock_index, moves.receiver[row], good, moves.receiver_tile[row], quantity, True)
    return OK, 0


def record_moves(moves, first, last, goods):
    for row in range(first, last):
        giver, receiver, good, quantity = moves.giver[row], moves.receiver[row], moves.good[row], moves.quantity[row]
        seen = goods.goods.gross_seen[good]
        goods.goods.gross_moved[good] = (goods.goods.gross_moved[good] if seen != 0 else 0.0) + quantity
        goods.goods.gross_seen[good] = 1
        code = add_flow(goods.flows, goods.flow_index, good, moves.purpose_code[row], moves.purpose_reference[row], quantity)
        if code != OK:
            return code
        if goods.agents.is_edge[giver] != 0:
            code = record_edge_goods(goods.edge_goods, goods.edge_index, giver, good, quantity, quantity)
            if code != OK:
                return code
        if goods.agents.is_edge[receiver] != 0:
            code = record_edge_goods(goods.edge_goods, goods.edge_index, receiver, good, quantity, -quantity)
            if code != OK:
                return code
    return OK


# ---- year_ledger_kernels and year_ledger_note_kernels --------------------------------------------------------------------

def new_pair(target, agent, subkey, extra):
    row = claim_row(target.rows)
    if row == NO_ROOM:
        return NO_ROOM
    rows = target.rows
    rows.key[row] = pack_key(agent, subkey, extra)
    rows.agent[row], rows.subkey[row], rows.extra[row] = agent, subkey, extra
    rows.amount[row], rows.second_amount[row], rows.next_in_agent[row], rows.live[row] = 0.0, 0.0, 0, 1
    from sim.book_index import index_add
    index_add(rows.key, target.hash_index, row)
    if target.chained:
        touch_figure(target.orders, target.counters, target.figure, agent)
        last = target.lasts[agent]
        if last == 0:
            target.firsts[agent] = row + 1
        else:
            rows.next_in_agent[last - 1] = row + 1
        target.lasts[agent] = row + 1
    return row


def add_pair(target, agent, subkey, extra, amount, second_amount):
    row = index_find(target.rows.key, target.hash_index, pack_key(agent, subkey, extra))
    if row == EMPTY:
        row = new_pair(target, agent, subkey, extra)
        if row == NO_ROOM:
            return -1
    target.rows.amount[row] += amount
    target.rows.second_amount[row] += second_amount
    return row
