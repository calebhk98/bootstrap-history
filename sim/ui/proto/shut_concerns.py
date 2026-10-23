"""What the concerns you know how to run but have shut would earn: the figure `state` states."""


def shut_concerns_yearly_value(earnings_and_upkeep):
    """Whole money a year of the profitable shut concerns, given (earnings, upkeep) of each shut concern; None when
    none of them would earn more than it costs."""
    return round(sum(earnings - upkeep for earnings, upkeep in earnings_and_upkeep if earnings > upkeep), 0) or None
