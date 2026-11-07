"""Every producer's year end: the close kernel over the year arrays, then each producer's effects on the record.

`close_producers_of_year(...)` is the loop that year_close.close_agents used to run per producer. The numbers come from
`close_run.close_producers` (one kernel for expectations, the close, the finances and the sales rules); what is left per
producer is the book and record writes: the dividend to its owners, an exit, a loan request, the plant that wore, and the
producer row replaced through producer_table with only the fields the close changes."""
import math
from typing import Dict

import numpy as np

from dataclasses import replace as replace_fields

from . import expansion_price, firm_year, ownership, practice, producer_exit, producer_table, shares
from . import producers_working_capital as working_capital
from .close_pack import pack
from .close_run import close_producers
from .year_arrays_closed import columns_after_close
from .replaced import replaced
from .types import LoanRequest, Transfer
from .year_arrays import YearArrays
from .close_kernel import REQUEST_EXPAND, REQUEST_NONE


def _share_pricer(arrays: YearArrays, ledger, traded, prepared):
    """`price_share_of(row, added_by_slot)`: the share of each output's price that stays when the producer adds that much."""
    columns, matrices = arrays.producers, arrays.matrices

    def share_of_row(row: int, added) -> np.ndarray:
        producer = columns.records[row]
        shares_of_slots = np.ones(len(added))
        pricer = expansion_price.price_share_of(ledger.bids_by_market, traded, arrays.area_map.area_of, producer.tile, prepared)
        for slot, column in enumerate(matrices.slot_goods[columns.recipe_row[row]]):
            if column < 0:
                break
            if matrices.slot_is_output[columns.recipe_row[row], slot] and added[slot] > 0.0:
                shares_of_slots[slot] = pricer(matrices.goods.ids[column], added[slot])
        return shares_of_slots
    return share_of_row


def _request_of(producer_id: str, currency: str, kind: int, amount: float, rate: float, term: float, collateral: float):
    purpose = shares.EXPAND_PURPOSE if kind == REQUEST_EXPAND else working_capital.WORKING_CAPITAL_PURPOSE
    return LoanRequest(producer_id, currency, amount, rate, term, collateral, purpose)


def _changes_of(producer, answer_row: Dict[str, object], written_goods, pooled) -> Dict[str, object]:
    """The fields the close changes, for one replacement of the row. The crew's practice after the year's runs (practice.py)
    is among them; growth in runs is hired hands."""
    expected = dict(producer.expected_prices)
    for good, value in written_goods:
        expected[good] = value
    changes = dict(capacity_runs=answer_row["capacity"], years_of_loss=answer_row["losses"], cash_target=answer_row["target"],
                   expected_prices=expected, net_earnings_history=answer_row["earnings"], revenue_history=answer_row["revenues"],
                   expected_sales=answer_row["expected_sales"], last_runs=answer_row["last_runs"],
                   staffed_runs=answer_row["staffed"])
    if answer_row["idle"]:
        changes["idle_years"] = answer_row["idle"]
    if producer.crew_runs:
        new_last_runs = answer_row["last_runs"]
        changes["crew_runs"] = practice.crew_runs_after_year(
            producer.crew_runs, max(0.0, new_last_runs) / max(1.0, producer.workshops),
            practice.hired_share(producer.last_runs, new_last_runs),
            {trade: pooled(producer.recipe_id, trade) for trade in producer.crew_runs})
    return changes


def close_producers_of_year(setup, record, view, ledger, arrays: YearArrays, cohorts_by_tile, property_income, pooled) -> YearArrays:
    """Close every producer. `property_income` (payee -> money) is added to as dividends are paid; `pooled(recipe_id, trade)`
    is the crews' pooled practice. Returns the year arrays in step with the table the close leaves (the next phase hands them
    to `sync`, which then has no row to read again)."""
    arrays = arrays.sync(setup, record, view)
    columns, matrices = arrays.producers, arrays.matrices
    traded, _round_prices = ledger.market_totals()
    bundle = pack(setup, record, view, ledger, arrays)
    answer = close_producers(arrays, bundle, _share_pricer(arrays, ledger, traded, {}))
    lists = {name: getattr(answer, name).tolist() for name in (
        "new_capacity", "new_losses", "new_target", "exited", "dividend", "request_kind", "request_amount", "request_rate",
        "request_term", "request_collateral", "expansion_runs", "replacement_runs", "new_count", "write_off", "new_idle",
        "new_expected_sales", "new_last_runs", "new_staffed", "new_expected", "written", "new_earnings", "new_revenues")}
    good_ids = matrices.goods.ids
    write_offs: Dict[str, float] = {}      # applied in one pass over the loans, and the dividends posted as one batch, after the loop
    dividends: list = []
    exits = producer_exit.ExitBatch(record)
    for row, producer_id in enumerate(columns.ids):
        producer = columns.records[row]
        if producer.idle_years > 0:      # bankrupt: idle, no dividend (Eurace@Unibi, Firm_bankruptcy_idle_counter)
            producer_table.put_producer(record.producers, replaced(producer, idle_years=producer.idle_years - 1))
            shares.note_dividend(record.capital_markets, producer_id, ())
            continue
        currency = bundle.currencies[row]
        amount = lists["dividend"][row]
        transfers = (Transfer(producer_id, producer.owner, currency if lists["exited"][row] else setup.currency_id, amount,
                              "dividend"),) if amount > 0.0 else ()
        shares.note_dividend(record.capital_markets, producer_id, transfers)
        if lists["exited"][row]:
            firm_year.write_off_many(record, write_offs)     # an exit remembers its defaults after those of the producers before it
            write_offs.clear()
            paid = exits.exit(producer_id, list(transfers))
            for transfer in paid:
                property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
            continue
        if lists["write_off"][row] > 0.0:
            write_offs[producer_id] = lists["write_off"][row]
        if transfers:
            paid = ownership.spread(record, transfers, cohorts_by_tile)
            dividends.extend(paid)
            for transfer in paid:
                property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
        worn = producer.capacity_runs - lists["new_capacity"][row]
        if worn > 0.0:
            ledger.plant_worn[producer_id] = worn
        if lists["replacement_runs"][row] > 0.0 and bundle.revenue[row] > bundle.running_costs[row]:
            record.credit.plan_rebuild(producer_id, lists["replacement_runs"][row])     # covering its costs, it rebuilds the wear its plan needs
        if lists["request_kind"][row] != REQUEST_NONE:
            record.credit.ask_for_loan(_request_of(producer_id, currency, lists["request_kind"][row], lists["request_amount"][row],
                                                   lists["request_rate"][row], lists["request_term"][row],
                                                   lists["request_collateral"][row]))
            record.credit.plan_expansion(producer_id, lists["expansion_runs"][row])
        count = lists["new_count"][row]
        staffed = lists["new_staffed"][row]
        written = [(good_ids[column], lists["new_expected"][row][slot])
                   for slot, column in enumerate(matrices.slot_goods[columns.recipe_row[row]])
                   if column >= 0 and lists["written"][row][slot]]
        producer_table.put_producer(record.producers, replaced(producer, **_changes_of(producer, dict(
            capacity=lists["new_capacity"][row], losses=lists["new_losses"][row], target=lists["new_target"][row],
            earnings=tuple(lists["new_earnings"][row][:count]), revenues=tuple(lists["new_revenues"][row][:count]),
            expected_sales=lists["new_expected_sales"][row], last_runs=lists["new_last_runs"][row],
            staffed=None if math.isnan(staffed) else staffed, idle=lists["new_idle"][row]), written, pooled)))
    firm_year.write_off_many(record, write_offs)
    exits.finish()
    record.book.transfer_many(dividends)
    return replace_fields(arrays, producers=columns_after_close(columns, record.producers, answer.exited, answer))
