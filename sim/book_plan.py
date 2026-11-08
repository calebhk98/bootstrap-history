"""Planning a batch: which cells it touches and what each would hold after it, before anything is written.

A plan is a `Plans` table (sim/book_tables.py) with one row per distinct cell, in the order the batch first touches it, and a
hash index of its own over the cells. A batch is refused when its plan overdraws a cell that may not go negative; nothing in
the book has changed by then, so a refused batch leaves no trace.

The rules (the book's present ones): an amount must not be negative; a cell that is not an edge account's must not end below
what it held before (or below zero if it held more) by more than a rounding share of what moved through it, floored at the
smallest normal float, so a residue an earlier, larger batch was allowed to leave is not this batch's doing."""
from sim.book_index import EMPTY, index_find, pack_key, start_position
from sim.book_tables import FREE, NEGATIVE_AMOUNT, NEGATIVE_QUANTITY
from sim.book_types import ROUNDING_SHARE, UNDERFLOW
from sim.compiled_tables.causes import OK
from sim.jit import njit


@njit
def clear_plan(plan, local_index):
    """Forget the plan's cells (and their places in the plan's own index) so it can take the next batch."""
    for row in range(plan.row_count[0]):
        local_index[plan.position[row]] = EMPTY
    plan.row_count[0] = 0


@njit
def touch(plan, local_index, key, holder):
    """The plan row for the cell, made (at row_count) when the batch has not touched it yet. Returns (row, is_new); a new
    row has only key and holder set. The plan has room for every touch the caller will make."""
    position = start_position(key, len(local_index))
    mask = len(local_index) - 1
    while True:
        row = local_index[position]
        if row == EMPTY:
            row = plan.row_count[0]
            plan.row_count[0] = row + 1
            plan.key[row] = key
            plan.holder[row] = holder
            plan.slot[row] = FREE
            plan.failing[row] = 0
            plan.position[row] = position
            local_index[position] = row
            return row, True
        if plan.key[row] == key:
            return row, False
        position = (position + 1) & mask


@njit
def add_to_cell(plan, local_index, key, holder, held, amount, receives):
    """Move amount into the cell (receives) or out of it; `held` is what the cell holds now. The first touch starts from
    `held`, later ones continue from the plan's running value, so repeated postings add in posting order."""
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


@njit
def plan_transfers(transfers, first, last, balances, stride, plan, local_index):
    """Plan transfer postings first .. last - 1 as one batch over balance cells. Returns (OK, 0), or (NEGATIVE_AMOUNT, the
    posting row) at the first negative amount, which is checked before any overdraft."""
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


@njit
def held_in_slot(stocks, slot):
    """What the stock slot holds; zero when the cell has no slot yet."""
    return 0.0 if slot == FREE else stocks.quantity[slot]


@njit
def add_to_stock(plan, local_index, stocks, stock_index, agent, good, tile, amount, receives):
    """add_to_cell for the stock cell (agent, good, tile), looking up its slot when the batch first touches it."""
    key = pack_key(agent, good, tile)
    row, is_new = touch(plan, local_index, key, agent)
    if is_new:
        slot = index_find(stocks.key, stock_index, key)
        plan.slot[row] = slot
        plan.before[row] = held_in_slot(stocks, slot)
        plan.after[row] = plan.before[row]
        plan.moved[row] = amount
    else:
        plan.moved[row] += amount
    if receives:
        plan.after[row] += amount
    else:
        plan.after[row] -= amount
    return row


@njit
def plan_moves(moves, first, last, stocks, stock_index, plan, local_index):
    """Plan goods-move postings first .. last - 1 as one batch over stock cells. Returns (OK, 0), or (NEGATIVE_QUANTITY, the
    posting row)."""
    for row in range(first, last):
        quantity = moves.quantity[row]
        if not quantity >= 0.0:
            return NEGATIVE_QUANTITY, row
        good = moves.good[row]
        add_to_stock(plan, local_index, stocks, stock_index, moves.giver[row], good, moves.tile[row], quantity, False)
        add_to_stock(plan, local_index, stocks, stock_index, moves.receiver[row], good, moves.receiver_tile[row], quantity, True)
    return OK, 0


@njit
def plan_settled_money(agents_in, paid, received, currency, stride, balances, plan):
    """Plan a market's summed settlement: for every position where something was paid or received, the agent's balance
    less what it paid plus what it received (in that order). One plan row per position, no merging, none for a position
    with nothing. Returns the number of plan rows."""
    for position in range(len(agents_in)):
        if paid[position] == 0.0 and received[position] == 0.0:
            continue
        agent = agents_in[position]
        cell = agent * stride + currency
        row = plan.row_count[0]
        plan.row_count[0] = row + 1
        plan.key[row] = cell
        plan.holder[row] = agent
        plan.slot[row] = FREE
        plan.failing[row] = 0
        plan.before[row] = balances.amount[cell]
        plan.after[row] = balances.amount[cell] - paid[position] + received[position]
        plan.moved[row] = paid[position] + received[position]
    return plan.row_count[0]


@njit
def plan_settled_stock(holders, tiles, good, given, taken, stocks, stock_index, plan):
    """plan_settled_money for one good's stock cells (holder, tile): less what was given plus what was taken. Returns the
    number of plan rows."""
    for position in range(len(holders)):
        if given[position] == 0.0 and taken[position] == 0.0:
            continue
        key = pack_key(holders[position], good, tiles[position])
        row = plan.row_count[0]
        plan.row_count[0] = row + 1
        plan.key[row] = key
        plan.holder[row] = holders[position]
        plan.slot[row] = index_find(stocks.key, stock_index, key)
        plan.failing[row] = 0
        plan.before[row] = held_in_slot(stocks, plan.slot[row])
        plan.after[row] = plan.before[row] - given[position] + taken[position]
        plan.moved[row] = given[position] + taken[position]
    return plan.row_count[0]


@njit
def overdrawn(before, after, moved):
    """Whether a cell that may not go negative would be overdrawn by the batch beyond rounding."""
    return after < min(0.0, before) - max(ROUNDING_SHARE * moved, UNDERFLOW)


@njit
def mark_overdrafts(plan, agents):
    """Set `failing` on every planned cell of an agent that is not an edge account and would be overdrawn. Returns how many."""
    count = 0
    for row in range(plan.row_count[0]):
        failing = agents.is_edge[plan.holder[row]] == 0 and overdrawn(plan.before[row], plan.after[row], plan.moved[row])
        plan.failing[row] = 1 if failing else 0
        count += 1 if failing else 0
    return count


@njit
def first_failing_cell(plan):
    """The cell of the first planned row marked failing, or -1."""
    for row in range(plan.row_count[0]):
        if plan.failing[row] != 0:
            return plan.key[row]
    return -1


@njit
def check_batch(plan, agents, cause):
    """(OK, 0) when no planned cell is overdrawn, else (cause, the first overdrawn cell)."""
    if mark_overdrafts(plan, agents) == 0:
        return OK, 0
    return cause, first_failing_cell(plan)


@njit
def check_one_payer(plan, agents, amount, cause):
    """The rule for a single posting made on its own: its payer (the plan's first cell), unless an edge account, must hold at
    least the amount less a rounding share. (OK, 0) or (cause, the payer's cell). The payer's row is marked failing."""
    if plan.row_count[0] == 0:
        return OK, 0
    if agents.is_edge[plan.holder[0]] == 0 and plan.before[0] < amount * (1.0 - ROUNDING_SHARE):
        plan.failing[0] = 1
        return cause, plan.key[0]
    return OK, 0
