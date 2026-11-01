"""A producer whose runs pay and whose buyers outrun its capacity grows toward them; it sheds only on losses
(`producers_close`, `producer_losses`). The growth is a year's change at most (producers.OUTPUT_CHANGE_SHARE_PER_YEAR),
as hands are hired and trained over seasons."""
import math


def grown_capacity(capacity: float, expected_runs: float, share_paying: float, step_share: float) -> float:
    """Capacity after growing toward the runs the producer expects to sell. Only the workplaces whose own cost the
    expected revenue covers (`share_paying`, producers.share_working) make those runs, so the capacity wanted is the
    expected runs over that share; the rise is no more than `step_share` of the capacity. Nothing grows when no
    workplace pays or the expectation is unknown."""
    if not (share_paying > 0.0 and capacity > 0.0 and math.isfinite(expected_runs) and math.isfinite(share_paying)):
        return capacity
    wanted = expected_runs / share_paying
    return capacity + min(max(0.0, wanted - capacity), step_share * capacity)
