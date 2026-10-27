"""When opening a concern is a net loss worth warning about."""


def flags_net_loss(upkeep_now, earnings_fully_ramped, is_capability_institution):
    """True when a concern costs more to run than it earns even fully ramped up, unless it is a capability institution,
    whose loss is the intended shape of the trade."""
    return upkeep_now > earnings_fully_ramped and not is_capability_institution
