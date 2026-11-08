"""Whole-table reads of the book, for a converter that holds ids: many balances, many stocks, one agent's holdings, totals.

An agent, tile or good number below zero stands for a name the book never saw; every read of it answers zero (or no slot),
because a missing holding is nothing held. None of these changes the book."""
import numpy

from sim.book_index import EMPTY, index_find, pack_key
from sim.book_tables import FREE
from sim.jit import njit


@njit
def read_balances(balances, stride, agent_numbers, currency):
    """Each agent's balance in the currency (agent number -1 or currency -1 reads zero)."""
    found = numpy.zeros(len(agent_numbers))
    if currency < 0:
        return found
    for position in range(len(agent_numbers)):
        if agent_numbers[position] >= 0:
            found[position] = balances.amount[agent_numbers[position] * stride + currency]
    return found


@njit
def find_slots(stocks, stock_index, agent_numbers, good, tile_numbers):
    """Each (agent, tile)'s stock slot for the good, -1 where nothing was ever held (or a number is -1)."""
    slots = numpy.full(len(agent_numbers), EMPTY, dtype=numpy.int64)
    if good < 0:
        return slots
    for position in range(len(agent_numbers)):
        if agent_numbers[position] >= 0 and tile_numbers[position] >= 0:
            slots[position] = index_find(stocks.key, stock_index, pack_key(agent_numbers[position], good, tile_numbers[position]))
    return slots


@njit
def read_stocks_at(stocks, slots):
    """The quantity in each slot (slot -1 reads zero)."""
    found = numpy.zeros(len(slots))
    for position in range(len(slots)):
        if slots[position] >= 0:
            found[position] = stocks.quantity[slots[position]]
    return found


@njit
def holder_slots(first_slot, next_in_agent):
    """The stock slots of one agent (its `first_slot`) in the order they were made."""
    count = 0
    slot = first_slot
    while slot != FREE:
        count += 1
        slot = next_in_agent[slot]
    slots = numpy.empty(count, dtype=numpy.int64)
    slot = first_slot
    for position in range(count):
        slots[position] = slot
        slot = next_in_agent[slot]
    return slots


@njit
def holder_columns(first_slot, next_in_agent, good, tile, quantity):
    """(good numbers, tile numbers, quantities) of one agent's stock slots, in the order they were made."""
    slots = holder_slots(first_slot, next_in_agent)
    return good[slots], tile[slots], quantity[slots]


@njit
def counted_stocks(stocks, agents):
    """(good numbers, quantities) of every live nonzero stock slot held by an agent that is not an edge account, in slot order."""
    count = 0
    for slot in range(stocks.row_count[0]):
        if stocks.live[slot] != 0 and stocks.quantity[slot] != 0.0 and agents.is_edge[stocks.agent[slot]] == 0:
            count += 1
    goods = numpy.empty(count, dtype=numpy.int64)
    quantities = numpy.empty(count)
    position = 0
    for slot in range(stocks.row_count[0]):
        if stocks.live[slot] != 0 and stocks.quantity[slot] != 0.0 and agents.is_edge[stocks.agent[slot]] == 0:
            goods[position] = stocks.good[slot]
            quantities[position] = stocks.quantity[slot]
            position += 1
    return goods, quantities


@njit
def currency_values(balances, stride, currency, agents, include_edges):
    """The currency's balance of every agent number (edge accounts only when include_edges), in agent number order."""
    count = 0
    for agent in range(agents.row_count[0]):
        if include_edges or agents.is_edge[agent] == 0:
            count += 1
    values = numpy.empty(count)
    position = 0
    for agent in range(agents.row_count[0]):
        if include_edges or agents.is_edge[agent] == 0:
            values[position] = balances.amount[agent * stride + currency]
            position += 1
    return values


@njit
def good_quantities(stocks, good):
    """The quantity in every live slot of the good, in slot order."""
    count = 0
    for slot in range(stocks.row_count[0]):
        if stocks.live[slot] != 0 and stocks.good[slot] == good:
            count += 1
    quantities = numpy.empty(count)
    position = 0
    for slot in range(stocks.row_count[0]):
        if stocks.live[slot] != 0 and stocks.good[slot] == good:
            quantities[position] = stocks.quantity[slot]
            position += 1
    return quantities
