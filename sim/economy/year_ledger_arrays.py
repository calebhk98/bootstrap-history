"""Adding whole arrays into the year ledger's tables: the entry points a converted caller uses.

Every function takes the `LedgerTables` and arrays of numbers (agents, goods, trades, markets and purposes numbered as the book
and the market memory number them), reserves the room the call can need, and runs one kernel. Arrays are aligned row for row;
a row is one agent in one settlement, one fill, or one cleared round. Rows are added in order, so a call holding many
settlements gives the figures and the entry order that settling them one at a time gave. Types: whole numbers int64, quantities
float64, flags bool_ (a kernel compiles one version per type, so pass exactly these).

Nothing here looks at the pending notes (`year_ledger_batch.py`): the ledger flushes them before it calls in."""
import numpy

from .year_ledger_kernels import (add_agent_amounts, add_pairs, add_rounds, note_labour_fills, note_settlement_foreign,
                                  note_settlement_goods, note_settlement_money)
from .year_ledger_tables import MONEY_OUT, SALES_IN, SALES_PURPOSE, WAGES_IN

NO_FLOATS = numpy.zeros(0)
NO_FLAGS = numpy.zeros(0, dtype=numpy.bool_)
NO_WHOLES = numpy.zeros(0, dtype=numpy.int64)


def add_money_out(tables, agents, amounts, positive_only: bool = False) -> None:
    """Each amount added to its agent's `money_out`, in order; with `positive_only`, amounts not above zero are skipped."""
    figures = tables.figures
    add_agent_amounts(figures.money_out, figures.order_money_out, tables.counters, MONEY_OUT, agents, amounts, positive_only)


def add_income(tables, wages: bool, agents, amounts) -> None:
    """Each amount added to its agent's `wages_in` (or, not `wages`, `sales_in`), in order."""
    figures = tables.figures
    if wages:
        add_agent_amounts(figures.wages_in, figures.order_wages_in, tables.counters, WAGES_IN, agents, amounts, False)
    else:
        add_agent_amounts(figures.sales_in, figures.order_sales_in, tables.counters, SALES_IN, agents, amounts, False)


def add_pair_amounts(tables, name: str, agents, subkeys, amounts, extras=NO_WHOLES, positive_only: bool = False) -> None:
    """Each amount added to the row of (agent, subkey) in the pair table `name` (`received`, `sold`, `output`, `grown`, ...), in
    order. A subkey is a good number, or for the foreign-money tables a purpose template with `extras` its reference."""
    if not len(agents):
        return
    store = tables.pairs[name]
    store.reserve(len(agents))
    add_pairs(store.target(), agents, subkeys, extras if len(extras) else numpy.zeros(len(agents), dtype=numpy.int64), amounts,
              numpy.zeros(len(agents)), positive_only)


def note_settlement_rows(tables, agents, paid, received, imports, exports, got_goods, goods_in, goods_out, purpose_kind, good,
                         template, reference, plant_bought) -> None:
    """Rows of settlements: per row the agent, money paid and received, goods in and out, whether it got goods, money across the
    border, the settlement's purpose kind (`OTHER_PURPOSE`, `WAGES_PURPOSE`, `SALES_PURPOSE`), the good sold, the purpose's
    (template, reference) for the foreign-money figures, and whether the payment was for goods the payer's plant is built from."""
    note_settlement_money(tables.figures, tables.counters, agents, paid, received, plant_bought, purpose_kind)
    if (purpose_kind == SALES_PURPOSE).any():
        tables.pairs["received"].reserve(len(agents))
        tables.pairs["sold"].reserve(len(agents))
        note_settlement_goods(tables.pairs["received"].target(), tables.pairs["sold"].target(), agents, got_goods, goods_in,
                              goods_out, good, purpose_kind)
    if imports.any() or exports.any():
        tables.pairs["imports_paid"].reserve(len(agents))
        tables.pairs["exports_received"].reserve(len(agents))
        note_settlement_foreign(tables.pairs["imports_paid"].target(), tables.pairs["exports_received"].target(), agents, imports,
                                exports, template, reference)


def note_hours_rows(tables, fill_agent, fill_slot, fill_quantity, fill_price, fill_is_buy, fill_trade, fill_market, fill_wage,
                    fill_settled, paid_by_slot, paid_to_slot) -> None:
    """Rows of labour fills: per row the agent, its slot among the market's distinct agents, hours, price, side, the trade and
    labour market (numbers of the market memory), the market's wage, and whether the hours count only as far as wages paid cover
    them (then `paid_by_slot` and `paid_to_slot` hold what each slot's agent paid or was paid, and are used up)."""
    tables.pairs["hours_hired"].reserve(len(fill_agent))
    tables.pairs["hours_hired_by_market"].reserve(len(fill_agent))
    note_labour_fills(tables.figures, tables.counters, tables.pairs["hours_hired"].target(),
                      tables.pairs["hours_hired_by_market"].target(), fill_agent, fill_slot, fill_quantity, fill_price, fill_is_buy,
                      fill_trade, fill_market, fill_wage, fill_settled, paid_by_slot, paid_to_slot)


def note_round_rows(tables, markets, quantities, prices, moved) -> None:
    """Cleared rounds in order: per round its goods market (a number in the market memory), the quantity it matched, its price
    (NaN for none) and the goods its settlement moved."""
    tables.fit_markets()
    tables.reserve_rounds(len(markets))
    add_rounds(tables.rounds, tables.market_figures.delivered, tables.market_figures.order_delivered, tables.market_counters,
               markets, quantities, prices, moved)
