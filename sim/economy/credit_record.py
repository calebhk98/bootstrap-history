"""What the economy keeps about credit from year to year: the contracts, the requests made at the last close, what
lenders have lost and what borrowers were lent."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from sim.contracts import TERM_LOAN, Contracts
from sim.loans.view import LoanRow
from sim.rekey import rekey

from . import credit_claims
from .record_parts import OwnedRecord
from .types import AgentId, CurrencyId, FundsOffer, Loan, LoanRequest, TileId


TRANSFER_TOLERANCE = 1e-9    # numerical: a share of a loan this close to the whole moves the loan itself


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
    claim_lives: Dict[AgentId, float] = field(default_factory=dict)       # each lender's mean loan term in years at the last year's close (claim_terms.py), before this year's defaults left the book
    book_claim_life: Optional[float] = None                              # the same over every claim on the book; None when the book was empty
    losses_seen: Dict[AgentId, float] = field(default_factory=dict)      # credit_losses as of the last year's close
    expansion_runs: Dict[AgentId, float] = field(default_factory=dict)   # capacity a loan request would build
    worn_runs: Dict[AgentId, float] = field(default_factory=dict)        # plant that wore out last year, to rebuild
    lenders_met: bool = False                                            # a lending has opened (open_lending), possibly with no savings on offer
    funds_offered: float = 0.0                                           # savings on offer at the last lending, home currency
    lowest_ask_offered: Optional[float] = None                           # the lowest rate any lender asked at the last lending; None before one
    offered_by_lender: Dict[AgentId, float] = field(default_factory=dict)  # each lender's savings on offer at the last lending
    ask_by_lender: Dict[AgentId, float] = field(default_factory=dict)    # each lender's lowest rate at the last lending
    lent_by_borrower: Dict[AgentId, float] = field(default_factory=dict)  # what each borrower was lent at the last lending
    lent_by_lender: Dict[AgentId, float] = field(default_factory=dict)   # what each lender put out at the last lending (lines counted: a room is claimed)
    credit_granted: Dict[AgentId, float] = field(default_factory=dict)   # what the last clearing granted each credit line asked for (credit_lines.py)
    clearing_year: int = -1                                              # the year the two sums below are of
    rate_times_lent: float = 0.0                                         # sum over the year's clearings of base rate times principal lent
    lent_in_clearings: float = 0.0                                       # principal the year's clearings lent
    last_clearing_cause: Optional[str] = None                            # why the last clearing lent nothing or held the rate (Clearing.cause); None when it priced loans
    land_yield: Optional[float] = None                                   # what a hectare of land earns over the price titles last sold at (title_sales_year.py); None before a sale
    public_premium: Optional[float] = None                                 # premium over the going rate the state's bonds offer households this year; None when out of reach (lender_ask.reachable_public_premium)

    AGENT_KEYED = ("remembered_defaults", "credit_losses", "loss_rates", "claim_lives", "losses_seen", "expansion_runs", "worn_runs",
                   "offered_by_lender", "ask_by_lender", "lent_by_borrower", "lent_by_lender", "credit_granted")
    SAVED_KEYS = {"contracts": "loans"}
    ENCODERS = {"contracts": lambda contracts: contracts.to_records(facilities=False)}
    DECODERS = {"contracts": _contracts_from,
                "loan_requests": lambda value: [LoanRequest(**each) for each in value]}

    OWNERS = ("credit_record", "lending", "banks", "bank_service", "bank_runs", "loss_memory", "debt_relief")

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

    def replace_loans(self, loans: List[Loan]) -> None:
        """The term loans are `loans` from now on."""
        self.contracts.term_loans = loans

    def add_loan(self, loan: Loan):
        """`loan` (a Contract, or any object with its fields) is struck last; the table keeps its own copy, and the loan's row is
        returned (changes to the Contract passed in do not reach the table; changes to the row do)."""
        store = self.contracts.loan_store
        return LoanRow(store, store.number_of_row(store.append_contract(loan)))

    def add_loans(self, loans: List[Loan]) -> None:
        self.contracts.loan_store.append_contracts(loans)

    def _parcel_id(self, loan: Loan, buyer: AgentId) -> str:
        """An id no contract holds yet for the part of `loan` that `buyer` takes: two parcels one buyer takes never share one."""
        store = self.contracts.loan_store
        taken = {store.texts[number] for number in store.table.number[:len(store)].tolist()}
        base = "%s|%s" % (loan.loan_id, buyer)
        candidate, number = base, 1
        while candidate in taken:
            number += 1
            candidate = "%s#%d" % (base, number)
        return candidate

    def transfer_loan(self, loan: Loan, buyer: AgentId, part: float) -> None:
        """`buyer` takes `part` (a share, at most one) of the loan's principal with the same share of its arrears and
        collateral: the whole loan changes lender, a part is split off as a contract of the buyer's own. `loan` is a row of the
        loan table (`record.credit.loans[...]`)."""
        if part >= 1.0 - TRANSFER_TOLERANCE:
            loan.lender = buyer
            return
        self.contracts.loan_store.split_off(loan.number, buyer, part, self._parcel_id(loan, buyer))

    def default_term_loans(self, borrower: AgentId) -> None:
        """The borrower's term loans leave the contracts as defaulted (the losses are booked by the caller)."""
        self.contracts.default(borrower, TERM_LOAN)

    def default_term_loans_of(self, borrowers) -> None:
        """`default_term_loans` for every borrower in `borrowers` at once."""
        self.contracts.default_many(set(borrowers), TERM_LOAN)

    def ask_for_loan(self, request: LoanRequest) -> None:
        """A request that waits for the next lending."""
        self.loan_requests.append(request)

    def ask_for_loans(self, requests: List[LoanRequest]) -> None:
        self.loan_requests.extend(requests)

    def plan_expansion(self, borrower: AgentId, runs: float) -> None:
        """The capacity `borrower`'s loan request would build; kept until the loan is struck."""
        self.expansion_runs[borrower] = runs

    def trim_expansion(self, borrower: AgentId, room: float) -> None:
        """The capacity planned for `borrower` falls to at most `room`; none left drops the plan."""
        if room > 0.0:
            self.expansion_runs[borrower] = min(self.expansion_runs.get(borrower, 0.0), room)
        else:
            self.expansion_runs.pop(borrower, None)

    def plan_rebuild(self, borrower: AgentId, runs: float) -> None:
        """The plant that wore out last year and `borrower` rebuilds."""
        self.worn_runs[borrower] = runs

    def forget_producer(self, borrower: AgentId) -> None:
        """Nothing is planned for `borrower` any more."""
        self.worn_runs.pop(borrower, None)
        self.expansion_runs.pop(borrower, None)

    def clear_expansion(self) -> None:
        self.expansion_runs = {}

    def take_requests(self) -> List[LoanRequest]:
        """The requests waiting, which are then cleared from the record."""
        requests, self.loan_requests = self.loan_requests, []
        return requests

    def take_rebuilds(self) -> Dict[AgentId, float]:
        """The plant to rebuild, which is then cleared from the record."""
        worn, self.worn_runs = self.worn_runs, {}
        return worn

    def open_lending(self, offers: Sequence[FundsOffer], currency: CurrencyId) -> None:
        """A lending begins: the savings on offer in `currency` (in all, by lender, and the lowest ask among them), and
        nothing lent or granted yet. A lender with several offers is on offer for their sum at the lowest of their asks."""
        self.lenders_met = True
        self.offered_by_lender, self.ask_by_lender = {}, {}
        for offer in offers:
            if offer.currency != currency or offer.amount <= 0.0:
                continue
            self.offered_by_lender[offer.lender] = self.offered_by_lender.get(offer.lender, 0.0) + offer.amount
            self.ask_by_lender[offer.lender] = min(offer.minimum_rate, self.ask_by_lender.get(offer.lender, offer.minimum_rate))
        self.funds_offered = sum(self.offered_by_lender.values())
        self.lowest_ask_offered = min(self.ask_by_lender.values(), default=None)
        self.lent_by_borrower = {}
        self.lent_by_lender = {}
        self.credit_granted = {}

    def grant_lines(self, granted: Dict[AgentId, float], asked: List[AgentId]) -> None:
        """What the clearing granted each credit line asked for; a line granted nothing is there with none."""
        self.credit_granted = granted
        for borrower in asked:
            granted.setdefault(borrower, 0.0)

    def note_clearing(self, year: int, rate: Optional[float], loans: Sequence[Loan], cause: Optional[str]) -> None:
        """A clearing of `year` priced `loans` at `rate` (or none: `cause` says why); the year's rate-times-principal sums gain it."""
        self.last_clearing_cause = cause
        lent = sum(loan.principal for loan in loans)
        if rate is None or lent <= 0.0:
            return
        if year != self.clearing_year:      # the first clearing of a new year that lent starts its sums afresh
            self.clearing_year, self.rate_times_lent, self.lent_in_clearings = year, 0.0, 0.0
        self.rate_times_lent += rate * lent
        self.lent_in_clearings += lent

    def set_public_premium(self, premium: Optional[float]) -> None:
        """The premium over the going rate the state's bonds offer households this year; None when out of their reach."""
        self.public_premium = premium

    def set_land_yield(self, yield_rate: Optional[float]) -> None:
        """What a hectare earns over the price titles last changed hands at; None before any sale."""
        self.land_yield = yield_rate

    def average_rate(self) -> Optional[float]:
        """The loan-weighted average base rate of the clearings of the latest year that lent; None before any did."""
        return self.rate_times_lent / self.lent_in_clearings if self.lent_in_clearings > 0.0 else None

    def note_lent(self, loan: Loan) -> None:
        self.lent_by_borrower[loan.borrower] = self.lent_by_borrower.get(loan.borrower, 0.0) + loan.principal
        self.lent_by_lender[loan.lender] = self.lent_by_lender.get(loan.lender, 0.0) + loan.principal

    def shrink_collateral(self, tile: TileId, keep: float) -> None:
        """Loans pledged on `tile` are secured by `keep` of the share they were, as the tile's land grows."""
        self.contracts.loan_store.shrink_collateral(tile, keep)

    def remember(self, defaults) -> None:
        """This year's defaults join what borrowers are remembered for; older ones fade."""
        self.remembered_defaults = credit_claims.remember_defaults(self.remembered_defaults, defaults)

    def add_loss(self, lender: AgentId, amount: float) -> None:
        """`lender` has lost `amount` more to default."""
        self.credit_losses[lender] = self.credit_losses.get(lender, 0.0) + amount

    def recover_loss(self, lender: AgentId, amount: float) -> None:
        """`lender` got `amount` of a past loss back; what it has lost never falls below zero."""
        self.credit_losses[lender] = max(0.0, self.credit_losses.get(lender, 0.0) - amount)
