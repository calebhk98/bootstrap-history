"""The market view with the credit market's holdings added: what an agent is owed and what it owns of firms.

A plain `YearView` answers the same three questions (`equity`, `claims`, `loss_rate`) with zero: it has no loans or firms.
"""
from typing import Callable, Mapping, Sequence

from . import lender_ask
from .credit_claims import claims_by_lender
from .market_memory import YearView
from .types import AgentId, CurrencyId, Loan


class CreditView(YearView):
    """A `YearView` that also answers `claims`, from the loans as they stand when asked."""

    def __init__(self, *arguments, loans: Callable[[], Sequence[Loan]] = lambda: (),
                 equity: Callable[["CreditView"], Mapping[AgentId, float]] = lambda view: {},
                 loss_rates: Callable[[], Mapping[AgentId, float]] = lambda: {},
                 pooled: Callable[[AgentId], float] = lambda agent: 0.0, **keywords) -> None:
        super().__init__(*arguments, **keywords)
        self._loans = loans
        self._pooled = pooled             # what the actors' pool owes an agent, in the economy's unit
        self._loss_rates = loss_rates
        self._equity_of_all = equity      # reads the view once, when first asked, and keeps the answer
        self._equity = None
        self._claims_seen = None          # (loan list, its length, its last loan) the claims below were summed over
        self._claims: dict = {}           # currency -> claims_by_lender over those loans

    def claims(self, agent: AgentId, currency: CurrencyId) -> float:
        """What the agent expects to collect on loans it has made and from the actors' pool it has deposited with."""
        loans = self._loans()
        seen = self._claims_seen
        last = loans[-1] if loans else None
        if seen is None or seen[0] is not loans or seen[1] != len(loans) or seen[2] is not last:
            self._claims_seen, self._claims = (loans, len(loans), last), {}
        if currency not in self._claims:
            self._claims[currency] = claims_by_lender(loans, currency)
        return self._claims[currency].get(agent, 0.0) + self._pooled(agent)


    def loss_rate(self, agent: AgentId, currency: CurrencyId) -> float:
        """The loss the agent expects per year of credit exposure (lender_ask.loss_rate)."""
        return lender_ask.loss_rate(self._loss_rates().get(agent, 0.0))

    def equity(self, agent: AgentId) -> float:
        """What the agent owns of the firms (equity.py), at the prices this view carries."""
        if self._equity is None:
            self._equity = dict(self._equity_of_all(self))
        return self._equity.get(agent, 0.0)

