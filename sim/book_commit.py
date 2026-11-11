"""Writing a planned batch into the book's tables, and the records every posting leaves (gross totals, the year's purpose
flows, an edge account's volume and net).

The records add in posting order, one posting at a time, so a float total comes out as it would from posting one by one.
Kernels that make rows (a stock slot, a purpose flow, an edge-goods row) take the room the caller reserved first
(`KeyedRows.reserve`); running out is a caller bug and answers TABLE_FULL."""
from sim.book_index import EMPTY, index_add, index_find, pack_key, unpack_key
from sim.book_tables import FREE, TABLE_FULL
from sim.compiled_tables.causes import OK
from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.jit import njit


@njit(inline="always")
def commit_money(plan, balances, agents):
    """Write every planned balance, mark it seen, and mark its agent known."""
    keys, holders, after = plan.key, plan.holder, plan.after
    amounts, seen, known = balances.amount, balances.seen, agents.known
    for row in range(plan.row_count[0]):
        cell = keys[row]
        amounts[cell] = after[row]
        seen[cell] = 1
        known[holders[row]] = 1


@njit
def create_slot(stocks, stock_index, agents, key):
    """A new stock slot for the packed key at zero, indexed and chained at the end of its agent's slots; NO_ROOM if full."""
    slot = claim_row(stocks)
    if slot == NO_ROOM:
        return NO_ROOM
    agent, good, tile = unpack_key(key)
    stocks.key[slot] = key
    stocks.agent[slot] = agent
    stocks.good[slot] = good
    stocks.tile[slot] = tile
    stocks.quantity[slot] = 0.0
    stocks.next_in_agent[slot] = FREE
    stocks.live[slot] = 1
    index_add(stocks.key, stock_index, slot)
    last = agents.last_slot[agent]
    if last == FREE:
        agents.first_slot[agent] = slot
    else:
        stocks.next_in_agent[last] = slot
    agents.last_slot[agent] = slot
    return slot


@njit(inline="always")
def commit_stock(plan, stocks, stock_index, agents):
    """Write every planned stock quantity, making the slots that do not exist yet in plan order, and mark the agent known.
    Returns OK or TABLE_FULL. The columns are held in hand; a table is passed on whole only to make a slot."""
    keys, holders, slots, after = plan.key, plan.holder, plan.slot, plan.after
    stock_keys, quantity, known = stocks.key, stocks.quantity, agents.known
    for row in range(plan.row_count[0]):
        slot = slots[row]
        if slot == FREE:
            slot = index_find(stock_keys, stock_index, keys[row])
        if slot == FREE:
            slot = create_slot(stocks, stock_index, agents, keys[row])
            if slot == NO_ROOM:
                return TABLE_FULL
        quantity[slot] = after[row]
        known[holders[row]] = 1
    return OK


@njit
def record_edge_money(balances, cell, volume, net):
    """Add to the edge cell's year volume and net; the first record sets them (so a first net of -0.0 stays -0.0)."""
    if balances.edge_seen[cell] == 0:
        balances.edge_seen[cell] = 1
        balances.edge_volume[cell] = volume
        balances.edge_net[cell] = net
    else:
        balances.edge_volume[cell] += volume
        balances.edge_net[cell] += net


@njit
def record_edge_goods(edge_goods, edge_index, agent, good, volume, net):
    """record_edge_money for an edge account's goods: the (agent, good) row is made at first sight. OK or TABLE_FULL."""
    key = pack_key(agent, good)
    row = index_find(edge_goods.key, edge_index, key)
    if row == EMPTY:
        row = claim_row(edge_goods)
        if row == NO_ROOM:
            return TABLE_FULL
        edge_goods.key[row] = key
        edge_goods.agent[row] = agent
        edge_goods.good[row] = good
        edge_goods.volume[row] = volume
        edge_goods.net[row] = net
        edge_goods.live[row] = 1
        index_add(edge_goods.key, edge_index, row)
    else:
        edge_goods.volume[row] += volume
        edge_goods.net[row] += net
    return OK


@njit
def add_flow(flows, flow_index, good, purpose_code, purpose_reference, quantity):
    """Add to this year's quantity of the good moved for the purpose; the row is made at first sight. OK or TABLE_FULL."""
    key = pack_key(good, purpose_code, purpose_reference)
    row = index_find(flows.key, flow_index, key)
    if row == EMPTY:
        row = claim_row(flows)
        if row == NO_ROOM:
            return TABLE_FULL
        flows.key[row] = key
        flows.good[row] = good
        flows.purpose_code[row] = purpose_code
        flows.purpose_reference[row] = purpose_reference
        flows.quantity[row] = 0.0 + quantity
        flows.live[row] = 1
        index_add(flows.key, flow_index, row)
    else:
        flows.quantity[row] += quantity
    return OK


@njit
def gross_so_far(total, seen):
    """The total a gross column holds: zero until something has been recorded."""
    return total if seen != 0 else 0.0


@njit(inline="always")
def record_transfers(transfers, first, last, money):
    """The records of transfer postings first .. last - 1: the currency's gross total, and the edge payer's and payee's year
    volume and net."""
    for row in range(first, last):
        amount, currency = transfers.amount[row], transfers.currency[row]
        gross = gross_so_far(money.currencies.gross_posted[currency], money.currencies.gross_seen[currency])
        money.currencies.gross_posted[currency] = gross + amount
        money.currencies.gross_seen[currency] = 1
        payer, payee = transfers.payer[row], transfers.payee[row]
        if money.agents.is_edge[payer] != 0:
            record_edge_money(money.balances, payer * money.stride + currency, amount, amount)
        if money.agents.is_edge[payee] != 0:
            record_edge_money(money.balances, payee * money.stride + currency, amount, -amount)


@njit(inline="always")
def record_moves(moves, first, last, goods):
    """The records of goods-move postings first .. last - 1, in order: the good's gross total, the purpose flow, the edge giver's
    and receiver's goods. OK or TABLE_FULL. The columns are held in hand and a table is passed on whole only to make a row: a kernel
    that passes a table to a call for each posting copies and counts every column each time."""
    gross_moved, gross_seen = goods.goods.gross_moved, goods.goods.gross_seen
    flow_keys, flow_quantity = goods.flows.key, goods.flows.quantity
    flow_index, is_edge = goods.flow_index, goods.agents.is_edge
    edge_keys, edge_volume, edge_net = goods.edge_goods.key, goods.edge_goods.volume, goods.edge_goods.net
    edge_index = goods.edge_index
    for row in range(first, last):
        giver, receiver, good, quantity = moves.giver[row], moves.receiver[row], moves.good[row], moves.quantity[row]
        gross = gross_so_far(gross_moved[good], gross_seen[good])
        gross_moved[good] = gross + quantity
        gross_seen[good] = 1
        flow = index_find(flow_keys, flow_index, pack_key(good, moves.purpose_code[row], moves.purpose_reference[row]))
        if flow == EMPTY:
            code = add_flow(goods.flows, flow_index, good, moves.purpose_code[row], moves.purpose_reference[row], quantity)
            if code != OK:
                return code
        else:
            flow_quantity[flow] += quantity
        for edge_agent, edge_net_delta in ((giver, quantity), (receiver, -quantity)):
            if is_edge[edge_agent] != 0:
                edge = index_find(edge_keys, edge_index, pack_key(edge_agent, good))
                if edge == EMPTY:
                    code = record_edge_goods(goods.edge_goods, edge_index, edge_agent, good, quantity, edge_net_delta)
                    if code != OK:
                        return code
                else:
                    edge_volume[edge] += quantity
                    edge_net[edge] += edge_net_delta
    return OK


@njit
def record_settled_money(agents_in, paid, received, currency, money):
    """The edge records of a summed settlement: each edge agent with something paid or received gets volume paid + received
    and net paid - received."""
    is_edge, stride = money.agents.is_edge, money.stride
    for position in range(len(agents_in)):
        if (paid[position] != 0.0 or received[position] != 0.0) and is_edge[agents_in[position]] != 0:
            record_edge_money(money.balances, agents_in[position] * stride + currency,
                              paid[position] + received[position], paid[position] - received[position])


@njit
def record_settled_stock(holders, good, given, taken, goods):
    """record_settled_money for one good's stock cells. OK or TABLE_FULL."""
    is_edge = goods.agents.is_edge
    for position in range(len(holders)):
        if (given[position] != 0.0 or taken[position] != 0.0) and is_edge[holders[position]] != 0:
            code = record_edge_goods(goods.edge_goods, goods.edge_index, holders[position], good,
                                     given[position] + taken[position], given[position] - taken[position])
            if code != OK:
                return code
    return OK
