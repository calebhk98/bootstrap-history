"""The land ceilings of a working: how much of a material (or of woodland) the ground and the state can support."""


def mine_ceiling_tonnes(favour_terms, state_reach, stranger_base, stranger_state_scale, revenue_multiple,
                        mineral_scale):
    """Tonnes a year of one material that can stand. `favour_terms` is the `{"base", "state_scale"}` of the best
    ceiling effect held (None for a stranger, who gets the stranger terms); a more capable state and a larger
    revenue raise the base, and the share of the material's reference output the ground holds scales it."""
    if favour_terms is not None:
        base = favour_terms["base"] + favour_terms["state_scale"] * state_reach
    else:
        base = stranger_base + stranger_state_scale * state_reach
    return base * revenue_multiple * mineral_scale


def room_under_ceiling(ceiling, standing, pending=0.0):
    """What may still be added under a ceiling once what stands and what is on order are counted; never negative."""
    return max(0.0, ceiling - standing - pending)
