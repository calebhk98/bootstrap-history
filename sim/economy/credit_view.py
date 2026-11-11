"""The market view with the credit market's holdings added: what an agent is owed and what it owns of firms.

A plain `YearView` answers the same three questions (`equity`, `claims`, `loss_rate`) with zero: it has no loans or firms.
"""
from typing import Callable, Mapping, Optional, Sequence

from sim.loans.view import LoanList

from . import lender_ask
from .credit_claims import claims_by_lender
from .market_memory import YearView
from .types import AgentId, CurrencyId, Loan


class CreditView(YearView):
    """A `YearView` that also answers `claims`, from the loans as they stand when asked."""

    def __init__(self, *arguments, loans: Callable[[], Sequence[Loan]] = lambda: (),
                 equity: Callable[["CreditView"], Mapping[AgentId, float]] = lambda view: {},
                 loss_rates: Callable[[], Mapping[AgentId, float]] = lambda: {},
                 pooled: Callable[[AgentId], float] = lambda agent: 0.0,
                 public_premium: Callable[[], Optional[float]] = lambda: None,
                 land_yield: Callable[[], Optional[float]] = lambda: None, **keywords) -> None:
        super().__init__(*arguments, **keywords)
        self._loans = loans
        self._pooled = pooled             # what the actors' pool owes an agent, in the economy's unit
        self._loss_rates = loss_rates
        self._land_yield = land_yield      # what a hectare earns over the price titles last sold at, in the economy's own currency
        self._public_premium = public_premium  # the state's bond premium in reach of a lender, in the economy's own currency
        self._equity_of_all = equity      # reads the view once, when first asked, and keeps the answer
        self._equity = None
        self._worths = None               # the producers' net worths (equity.producer_worths), built once for the view
        self._claims_seen = None          # (loan list, its length, its last loan) the claims below were summed over
        self._claims: dict = {}           # currency -> claims_by_lender over those loans

    def claims(self, agent: AgentId, currency: CurrencyId) -> float:
        """What the agent expects to collect on loans it has made and from the actors' pool it has deposited with."""
        loans = self._loans()
        seen = self._claims_seen
        stamp = loans.store.version if isinstance(loans, LoanList) else len(loans)       # the table's version, a plain list's length
        last = None if isinstance(loans, LoanList) or not loans else loans[-1]
        if seen is None or seen[0] is not loans or seen[1] != stamp or seen[2] is not last:
            self._claims_seen, self._claims = (loans, stamp, last), {}
        if currency not in self._claims:
            self._claims[currency] = claims_by_lender(loans, currency)
        return self._claims[currency].get(agent, 0.0) + self._pooled(agent)


    def loss_rate(self, agent: AgentId, currency: CurrencyId) -> float:
        """The loss the agent expects per year of credit exposure (lender_ask.loss_rate)."""
        return lender_ask.loss_rate(self._loss_rates().get(agent, 0.0))

    def land_yield(self, currency: CurrencyId) -> Optional[float]:
        """What a title to land yields its holder over the price titles last changed hands at (title_sales_year); only the economy's own currency has one."""
        return self._land_yield() if currency == self._currency else None

    def public_premium(self, currency: CurrencyId) -> Optional[float]:
        """The premium over the going rate of the state's bonds where a lender can buy them (lender_ask.reachable_public_premium); only the economy's own currency has one."""
        return self._public_premium() if currency == self._currency else None

    def equity(self, agent: AgentId) -> float:
        """What the agent owns of the firms (equity.py), at the prices this view carries."""
        if self._equity is None:
            self._equity = dict(self._equity_of_all(self))
        return self._equity.get(agent, 0.0)


    def kept_worths(self, build: Callable[[], Mapping[AgentId, float]]) -> Mapping[AgentId, float]:
        """The producers' net worths, built by `build()` when first asked and kept for the view's life like `equity`, which is split
        from them: the households' share wealth and the portfolio trading read one build. Read only."""
        if self._worths is None:
            self._worths = build()
        return self._worths
