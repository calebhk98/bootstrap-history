"""What a merchant can pay for carriers: its bids are bounded by its purse (as a producer's are by its wage line), and the working-capital
loan it asks at the year's close covers the wage bill of the hours its plan wants that its cash does not."""
from typing import Callable, Dict, Iterable, List, Optional, Tuple

BidFigures = Tuple[str, str, str, float, float]     # (employer, trade, area, hours, maximum wage), as labour_bid_sink.BidFigures


def wage_bill(hours_and_wages: Iterable[Tuple[float, float]]) -> float:
    """The money that hiring each (hours, wage per hour) costs."""
    return sum(hours * wage for hours, wage in hours_and_wages)


def funded_share(bill: float, cash: float) -> float:
    """The share of a wage bill the cash pays: 1 for a bill the cash covers or no bill, 0 for no cash."""
    if bill <= 0.0 or cash >= bill:
        return 1.0
    return max(0.0, cash) / bill


def loan_wanted(bill: float, worth: float, cash: float) -> Optional[float]:
    """The loan that pays the part of `bill` the cash does not, asked only where the hours are worth more than their wages (`worth`); None otherwise."""
    short = bill - max(0.0, cash)
    if short > 0.0 and bill > 0.0 and worth > bill:
        return short
    return None


def fund_bids(figures: Iterable[BidFigures], wage_of: Callable[[str, str], float], cash_of: Callable[[str], float]) -> List[BidFigures]:
    """Each employer's bids scaled by the share of their wage bill its cash pays (`wage_of(trade, area)` per hour, `cash_of(employer)`); a bid
    scaled to no hours is left out. The maximum wages stay."""
    rows = list(figures)
    bills: Dict[str, float] = {}
    for employer, trade, area, hours, _maximum in rows:
        bills[employer] = bills.get(employer, 0.0) + hours * wage_of(trade, area)
    shares = {employer: funded_share(bill, cash_of(employer)) for employer, bill in bills.items()}
    return [(employer, trade, area, hours * shares[employer], maximum) for employer, trade, area, hours, maximum in rows
            if hours * shares[employer] > 0.0]
