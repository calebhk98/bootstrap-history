"""The ledger's columns for a good's settled markets in one kernel call (`goods_settle._noted_by_ids` hands them to
`YearLedger.note_settlement_rows`): per listed agent the purpose, the good, the foreign-money purpose slots and whether the payment was for
goods the payer's plant is built from, and the buyers the second round of respending reads (`GoodClearing.bought`).
The plain numpy version is kept in `sim/tests/settlement_ids_plain.py`."""
import numpy

from sim.jit import njit

FOREIGN_MARKET = -1       # in `template` and `reference`: this row's market moved money across the border, its purpose slot is set by the caller


@njit
def note_columns(agent_offset, slots, agent, paid, got_goods, paid_as_buyer, buyer_net, goods_in, imports, exports, makers_sorted,
                 sales_purpose, good_number):
    """(purpose kind, good, template, reference, plant bought, any foreign, bought place, bought agent, bought units, bought money)
    for the settled markets `slots` whose listed agents are cut by `agent_offset`. `template` and `reference` are `FOREIGN_MARKET` on every row of a
    market with money across the border and zero elsewhere; `makers_sorted` are the book numbers of the producers whose plant is built from
    the good, ascending."""
    rows = agent_offset[len(agent_offset) - 1]
    purpose_kind = numpy.full(rows, sales_purpose, dtype=numpy.int64)
    good = numpy.full(rows, good_number, dtype=numpy.int64)
    template = numpy.zeros(rows, dtype=numpy.int64)
    reference = numpy.zeros(rows, dtype=numpy.int64)
    plant_bought = numpy.zeros(rows, dtype=numpy.bool_)
    found = 0
    any_foreign = False
    for market in range(len(agent_offset) - 1):
        first, last = agent_offset[market], agent_offset[market + 1]
        foreign = False
        for row in range(first, last):
            foreign = foreign or imports[row] != 0.0 or exports[row] != 0.0
            if got_goods[row] or paid_as_buyer[row]:
                found += 1
            if paid[row] > 0.0 and got_goods[row] and len(makers_sorted) > 0:
                at = numpy.searchsorted(makers_sorted, agent[row])
                plant_bought[row] = at < len(makers_sorted) and makers_sorted[at] == agent[row]
        if foreign:
            any_foreign = True
            template[first:last] = FOREIGN_MARKET
            reference[first:last] = FOREIGN_MARKET
    bought_place = numpy.zeros(found, dtype=numpy.int64)
    bought_agent = numpy.zeros(found, dtype=numpy.int64)
    bought_units = numpy.zeros(found)
    bought_money = numpy.zeros(found)
    at = 0
    for market in range(len(agent_offset) - 1):
        for row in range(agent_offset[market], agent_offset[market + 1]):
            if got_goods[row] or paid_as_buyer[row]:
                bought_place[at] = slots[market]
                bought_agent[at] = agent[row]
                bought_units[at] = goods_in[row]
                bought_money[at] = buyer_net[row] if paid_as_buyer[row] else 0.0
                at += 1
    return (purpose_kind, good, template, reference, plant_bought, any_foreign, bought_place, bought_agent, bought_units, bought_money)
