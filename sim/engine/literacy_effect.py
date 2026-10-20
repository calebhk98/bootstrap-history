"""How far a technology's literacy effect moves a reading share."""


def literacy_after_effect(before, delta, ceiling):
    """The share a technology's `delta` leaves: not above the ceiling (a share already above it stays), not below 0."""
    return max(0.0, min(max(ceiling, before), before + delta))
