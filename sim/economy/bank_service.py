"""A bank's year end: it pays its depositors what it can, the one default rule writes off what it cannot, and the
founder is paid what the bank holds beyond its capital.

Called by `lending.service` after the year's loans were serviced, so the bank pays out of what its borrowers have
just paid it. The depositors share what the bank can pay in proportion to what each is owed (a bank does not
pay the first in line); a deposit asked back falls due in full (banks.run_on_insolvent), and one the bank pays
less than the default share of is a default of the bank.
"""
from typing import Dict, List, Tuple

from . import banks, credit, credit_claims, ownership
from .types import AgentId, Loan, Transfer

EPSILON = 1e-9


def service_deposits(record, money: str, year: int) -> Dict[AgentId, float]:
    """Pay every bank's depositors their interest and what is due; book the defaults and the founder's dividend.
    Returns the interest each depositor received."""
    received: Dict[AgentId, float] = {}
    for bank_id, bank in sorted(record.banks.items()):
        deposits = [loan for loan in banks.deposits_of(record, bank_id) if loan.issued_year < year]
        if deposits:
            kept, defaults, interest = _pay(record, bank_id, deposits, money, year)
            for lender, amount in interest.items():
                received[lender] = received.get(lender, 0.0) + amount
            untouched = [loan for loan in record.loans if loan.borrower != bank_id or loan.issued_year >= year]
            record.loans = untouched + kept
            for lender, lost in credit_claims.losses_by_lender(defaults).items():
                record.credit_losses[lender] = record.credit_losses.get(lender, 0.0) + lost
            record.remembered_defaults = credit_claims.remember_defaults(record.remembered_defaults, defaults)
            if defaults and bank.failed_year < 0:
                banks.fail(record, bank, year, money)
        if bank.failed_year < 0:
            _return_idle(record, bank, money)
            _pay_founder(record, bank, money)
    return received


def _pay(record, bank_id: AgentId, deposits: List[Loan], money: str, year: int,
         ) -> Tuple[List[Loan], List, Dict[AgentId, float]]:
    due = {loan.loan_id: _due(loan) for loan in deposits}
    total = sum(due.values())
    cash = max(0.0, record.book.balance(bank_id, money))
    share = min(1.0, cash / total) if total > 0.0 else 0.0
    kept: List[Loan] = []
    defaults: List = []
    interest: Dict[AgentId, float] = {}
    for loan in sorted(deposits, key=lambda each: each.loan_id):
        transfers, serviced, lost, receipts = credit.service_split([loan], {bank_id: due[loan.loan_id] * share}, year)
        record.book.transfer_many(transfers)
        kept.extend(serviced)
        defaults.extend(lost)
        for lender, receipt in receipts.items():
            interest[lender] = interest.get(lender, 0.0) + receipt.interest
    return kept, defaults, interest


def _return_idle(record, bank, money: str) -> None:
    """Cash repaid to the bank beyond its reserve and its capital goes back to the depositors, in proportion, as
    repaid deposits: the bank pays interest only on what it has lent."""
    deposits = banks.deposits_of(record, bank.agent_id)
    owed = sum(loan.principal for loan in deposits)
    idle = (record.book.balance(bank.agent_id, money) - bank.reserve_share * banks.owed_to_depositors(record, bank.agent_id)
            - max(0.0, banks.capital_of(record, bank.agent_id, money)))
    paid = min(idle, owed)
    if paid <= EPSILON or owed <= 0.0:
        return
    record.book.transfer_many([Transfer(bank.agent_id, loan.lender, money, paid * loan.principal / owed, "deposit repaid")
                               for loan in deposits])
    for loan in deposits:
        loan.principal -= paid * loan.principal / owed
    record.loans = [loan for loan in record.loans
                    if loan.borrower != bank.agent_id or loan.principal > EPSILON or loan.arrears > EPSILON]


def _due(loan: Loan) -> float:
    installment = loan.principal if loan.years_left <= 1.0 else loan.principal / loan.years_left
    return loan.arrears + loan.principal * loan.rate + installment


def _pay_founder(record, bank, money: str) -> None:
    """What the bank holds beyond its deposits, the capital its founder paid in and the capital it keeps behind its
    loans goes to the founder as a dividend (as far as it is cash beyond the reserve), shared on to the founder's
    tile like any dividend."""
    owed = banks.owed_to_depositors(record, bank.agent_id)
    required = max(bank.paid_in, banks.BANK_CAPITAL_SHARE_OF_LOANS * banks.loans_out(record, bank.agent_id))
    surplus = banks.capital_of(record, bank.agent_id, money) - required
    cash = record.book.balance(bank.agent_id, money) - bank.reserve_share * owed
    paid = min(surplus, cash)
    if paid > 0.0:
        record.book.transfer_many(ownership.spread(record, [Transfer(bank.agent_id, bank.founder, money, paid, "dividend")]))
