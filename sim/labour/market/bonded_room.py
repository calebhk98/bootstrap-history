"""How much of a bonded purchase an employer's own plan has room for (Complaint 644). Plain functions.

Buying a bonded person is a capital outlay: the present value of the person's hours, paid now. An employer pays it
only from money its year plan leaves free: the cash the plan assigns to no line (`outlay_room` in the year's inputs),
and the wage line of the hours it bid for and could not fill, since the person fills that vacancy. Cash the plan
assigned to other lines is not touched. The cost of a purchase is shared between the employers that have a vacancy
in proportion to those vacancies, and the purchase is cut to the size at which no employer's share passes its room.
"""
import dataclasses
from typing import Dict, List, Mapping, Sequence, Tuple


@dataclasses.dataclass(frozen=True)
class Buyer:
    employer: str
    vacant_hours: float     # hours bid for in the market and not hired
    wage_line: float        # the money the plan set for those hours: vacant hours at the heading wage
    free_cash: float        # money the plan assigns to no line, still unspent


def hours_by_market(bids: Sequence) -> Dict[Tuple[str, str], Dict[str, float]]:
    """(area, trade) -> employer -> hours bid for, over the bids with hours: what `buyers_in` reads, built once."""
    grouped: Dict[Tuple[str, str], Dict[str, float]] = {}
    for bid in bids:
        if bid.hours > 0.0:
            hours = grouped.setdefault((bid.area, bid.trade), {})
            hours[bid.employer] = hours.get(bid.employer, 0.0) + bid.hours
    return grouped


def buyers_in(bid_hours: Mapping[Tuple[str, str], Mapping[str, float]], clearing,
              unassigned: Mapping[str, float]) -> List[Buyer]:
    """The employers with a vacancy in the market (`clearing`) and some room to pay for a person, in id order.
    `bid_hours` is `hours_by_market(bids)`."""
    hours = bid_hours.get((clearing.area, clearing.trade), {})
    found = []
    for employer in sorted(hours):
        vacant = max(0.0, hours[employer] - clearing.hired_by_employer.get(employer, 0.0))
        line = vacant * max(0.0, clearing.heading_wage)
        free = max(0.0, unassigned.get(employer, 0.0))
        if vacant > 0.0 and line + free > 0.0:
            found.append(Buyer(employer, vacant, line, free))
    return found


def shares_and_ceiling(buyers: Sequence[Buyer]) -> Tuple[Dict[str, float], float, float]:
    """({employer: share of the cost}, the most the purchase may cost, the vacant hours of the buyers). Shares follow
    vacant hours; the ceiling is the dearest purchase at which every employer's share stays within its room."""
    vacant = sum(buyer.vacant_hours for buyer in buyers)
    if vacant <= 0.0:
        return {}, 0.0, 0.0
    shares = {buyer.employer: buyer.vacant_hours / vacant for buyer in buyers}
    ceiling = min((buyer.wage_line + buyer.free_cash) / shares[buyer.employer] for buyer in buyers)
    return shares, ceiling, vacant


def spend(buyers: Sequence[Buyer], shares: Mapping[str, float], cost: float, unassigned: Dict[str, float]) -> None:
    """Draw `cost`, shared by `shares`, from the employers' free cash after their wage lines are used."""
    for buyer in buyers:
        from_free = max(0.0, cost * shares[buyer.employer] - buyer.wage_line)
        unassigned[buyer.employer] = max(0.0, unassigned.get(buyer.employer, 0.0) - from_free)
