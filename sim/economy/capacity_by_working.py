"""A producer's capacity under the clearing rule set, where it has no plant: it moves a share of the way to the capacity
at which the runs it worked would be the normal share of its workplaces, the same share up and down and by no more than
a year's change. Capacity is the workplaces a producer stands for and only those whose cost the price covers work
(`producers.share_working`); the normal share is the share that works when a run brings in exactly what it costs. So a
producer that works more of its workplaces than that (the price stands above its cost) gains workplaces, one that works
fewer loses them, and at rest every good sells at what it costs to make. The target reads the runs worked, so workplaces
are not added where something else holds the runs back (hands of the trade, an input, buyers), and the capacity a
producer rests at does not depend on the path that led there."""
from sim.constants import declare
from sim.jit import njit

CAPACITY_SHARE_MOVED_PER_YEAR = declare(
    "CAPACITY_SHARE_MOVED_PER_YEAR", 0.2, kind="temporary_heuristic",
    unit="share of the gap between a producer's capacity and the capacity its worked runs call for, closed a year",
    source=None, confidence="D",
    retire="Complaints/473: the pace at which workplaces are set up and given up (a recipe's own time to build and to train) gives it",
    why="How fast workplaces join a producer that works more than the normal share of them and leave one that works "
        "fewer. It is slow against the year's own answer of output to the price (a producer works more or fewer of the "
        "workplaces it has), so capacity follows a gap that lasts and not a year's swing. Not fitted.")


@njit
def capacity_toward_working(capacity, worked_runs, normal_share, share_moved, most_change):
    """The capacity a year on: `capacity` moved `share_moved` of the way to `worked_runs / normal_share`, by no more than
    `most_change` of it either way; unchanged where there is no normal share to read."""
    if not normal_share > 0.0:
        return capacity
    limit = most_change * capacity
    return capacity + max(-limit, min(limit, share_moved * (worked_runs / normal_share - capacity)))
