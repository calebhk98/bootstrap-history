"""The start gate's rules as plain functions of the figures they judge. The module fetches the figures from views."""
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# A project with no hands in a trade it owes hours to is abandoned on this stalled year.
STALL_YEARS_BEFORE_ABANDONMENT = 4


def arrears_blocks(insolvent_years: int, grace_years: int, capital: float, surplus: Callable[[], float],
                   project_cost: Callable[[], float], revenue: Callable[[], float], cheap_floor: Callable[[], float],
                   surplus_multiple: float, hard_floor: Callable[[], float], hard_revenue_multiple: float) -> bool:
    """Whether persistent insolvency stops a new project of this size. A household in arrears for `grace_years` or
    more may still start what it can pay for out of what is LEFT of a year's income (`surplus`, not turnover), and
    is stopped outright once its debt passes a floor or a multiple of its revenue. Every figure is a callable
    because revenue is dear to work out and is wanted only when the household is insolvent."""
    if insolvent_years < grace_years:
        return False
    surplus_left = surplus()
    cheap_enough = project_cost() <= max(cheap_floor(), surplus_left * surplus_multiple)
    return not cheap_enough and capital < -max(hard_floor(), revenue() * hard_revenue_multiple)


def horizon_note(credit_frozen_until: float, horizon_end: float) -> str:
    """The clause saying a credit freeze outlasts the run, or nothing when it lifts inside it."""
    if credit_frozen_until > horizon_end:
        return " - which is past the horizon at %d, so not within this run" % int(horizon_end)
    return ""


def credit_frozen_text(credit_frozen_until: float, horizon_end: float) -> str:
    return ("nobody here will fund new work: your creditors were "
            "left unpaid and the word is out. They will deal with "
            "you again in %d%s, and until then you may finish what "
            "is running, and pay for something out of money you "
            "actually hold."
            % (int(credit_frozen_until), horizon_note(credit_frozen_until, horizon_end)))


def approval_stance(state_interest_score: float, wary_patron: Optional[str], opposed_patron: Optional[str],
                    patron_is_running: Callable[[str], bool], protection: float, wary_threshold: float,
                    opposed_threshold: float, protection_override: float) -> Optional[str]:
    """Which social wall stops the project: "wary" (a local patron's name is enough cover), "opposed" (senatorial
    patronage or high personal protection is needed), or None when the state lets it be."""
    if wary_patron and state_interest_score < wary_threshold and not patron_is_running(wary_patron):
        return "wary"
    if opposed_patron and state_interest_score < opposed_threshold and not (
            patron_is_running(opposed_patron) or protection > protection_override):
        return "opposed"
    return None


def substitution_outcome(groups: Sequence[Any], best_of_group: Callable[[Any], float]) -> Tuple[float, bool, Any]:
    """Resolve `req_any` groups: (quality, whether every group has an option, the first group with none). The
    quality is the product of each group's best option; one group with no option makes it (0.0, False, group)."""
    quality = 1.0
    for group in groups:
        best = best_of_group(group)
        if best <= 0:
            return 0.0, False, group
        quality *= best
    return quality, True, None


def substitution_gap(group: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Which group failed and what would have satisfied it, as words: a group key is a slug, so it is said as
    "a fuel", not shown raw."""
    name = (group.get("name") or group.get("group") or "").replace("_", " ")
    if name:
        name = ("an " if name[0] in "aeiou" else "a ") + name
    options = group.get("options") or {}
    return (name or "one of the things it can be made from", sorted(options, key=lambda option: -float(options[option]))[:4])


def bounty_possible(category: str, craft_categories: Sequence[str], prerequisites_done: bool,
                    cost_factor: Callable[[], float], cost_advantage: float) -> bool:
    """Whether a public prize can buy this: the craft already exists in the society (a craft category, or one the
    society is measurably good at, `cost_factor()` under `cost_advantage`) and its prerequisites are known. The cost
    factor is asked for only when the category is not a craft one."""
    if category in craft_categories:
        return prerequisites_done
    if cost_factor() < cost_advantage:
        return prerequisites_done
    return False


def trade_wait_years(supply_now: float, year: int, training_rows: Sequence[Sequence[Any]], trade: str) -> Optional[float]:
    """0 when hands exist now; else years until the soonest trainees join; None when nobody is on the way."""
    if supply_now > 0.0:
        return 0.0
    waits = [max(0.0, row[1] - year) for row in training_rows if len(row) > 3 and row[2] == trade and row[3] > 0]
    return min(waits) if waits else None


def trade_wait_outlasts(wait: Optional[float], stall_years_before_abandonment: int) -> bool:
    """True when no hands exist and none arrive before the stall gate would abandon the project."""
    return wait is None or wait >= stall_years_before_abandonment - 1
