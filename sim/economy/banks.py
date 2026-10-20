"""A bank is an agent with a purse: households deposit their savings with it, it lends them on, and it can fail.

A deposit is a term loan in the shared registry whose lender is the depositor and whose borrower is the bank, at
the rate the depositor asked as a lender, so the credit view already counts it in the depositor's wealth and
against the bank. Households pledge their funds to the bank; the bank offers them, with the cash it holds beyond
its reserve, to the credit market like any lender, asking the depositors' rates plus its spread (bank_spread.py), and takes the
deposit only when it lends, so it pays interest on no more than it has lent (the way the actors' pool takes
funds as they are drawn). The loans it makes are ordinary loans with the bank as lender, serviced
and defaulted by the one rule (credit.py). The bank pays its depositors out of what its borrowers paid it
(bank_service.py). It is insolvent when what it holds and is owed, as its lenders would value it, falls short of
what it owes, which happens only once its capital is gone. Its depositors then ask for their money back; what it
cannot pay is arrears, which the one default rule writes off, so the depositors bear the loss.

A society founds banks only once it holds the institution (`YearInputs.institutions` names `DEPOSIT_BANKING`); a
household with the means founds one when none stands. Any agent may found one with `found`.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from sim.constants import declare
from sim.world import capital_market

from . import bank_spread, credit_claims
from .types import AgentId, FundsOffer, Loan, Transfer

DEPOSIT_BANKING = "deposit_banking"        # the institution a society must hold for its households to found banks
DEPOSIT_TERM_YEARS = 1.0e9                 # a deposit has no term: the installment due each year is nil until the depositor demands it
DEPOSIT_PURPOSE = "deposit"
BANK_FOUNDING_SHARE_OF_CASH = declare(
    "BANK_FOUNDING_SHARE_OF_CASH", 0.5, kind="temporary_heuristic",
    unit="share of the founder's cash", source=None, confidence="D",
    retire="Complaints/106: a founder weighs the bank's expected return against its other uses of the capital",
    why="The capital a household with the means puts into the bank it founds. Stands in for a founder's "
        "assessment of the deposits it can attract and the loans it can place.")
BANK_CAPITAL_SHARE_OF_LOANS = declare(
    "BANK_CAPITAL_SHARE_OF_LOANS", 0.1, kind="temporary_heuristic",
    unit="share of the loans a bank has out", source=None, confidence="D",
    retire="Complaints/106: a bank sizes its capital to the losses its loan book can bear",
    why="The capital a bank keeps behind its loans before paying its founder a dividend. Stands in for its "
        "owners' judgement of the losses the loans could bring.")


@dataclass
class Bank:
    agent_id: AgentId
    founder: AgentId
    founded_year: int
    reserve_share: float = capital_market.LENDER_RESERVE_SHARE   # share of its deposits it keeps in cash and does not lend
    failed_year: int = -1                                        # the year its depositors ran; below zero while it stands
    paid_in: float = 0.0                                         # the capital its founder put in, which no dividend returns


def is_deposit(record, loan: Loan) -> bool:
    return loan.borrower in record.banks


def standing(record) -> List[Bank]:
    return [bank for _id, bank in sorted(record.banks.items()) if bank.failed_year < 0]


def deposits_of(record, bank_id: AgentId) -> List[Loan]:
    return [loan for loan in record.loans if loan.borrower == bank_id]


def owed_to_depositors(record, bank_id: AgentId) -> float:
    return sum(loan.principal + loan.arrears for loan in deposits_of(record, bank_id))


def assets_of(record, bank_id: AgentId, money: str) -> float:
    """What the bank holds in cash and is owed on its loans, as the loans' lenders value them."""
    claims = credit_claims.claims_by_lender((loan for loan in record.loans if loan.lender == bank_id), money)
    return record.book.balance(bank_id, money) + claims.get(bank_id, 0.0)


def capital_of(record, bank_id: AgentId, money: str) -> float:
    """What would be left for the founder if the bank paid its depositors everything now."""
    return assets_of(record, bank_id, money) - owed_to_depositors(record, bank_id)


def loans_out(record, bank_id: AgentId) -> float:
    return sum(loan.principal for loan in record.loans if loan.lender == bank_id and not is_deposit(record, loan))


def found(record, founder: AgentId, capital: float, year: int, money: str,
          reserve_share: Optional[float] = None) -> Optional[Bank]:
    """The founder puts `capital` of its cash into a new bank. None when it holds less."""
    capital = min(capital, record.book.balance(founder, money))
    if capital <= 0.0:
        return None
    bank_id = "bank:%d" % len(record.banks)
    bank = Bank(bank_id, founder, year, paid_in=capital)
    if reserve_share is not None:
        bank.reserve_share = reserve_share
    record.book.transfer(Transfer(founder, bank_id, money, capital, "bank capital"))
    record.banks[bank_id] = bank
    return bank


def found_when_allowed(setup, record, institutions: Sequence[str], year: int) -> Optional[Bank]:
    """The richest household founds a bank when the society holds the institution and none stands."""
    if DEPOSIT_BANKING not in institutions or standing(record) or not record.cohorts:
        return None
    money = setup.currency_id
    founder = max(sorted(record.cohorts), key=lambda cohort_id: record.book.balance(cohort_id, money))
    return found(record, founder, BANK_FOUNDING_SHARE_OF_CASH * record.book.balance(founder, money), year, money)


def solvency(record, bank_id: AgentId, money: str) -> float:
    """Assets over what is owed depositors; one when it owes nothing."""
    owed = owed_to_depositors(record, bank_id)
    return assets_of(record, bank_id, money) / owed if owed > 0.0 else 1.0


def run_on_insolvent(record, money: str, year: int) -> List[AgentId]:
    """Depositors review their banks as the year opens: where a bank's assets no longer cover its deposits they all
    ask for their money. The bank stops lending and taking deposits, and each deposit falls due at the year's end.
    Returns the banks that failed."""
    failed = []
    for bank in standing(record):
        if capital_of(record, bank.agent_id, money) < 0.0:
            bank.failed_year = year
            failed.append(bank.agent_id)
            for deposit in deposits_of(record, bank.agent_id):
                deposit.years_left = 1.0
    return failed


def free_cash(record, bank: Bank, money: str) -> float:
    """The cash the bank holds beyond the reserve it keeps against its deposits."""
    return max(0.0, record.book.balance(bank.agent_id, money) - bank.reserve_share * owed_to_depositors(record, bank.agent_id))


def spread_of(record, bank: Bank, money: str) -> float:
    """What the bank adds to its depositors' rate: its loss record and how thin its capital is behind its loans."""
    loans = loans_out(record, bank.agent_id)
    return bank_spread.spread(record.loss_rates.get(bank.agent_id, 0.0), loans,
                              capital_of(record, bank.agent_id, money), BANK_CAPITAL_SHARE_OF_LOANS)


def ask_of(record, bank: Bank, money: str, pledged: Sequence[FundsOffer] = ()) -> float:
    """The rate the bank asks to lend: what it pays its depositors on average, plus its spread. The depositors are
    those who would place funds with it this year, or those it has."""
    rated = [(offer.amount, offer.minimum_rate) for offer in pledged] or [
        (deposit.principal, deposit.rate) for deposit in deposits_of(record, bank.agent_id)]
    total = sum(amount for amount, _rate in rated)
    return (sum(amount * rate for amount, rate in rated) / total if total > 0.0 else 0.0) + spread_of(record, bank, money)


def intermediate(setup, record, offers: Sequence[FundsOffer], year: int, institutions: Sequence[str] = (),
                 ) -> Tuple[List[FundsOffer], Dict[AgentId, List[FundsOffer]]]:
    """(the year's offers, the funds pledged to each bank) once households have pledged theirs to a bank. A
    household that can pledge funds to a standing bank, the best covered, does; its cash stays with it until the
    bank lends (`draw_deposits`), so a deposit exists only for a loan. The bank offers what it holds beyond its
    reserve and what its depositors pledged, less the reserve it must keep against the deposits they would then
    make. Failed banks are run on first. Offers from households without a bank to go to stand."""
    money = setup.currency_id
    run_on_insolvent(record, money, year)
    found_when_allowed(setup, record, institutions, year)
    standing_banks = standing(record)
    if not standing_banks:
        return list(offers), {}
    best = max(standing_banks, key=lambda bank: (solvency(record, bank.agent_id, money), bank.agent_id))
    kept: List[FundsOffer] = []
    pledged: List[FundsOffer] = []
    for offer in offers:
        if offer.lender in record.cohorts and offer.currency == money and offer.amount > 0.0:
            pledged.append(offer)
        else:
            kept.append(offer)
    placed = {best.agent_id: pledged}
    for bank in standing_banks:
        funds = free_cash(record, bank, money) + (1.0 - bank.reserve_share) * sum(
            offer.amount for offer in placed.get(bank.agent_id, ()))
        if funds > 0.0:
            kept.append(FundsOffer(bank.agent_id, money, funds, ask_of(record, bank, money, placed.get(bank.agent_id, ()))))
    return kept, placed


def draw_deposits(record, loans: Sequence[Loan], pledged: Dict[AgentId, List[FundsOffer]], year: int, money: str,
                  ) -> None:
    """The banks lent `loans`: each takes its depositors' pledged funds for what its own free cash did not cover,
    keeping the reserve against them, and the deposits become the depositors' claims on it. Call before the loans
    are disbursed."""
    lent: Dict[AgentId, float] = {}
    for loan in loans:
        if loan.lender in record.banks:
            lent[loan.lender] = lent.get(loan.lender, 0.0) + loan.principal
    placed: List[Transfer] = []
    for bank_id, total in sorted(lent.items()):
        bank = record.banks[bank_id]
        offers = [offer for offer in pledged.get(bank_id, ()) if offer.amount > 0.0]
        pledged_total = sum(offer.amount for offer in offers)
        needed = (total - free_cash(record, bank, money)) / (1.0 - bank.reserve_share)
        if needed <= 0.0 or pledged_total <= 0.0:
            continue
        share = min(1.0, needed / pledged_total)
        for offer in offers:
            amount = offer.amount * share
            placed.append(Transfer(offer.lender, bank_id, money, amount, DEPOSIT_PURPOSE))
            record.loans.append(Loan("deposit:%d:%s:%s" % (year, bank_id, offer.lender), offer.lender, bank_id, money,
                                     amount, rate=offer.minimum_rate, years_left=DEPOSIT_TERM_YEARS, issued_year=year))
    record.book.transfer_many(placed)
