"""The opening's interest rate: where what households save meets what borrowers ask.

The civilisation's data rate is only the starting guess. Households' saving wish falls as the rate falls
(households_orders.savings_target), so at the data rate they may wish to keep far more than anyone borrows
and the income fixed point (opening_income.py) collapses to pay for what they do not save. The rate the
opening starts at is the one where, at full employment, the funds households offer equal the loans
borrowers ask for. Below the lowest rate lenders accept there is no lending to clear, so a society whose
saving exceeds its borrowing at that rate has no clearing rate: it opens at that lowest rate, as the
year's lending would take it, and the saving that remains needs an asset to buy (Complaint 538).
"""
import dataclasses
import math
from typing import Callable, Dict

from sim.world import capital_market

from . import lending
from .households_orders import HOUSEHOLD_TIME_PREFERENCE, goods_orders
from .households_basket import need_prices
from .market_memory import YearView
from .producers_close import working_capital_target
from .replaced import replaced
from .setup import labour_area

RATE_SEARCH_STEPS = 60               # a numerical bound: the search halves its interval each step
CLEARING_TOLERANCE_SHARE = 1e-3   # numerical: funds offered within this share of the larger side count as matching


@dataclasses.dataclass(frozen=True)
class RateSearch:
    rate: float            # the rate the opening starts at
    clears: bool           # funds offered match loans asked for at `rate`
    saving: float          # funds households offer at full employment and `rate`
    requests: float        # loans borrowers ask for at `rate`
    guess: float           # the civilisation's data rate
    lowest: float          # the lowest rate lenders accept


def clearing_rate(saving_at: Callable[[float], float], requests_at: Callable[[float], float],
                  lowest: float, guess: float) -> RateSearch:
    """The rate in [lowest, guess] where `saving_at(rate)` equals `requests_at(rate)`. When saving exceeds
    requests at every rate the search covers, the rate is the lowest and the search says it does not clear;
    when requests exceed saving at every rate it is the guess and the search says so too."""
    lowest = min(lowest, guess)
    tolerance = CLEARING_TOLERANCE_SHARE * max(abs(saving_at(guess)), abs(requests_at(guess)), 1e-300)

    def excess(rate):
        return saving_at(rate) - requests_at(rate)

    def found(rate, clears):
        return RateSearch(rate, clears, saving_at(rate), requests_at(rate), guess, lowest)

    if abs(excess(lowest)) <= tolerance:
        return found(lowest, True)
    if excess(lowest) > 0.0:
        return found(lowest, False)
    if abs(excess(guess)) <= tolerance:
        return found(guess, True)
    if excess(guess) < 0.0:
        return found(guess, False)
    low, high = lowest, guess        # excess is negative at low and positive at high
    for _step in range(RATE_SEARCH_STEPS):
        middle = 0.5 * (low + high)
        gap = excess(middle)
        if abs(gap) <= tolerance:
            return found(middle, True)
        low, high = (middle, high) if gap < 0.0 else (low, middle)
    return found(0.5 * (low + high), True)


def lowest_rate(setup, record) -> float:
    """The lowest rate lenders accept: households' time preference plus the inflation they expect, and no
    lower than the credit market's floor."""
    inflation = min((max(0.0, cohort.expected_inflation) for cohort in record.cohorts.values()), default=0.0)
    market_floor = capital_market.RATE_FLOOR_SHARE * setup.opening_rate
    return max(market_floor, HOUSEHOLD_TIME_PREFERENCE + inflation)


def _at_rate(record, setup, rate):
    """The record's market rate set to `rate` while a measurement runs; returns what to restore."""
    before = record.memory.rates.get(setup.currency_id)
    record.memory.rates[setup.currency_id] = rate
    return before


def households_saving(setup, record, view, per_head_total: float, rate: float) -> float:
    """Funds households offer to lenders in a year at the opening, were their incomes scaled so the total
    were `per_head_total` (income over all people): the cash they hold less what they spend and keep."""
    income = math.fsum(cohort.last_year_income for cohort in record.cohorts.values())
    if income <= 0.0:
        return 0.0
    scale = per_head_total / income
    before = _at_rate(record, setup, rate)
    try:
        offered = 0.0
        for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
            scaled = replaced(cohort, last_year_income=cohort.last_year_income * scale)
            orders = goods_orders(scaled, view, scaled.last_year_income, scaled.last_year_income,
                                  setup.basket_for(cohort.tile), setup.specs,
                                  need_prices(setup.basket_for(cohort.tile), view, cohort.tile))
            offered += math.fsum(offer.amount for offer in orders.funds_offers)
        return offered
    finally:
        record.memory.rates[setup.currency_id] = before


def borrowers_requests(setup, record, view, area_map, carriage, rate: float) -> float:
    """Loans asked for on the opening's first day at `rate`: producers' working capital beyond the cash they
    hold, merchants' cargo beyond theirs, and the requests already queued (the state's)."""
    before = _at_rate(record, setup, rate)
    try:
        money = setup.currency_id
        producers = math.fsum(
            max(0.0, working_capital_target(setup.recipes[producer.recipe_id], producer.capacity_runs,
                                            setup.opening_prices, setup.opening_wages)
                - record.book.balance(producer.agent_id, money))
            for producer in record.producers.values())
        merchants = math.fsum(request.amount for request in
                              lending.merchant_requests(setup, record, view, area_map, carriage))
        queued = math.fsum(request.amount for request in record.loan_requests)
        return producers + merchants + queued
    finally:
        record.memory.rates[setup.currency_id] = before


def find_rate(setup, record, area_map, carriage, full_employment_total: float) -> RateSearch:
    """The opening's rate, measured on an opened `record` (at the data rate) with households' income raised to
    the full-employment total."""
    view = YearView(record.memory, record.book, area_map, setup.currency_id, labour_area)
    return clearing_rate(
        lambda rate: households_saving(setup, record, view, full_employment_total, rate),
        lambda rate: borrowers_requests(setup, record, view, area_map, carriage, rate),
        lowest_rate(setup, record), setup.opening_rate)


def summary(search: RateSearch) -> Dict[str, object]:
    return dataclasses.asdict(search)
