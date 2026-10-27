"""Plain rules behind what finishing or failing a project reports, called with figures and not with a game."""


def severity_of_loss(lost, means, on_goal_road, minor_share, goal_road_weight):
    """'minor' when the loss, weighted up on the goal's road, is under a share of the player's means, else 'major'."""
    weight = goal_road_weight if on_goal_road else 1.0
    return "minor" if lost * weight < minor_share * max(means, 1.0) else "major"


def road_line(fog, road_done, road_total):
    """The goal-effect line for a completion on the road to the goal; fog hides the total."""
    if fog:
        return "goal effect: this is on the road to your goal"
    return "goal effect: on the road to your goal, %d of %d steps done" % (road_done, road_total)


def staff_shortfall(need_scholars, need_craftsmen, free_scholars, free_craftsmen, tolerance=0.01):
    """(need scholars, need craftsmen, free scholars, free craftsmen) when free staff could not supervise, else None."""
    if need_scholars > free_scholars + tolerance or need_craftsmen > free_craftsmen + tolerance:
        return need_scholars, need_craftsmen, free_scholars, free_craftsmen
    return None
