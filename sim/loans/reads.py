"""The per-agent figures of the loans (what lenders are owed, what borrowers owe, what the market holds against a borrower), read
from the table by the kernels of `read_kernels.py` and handed back as the dicts the credit rules take: in the order the agents first
appear among the loans, each total added in loan order."""
from typing import Dict, Mapping, Optional

import numpy

from .read_kernels import claim_values, debt_total_by_agent, total_by_agent
from .store import LoanStore


def _selected(store: LoanStore, currency: Optional[str]) -> Optional[numpy.ndarray]:
    """A boolean per row for the loans in `currency` (all when none is named); None when no loan can be in it."""
    count = len(store)
    if currency is None:
        return numpy.ones(count, dtype=numpy.bool_)
    number = store.currencies.find(currency)
    if number is None:
        return None
    return store.table.currency[:count] == number


def totals_by_agent(store: LoanStore, agent_column: numpy.ndarray, values: numpy.ndarray, selected: Optional[numpy.ndarray],
                    start: Optional[Mapping[str, float]] = None) -> Dict[str, float]:
    """{agent: sum of its selected rows' values} added in row order from `start` (a mapping, copied first: its keys come first),
    the agents new to it in order of first appearance."""
    result: Dict[str, float] = dict(start) if start else {}
    if selected is None or len(store) == 0:
        return result
    totals, first_row = total_by_agent(agent_column, values, selected, len(store), _begin(store, result))
    return _listed(store, result, totals, first_row)


def _begin(store: LoanStore, start: Mapping[str, float]) -> numpy.ndarray:
    """The running total each agent number begins at: its value in `start`, else nothing."""
    begin = numpy.zeros(len(store.agents))
    for name, value in start.items():
        number = store.agents.find(name)
        if number is not None:
            begin[number] = value
    return begin


def _listed(store: LoanStore, result: Dict[str, float], totals: numpy.ndarray, first_row: numpy.ndarray) -> Dict[str, float]:
    """`result` with the agents that have loans set to their totals, the new ones in order of first appearance."""
    names = store.agents.name_list
    seen = numpy.nonzero(first_row >= 0)[0]
    for number in seen[numpy.argsort(first_row[seen], kind="stable")].tolist():
        result[names[number]] = float(totals[number])
    return result


def claims_by_lender(store: LoanStore, arrears_share: float, currency: Optional[str] = None) -> Dict[str, float]:
    """What each lender expects to collect (credit_claims.claim_value of each loan, added in loan order)."""
    table = store.table
    claims = claim_values(table.principal, table.arrears, len(store), arrears_share)
    return totals_by_agent(store, table.lender, claims, _selected(store, currency))


def debts_by_borrower(store: LoanStore, currency: Optional[str] = None) -> Dict[str, float]:
    """What each borrower owes: principal and arrears."""
    selected = _selected(store, currency)
    if selected is None or len(store) == 0:
        return {}
    table = store.table
    totals, first_row = debt_total_by_agent(table.borrower, table.principal, table.arrears, selected, len(store), len(store.agents))
    return _listed(store, {}, totals, first_row)


def principal_by_borrower(store: LoanStore) -> Dict[str, float]:
    table = store.table
    return totals_by_agent(store, table.borrower, table.principal, _selected(store, None))


def arrears_history(store: LoanStore, remembered_losses: Mapping[str, float]) -> Dict[str, float]:
    """What the market holds against each borrower: the losses it caused earlier, then its loans' arrears added in loan order."""
    table = store.table
    return totals_by_agent(store, table.borrower, table.arrears, _selected(store, None), remembered_losses)
