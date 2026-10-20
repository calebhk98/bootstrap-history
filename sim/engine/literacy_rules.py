"""Plain rules for how far literacy can reach, called with figures and not a game."""


def common_ceiling(unable_share, farm_children_kept_home, farm_share_of_hours):
    """Commoners who can attend school after the farms' call on their children's time."""
    return (1.0 - unable_share) * (1.0 - farm_children_kept_home * farm_share_of_hours)
