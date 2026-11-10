"""A year's labour markets settled on the book in one kernel call.

Each market (in the order given) is settled on the balances the earlier ones left, exactly as `Book.post_settled` applied one
market's summed settlement after another: the pairs go through `settlement_kernel.settle_pairs` (a payer is limited to the money
it holds, an edge account is not), the per-agent sums are applied with `book_apply.apply_settled`, and the currency's gross
total grows by the exact sum of what was paid. Nothing here makes an object per market.
"""
import numpy

from sim.book_apply import apply_settled
from sim.book_commit import gross_so_far
from sim.compiled_tables.causes import OK
from sim.jit import njit

from .settlement_kernel import settle_pairs
from .year_ledger_note_kernels import exact_sum


@njit
def settle_wage_markets(book, scratch, currency, good, agent_start, agent_book, pair_start, pair_buyer_agent, pair_seller_agent,
                        pair_quantity, wage):
    """Settle market `m` (pairs `pair_start[m]:pair_start[m + 1]`, agents `agent_start[m]:agent_start[m + 1]` as book numbers
    in `agent_book`; a pair's buyer and seller are positions among the market's agents) at its one `wage`, and apply it to the
    book. `good` is the number the book gave the trade, which no stock moves in. Returns (paid, received, imports, exports,
    failed_market, cause, culprit): the money each listed agent paid and received and the foreign-money figures of the ledger,
    all per agent in the order of `agent_book`; and, if the book refused a market (an overdraft beyond rounding), its number
    (else -1), the cause and the cell, with that market's figures given but it and the ones after not applied."""
    markets = len(pair_start) - 1
    total = len(agent_book)
    paid = numpy.zeros(total)
    received = numpy.zeros(total)
    imports = numpy.zeros(total)
    exports = numpy.zeros(total)
    no_holders = numpy.zeros(0, dtype=numpy.int64)
    no_goods = numpy.zeros(0)
    agents_table = book.money.agents
    for market in range(markets):
        first_pair, last_pair = pair_start[market], pair_start[market + 1]
        if first_pair == last_pair:
            continue
        first, last = agent_start[market], agent_start[market + 1]
        count = last - first
        here = agent_book[first:last]
        cash = numpy.zeros(count)
        edge = numpy.zeros(count, dtype=numpy.bool_)
        mint = numpy.zeros(count, dtype=numpy.bool_)
        external = numpy.zeros(count, dtype=numpy.bool_)
        for place in range(count):
            agent = here[place]
            cash[place] = book.money.balances.amount[agent * book.money.stride + currency]
            edge[place] = agents_table.is_edge[agent] != 0
            mint[place] = agents_table.is_mint[agent] != 0
            external[place] = agents_table.is_external[agent] != 0
        asks = numpy.full(last_pair - first_pair, wage[market])
        _goods, _money, _payer, market_paid, market_received, _in, _out, _net, _got, _as_buyer, market_imports, market_exports, \
            _given, _taken, _to_mint = settle_pairs(
                pair_buyer_agent[first_pair:last_pair], pair_seller_agent[first_pair:last_pair], pair_quantity[first_pair:last_pair],
                asks, False, False, numpy.arange(count), numpy.zeros(count), cash, edge, mint, external,
                numpy.zeros(count, dtype=numpy.bool_), numpy.zeros(count, dtype=numpy.bool_))
        paid[first:last] = market_paid
        received[first:last] = market_received
        cause, culprit = apply_settled(book, scratch, currency, here, market_paid, market_received, no_holders, no_holders, good,
                                       no_goods, no_goods)
        if cause != OK:
            return paid, received, imports, exports, market, cause, culprit
        currencies = book.money.currencies
        before = gross_so_far(currencies.gross_posted[currency], currencies.gross_seen[currency])
        currencies.gross_posted[currency] = before + exact_sum(market_paid, count)
        currencies.gross_seen[currency] = 1
        imports[first:last] = market_imports
        exports[first:last] = market_exports
    return paid, received, imports, exports, -1, OK, -1
