"""How much of a trade's hours the unskilled wage can really be an option for (`clearing.unskilled_option`)."""
from typing import Optional


def share_reaching_unskilled(jobs_hours: float, trade_hours: float) -> float:
    """The share of a trade's hours that the unskilled jobs at the unskilled wage can take: the hours employers bid at
    that wage or more, over the hours the trade has, at most all of them. A trade with no hours has nothing to take."""
    if trade_hours <= 0.0:
        return 1.0
    return min(1.0, max(0.0, jobs_hours) / trade_hours)


def reservation_with_unskilled_option(own: float, option: Optional[float], jobs_hours: float, trade_hours: float) -> float:
    """The mean ask of a trade's hours when the share the unskilled jobs can take asks the unskilled wage and the rest ask
    `own` (the trade's reservation without the option). Unchanged at `own` where there is no option or it is below,
    and the whole option where the jobs can take every hour of the trade; continuous between."""
    if option is None or option <= own:
        return own
    return own + share_reaching_unskilled(jobs_hours, trade_hours) * (option - own)
