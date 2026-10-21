"""Which active projects a material shortage slows: only those that draw on the scarce pool."""

COKE_REPLACES = ("charcoal_kg", "firewood_kg")


def input_pools(materials, uses_coke, pool_of, lab_scale_suffix, kilogram_suffix="_kg"):
    """The pools a project's material inputs draw on. A project on coke draws coal where it names charcoal or
    firewood; gram-scale purchases never take part in the flow throttle."""
    pools = set()
    for material in materials:
        effective = "coal_kg" if uses_coke and material in COKE_REPLACES else material
        if effective.endswith(lab_scale_suffix) and not effective.endswith(kilogram_suffix):
            continue
        pools.add(pool_of(effective))
    return pools


def shared_throttle(factor, binding, project_pools):
    """The portfolio's throttle `factor` for a project that draws on the `binding` pool; full pace for any other, and
    for a throttle too slight to matter."""
    if factor >= 0.999 or not binding:
        return 1.0
    return factor if binding in project_pools else 1.0
