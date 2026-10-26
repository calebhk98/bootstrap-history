"""What a bribe buys and what it takes: scandal bought down, and protection that keeps an accusation from being made.

Plain arithmetic on the figures handed in. `income` is the revenue the sum is measured against (at least one), `weight`
the civilisation's bribability."""
from typing import NamedTuple

NO_SCANDAL = 0.0005
MIN_PROTECTION_GAIN = 0.005
NEARLY_AT_CAP = 0.29
SLACK = 0.5


class BribeRefusal(NamedTuple):
    cause: str                 # not_positive, over_capital, too_little, already_protected
    floor: float = 0.0         # too_little: about what would begin to move protection


class BribePlan(NamedTuple):
    paid: float                # taken from the purse (never more than the bribe can use)
    refused: float             # of what was offered, not taken
    bribes_year_to_date: float
    scandal: float


def protection_bought(bribes_year_to_date: float, income: float, weight: float, income_share: float,
                      cap: float) -> float:
    """Protection that bribes spent so far this year add up to, bounded by the most money alone can buy."""
    return min(cap, (bribes_year_to_date / (income * income_share)) * weight)


def refusal_for(amount: float, capital: float, scandal: float, bribes_year_to_date: float, income: float, weight: float,
                memory_decay: float, protection_cap: float, income_share: float):
    """Why the bribe is not taken at all, or None. Nothing is charged for nothing: with no scandal to answer, a sum
    that would not move protection is refused before any money is taken."""
    if amount <= 0:
        return BribeRefusal("not_positive")
    if amount > capital:
        return BribeRefusal("over_capital")
    if scandal <= NO_SCANDAL:
        spent = memory_decay * bribes_year_to_date + amount
        would = protection_bought(spent, income, weight, income_share, protection_cap)
        already = protection_bought(bribes_year_to_date, income, weight, income_share, protection_cap)
        if would - already < MIN_PROTECTION_GAIN:
            if already < NEARLY_AT_CAP:
                floor = MIN_PROTECTION_GAIN * (income * income_share) / max(1e-9, weight)
                return BribeRefusal("too_little", max(1.0, floor))
            return BribeRefusal("already_protected")
    return None


def plan(amount: float, scandal: float, bribes_year_to_date: float, income: float, weight: float, memory_decay: float,
         protection_cap: float, income_share: float, scandal_per_point: float) -> BribePlan:
    """Never take more than it can spend: scandal stops at zero and the protection it buys saturates at the cap, so
    an arbitrarily large sum buys no more than a bounded one."""
    bribability = max(1e-9, weight)
    for_scandal = scandal * scandal_per_point / bribability
    for_protection = max(0.0, (protection_cap * income * income_share) / bribability - memory_decay * bribes_year_to_date)
    useful = max(for_scandal, for_protection)
    refused = 0.0
    if amount > useful + SLACK:
        refused, amount = amount - useful, useful
    return BribePlan(amount, refused, memory_decay * bribes_year_to_date + amount,
                     max(0.0, scandal - amount / scandal_per_point * bribability))
