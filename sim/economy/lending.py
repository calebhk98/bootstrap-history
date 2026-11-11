"""The year's credit, around `credit.service` and `credit.clear`: who asks, and what follows from the result.

Producers ask at their year's close (producers_close). Households and merchants ask at the start of the
year, when they see their cash fall short of a floor or of the cargo they would carry; their loans reach
them before their orders (the year loop clears credit first). Everything here works on an agent id and the
record, so a firm, a state or another player borrows by the same rules.
"""
import dataclasses
from typing import Dict, List

import numpy as np

from sim.world import capital_market

from sim.loans.columns import NO_TILE

from . import bank_service, bondage, cohort_prime, credit, credit_claims, credit_service, households_credit, lender_ask, loss_memory, merchants_book, merchants_credit, merchants_credit_batch, titles, titles_ground, titles_value, transfer_rows
from .cohort_store import table_of
from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from . import household_work_year
from .household_work_year import kept_basket
from .producers_working_capital import WORKING_CAPITAL_PURPOSE
from .goods_order_tables import LOAN
from .order_rows import OrderRows
from .types import FundsOffer
from .households_basket import cohort_need_prices
from .inventory import held_stock
from .merchant_table import MerchantTable
from .rates import own_rate


def service(record, money: str, year: int, bondage_years: float = 0.0) -> Dict[str, float]:
    """The year's payments (`_collect`), then every lender's loss rate ages by the year's losses."""
    received = _collect(record, money, year, bondage_years)
    loss_memory.age(record, money, year)
    return received


def _collect(record, money: str, year: int, bondage_years: float) -> Dict[str, float]:
    """Collect the year's payments at its end, after sales, from loans made in earlier years (a borrower's
    first payment falls due a year after it borrowed). Books the defaults: a lender's loss, a defaulter's
    record, a merchant's staked capital after what it repaid or was freed of. Returns the interest each
    lender received, which is its income; returned principal is not income."""
    store = record.credit.contracts.loan_store
    serving = credit_service.due_rows(store, year, list(record.capital_markets.banks))
    if not len(serving):
        return bank_service.service_deposits(record, money, year)
    borrowers = list(dict.fromkeys(store.agent_name(number) for number in store.table.borrower[serving].tolist()))
    cash = dict(zip(borrowers, record.book.balances_at(record.book.rows_of(borrowers), money).tolist()))
    served = credit_service.serve(store, serving, cash)
    transfer_rows.post_payments(record.book, *served.payments(year))
    received = {lender: receipt.interest for lender, receipt in served.receipts().items() if receipt.interest > 0.0}
    merchants_credit.stake(record.merchants, credit_service.principal_changes(store, served, serving))
    defaults = served.defaults()
    pledged_rows = {store.texts[number]: row for number, row in zip(store.table.number[serving].tolist(), serving.tolist())
                    if store.table.collateral_tile[row] != NO_TILE}
    taken = [dataclasses.replace(default, loss=max(0.0, default.loss - titles.foreclose(record, store.snapshot(pledged_rows[default.loan_id]))))
             if default.loan_id in pledged_rows else default for default in defaults]
    for agent, lost in credit_claims.losses_by_lender(taken).items():
        record.credit.add_loss(agent, lost)
    bondage.enter(record, taken, bondage_years)
    record.credit.remembered_defaults = credit_claims.remember_defaults(record.credit.remembered_defaults, defaults)
    credit_service.apply_served(store, served, serving)
    for depositor, interest in bank_service.service_deposits(record, money, year).items():
        received[depositor] = received.get(depositor, 0.0) + interest
    return received


def expected_inflation_of(record) -> float:
    """The inflation lenders expect, as the people-weighted mean of the cohorts' own expectations; none before
    any cohort has people. The real-rate bound on the credit market adds it to the bound."""
    store = table_of(record.cohorts)
    rows = np.arange(store.count, dtype=np.int64)
    held, expected = store.floats("people", rows), store.floats("expected_inflation", rows)
    people = sum(max(0.0, each) for each in held)
    if people <= 0.0:
        return 0.0
    return sum(max(0.0, each) * inflation for each, inflation in zip(held, expected)) / people


def lend_working_capital(setup, record, view) -> None:
    """Strike the producers' working-capital loans before the year's plans, so the cash is there to plan with.
    Each is dated to the last close, which makes its one payment fall due at this year's end, out of the sales
    its runs bring. Lenders are the households' cash above their targets; the other requests wait for the
    year's ordinary lending."""
    asked = [request for request in record.credit.loan_requests if request.purpose == WORKING_CAPITAL_PURPOSE]
    if not asked:
        return
    record.credit.loan_requests = [request for request in record.credit.loan_requests if request.purpose != WORKING_CAPITAL_PURPOSE]
    money = setup.currency_id
    store = table_of(record.cohorts)
    order = store.order()
    ids = [store.ids[row] for row in order.tolist()]
    targets, expected_inflation = store.floats("cash_target", order), dict(zip(ids, store.floats("expected_inflation", order)))
    held = record.book.balances_of(ids, money).tolist()
    spare = {cohort_id: balance - target for cohort_id, balance, target in zip(ids, held, targets)}
    spare = {cohort_id: amount for cohort_id, amount in spare.items() if amount > 0.0}
    if not spare:
        return
    offers = [FundsOffer(cohort_id, money, amount, lender_ask.lowest_ask(
                  HOUSEHOLD_TIME_PREFERENCE, expected_inflation[cohort_id],
                  expected_loss_rate=lender_ask.loss_rate(record.credit.loss_rates.get(cohort_id, 0.0)),
                  land_yield=record.credit.land_yield, public_premium=record.credit.public_premium))
              for cohort_id, amount in spare.items()]
    clearing = credit.clear_with_cause(
        asked, offers, money, record.memory.rates.get(money), credit_claims.principal_by_borrower(record.credit.loans),
        credit_claims.arrears_history(record.credit.loans, record.credit.remembered_defaults), year=view.year - 1,
        clearing="working_capital",
        rate_ceiling=capital_market.RATE_CEILING_SHARE * setup.opening_rate,
        expected_inflation=expected_inflation_of(record))
    loans = clearing.loans
    record.credit.note_clearing(view.year, clearing.rate, loans, clearing.cause)
    transfer_rows.post_payments(record.book, *credit.disbursement_rows(loans))
    record.credit.add_loans(loans)
    merchants_credit.stake(record.merchants, {loan.borrower: loan.principal for loan in loans})


def household_requests(setup, record, view, ledger, priced_by_tile) -> List:
    """Loans households ask for to meet the floors their cash does not cover."""
    money = setup.currency_id
    debts = credit_claims.debts_by_borrower(record.credit.loans, money)
    rate = own_rate(view, money)
    requests = []
    cohort_prime.prime_cohort_baskets(setup, record, view, True)
    store = table_of(record.cohorts)
    order = store.order()
    held = record.book.balance_by_agent([store.ids[row] for row in order.tolist()], money)
    for cohort, key in zip(store.figures(order), household_work_year.signatures_of(record, store, order)):
        cohort_id = cohort.agent_id
        priced = _priced_basket(view, key, household_work_year.basket_of_signature(setup, key), priced_by_tile)
        if not priced or cohort.people <= 0.0:
            continue
        shortfall = (households_credit.floor_cost_unmet(cohort, priced, ledger.grown_units.get(cohort_id))
                     - held[cohort_id])
        asked = households_credit.subsistence_request(cohort, shortfall, money, rate, debts.get(cohort_id, 0.0))
        if asked is not None:
            requests.append(_pledging_title(setup, record, cohort, asked, rate))
    return requests


def _pledging_title(setup, record, cohort, request, live_rate):
    """The request with the household's whole free title on its tile pledged to it: a peasant pledges the plot."""
    tile = setup.tiles.get(cohort.tile)
    free = titles.free_share(record, cohort.agent_id, cohort.tile)
    if tile is None or free <= 0.0:
        return request
    worth = titles_value.share_value(titles_ground.arable_hectares(record, cohort.tile, tile), record.land.land_rent.get(cohort.tile, 0.0), free,
                                     titles_value.capitalising_rate(live_rate, setup.opening_rate))
    if worth <= 0.0:
        return request
    return dataclasses.replace(request, collateral_value=worth, collateral_tile=cohort.tile, collateral_share=free)


def merchant_requests(setup, record, view, area_map, carriage) -> List:
    money = setup.currency_id
    rate = own_rate(view, money)
    debts = credit_claims.debts_by_borrower(record.credit.loans, money)
    if not record.merchants:
        return []
    route = merchants_book.route_pass(view, carriage, area_map, setup.specs)
    return merchants_credit_batch.credit_requests(MerchantTable.of(record.memory.tables), route, record.book, debts, money, rate)


def bid_household_loans(setup, record, view, ledger, loans, order_book, priced_by_tile) -> None:
    """A household that borrowed bids its loan for the floors it was short of."""
    lent: Dict[str, float] = {}
    for loan in loans:
        if loan.borrower in record.cohorts:
            lent[loan.borrower] = lent.get(loan.borrower, 0.0) + loan.principal
    rows = OrderRows(order_book, LOAN)
    store = table_of(record.cohorts)
    borrowers = sorted(lent.items())
    figures = store.figures(store.rows_of([cohort_id for cohort_id, _budget in borrowers]))
    keys = household_work_year.signatures_of_figures(record, figures)
    for cohort, key, (cohort_id, budget) in zip(figures, keys, borrowers):
        basket = kept_basket(setup, key)
        rows.bids_from(households_credit.floor_bids(cohort, _priced_basket(view, key, basket, priced_by_tile), budget,
                                                    ledger.grown_units.get(cohort_id), setup.specs, view, basket))
    rows.write()


def _priced_basket(view, key, basket, priced_by_tile):
    if key not in priced_by_tile:
        priced_by_tile[key] = cohort_need_prices(basket, view, key[0], key)
    return priced_by_tile[key]

