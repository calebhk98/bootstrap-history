"""An ensemble of spin-up replays for `spin-up-trace --stages --ensemble` (Complaint 473). The spin-up is chaotic, so
member k's opening differs from member 0's only by its households' cash scaled by `cash_factor(k)`, a rounding-level
perturbation. This is a measurement device: the game's own spin-up never applies it."""
import statistics

from sim.economy import api as economy_api
from sim.economy.api import EDGE_ISSUE, Transfer

from .spin_up_gap import QUANTITY_FLOORS

CASH_STEP = 1e-12     # member k scales every household cohort's cash by 1 + k * CASH_STEP


def cash_factor(member):
    """The factor member `member`'s households' cash is multiplied by; member 0 is unperturbed."""
    return 1.0 + member * CASH_STEP


def scaling_transfers(balances, currency, factor):
    """The transfers that take each account of `balances` ({account: money}) to `factor` times its money, against the
    issue edge; none when the factor is one. A factor below one returns money to the edge."""
    transfers = []
    for account, money in balances.items():
        change = money * (factor - 1.0)
        if change > 0.0:
            transfers.append(Transfer(EDGE_ISSUE, account, currency, change, "ensemble perturbation"))
        elif change < 0.0:
            transfers.append(Transfer(account, EDGE_ISSUE, currency, -change, "ensemble perturbation"))
    return transfers


def perturb_household_cash(economy, factor):
    """Scale every household cohort's cash in the blank `economy` by `factor`."""
    currency = economy_api.currency_id(economy)
    balances = {account: economy_api.account_balance(economy, account)
                for account in economy_api.household_cohort_ids(economy)}
    economy_api.post_transfers(economy, scaling_transfers(balances, currency, factor))


def _mean(values):
    return sum(values) / len(values)


def stage_trend(series, floor, base):
    """Change from the first half's mean to the second half's mean of `series`, as a share of the larger of `floor` and
    `base` (default: the second half's mean); none values are skipped and none is returned when fewer than two remain. A
    zero denominator reads as no change when the means are equal and as a whole change otherwise."""
    values = [value for value in series if value is not None]
    if len(values) < 2:
        return None
    half = len(values) // 2
    first, second = _mean(values[:half]), _mean(values[len(values) - half:])
    denominator = max(abs(second) if base is None else abs(base), floor)
    if denominator <= 0.0:
        return 0.0 if first == second else (1.0 if second > first else -1.0)
    return (second - first) / denominator


def trimmed_trends(rows):
    """{quantity: trend of the trimmed stage's rows}: each spin_up_gap quantity against its floor (unmet need against the
    second half's mean food need), and "prices" as the watched good's trend that is largest in size."""
    trimmed = [row for row in rows if row["stage"] == "trimmed"]
    half = len(trimmed) // 2
    trends = {}
    for name, floor in QUANTITY_FLOORS.items():
        base = None
        if name == "unmet_need":
            needs = [row["food_need"] for row in trimmed[len(trimmed) - half:] if row.get("food_need") is not None]
            base = _mean(needs) if needs else None
        trends[name] = stage_trend([row.get(name) for row in trimmed], floor, base)
    goods = sorted({good for row in trimmed for good in row["prices"]})
    by_good = [stage_trend([row["prices"].get(good) for row in trimmed], 0.0, None) for good in goods]
    by_good = [trend for trend in by_good if trend is not None]
    trends["prices"] = max(by_good, key=abs) if by_good else None
    return trends


def summarise_members(member_values):
    """{quantity: {"gaps": each member's value, "median", "spread" (largest minus smallest)}} from one {quantity: value}
    per member; members with no value for a quantity are left out of it."""
    summary = {}
    for name in sorted({name for member in member_values for name in member}):
        values = [member[name] for member in member_values if member.get(name) is not None]
        if values:
            summary[name] = {"gaps": values, "median": statistics.median(values), "spread": max(values) - min(values)}
    return summary
