"""The year's credit, around `credit.service` and `credit.clear`: who asks, and what follows from the result.

Producers ask at their year's close (producers_close). Households and merchants ask at the start of the
year, when they see their cash fall short of a floor or of the cargo they would carry; their loans reach
them before their orders (the year loop clears credit first). Everything here works on an agent id and the
record, so a firm, a state or another player borrows by the same rules.
"""
import dataclasses
from typing import Dict, List

from sim.world import capital_market

from . import bank_service, banks, bondage, credit, credit_claims, households_credit, lender_ask, loss_memory, merchants_credit, titles, titles_ground, titles_value
from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .household_work_year import basket_key, cohort_basket
from .producers_close import WORKING_CAPITAL_PURPOSE
from .types import FundsOffer
from .households_basket import need_prices
from .year_goods import _held_stock


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
    due = [loan for loan in record.loans if loan.issued_year < year and not banks.is_deposit(record, loan)]
    if not due:
        return bank_service.service_deposits(record, money, year)
    cash = {loan.borrower: record.book.balance(loan.borrower, money) for loan in due}
    transfers, serviced, defaults, receipts = credit.service_split(due, cash, year)
    record.book.transfer_many(transfers)
    received = {lender: receipt.interest for lender, receipt in receipts.items() if receipt.interest > 0.0}
    owed_before = credit_claims.principal_by_borrower(due)
    owed_after = credit_claims.principal_by_borrower(serviced)
    merchants_credit.stake(record.merchants, {agent: owed_after.get(agent, 0.0) - owed
                                              for agent, owed in owed_before.items()})
    pledged_loans = {loan.loan_id: loan for loan in due if loan.collateral_tile}
    taken = [dataclasses.replace(default, loss=max(0.0, default.loss - titles.foreclose(record, pledged_loans[default.loan_id])))
             if default.loan_id in pledged_loans else default for default in defaults]
    for agent, lost in credit_claims.losses_by_lender(taken).items():
        record.credit_losses[agent] = record.credit_losses.get(agent, 0.0) + lost
    bondage.enter(record, taken, bondage_years)
    record.remembered_defaults = credit_claims.remember_defaults(record.remembered_defaults, defaults)
    record.loans = [loan for loan in record.loans if loan.issued_year >= year or banks.is_deposit(record, loan)] + serviced
    for depositor, interest in bank_service.service_deposits(record, money, year).items():
        received[depositor] = received.get(depositor, 0.0) + interest
    return received


def lend_working_capital(setup, record, view) -> None:
    """Strike the producers' working-capital loans before the year's plans, so the cash is there to plan with.
    Each is dated to the last close, which makes its one payment fall due at this year's end, out of the sales
    its runs bring. Lenders are the households' cash above their targets; the other requests wait for the
    year's ordinary lending."""
    asked = [request for request in record.loan_requests if request.purpose == WORKING_CAPITAL_PURPOSE]
    if not asked:
        return
    record.loan_requests = [request for request in record.loan_requests if request.purpose != WORKING_CAPITAL_PURPOSE]
    money = setup.currency_id
    spare = {cohort_id: record.book.balance(cohort_id, money) - cohort.cash_target
             for cohort_id, cohort in sorted(record.cohorts.items())}
    spare = {cohort_id: amount for cohort_id, amount in spare.items() if amount > 0.0}
    if not spare:
        return
    offers = [FundsOffer(cohort_id, money, amount, lender_ask.lowest_ask(
                  HOUSEHOLD_TIME_PREFERENCE, record.cohorts[cohort_id].expected_inflation,
                  expected_loss_rate=lender_ask.loss_rate(record.loss_rates.get(cohort_id, 0.0))))
              for cohort_id, amount in spare.items()]
    loans, _rate, _unmet = credit.clear(
        asked, offers, money, record.memory.rates.get(money), credit_claims.principal_by_borrower(record.loans),
        credit_claims.arrears_history(record.loans, record.remembered_defaults), year=view.year - 1,
        rate_ceiling=capital_market.RATE_CEILING_SHARE * setup.opening_rate)
    record.book.transfer_many(credit.disbursements(loans))
    record.loans.extend(loans)
    merchants_credit.stake(record.merchants, {loan.borrower: loan.principal for loan in loans})


def household_requests(setup, record, view, ledger, priced_by_tile) -> List:
    """Loans households ask for to meet the floors their cash does not cover."""
    money = setup.currency_id
    debts = credit_claims.debts_by_borrower(record.loans, money)
    rate = view.interest_rate(money)
    requests = []
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
    worth = titles_value.share_value(titles_ground.arable_hectares(record, cohort.tile, tile), record.land_rent.get(cohort.tile, 0.0), free,
                                     titles_value.capitalising_rate(live_rate, setup.opening_rate))
    if worth <= 0.0:
        return request
    return dataclasses.replace(request, collateral_value=worth, collateral_tile=cohort.tile, collateral_share=free)


def merchant_requests(setup, record, view, area_map, carriage) -> List:
    money = setup.currency_id
    rate = view.interest_rate(money)
    debts = credit_claims.debts_by_borrower(record.loans, money)
    requests = []
    for merchant_id, merchant in sorted(record.merchants.items()):
        asked = merchants_credit.credit_request(
            merchant, view, carriage, area_map, record.book.balance(merchant_id, money),
            _held_stock(record.book, merchant_id), setup.specs, rate, debts.get(merchant_id, 0.0), money)
        if asked is not None:
            requests.append(asked)
    return requests


def bid_household_loans(setup, record, view, ledger, loans, order_book, priced_by_tile) -> None:
    """A household that borrowed bids its loan for the floors it was short of."""
    lent: Dict[str, float] = {}
    for loan in loans:
        if loan.borrower in record.cohorts:
            lent[loan.borrower] = lent.get(loan.borrower, 0.0) + loan.principal
    for cohort_id, budget in sorted(lent.items()):
        cohort = record.cohorts[cohort_id]
        basket = cohort_basket(setup, record, cohort)
        for bid in households_credit.floor_bids(cohort, _priced_basket(view, basket_key(record, cohort), basket, priced_by_tile), budget,
                                                ledger.grown_units.get(cohort_id), setup.specs, view, basket):
            order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)


def _priced_basket(view, key, basket, priced_by_tile):
    if key not in priced_by_tile:
        priced_by_tile[key] = need_prices(basket, view, key[0])
    return priced_by_tile[key]


def _priced(setup, view, tile, priced_by_tile):
    if tile not in priced_by_tile:
        priced_by_tile[tile] = need_prices(setup.basket_for(tile), view, tile)
    return priced_by_tile[tile]
