"""What the economy keeps about credit from year to year: the contracts, the requests made at the last close, what
lenders have lost and what borrowers were lent."""
from dataclasses import dataclass, field
from typing import Dict, List

from sim.contracts import Contracts
from sim.rekey import rekey

from .record_parts import OwnedRecord
from .types import AgentId, Loan, LoanRequest


def _contracts_from(records) -> Contracts:
    contracts = Contracts()
    contracts.load_records(records)
    return contracts


@dataclass
class CreditRecord(OwnedRecord):
    contracts: Contracts = field(default_factory=Contracts)               # every debt: term loans here, facilities the purses'
    loan_requests: List[LoanRequest] = field(default_factory=list)       # made at last year's close
    remembered_defaults: Dict[AgentId, float] = field(default_factory=dict)   # losses a borrower caused, fading
    credit_losses: Dict[AgentId, float] = field(default_factory=dict)    # what each lender has lost to default
    loss_rates: Dict[AgentId, float] = field(default_factory=dict)       # each lender's expected loss per year of exposure, aging (loss_memory.py)
    losses_seen: Dict[AgentId, float] = field(default_factory=dict)      # credit_losses as of the last year's close
    expansion_runs: Dict[AgentId, float] = field(default_factory=dict)   # capacity a loan request would build
    worn_runs: Dict[AgentId, float] = field(default_factory=dict)        # plant that wore out last year, to rebuild
    funds_offered: float = 0.0                                           # savings on offer at the last lending, home currency
    lent_by_borrower: Dict[AgentId, float] = field(default_factory=dict)  # what each borrower was lent at the last lending
    credit_granted: Dict[AgentId, float] = field(default_factory=dict)   # what the last clearing granted each credit line asked for (credit_lines.py)

    AGENT_KEYED = ("remembered_defaults", "credit_losses", "loss_rates", "losses_seen", "expansion_runs", "worn_runs",
                   "lent_by_borrower", "credit_granted")
    SAVED_KEYS = {"contracts": "loans"}
    ENCODERS = {"contracts": lambda contracts: contracts.to_records(facilities=False)}
    DECODERS = {"contracts": _contracts_from,
                "loan_requests": lambda value: [LoanRequest(**each) for each in value]}

    @property
    def loans(self) -> List[Loan]:
        """The term loans, in the order they were struck."""
        return self.contracts.term_loans

    @loans.setter
    def loans(self, loans: List[Loan]) -> None:
        self.contracts.term_loans = loans

    def rename_agent(self, old: AgentId, new: AgentId) -> None:
        """`old` becomes `new` in the contracts, the stores keyed by an agent id and as the borrower of a request."""
        self.contracts.rename(old, new)
        super().rename_agent(old, new)
        self.loan_requests = rekey(self.loan_requests, old, new)

    def add_loss(self, lender: AgentId, amount: float) -> None:
        """`lender` has lost `amount` more to default."""
        self.credit_losses[lender] = self.credit_losses.get(lender, 0.0) + amount

    def recover_loss(self, lender: AgentId, amount: float) -> None:
        """`lender` got `amount` of a past loss back; what it has lost never falls below zero."""
        self.credit_losses[lender] = max(0.0, self.credit_losses.get(lender, 0.0) - amount)
