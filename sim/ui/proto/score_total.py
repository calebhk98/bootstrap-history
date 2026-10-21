"""The total of a score from its components, and the points it is worth."""

POINTS_FOR_A_PERFECT_RUN = 1000


def score_total(components):
    """(total, points): the sum of the components' weighted figures, and that total on a 0-1000 scale. Both are None
    while any component is withheld, since a total over some of the components is not comparable."""
    if not all(component["normalized"] is not None for component in components.values()):
        return None, None
    total = round(sum(component["weighted"] for component in components.values()), 4)
    return total, round(total * POINTS_FOR_A_PERFECT_RUN)
