"""Plain rules for literacy: how far it can reach, what a technology and a school do to it, called with figures."""


def common_ceiling(unable_share, farm_children_kept_home, farm_share_of_hours):
    """Commoners who can attend school after the farms' call on their children's time."""
    return (1.0 - unable_share) * (1.0 - farm_children_kept_home * farm_share_of_hours)


def literacy_after_effect(before, delta, ceiling):
    """The share a technology's `delta` leaves: not above the ceiling (a share already above it stays), not below 0."""
    return max(0.0, min(max(ceiling, before), before + delta))


def census_phrase(year, school_started, generation_years):
    """A generation of schooling is claimed only once the school has run for a generation."""
    if school_started is not None and year - school_started >= generation_years:
        return "a generation of schooling shows in the census"
    return "schooling shows in the census"


def schooling_flow(schools, field, required_school_shut):
    """Teaching flow of the open schools: `schools` are (value, fields the school reaches or None for all of them).
    Nothing when a school the others depend on is shut; with a `field`, only the schools that reach it count."""
    if required_school_shut:
        return 0.0
    if field is None:
        return sum(value for value, _reaches in schools)
    return sum(value for value, reaches in schools if reaches is None or field in reaches)


def printing_boosted_flow(flow, boost, diffusion):
    """The flow once diffused printing is counted: texts make the same effort teach faster, but a flow of zero stays zero."""
    if flow <= 0.0:
        return 0.0
    return flow * (1.0 + boost * diffusion)
