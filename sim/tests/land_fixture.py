"""A village for rule tests of land concentration: equal smallholder households on one tile that borrow
against their plots when a harvest falls short of their floor, and a lender that can take the plot on default.
Plain records, no whole game: each year is the credit, spending, harvest and loan-service rules called in turn.
Harvests are an input of the scenario (`income_for(household, year)`), so a shock is built, not drawn here."""
import dataclasses
import types
from typing import Callable, Dict, Optional

from sim.economy import credit, credit_claims, lending, titles, titles_inheritance
from sim.economy.accounts import Book
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.households_credit import subsistence_request
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec, FundsOffer, TileSpec, Transfer

MONEY = "coin"
TILE = "village"
LENDER = "lender:village"
RATE = 0.05
RENT_PER_HECTARE = 2.0
FLOOR_COST = 100.0                 # what a household must spend a year
NORMAL_INCOME = 300.0
FAILED_INCOME = 0.1 * FLOOR_COST
BUFFER_FLOORS = 0.5                # the cash a household keeps, in years of its floor; it spends what it holds above that


def village(households: int = 10, lender_is_a_household: bool = False):
    """(setup, record): equal households each holding an equal share of the tile. The lender is an outsider holding
    no land, or (`lender_is_a_household`) the last household, which is then rich in cash."""
    tile = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0)
    setup = types.SimpleNamespace(currency_id=MONEY, tiles={TILE: tile}, opening_rate=RATE)
    record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec(MONEY, "fiat", None, 0.0, None))
    for cohort in cohorts_for_tile(TILE, 30.0 * households, 0.5, 0.4, class_count=households):
        record.cohorts[cohort.agent_id] = dataclasses.replace(cohort, ownership_share=1.0 / households,
                                                              last_year_income=NORMAL_INCOME)
    titles.seed(record)
    record.land_rent = {TILE: RENT_PER_HECTARE}
    lender = household_ids(record)[-1] if lender_is_a_household else LENDER
    record.book.transfer(Transfer("edge:legacy", lender, MONEY, 1e9, "opening"))
    return setup, record


def household_ids(record):
    return sorted(record.cohorts)


def borrow_and_spend(setup, record, year: int, lender: str = LENDER) -> None:
    """Every household asks for what its cash does not cover of its floor, pledging its free plot; the credit market
    clears all the requests at once (loan ids are per clearing); each then spends its floor."""
    debts = credit_claims.debts_by_borrower(record.loans, MONEY)
    requests = []
    for household in household_ids(record):
        cohort = record.cohorts[household]
        asked = subsistence_request(cohort, FLOOR_COST - record.book.balance(household, MONEY), MONEY, RATE,
                                    debts.get(household, 0.0))
        if asked is not None:
            requests.append(lending._pledging_title(setup, record, cohort, asked, RATE))
    if requests:
        loans, _rate, _unmet = credit.clear(requests, [FundsOffer(lender, MONEY, 1e8, RATE)], MONEY, RATE, debts,
                                            credit_claims.arrears_history(record.loans, record.remembered_defaults),
                                            year=year)
        record.book.transfer_many(credit.disbursements(loans))
        record.loans.extend(loans)
    for household in household_ids(record):
        record.book.transfer(Transfer(household, "edge:market", MONEY,
                                      min(FLOOR_COST, record.book.balance(household, MONEY)), "spending"))


def spend_above_buffer(record, household: str) -> None:
    """A household with nothing to save for beyond a small buffer spends the rest, so a run of bad harvests meets
    empty hands (a buffer-stock household that saved everything would never borrow)."""
    surplus = record.book.balance(household, MONEY) - BUFFER_FLOORS * FLOOR_COST
    if surplus > 0.0:
        record.book.transfer(Transfer(household, "edge:market", MONEY, surplus, "spending"))


def run(setup, record, years: int, income_for: Callable[[str, int], float], inheritance: bool = False,
        on_year: Optional[Callable[[int], None]] = None, lender: Optional[str] = None,
        partible_share: float = titles_inheritance.PARTIBLE_ESTATE_SHARE) -> None:
    """Each year every household borrows and spends, harvests `income_for(household, year)`, and the year's loans
    are serviced (a default passes the pledged plot to the lender); with `inheritance` the estates then divide.
    `lender` (default: the outside lender) is the household cohort that lends, when the lender is one of the village."""
    for year in range(years):
        borrow_and_spend(setup, record, year, lender or LENDER)
        for household in household_ids(record):
            record.book.transfer(Transfer("edge:harvest", household, MONEY, income_for(household, year), "harvest"))
        lending.service(record, MONEY, year)
        for household in household_ids(record):
            if household != lender:
                spend_above_buffer(record, household)
        if inheritance:
            titles_inheritance.divide_estates(record, partible_share=partible_share)
        if on_year is not None:
            on_year(year)


def hectares_held(setup, record) -> Dict[str, float]:
    """Hectares each holder holds by title, households and the lender alike."""
    from sim.economy import titles_concentration
    return titles_concentration.hectares_by_holder(setup.tiles, record)
