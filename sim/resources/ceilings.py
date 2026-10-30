"""The land ceilings of a working or a woodland: how much of a material, or of coppice, the ground and the state can support."""


def mine_ceiling_tonnes(favour_terms, inspection_share, stranger_base, stranger_state_scale, revenue_multiple,
                        mineral_scale):
    """Tonnes a year of one material that can stand. `favour_terms` is the `{"base", "state_scale"}` of the best
    ceiling effect held (None for a stranger, who gets the stranger terms); more of the people under inspection and a larger
    revenue raise the base, and the share of the material's reference output the ground holds scales it."""
    if favour_terms is not None:
        base = favour_terms["base"] + favour_terms["state_scale"] * inspection_share
    else:
        base = stranger_base + stranger_state_scale * inspection_share
    return base * revenue_multiple * mineral_scale


def room_under_ceiling(ceiling, standing, pending=0.0):
    """What may still be added under a ceiling once what stands and what is on order are counted; never negative."""
    return max(0.0, ceiling - standing - pending)


def revenue_scale_multiple(revenue, revenue_scale, cap_multiple):
    """1 plus the revenue in units of the scale revenue, the revenue part capped; negative revenue adds nothing."""
    return 1.0 + min(cap_multiple, max(0.0, revenue) / revenue_scale)


def forest_ceiling_hectares(land_area_km2, state_reach, base_per_million_km2, per_million_km2_per_capacity,
                            revenue_multiple):
    """Hectares of woodland per million km2 of land (more for a more capable state), scaled by the revenue multiple."""
    return ((base_per_million_km2 + per_million_km2_per_capacity * state_reach)
            * (land_area_km2 / 1.0e6) * revenue_multiple)
