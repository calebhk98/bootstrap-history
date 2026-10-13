"""The market view with the credit market's holdings added: what an agent is owed.

`claims_of(view, agent, currency)` reads it from any view and gives zero from one that has no loans.
"""
from typing import Callable, Sequence

from .credit_claims import claims_by_lender
from .market_memory import YearView
from .types import AgentId, CurrencyId, Loan


class CreditView(YearView):
    """A `YearView` that also answers `claims`, from the loans as they stand when asked."""

    def __init__(self, *arguments, loans: Callable[[], Sequence[Loan]] = lambda: (), **keywords) -> None:
        super().__init__(*arguments, **keywords)
        self._loans = loans
        self._claims_seen = None          # (loan list, its length, its last loan) the claims below were summed over
        self._claims: dict = {}           # currency -> claims_by_lender over those loans

    def claims(self, agent: AgentId, currency: CurrencyId) -> float:
        """What the agent expects to collect on loans it has made."""
        loans = self._loans()
        seen = self._claims_seen
        last = loans[-1] if loans else None
        if seen is None or seen[0] is not loans or seen[1] != len(loans) or seen[2] is not last:
            self._claims_seen, self._claims = (loans, len(loans), last), {}
        if currency not in self._claims:
            self._claims[currency] = claims_by_lender(loans, currency)
        return self._claims[currency].get(agent, 0.0)


def claims_of(view, agent: AgentId, currency: CurrencyId) -> float:
    reader = getattr(view, "claims", None)
    return reader(agent, currency) if reader is not None else 0.0
