"""Applying postings to the book: plan the batch, refuse it whole or write it whole, and leave the records.

`apply_batches` is the kernel a converter calls with the two posting tables (rows grouped by batch, `*_starts` the first row
of each batch and one past the last). A batch holds transfers and goods moves together: all of them or none, with money
checked before goods, as the book always did. Each batch's outcome is a row of `BatchOutcomes`; with `stop_on_refusal` the
kernel returns at the first refused batch and leaves that batch's plans (and their failing marks) for the boundary to read.
The boundary (`sim/book_post.py`) turns an outcome into `InsufficientFunds`, `InsufficientGoods` or `NegativeAmount`.

`apply_money` and `apply_goods` are the same rules for one batch that holds only transfers, or only goods moves; they take
only the half of the book's tables they use, which keeps the cost of a call with a few postings down.

RULE_BATCH is the rule of a batch (an overdraft the batch makes or deepens fails); RULE_SINGLE is the rule of one posting
made on its own, which checks the payer's balance before the posting (the book's `transfer` and `move`)."""
from sim.book_commit import (commit_money, commit_stock, record_moves, record_settled_money, record_settled_stock,
                             record_transfers)
from sim.book_plan import (check_batch, check_one_payer, clear_plan, first_failing_cell, mark_overdrafts, plan_moves,
                           plan_settled_money, plan_settled_stock, plan_transfers)
from sim.book_tables import INSUFFICIENT_FUNDS, INSUFFICIENT_GOODS
from sim.compiled_tables.causes import OK
from sim.jit import njit

RULE_BATCH = 0
RULE_SINGLE = 1


@njit(inline="always")
def check_plan(plan, agents, amount, cause, rule):
    """(OK, 0) when the plan overdraws nothing under the rule, else (cause, the first offending cell)."""
    if rule == RULE_SINGLE:
        return check_one_payer(plan, agents, amount, cause)
    return check_batch(plan, agents, cause)


@njit(inline="always")
def plan_money_batch(transfers, first, last, money, plan, local_index, rule):
    """Plan and check transfers first .. last - 1 as one batch. (OK, 0), or (cause, culprit) with nothing written."""
    clear_plan(plan, local_index)
    code, culprit = plan_transfers(transfers, first, last, money.balances, money.stride, plan, local_index)
    if code == OK and last > first:
        return check_plan(plan, money.agents, transfers.amount[first], INSUFFICIENT_FUNDS, rule)
    return code, culprit


@njit(inline="always")
def plan_goods_batch(moves, first, last, goods, plan, local_index, rule):
    """plan_money_batch for goods moves first .. last - 1."""
    clear_plan(plan, local_index)
    code, culprit = plan_moves(moves, first, last, goods.stocks, goods.stock_index, plan, local_index)
    if code == OK and last > first:
        return check_plan(plan, goods.agents, moves.quantity[first], INSUFFICIENT_GOODS, rule)
    return code, culprit


@njit(inline="always")
def apply_money(transfers, first, last, money, plan, local_index, rule):
    """Apply transfers first .. last - 1 as one batch holding no goods. Returns (OK, -1) or (cause, culprit)."""
    code, culprit = plan_money_batch(transfers, first, last, money, plan, local_index, rule)
    if code != OK:
        return code, culprit
    commit_money(plan, money.balances, money.agents)
    record_transfers(transfers, first, last, money)
    return OK, -1


@njit(inline="always")
def apply_goods(moves, first, last, goods, plan, local_index, rule):
    """Apply goods moves first .. last - 1 as one batch holding no transfers. Returns (OK, -1) or (cause, culprit)."""
    code, culprit = plan_goods_batch(moves, first, last, goods, plan, local_index, rule)
    if code != OK:
        return code, culprit
    code = commit_stock(plan, goods.stocks, goods.stock_index, goods.agents)
    if code != OK:
        return code, -1
    return record_moves(moves, first, last, goods), -1


@njit(inline="always")
def apply_one_batch(transfers, transfer_first, transfer_last, moves, move_first, move_last, book, scratch, rule):
    """Plan, check and write one batch of both kinds. Returns (OK, -1) when applied, else (cause, culprit) with the book
    unchanged. A batch with no goods moves (or no transfers) runs only the money (or goods) half: the other half's plan is left
    as the batch before it left it, which nothing reads."""
    if move_last == move_first:
        return apply_money(transfers, transfer_first, transfer_last, book.money, scratch.money_plan, scratch.money_local, rule)
    if transfer_last == transfer_first:
        return apply_goods(moves, move_first, move_last, book.goods, scratch.goods_plan, scratch.goods_local, rule)
    code, culprit = plan_money_batch(transfers, transfer_first, transfer_last, book.money, scratch.money_plan,
                                     scratch.money_local, rule)
    if code != OK:
        return code, culprit
    code, culprit = plan_goods_batch(moves, move_first, move_last, book.goods, scratch.goods_plan, scratch.goods_local, rule)
    if code != OK:
        return code, culprit
    commit_money(scratch.money_plan, book.money.balances, book.money.agents)
    code = commit_stock(scratch.goods_plan, book.goods.stocks, book.goods.stock_index, book.goods.agents)
    if code != OK:
        return code, -1
    record_transfers(transfers, transfer_first, transfer_last, book.money)
    return record_moves(moves, move_first, move_last, book.goods), -1


@njit
def apply_batches(transfers, transfer_starts, moves, move_starts, batch_count, book, scratch, outcomes, rule, stop_on_refusal):
    """Apply batches 0 .. batch_count - 1 in order, writing each one's outcome. Returns how many were refused."""
    refused = 0
    for batch in range(batch_count):
        code, culprit = apply_one_batch(transfers, transfer_starts[batch], transfer_starts[batch + 1], moves,
                                        move_starts[batch], move_starts[batch + 1], book, scratch, rule)
        outcomes.code[batch] = code
        outcomes.culprit[batch] = culprit
        outcomes.row_count[0] = batch + 1
        if code != OK:
            refused += 1
            if stop_on_refusal:
                return refused
    return refused


@njit
def apply_settled(book, scratch, currency, money_agents, paid, received, stock_holders, stock_tiles, good, given, taken):
    """Apply a market's summed settlement (money in one currency, one good's stock cells). Returns (OK, -1) or (cause,
    culprit) with nothing written."""
    scratch.money_plan.row_count[0] = 0
    scratch.goods_plan.row_count[0] = 0
    plan_settled_money(money_agents, paid, received, currency, book.money.stride, book.money.balances, scratch.money_plan)
    if mark_overdrafts(scratch.money_plan, book.money.agents) != 0:
        return INSUFFICIENT_FUNDS, first_failing_cell(scratch.money_plan)
    plan_settled_stock(stock_holders, stock_tiles, good, given, taken, book.goods.stocks, book.goods.stock_index,
                       scratch.goods_plan)
    if mark_overdrafts(scratch.goods_plan, book.goods.agents) != 0:
        return INSUFFICIENT_GOODS, first_failing_cell(scratch.goods_plan)
    commit_money(scratch.money_plan, book.money.balances, book.money.agents)
    code = commit_stock(scratch.goods_plan, book.goods.stocks, book.goods.stock_index, book.goods.agents)
    if code != OK:
        return code, -1
    record_settled_money(money_agents, paid, received, currency, book.money)
    return record_settled_stock(stock_holders, good, given, taken, book.goods), -1
