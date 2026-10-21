"""The founder's own hours in a year: what the pool is, what is already spoken for, what is left to sell or spend."""


def hours_pool(founder_alive, own_hours, bonded, bonded_share, deputies, hours_per_deputy):
    """The year's own hours: the founder's (a bonded founder keeps only `bonded_share` of them) while alive,
    plus the hours of each deputy."""
    total = 0.0
    if founder_alive:
        total += own_hours * (bonded_share if bonded else 1.0)
    return total + deputies * hours_per_deputy


def hours_committed(teaching, relocation, supervision, sold_for_wages):
    """Hours spoken for before any project sees them. Hours sold for wages are among them: there is one year, so
    a sale cannot be spent a second time on projects."""
    return teaching + (relocation or 0.0) + (supervision or 0.0) + sold_for_wages


def hours_free(pool, committed):
    """Hours of the pool not yet spoken for (never negative)."""
    return max(0.0, pool - committed)
