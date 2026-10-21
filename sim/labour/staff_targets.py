"""What the automatic hiring aims at."""


def scholar_target(institutional_capacity, extra_room, extra_share, wall):
    """The scholar headcount auto-hiring asks for: the institutions' capacity plus its share of the supervision room,
    never past the wall a manual `hire` is refused at."""
    return min(institutional_capacity + extra_room * extra_share, wall)
