"""Debt bondage for a household cohort: a default by a household with no land left puts it into service to its
creditor, where the society has debt bondage (`EconomySetup.debt_bondage_years`, the same rule and term the
founder's default follows: sim/engine/economy_credit.py).

For the term, a share of the hours of the cohort's working people is owed to the creditor. The cohort still
sells its hours in the labour market; the creditor takes that share of what they fetched (the product of the
hours), as far as the cohort holds the cash, and it comes off the debt and off the creditor's credit loss. The
bond ends when the debt is worked off or the term is served; what is left was already written off as the loss.
"""
from typing import Dict, Iterable, List, Mapping

from sim.constants import declare

from . import titles
from .types import CurrencyId, Transfer

BONDED_HOURS_OWED_SHARE = declare(
    "BONDED_HOURS_OWED_SHARE", 0.75, kind="temporary_heuristic",
    unit="share of a bonded household's working hours owed to its creditor",
    source=None, confidence="D",
    why="Most of a bonded person's hours belong to the creditor; the same share the founder's bondage leaves "
        "(BONDAGE_HOURS_SHARE is what stays its own). No actual bondage contract terms are modelled.",
    retire="538 bondage contracts as data")


def enter(record, defaults: Iterable, term_years: float) -> List[str]:
    """Household cohorts whose default left them with no land go into bondage to the lender, for the debt the
    collateral did not cover. Returns the cohorts bonded now. A society without debt bondage (term zero) has none."""
    entered: List[str] = []
    if term_years <= 0.0:
        return entered
    for default in defaults:
        cohort = record.cohorts.get(default.borrower)
        if cohort is None or default.loss <= titles.EPSILON:
            continue
        if titles.holding(record, cohort.tile, cohort.agent_id) > titles.EPSILON:
            continue                                       # still holds land: not yet destitute
        bond = record.bondage.get(cohort.agent_id)
        if bond is None:
            record.bondage[cohort.agent_id] = {"creditor": default.lender, "debt": default.loss, "years_left": term_years}
            entered.append(cohort.agent_id)
        else:
            bond["debt"] += default.loss
    return entered


def service(record, currency: CurrencyId, wages: Mapping[str, float]) -> List[Transfer]:
    """One year of bonded labour: each bonded cohort pays its creditor the owed share of its wages, no more than
    the debt left or the cash it holds. Returns the payments (the caller books them)."""
    payments: List[Transfer] = []
    for cohort_id, bond in sorted(record.bondage.items()):
        owed = min(bond["debt"], BONDED_HOURS_OWED_SHARE * wages.get(cohort_id, 0.0))
        paid = min(owed, max(0.0, record.book.balance(cohort_id, currency)))
        if paid > 0.0:
            payments.append(Transfer(cohort_id, bond["creditor"], currency, paid, "bonded_labour"))
            bond["debt"] -= paid
            record.credit_losses[bond["creditor"]] = max(0.0, record.credit_losses.get(bond["creditor"], 0.0) - paid)
        bond["years_left"] -= 1.0
    record.bondage = {cohort_id: bond for cohort_id, bond in record.bondage.items()
                      if bond["debt"] > titles.EPSILON and bond["years_left"] > 0.0}
    return payments


def bonded(record) -> Dict[str, str]:
    """Cohort -> its creditor, for every household in bondage."""
    return {cohort_id: bond["creditor"] for cohort_id, bond in sorted(record.bondage.items())}
