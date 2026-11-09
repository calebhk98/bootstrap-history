"""The year's credit, around `credit.service` and `credit.clear`: who asks, and what follows from the result.

Producers ask at their year's close (producers_close). Households and merchants ask at the start of the
year, when they see their cash fall short of a floor or of the cargo they would carry; their loans reach
them before their orders (the year loop clears credit first). Everything here works on an agent id and the
record, so a firm, a state or another player borrows by the same rules.
"""
import dataclasses
from typing import Dict, List

from sim.world import capital_market

from sim.loans.columns import NO_TILE

from . import bank_service, bondage, cohort_prime, credit, credit_claims, credit_service, households_credit, lender_ask, loss_memory, merchants_book, merchants_credit, merchants_credit_batch, titles, titles_ground, titles_value, transfer_rows
from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from .household_work_year import basket_key, cohort_basket
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
    loss_memory.age(record, money)
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
    cohorts = record.cohorts
    people = sum(max(0.0, cohort.people) for cohort in cohorts.values())
    if people <= 0.0:
        return 0.0
    return sum(max(0.0, cohort.people) * cohort.expected_inflation for cohort in cohorts.values()) / people


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
    spare = {cohort_id: record.book.balance(cohort_id, money) - cohort.cash_target
             for cohort_id, cohort in sorted(record.cohorts.items())}
    spare = {cohort_id: amount for cohort_id, amount in spare.items() if amount > 0.0}
    if not spare:
        return
    offers = [FundsOffer(cohort_id, money, amount, lender_ask.lowest_ask(
                  HOUSEHOLD_TIME_PREFERENCE, record.cohorts[cohort_id].expected_inflation,
                  expected_loss_rate=lender_ask.loss_rate(record.credit.loss_rates.get(cohort_id, 0.0))))
              for cohort_id, amount in spare.items()]
    loans, _rate, _unmet = credit.clear(
        asked, offers, money, record.memory.rates.get(money), credit_claims.principal_by_borrower(record.credit.loans),
        credit_claims.arrears_history(record.credit.loans, record.credit.remembered_defaults), year=view.year - 1,
        clearing="working_capital",
        rate_ceiling=capital_market.RATE_CEILING_SHARE * setup.opening_rate,
        expected_inflation=expected_inflation_of(record))
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
    for cohort_id, cohort in sorted(record.cohorts.items()):
        key = basket_key(record, cohort)
        priced = _priced_basket(view, key, cohort_basket(setup, record, cohort), priced_by_tile)
        if not priced or cohort.people <= 0.0:
            continue
        shortfall = (households_credit.floor_cost_unmet(cohort, priced, ledger.grown_units.get(cohort_id))
                     - record.book.balance(cohort_id, money))
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
    for cohort_id, budget in sorted(lent.items()):
        cohort = record.cohorts[cohort_id]
        basket = cohort_basket(setup, record, cohort)
        rows.bids_from(households_credit.floor_bids(cohort, _priced_basket(view, basket_key(record, cohort), basket, priced_by_tile), budget,
                                                    ledger.grown_units.get(cohort_id), setup.specs, view, basket))
    rows.write()


def _priced_basket(view, key, basket, priced_by_tile):
    if key not in priced_by_tile:
        priced_by_tile[key] = cohort_need_prices(basket, view, key[0], key)
    return priced_by_tile[key]

