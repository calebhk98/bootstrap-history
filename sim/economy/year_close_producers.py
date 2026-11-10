"""Every producer's year end: the close kernel over the year arrays, then each producer's effects on the record.

`close_producers_of_year(...)` is what year_close.close_agents runs for the producers. The numbers come from
`close_run.close_producers` (one kernel for expectations, the close, the finances and the sales rules). The effects are tables
and a short loop: the dividends of every producer that pays are posting rows from one kernel and one batch (year_close_dividends.py),
the dividends noted, the plant worn and the new producer records come from the answer's columns; Python still runs, in producer
order, the rows that need the credit record or an exit (an exit, a write-off of loans, a loan request, a rebuild plan), which are a
few hundred a year."""
from dataclasses import replace as replace_fields
from typing import Dict

import numpy as np

from . import producer_exit, shares
from . import producers_working_capital as working_capital
from .close_kernel import REQUEST_EXPAND, REQUEST_NONE
from .close_pack import pack
from .close_run import close_producers
from .loan_write_offs import LoanWriteOffs
from .types import LoanRequest, Transfer
from .year_arrays import YearArrays
from .producer_close_write import write_close
from .year_arrays_producers import ProducerColumns
from .year_close_dividends import add_property_income, dividend_plan, post_dividends
from .year_close_ledger import note_plant_worn
from .year_close_owners import Participants
from .year_close_shares import share_pricer


def _request_of(producer_id: str, currency: str, kind: int, amount: float, rate: float, term: float, collateral: float):
    purpose = shares.EXPAND_PURPOSE if kind == REQUEST_EXPAND else working_capital.WORKING_CAPITAL_PURPOSE
    return LoanRequest(producer_id, currency, amount, rate, term, collateral, purpose)


def close_producers_of_year(setup, record, view, ledger, arrays: YearArrays, property_income, pooled) -> YearArrays:
    """Close every producer. `property_income` (payee -> money) is added to as dividends are paid; `pooled(recipe_id, trade)`
    is the crews' pooled practice. Returns the year arrays in step with the table the close leaves (the next phase hands them
    to `sync`, which then has no row to read again)."""
    arrays = arrays.sync(setup, record, view)
    columns = arrays.producers
    traded, _round_prices = ledger.market_totals()
    bundle = pack(setup, record, view, ledger, arrays)
    answer = close_producers(arrays, bundle, share_pricer(arrays, ledger, traded))
    ids = columns.ids
    ran = columns.idle_years <= 0         # the rows the close kernel ran; the others sat out the year
    exited = answer.exited
    dividend = answer.dividend
    paying = ran & ~exited & (dividend > 0.0)
    noted = [amount if pays else 0 for amount, pays in zip(dividend.tolist(), (ran & (dividend > 0.0)).tolist())]
    shares.note_dividends(record.capital_markets, zip(ids, noted))        # an exit forgets it below
    worn = np.nonzero(ran & ~exited & (columns.capacity_runs - answer.new_capacity > 0.0))[0]
    note_plant_worn(ledger, [ids[row] for row in worn.tolist()], (columns.capacity_runs - answer.new_capacity)[worn])
    participants = Participants()
    exit_rows, exit_payees, exit_amounts = _effects_by_row(setup, record, columns, answer, bundle, participants)
    plan = dividend_plan(record, columns, dividend, np.nonzero(paying)[0], participants)
    post_dividends(record.book, setup.currency_id, plan, ids, participants)
    add_property_income(property_income, participants, np.concatenate([plan.row, np.array(exit_rows, dtype=np.int64)]),
                        np.concatenate([plan.payee, np.array(exit_payees, dtype=np.int64)]),
                        np.concatenate([plan.amount, np.array(exit_amounts, dtype=np.float64)]))
    write_close(record.producers, columns, answer, pooled)
    return replace_fields(arrays, producers=ProducerColumns.of(record.producers, columns.matrices, columns.tiles))


def _effects_by_row(setup, record, columns, answer, bundle, participants: Participants):
    """The rows that act on the credit record or leave, in producer order: an exit pays its lenders and owner at once, a write-off of
    loans waits for the next exit or the end, and a rebuild plan or loan request is recorded. Returns the exits' payments to the
    owners as (row, payee participant, amount) lists, for the property income."""
    ids = columns.ids
    ran = columns.idle_years <= 0
    kept = ran & ~answer.exited
    asks = answer.request_kind != REQUEST_NONE
    rebuilds = (answer.replacement_runs > 0.0) & (bundle.revenue > bundle.running_costs)
    rows = np.nonzero(ran & (answer.exited | (kept & ((answer.write_off > 0.0) | asks | rebuilds))))[0].tolist()
    loan_write_offs = LoanWriteOffs(record)
    write_offs: Dict[str, float] = {}      # applied in one pass over the loans when an exit comes and at the end
    exits = producer_exit.ExitBatch(record)
    exits.hold([ids[row] for row in rows if answer.exited[row]])
    owners = columns.owners()
    exit_rows, exit_payees, exit_amounts = [], [], []
    for row in rows:
        producer_id = ids[row]
        if answer.exited[row]:
            loan_write_offs.apply(write_offs)     # an exit remembers its defaults after those of the producers before it
            write_offs.clear()
            amount = float(answer.dividend[row])
            payout = [Transfer(producer_id, owners[row], bundle.currencies[row], amount, "dividend")] if amount > 0.0 else []
            for transfer in exits.exit(producer_id, payout):
                exit_rows.append(row)
                exit_payees.append(participants.of(transfer.payee))
                exit_amounts.append(transfer.amount)
            continue
        if answer.write_off[row] > 0.0:
            write_offs[producer_id] = float(answer.write_off[row])
        if rebuilds[row]:
            record.credit.plan_rebuild(producer_id, float(answer.replacement_runs[row]))     # covering its costs, it rebuilds the wear its plan needs
        if asks[row]:
            record.credit.ask_for_loan(_request_of(producer_id, bundle.currencies[row], int(answer.request_kind[row]),
                                                   float(answer.request_amount[row]), float(answer.request_rate[row]),
                                                   float(answer.request_term[row]), float(answer.request_collateral[row])))
            record.credit.plan_expansion(producer_id, float(answer.expansion_runs[row]))
    loan_write_offs.apply(write_offs)
    exits.finish()
    return exit_rows, exit_payees, exit_amounts
