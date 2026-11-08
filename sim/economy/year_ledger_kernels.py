"""Kernels that add into the year ledger's tables: a figure of one agent, a row of a pair table (the settlement, labour and round
kernels built on them are in year_ledger_note_kernels.py).

Every kernel adds in the order the old dict code did (one add per input row, left to right), so a figure and the order its
keys first appeared are what the dicts held. A kernel never grows a table: the caller (`year_ledger_store.py`) reserves room
for as many new rows or agents as the call can add. `add_pair` answers -1 when the table is full, which a caller that reserved
correctly never sees."""
from sim.book_index import EMPTY, index_add, index_find, pack_key
from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.economy.year_ledger_tables import MEMBERS, NEXT_ENTRY
from sim.jit import njit


# ---- figures of one agent or market ------------------------------------------------------------------------------------

@njit
def touch(orders, counters, figure, slot):
    """Make the slot a member of the figure if it is not (it takes the next entry number). Returns whether it was new."""
    if orders[slot] != 0:
        return False
    number = counters[2 * figure + NEXT_ENTRY] + 1
    counters[2 * figure + NEXT_ENTRY] = number
    counters[2 * figure + MEMBERS] += 1
    orders[slot] = number
    return True


@njit
def add_to_figure(values, orders, counters, figure, slot, amount):
    """`dict[slot] = dict.get(slot, 0.0) + amount`: the slot becomes a member (starting from zero) and takes the amount."""
    if touch(orders, counters, figure, slot):
        values[slot] = 0.0
    values[slot] += amount


@njit
def set_figure(values, orders, counters, figure, slot, amount):
    """`dict[slot] = amount`: the slot becomes a member (keeping its place if it was one) holding exactly the amount."""
    touch(orders, counters, figure, slot)
    values[slot] = amount


@njit
def remove_from_figure(orders, counters, figure, slot):
    """Take the slot out of the figure (a no-op when it is not a member)."""
    if orders[slot] != 0:
        orders[slot] = 0
        counters[2 * figure + MEMBERS] -= 1


@njit
def add_agent_amounts(values, orders, counters, figure, agents, amounts, positive_only):
    """`add_to_figure` for each (agent, amount) in order; with `positive_only`, amounts that are not above zero are skipped."""
    for i in range(len(agents)):
        if amounts[i] > 0.0 or not positive_only:
            add_to_figure(values, orders, counters, figure, agents[i], amounts[i])


# ---- rows of a pair table -----------------------------------------------------------------------------------------------

@njit
def find_pair(target, agent, subkey, extra):
    """The live row for (agent, subkey, extra), or EMPTY."""
    return index_find(target.rows.key, target.hash_index, pack_key(agent, subkey, extra))


@njit
def _link_row(target, agent, row):
    """Append the row to the agent's chain and make the agent a member of the figure its rows belong to."""
    touch(target.orders, target.counters, target.figure, agent)
    last = target.lasts[agent]
    if last == 0:
        target.firsts[agent] = row + 1
    else:
        target.rows.next_in_agent[last - 1] = row + 1
    target.lasts[agent] = row + 1


@njit
def new_pair(target, agent, subkey, extra):
    """A new, zeroed, live row for the key (which must be absent), indexed and chained; NO_ROOM when the table is full."""
    row = claim_row(target.rows)
    if row == NO_ROOM:
        return NO_ROOM
    key = pack_key(agent, subkey, extra)
    target.rows.key[row] = key
    target.rows.agent[row] = agent
    target.rows.subkey[row] = subkey
    target.rows.extra[row] = extra
    target.rows.amount[row] = 0.0
    target.rows.second_amount[row] = 0.0
    target.rows.next_in_agent[row] = 0
    target.rows.live[row] = 1
    index_add(target.rows.key, target.hash_index, row)
    if target.chained:
        _link_row(target, agent, row)
    return row


@njit
def add_pair(target, agent, subkey, extra, amount, second_amount):
    """`dict[key] = dict.get(key, 0.0) + amount` (and the same for the second figure). Returns the row, or -1 when full."""
    row = find_pair(target, agent, subkey, extra)
    if row == EMPTY:
        row = new_pair(target, agent, subkey, extra)
        if row == NO_ROOM:
            return -1
    target.rows.amount[row] += amount
    target.rows.second_amount[row] += second_amount
    return row


@njit
def set_pair(target, agent, subkey, extra, amount, second_amount):
    """`dict[key] = amount`: the row is made if it is absent and holds exactly the figures. Returns the row, or -1 when full."""
    row = find_pair(target, agent, subkey, extra)
    if row == EMPTY:
        row = new_pair(target, agent, subkey, extra)
        if row == NO_ROOM:
            return -1
    target.rows.amount[row] = amount
    target.rows.second_amount[row] = second_amount
    return row


@njit
def kill_row(target, row):
    """The row stops being a member: nothing finds it again (its index entry stays, pointing at a key nothing matches)."""
    target.rows.key[row] = -1
    target.rows.live[row] = 0


@njit
def clear_agent_rows(target, agent):
    """Remove every row of the agent in a chained table, leaving the agent a member with no rows (`dict[agent] = {}`)."""
    link = target.firsts[agent]
    while link != 0:
        row = link - 1
        link = target.rows.next_in_agent[row]
        kill_row(target, row)
    target.firsts[agent] = 0
    target.lasts[agent] = 0


@njit
def add_pairs(target, agents, subkeys, extras, amounts, second_amounts, positive_only):
    """`add_pair` for each input in order; with `positive_only`, amounts that are not above zero are skipped."""
    for i in range(len(agents)):
        if amounts[i] > 0.0 or not positive_only:
            add_pair(target, agents[i], subkeys[i], extras[i], amounts[i], second_amounts[i])
