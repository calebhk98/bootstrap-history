"""The credit rate in a year when savers offered funds and nobody borrowed."""
from typing import Optional, Sequence

from .credit import RATE_ADJUSTMENT_SHARE_PER_YEAR
from .labour import sticky_move
from .types import FundsOffer


def rate_with_no_borrowers(last_rate: Optional[float], funds: Sequence[FundsOffer]) -> Optional[float]:
    """Lenders compete the rate down toward the lowest ask among them, at the market's usual pace; with no
    funds on offer the rate is left where it was."""
    if not funds:
        return last_rate
    return sticky_move(last_rate, min(offer.minimum_rate for offer in funds), RATE_ADJUSTMENT_SHARE_PER_YEAR)
