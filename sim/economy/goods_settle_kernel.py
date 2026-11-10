"""A good's traded markets settled, applied on the book and noted in the year ledger in one kernel call.

`settle_good_markets` does in order what `settlement_ids.settle_by_ids` and `goods_settle._noted_by_ids` do with a call each: it picks the
markets that traded, numbers the pairs' (agent, tile) keys and agents (`settlement_number_kernel.number_good`), reads the sellers' stocks and
the payers' purses, settles the markets one after another (`settlement_batch_kernel.settle_markets`), applies the sums on the book
(`book_apply.apply_settled`), adds the gross totals and the good's flow (`book_settled.record_totals` as a kernel), and notes the rows in
the ledger (`settlement_note_kernel.note_columns`, then the ledger's note kernels). Nothing is written until every check has passed: a status
other than `SETTLED` leaves the book and the ledger as they were and tells the caller (`goods_settle_one_call`) what to do.

With no customs accounts the border targets are `None` (the kernel is compiled for that apart from the other). The caller reserves room before the call (a kernel cannot grow a table); a table too small for what the call may add gives `NEEDS_ROOM` with
the counts to reserve, and a purpose the book has not numbered yet gives `NEEDS_PURPOSE`. The sums are the old path's, in its order."""
import numpy

from sim.book_apply import apply_settled
from sim.book_commit import add_flow
from sim.book_index import index_find, pack_key
from sim.book_read_kernels import read_balances, read_stocks_at
from sim.compiled_tables.causes import OK
from sim.economy.goods_clearing_kernel import TABLE_TRADED
from sim.economy.settlement_batch_kernel import settle_markets
from sim.economy.settlement_note_kernel import FOREIGN_MARKET, note_columns
from sim.economy.settlement_number_kernel import delivered_by_market, number_good
from sim.economy.year_ledger_note_kernels import exact_sum, note_settlement_foreign, note_settlement_goods, note_settlement_money
from sim.economy.year_ledger_tables import SALES_PURPOSE
from sim.jit import njit

# The status the call answers with.
SETTLED, NO_PAIRS, NOT_TRADED, NEEDS_ROOM, NEEDS_PURPOSE, REFUSED = range(6)
NO_CODE = -1       # a purpose code the book has not numbered


@njit
def _room(table, extra):
    """Whether the table has room for `extra` more rows."""
    return table.capacity[0] - table.row_count[0] >= extra


@njit
def _flag_of(numbers, agent):
    """Whether the agent number is among `numbers` (the few customs accounts)."""
    for each in numbers:
        if each == agent:
            return True
    return False


@njit
def _picked(quantity, way):
    """(the markets that traded, whether every one of them traded in the batch)."""
    count = 0
    for place in range(len(quantity)):
        if quantity[place] > 0.0:
            count += 1
    positions = numpy.zeros(count, dtype=numpy.int64)
    at = 0
    all_traded = True
    for place in range(len(quantity)):
        if quantity[place] > 0.0:
            positions[at] = place
            at += 1
            all_traded = all_traded and way[place] == TABLE_TRADED
    return positions, all_traded


@njit
def _sellers_stock(stocks, stock_index, holder, tile, sold_from, good):
    """The stock each (agent, tile) key holds of the good, read for the keys some pair sells from (zero for the rest), as
    `book_read_kernels.find_slots` and `read_stocks_at` read it."""
    sells = numpy.zeros(len(holder), dtype=numpy.bool_)
    for pair in range(len(sold_from)):
        sells[sold_from[pair]] = True
    state = numpy.zeros(len(holder))
    for key in range(len(holder)):
        if sells[key] and holder[key] >= 0 and tile[key] >= 0:
            slot = index_find(stocks.key, stock_index, pack_key(holder[key], good, tile[key]))
            if slot >= 0:
                state[key] = stocks.quantity[slot]
    return state


@njit
def _agent_flags(table, agents, imports, exports):
    """Per batch agent: the edge, mint and external flags of the book and whether it is a customs account (import, export)."""
    count = len(agents)
    edge, mint, external = numpy.zeros(count, dtype=numpy.bool_), numpy.zeros(count, dtype=numpy.bool_), numpy.zeros(count, dtype=numpy.bool_)
    imported, exported = numpy.zeros(count, dtype=numpy.bool_), numpy.zeros(count, dtype=numpy.bool_)
    for place in range(count):
        edge[place] = table.is_edge[agents[place]] != 0
        mint[place] = table.is_mint[agents[place]] != 0
        external[place] = table.is_external[agents[place]] != 0
        imported[place] = _flag_of(imports, agents[place])
        exported[place] = _flag_of(exports, agents[place])
    return edge, mint, external, imported, exported


@njit
def _room_across(imports_target, exports_target, money_across, rows):
    """Whether the pair tables for money across the border have room for a settlement that moved some. With no customs accounts the
    targets are `None` and no money can cross."""
    if imports_target is None:
        return not money_across
    return not money_across or (_room(imports_target.rows, rows) and _room(exports_target.rows, rows))


@njit
def _note_across(imports_target, exports_target, money_across, agent, imports, exports, template, reference):
    """`note_settlement_foreign` when money crossed the border (the targets are `None` without customs accounts: nothing crossed)."""
    if imports_target is not None and money_across:
        note_settlement_foreign(imports_target, exports_target, agent, imports, exports, template, reference)


@njit
def _record_totals(currencies, goods, currency, good, batch_paid, batch_given, purpose_template, purpose_reference, flows, flow_index):
    """`book_settled.record_totals`: the exact sums added to the currency's and the good's gross totals, and the good's flow for the purpose."""
    before = currencies.gross_posted[currency] if currencies.gross_seen[currency] else 0.0
    currencies.gross_posted[currency] = before + exact_sum(batch_paid, len(batch_paid))
    currencies.gross_seen[currency] = 1
    moved = exact_sum(batch_given, len(batch_given))
    if moved > 0.0:
        before = goods.gross_moved[good] if goods.gross_seen[good] else 0.0
        goods.gross_moved[good] = before + moved
        goods.gross_seen[good] = 1
        add_flow(flows, flow_index, good, purpose_template, purpose_reference, moved)


@njit
def settle_good_markets(quantity, way, market_slot, pair_ptr, pair_bid, pair_offer, pair_quantity, ask, bid_rows, offer_rows, bid_buyer,
                        bid_tile, offer_seller, offer_tile, tile_stride, empty_tile, good, currency, import_numbers, export_numbers,
                        makers_sorted, purpose_template, purpose_reference, book, scratch, figures, counters, received_target, sold_target,
                        imports_target, exports_target):
    """Settle the markets of a good that traded (`quantity` above zero; `way` and `market_slot` are the good's clearing columns) from the
    batch's pair and order columns, apply them on `book`, and note them in the ledger's `figures` and pair targets. The purpose is
    (`purpose_template`, `purpose_reference`), `NO_CODE` while the book has not numbered it. `scratch` is the book's settlement plans.

    Returns (status, keys, batch agents, rows, whether money crossed the border, goods moved per market (one entry per market of the good),
    the markets that traded, agent_offset, agent, goods_in, got_goods, buyer_net, paid_as_buyer, bought place, bought agent, bought units,
    bought money, whether any key delivered to the mint, key_offset, key holder, key tile, key_to_mint); the arrays after `status` and the
    counts are empty unless the status is `SETTLED`."""
    nothing, no_floats, no_flags = numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0), numpy.zeros(0, dtype=numpy.bool_)
    delivered = numpy.zeros(len(quantity))
    agent_offset, agent, key_offset, key_holder, key_tile = nothing, nothing, nothing, nothing, nothing
    goods_in, buyer_net, key_to_mint = no_floats, no_floats, no_floats
    got_goods, paid_as_buyer = no_flags, no_flags
    bought = (nothing, nothing, no_floats, no_floats)
    status, keys, batch_agents, rows, money_across, any_to_mint = NO_PAIRS, 0, 0, 0, False, False
    foreign = False
    positions, all_traded = _picked(quantity, way)
    if len(positions) > 0:
        status = SETTLED if all_traded else NOT_TRADED
    batch_slots = market_slot[positions] if status == SETTLED else nothing
    if status == SETTLED and not (pair_ptr[batch_slots + 1] - pair_ptr[batch_slots]).any():
        status = NO_PAIRS
    if status == SETTLED:
        (pair_positions, pair_offset, agent_offset, key_offset, buyer_key, seller_key, key_global, agent_global, key_agent_local, holder, tile,
         agents, sold_from) = number_good(pair_ptr, batch_slots, pair_bid, pair_offer, bid_rows, offer_rows, bid_buyer, bid_tile, offer_seller,
                                          offer_tile, tile_stride, empty_tile)
        keys, batch_agents, rows = len(holder), len(agents), len(agent_global)
        stock_state = _sellers_stock(book.goods.stocks, book.goods.stock_index, holder, tile, sold_from, good)
        cash_state = read_balances(book.money.balances, book.money.stride, agents, currency)
        edge, mint, external, imported, exported = _agent_flags(book.money.agents, agents, import_numbers, export_numbers)
        (goods, _money, _payer, paid, received, goods_in, goods_out, buyer_net, got_goods, paid_as_buyer, imports, exports, _given, _taken,
         key_to_mint, batch_paid, batch_received, batch_given, batch_taken) = settle_markets(
            pair_offset, agent_offset, key_offset, buyer_key, seller_key, pair_quantity[pair_positions], ask[pair_offer[pair_positions]],
            key_agent_local, key_global, agent_global, stock_state, cash_state, edge, mint, external, imported, exported, True, True)
        agent = agents[agent_global]
        key_holder, key_tile = holder[key_global], tile[key_global]
        (purpose_kind, good_column, template, reference, plant_bought, foreign, bought_place, bought_agent, bought_units,
         bought_money) = note_columns(agent_offset, positions, agent, paid, got_goods, paid_as_buyer, buyer_net, goods_in, imports, exports,
                                      makers_sorted, SALES_PURPOSE, good)
        bought = (bought_place, bought_agent, bought_units, bought_money)
        moved = exact_sum(batch_given, len(batch_given))
        scratch_short = len(scratch.money_plan.key) <= batch_agents or len(scratch.goods_plan.key) <= keys
        money_across = imports.any() or exports.any()
        if (not _room(book.goods.stocks, keys) or not _room(book.goods.edge_goods, keys) or not _room(book.goods.flows, 1) or scratch_short
                or not _room(received_target.rows, rows) or not _room(sold_target.rows, rows) or not _room_across(
                    imports_target, exports_target, money_across, rows)):
            status = NEEDS_ROOM
        elif (foreign or moved > 0.0) and purpose_template == NO_CODE:
            status = NEEDS_PURPOSE
        else:
            code, _culprit = apply_settled(book, scratch, currency, agents, batch_paid, batch_received, holder, tile, good, batch_given,
                                           batch_taken)
            if code != OK:
                status = REFUSED
            else:
                _record_totals(book.money.currencies, book.goods.goods, currency, good, batch_paid, batch_given, purpose_template,
                               purpose_reference, book.goods.flows, book.goods.flow_index)
                for each in range(len(template)):
                    if template[each] == FOREIGN_MARKET:
                        template[each], reference[each] = purpose_template, purpose_reference
                note_settlement_money(figures, counters, agent, paid, received, plant_bought, purpose_kind)
                note_settlement_goods(received_target, sold_target, agent, got_goods, goods_in, goods_out, good_column, purpose_kind)
                _note_across(imports_target, exports_target, money_across, agent, imports, exports, template, reference)
                moved_by_market = delivered_by_market(goods, pair_offset)
                for market in range(len(positions)):
                    delivered[positions[market]] = moved_by_market[market]
                any_to_mint = (key_to_mint > 0.0).any()
        if status != SETTLED:
            agent_offset, agent, key_offset, key_holder, key_tile = nothing, nothing, nothing, nothing, nothing
            goods_in, buyer_net, key_to_mint = no_floats, no_floats, no_floats
            got_goods, paid_as_buyer = no_flags, no_flags
            bought = (nothing, nothing, no_floats, no_floats)
    return (status, keys, batch_agents, rows, money_across, delivered, positions, agent_offset, agent, goods_in, got_goods, buyer_net, paid_as_buyer,
            bought[0], bought[1], bought[2], bought[3], any_to_mint, key_offset, key_holder, key_tile, key_to_mint)
