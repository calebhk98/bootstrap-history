"""The year's credit, around `credit.service` and `credit.clear`: who asks, and what follows from the result.

Producers ask at their year's close (producers_close). Households and merchants ask at the start of the
year, when they see their cash fall short of a floor or of the cargo they would carry; their loans reach
them before their orders (the year loop clears credit first). Everything here works on an agent id and the
record, so a firm, a state or another player borrows by the same rules.
"""
from typing import Dict, List

from . import credit, credit_claims, households_credit, merchants_credit
from .households_basket import need_prices
from .year_goods import _held_stock


def service(record, money: str, year: int) -> Dict[str, float]:
    """Collect the year's payments at its end, after sales, from loans made in earlier years (a borrower's
    first payment falls due a year after it borrowed). Books the defaults: a lender's loss, a defaulter's
    record, a merchant's staked capital after what it repaid or was freed of. Returns the money each
    lender received, which is its income next year."""
    due = [loan for loan in record.loans if loan.issued_year < year]
    if not due:
        return {}
    cash = {loan.borrower: record.book.balance(loan.borrower, money) for loan in due}
    transfers, serviced, defaults = credit.service(due, cash, year)
    record.book.transfer_many(transfers)
    received: Dict[str, float] = {}
    for transfer in transfers:
        received[transfer.payee] = received.get(transfer.payee, 0.0) + transfer.amount
    owed_before = credit_claims.principal_by_borrower(due)
    owed_after = credit_claims.principal_by_borrower(serviced)
    merchants_credit.stake(record.merchants, {agent: owed_after.get(agent, 0.0) - owed
                                              for agent, owed in owed_before.items()})
    for agent, lost in credit_claims.losses_by_lender(defaults).items():
        record.credit_losses[agent] = record.credit_losses.get(agent, 0.0) + lost
    record.remembered_defaults = credit_claims.remember_defaults(record.remembered_defaults, defaults)
    record.loans = [loan for loan in record.loans if loan.issued_year >= year] + serviced
    return received


def household_requests(setup, record, view, ledger, priced_by_tile) -> List:
    """Loans households ask for to meet the floors their cash does not cover."""
    money = setup.currency_id
    debts = credit_claims.debts_by_borrower(record.loans, money)
    rate = view.interest_rate(money)
    requests = []
    for cohort_id, cohort in sorted(record.cohorts.items()):
        priced = _priced(setup, view, cohort.tile, priced_by_tile)
        if not priced or cohort.people <= 0.0:
            continue
        shortfall = (households_credit.floor_cost_unmet(cohort, priced, ledger.grown_units.get(cohort_id))
                     - record.book.balance(cohort_id, money))
        asked = households_credit.subsistence_request(cohort, shortfall, money, rate, debts.get(cohort_id, 0.0))
        if asked is not None:
            requests.append(asked)
    return requests


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
        basket = setup.basket_for(cohort.tile)
        for bid in households_credit.floor_bids(cohort, _priced(setup, view, cohort.tile, priced_by_tile), budget,
                                                ledger.grown_units.get(cohort_id), setup.specs, view, basket):
            order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)


def _priced(setup, view, tile, priced_by_tile):
    if tile not in priced_by_tile:
        priced_by_tile[tile] = need_prices(setup.basket_for(tile), view, tile)
    return priced_by_tile[tile]
