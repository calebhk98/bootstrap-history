"""What a producer's turn reads, in blocks: the planned runs from the plan table's column and the hours hired from the ledger's pair table.

    planned_runs      the runs planned for each producer of the turn (None where a producer has no plan), read from `PlanTable.runs` by position
    pair_amounts      `amount` of the ledger pair row (agent number, subkey number) of each request, 0.0 where the pair has no row
    hours_hired_of    per producer, the hours it hired this year of each trade it asks about, one `pair_amounts` call for all of them
"""
from typing import Dict, List, Sequence

import numpy

from sim.book_index import EMPTY, index_find, pack_key
from sim.jit import njit


@njit
def pair_amounts(pair_rows, pair_index, agent_numbers, subkeys):
    """The amount of the pair row (agent, subkey, 0) for each request; 0.0 where the pair has no row or a number is -1 (a name the
    numbering never met)."""
    found = numpy.zeros(len(agent_numbers))
    for place in range(len(agent_numbers)):
        if agent_numbers[place] >= 0 and subkeys[place] >= 0:
            position = index_find(pair_rows.key, pair_index, pack_key(agent_numbers[place], subkeys[place], 0))
            if position != EMPTY:
                found[place] = 0.0 + pair_rows.amount[position]
    return found


def planned_runs(plans, producer_ids: Sequence[str]) -> List:
    """The runs planned for each producer, None for one with no plan. A `PlanTable` is read through its runs column; any other mapping
    of producer to plan (a test's) through `get`."""
    columns = getattr(plans, "runs", None)
    if columns is None:
        return [None if (plan := plans.get(producer_id)) is None else plan.runs for producer_id in producer_ids]
    position = plans.position
    return [None if (place := position.get(producer_id)) is None else columns[place] for producer_id in producer_ids]


def hours_hired_of(ledger, requests: Sequence[tuple]) -> List[Dict[str, float]]:
    """For each request (producer id, trades), the producer's hired hours by trade as `ledger.hours_hired.get(producer, {})` gives them,
    with a trade nothing was hired in as 0.0. The ledger's pending notes are added first; no name is numbered."""
    tables = ledger.tables
    tables.flush()
    agents = tables.book.agent_ids.numbers
    trades = tables.markets.trades.numbers
    agent_column, trade_column, sizes = [], [], []
    for producer_id, wanted in requests:
        agent = agents.get(producer_id, -1)
        for trade in wanted:
            agent_column.append(agent)
            trade_column.append(trades.get(trade, -1))
        sizes.append(len(wanted))
    store = tables.pairs["hours_hired"]
    amounts = iter(pair_amounts(store.rows.table, store.rows.index, numpy.array(agent_column, dtype=numpy.int64),
                                numpy.array(trade_column, dtype=numpy.int64)).tolist()) if agent_column else iter(())
    return [{trade: next(amounts) for trade in wanted} for _producer_id, wanted in requests]
