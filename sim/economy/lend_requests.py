"""What each borrower asked for in one credit clearing, when it made several requests."""
from typing import Callable, Dict, Iterable, Optional, Tuple


def asked_and_worth(requests: Iterable, worth_of: Callable[[object], Optional[float]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """(amount asked by borrower, plant worth ratio by borrower). A borrower's requests add up in the amount asked; its
    worth is the mean of its requests' worth weighted by amount. `worth_of(request)` is None for a borrower with no plant,
    which has no entry in the worth."""
    asked: Dict[str, float] = {}
    weighted: Dict[str, float] = {}
    weight: Dict[str, float] = {}
    for request in requests:
        asked[request.borrower] = asked.get(request.borrower, 0.0) + request.amount
        worth = worth_of(request)
        if worth is not None:
            weighted[request.borrower] = weighted.get(request.borrower, 0.0) + worth * request.amount
            weight[request.borrower] = weight.get(request.borrower, 0.0) + request.amount
    return asked, {borrower: weighted[borrower] / weight[borrower] for borrower in weighted if weight[borrower] > 0.0}
