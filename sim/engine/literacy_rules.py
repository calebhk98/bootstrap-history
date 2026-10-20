"""Plain rules for how far literacy can reach, called with figures and not a game."""


def target_after_effect(before, delta, ceiling):
    """Where a technology's literacy effect leaves a field: never past its ceiling (or past where it already stood),
    and never below nothing."""
    return max(0.0, min(max(ceiling, before), before + delta))


def common_ceiling(unable_share, farm_children_kept_home, farm_share_of_hours):
    """Commoners who can attend school after the farms' call on their children's time."""
    return (1.0 - unable_share) * (1.0 - farm_children_kept_home * farm_share_of_hours)
