"""Who gets the hours of a market that pays one wage: each bid wants the hours its worth covers at that wage, and when
the bids together want more than is offered every bid is cut by the same share."""
from typing import Dict, List, Sequence, Tuple


def wanted_at_wage(wage: float, floor: float, bid_caps: Sequence[float], bid_hours: Sequence[float]) -> List[float]:
    """The hours each bid wants at `wage`, on the schedule `clearing.hours_wanted_at` sums: the hours of the bids at one
    cap (the most an hour is worth to the bidder) are spread evenly over the wages from the next lower cap (`floor` under
    the lowest) up to that cap, so a bid wants all its hours at or under that lower wage, none at its cap or above, and a
    share falling in a straight line between. A bid whose cap is the floor wants all its hours at the floor. Bids capped
    under the floor want none."""
    caps = sorted({cap for cap in bid_caps if cap >= floor})
    lower_of: Dict[float, float] = {}
    lower = floor
    for cap in caps:
        lower_of[cap] = lower
        lower = cap
    wanted = []
    for cap, hours in zip(bid_caps, bid_hours):
        if cap < floor:
            wanted.append(0.0)
        elif wage <= lower_of[cap]:
            wanted.append(hours)
        elif wage < cap:
            wanted.append(hours * (cap - wage) / (cap - lower_of[cap]))
        else:
            wanted.append(0.0)
    return wanted


def hires_at_wage(offered: float, wanted: Sequence[float]) -> List[float]:
    """The hours each bid is given: what it wants, cut for every bid by the same share when they want more than `offered`."""
    total = sum(wanted)
    if total <= 0.0 or offered <= 0.0:
        return [0.0 for _hours in wanted]
    share = min(1.0, offered / total)
    return [hours * share for hours in wanted]


def by_employer(employers: Sequence[str], hours: Sequence[float]) -> Dict[str, float]:
    """Hours summed per employer, employers in name order."""
    total: Dict[str, float] = {}
    for employer, amount in sorted(zip(employers, hours)):
        total[employer] = total.get(employer, 0.0) + amount
    return total


def ranks_of(employers: Sequence[str], bid_caps: Sequence[float], wanted: Sequence[float]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """(hours wanted, standing) per employer among the bids that want hours: an employer's standing is its highest cap,
    which is what poaching ranks employers by."""
    hours: Dict[str, float] = {}
    standing: Dict[str, float] = {}
    for employer, cap, amount in sorted(zip(employers, bid_caps, wanted)):
        if amount <= 0.0:
            continue
        hours[employer] = hours.get(employer, 0.0) + amount
        standing[employer] = max(standing.get(employer, 0.0), cap)
    return hours, standing
