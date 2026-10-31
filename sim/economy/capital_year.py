"""The capital markets' part of the economy's year, called from `Economy._run_year` so that file holds one line each.

Before the year's lending households trade shares to their portfolio fraction (portfolio_year.py), then the holders of shares and loans may sell (secondary_trade.py), the households short of
cash among them selling for the cash they would otherwise borrow; then depositors review their banks, and a bank
asked for more than it holds sells loans or fails (bank_runs.py).
"""
from typing import Dict, List, Sequence

from sim.constants import declare

from . import bank_runs, funds as fund_pools, insurance, lending, portfolio_year, secondary_trade
from .funds import POOLED_FUNDS
from .insurance import HARVEST, INSURANCE_UNDERWRITING, RISK_POOLING
from .secondary_trade import Shortfall
from .types import AgentId, FundsOffer

INSURER_FOUNDING_SHARE_OF_CASH = declare(
    "INSURER_FOUNDING_SHARE_OF_CASH", 0.5, kind="temporary_heuristic",
    unit="share of the founder's cash", source=None, confidence="D",
    retire="Complaints/106: a founder sizes an insurer's capital to the worst year of the hazards it would cover",
    why="The capital the richest household puts into the insurer it founds when none stands. Stands in for a founder's "
        "judgement of the claims the insurer must be able to meet.")


def holds_a_claim(record) -> bool:
    """Whether any household holds shares or a loan it could sell."""
    if any(holders for holders in record.shares.values()):
        return True
    return any(loan.lender in record.cohorts and secondary_trade.tradable(record, loan) for loan in record.loans)


def holds_units(record) -> bool:
    return any(fund.units for fund in record.capital.funds.values())


def shortfalls(setup, record, view, ledger) -> Dict[AgentId, Shortfall]:
    """What each household short of cash for its floors would borrow, and the most it would pay to."""
    requests = lending.household_requests(setup, record, view, ledger, {})
    return {request.borrower: Shortfall(request.amount, request.maximum_rate)
            for request in requests if request.borrower in record.cohorts}


def before_lending(setup, record, view, ledger, funds: Sequence[FundsOffer], year: int,
                   institutions: Sequence[str]) -> List[FundsOffer]:
    """The offers savers bring to the year's lending, after the funds' redemptions, secondary trading and the
    withdrawals from banks. A household short of cash redeems fund units first (at their worth), then sells claims."""
    money = setup.currency_id
    rate = view.interest_rate(money)
    funds = list(funds)
    trading = any(name in institutions for name in (secondary_trade.SHARE_TRADING, secondary_trade.BOND_MARKET))
    pooling = POOLED_FUNDS in institutions
    if pooling and not fund_pools.standing(record) and record.cohorts:
        fund_pools.found(record, max(sorted(record.cohorts), key=lambda cohort_id: record.book.balance(cohort_id, money)), year)
    short: Dict[AgentId, Shortfall] = {}
    if (pooling and holds_units(record)) or (trading and holds_a_claim(record)):
        short = shortfalls(setup, record, view, ledger)
    if pooling and short:
        funds, short = _redeem_units(setup, record, funds, short, rate, institutions)
    if pooling:
        funds = funds + [offer for offer in (fund_pools.offer_of(setup, record, fund, rate) for fund in fund_pools.standing(record))
                         if offer is not None]
    funds = portfolio_year.run(setup, record, view, funds, institutions)       # households buy or sell shares to their portfolio fraction
    if trading and (holds_a_claim(record) or any(offer.lender in record.capital.funds for offer in funds)):
        funds, _trades = secondary_trade.run(setup, record, funds, short, rate, institutions)
    if not record.banks:
        return funds
    return bank_runs.run(setup, record, funds, year, institutions, rate)


def _redeem_units(setup, record, funds, short, rate, institutions):
    """Households short of cash redeem the fund units they hold for what they need; what they still need after."""
    money = setup.currency_id
    remaining = dict(short)
    for fund in fund_pools.standing(record):
        for holder, shortfall in sorted(short.items()):
            if holder in fund.units and remaining[holder].amount > 0.0:
                before = record.book.balance(holder, money)
                funds = fund_pools.redeem_for_cash(setup, record, fund, holder, remaining[holder].amount, funds, rate, institutions)
                got = record.book.balance(holder, money) - before
                remaining[holder] = Shortfall(max(0.0, remaining[holder].amount - got), shortfall.borrowing_rate)
    return funds, {holder: shortfall for holder, shortfall in remaining.items() if shortfall.amount > 0.0}


def snapshot(record, money: str, funds: Sequence[FundsOffer]) -> Dict[AgentId, float]:
    """What each household saver holds beyond the funds it offered the year's lending: the cash it keeps."""
    return {offer.lender: record.book.balance(offer.lender, money) - offer.amount
            for offer in funds if offer.lender in record.cohorts and offer.currency == money}


def invest_idle(setup, record, view, funds: Sequence[FundsOffer], kept: Dict[AgentId, float], institutions: Sequence[str]) -> None:
    """The savings a household offered and did not lend or put in shares go into a fund: its founder's into a fund that
    has no units yet, others' into the fund whose expected yield is highest, when that is at least what it asked."""
    if POOLED_FUNDS not in institutions or not fund_pools.standing(record):
        return
    money = setup.currency_id
    rate = view.interest_rate(money)
    yields = {fund.agent_id: fund_pools.yield_of(setup, record, fund, rate) for fund in fund_pools.standing(record)}
    for offer in sorted(funds, key=lambda each: each.lender):
        if offer.lender not in kept:
            continue
        idle = record.book.balance(offer.lender, money) - kept[offer.lender]
        idle = min(idle, offer.amount)
        if idle <= 0.0:
            continue
        seeding = [fund for fund in fund_pools.standing(record) if fund.manager == offer.lender and not fund.units]
        if seeding:
            fund_pools.subscribe(setup, record, seeding[0], offer.lender, idle, rate)
            continue
        paying = [(yields[fund.agent_id], fund.agent_id) for fund in fund_pools.standing(record)
                  if yields[fund.agent_id] is not None and yields[fund.agent_id] >= offer.minimum_rate and fund.units]
        if paying:
            fund_pools.subscribe(setup, record, record.capital.funds[max(paying)[1]], offer.lender, idle, rate)


def note_exposure(setup, record, view, area_map, ledger, harvest_factor: float, institutions: Sequence[str]) -> None:
    """What each household's own plot would yield in a normal year, in money, which is what a harvest policy covers:
    this year's yield over the weather that shaped it, at the price of the good where it grew."""
    if not any(name in institutions for name in (INSURANCE_UNDERWRITING, RISK_POOLING)) or harvest_factor <= 0.0:
        return
    exposed = {}
    for cohort_id, grown in sorted(ledger.grown.items()):
        cohort = record.cohorts.get(cohort_id)
        if cohort is None:
            continue
        value = 0.0
        for good, quantity in sorted(grown.items()):
            price = view.price(good, area_map.area_of(good, cohort.tile))
            if price is not None:
                value += quantity * price
        if value > 0.0:
            exposed[cohort_id] = {HARVEST: value / harvest_factor}
    record.capital.exposure = exposed


def insure(setup, record, view, harvest_factor: float, year: int, institutions: Sequence[str]) -> None:
    """The year's insurance: the hazard's record prices cover, households that cannot bear the worst year buy it from
    a company or a mutual their society knows how to run, premiums are paid, and the year's weather settles the
    claims. The year then joins the record, so it prices the next year's cover and not this one's."""
    money = setup.currency_id
    state = record.capital
    rate = view.interest_rate(money)
    company_open, mutual_open = INSURANCE_UNDERWRITING in institutions, RISK_POOLING in institutions
    if (company_open or mutual_open) and state.exposure:
        _arrange_cover(record, money, rate, year, company_open, mutual_open)
        insurance.collect_premiums(record, money, rate)
    insurance.settle(record, money, HARVEST, insurance.loss_share_of(harvest_factor), year)
    for insurer in insurance.standing(state):
        insurance.pay_founder(record, insurer, money, insurance.required_capital(state, insurer.agent_id))


def _arrange_cover(record, money: str, rate: float, year: int, company_open: bool, mutual_open: bool) -> None:
    state = record.capital
    if HARVEST not in state.hazards:
        return
    price = insurance.premium_rate(state, HARVEST, rate)
    expected = insurance.expected_loss_share(state, HARVEST)
    wanting = {holder: held[HARVEST] for holder, held in sorted(state.exposure.items())
               if holder in record.cohorts and held.get(HARVEST, 0.0) > 0.0
               and insurance.wants_cover(record.book.balance(holder, money), held[HARVEST],
                                         min(price, expected) if mutual_open else price, state, HARVEST)}
    state.policies = [policy for policy in state.policies if policy.holder in wanting or policy.hazard != HARVEST]
    if not wanting:
        return
    richest = max(sorted(record.cohorts), key=lambda cohort_id: record.book.balance(cohort_id, money))
    mutuals, companies = insurance.standing(state, mutual=True), insurance.standing(state)
    if mutual_open and not mutuals:
        mutuals = [insurance.found(record, richest, 0.0, year, money, mutual=True)]
    if company_open and not mutual_open and not companies:
        capital = INSURER_FOUNDING_SHARE_OF_CASH * record.book.balance(richest, money)
        companies = [each for each in [insurance.found(record, richest, capital, year, money)] if each is not None]
    chosen = mutuals[0] if mutual_open and mutuals else (companies[0] if companies else None)
    if chosen is None:
        return
    for holder, insured in wanting.items():
        insurance.insure(state, chosen.agent_id, holder, HARVEST, insured)
