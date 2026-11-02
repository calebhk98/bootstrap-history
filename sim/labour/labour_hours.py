"""The founder's own hours in a year: the pool they are drawn from and what is already spoken for."""
from sim.constants import declare

from .founder_hours import hours_committed, hours_pool


class FounderHours:
    def __init__(self, world):
        self._world = world

    BONDAGE_HOURS_SHARE = declare(
        "BONDAGE_HOURS_SHARE", 0.25, kind="temporary_heuristic",
        unit="fraction of founder_hours_per_year", source=None, confidence="D",
        why="What fraction of a bonded founder's day is still their own to "
            "spend, the rest being owed to whoever holds the bond. Not zero, "
            "because nobody works every waking hour and the evenings are "
            "where this model assumes the work gets done; not derived from "
            "any actual bondage contract terms, of which this engine has "
            "none, only picked so bondage costs something real without "
            "being a total stop.")

    def director_pool(self):
        # In bondage most of your hours are owed to somebody else, not all: the evenings are where the work gets done.
        return hours_pool(self._world.founder_alive, self._world.cfg["founder_hours_per_year"],
                          self._world.bondage_years_left > 0, self.BONDAGE_HOURS_SHARE,
                          self._world.workforce.directors_extra, self._world.cfg["director_hours_per_year"])

    def director_hours_committed(self):
        """Hours of your own year already spoken for before any project sees them.

        WAGE HOURS BELONG HERE: keeping a separate tally for `work` would let
        a founder sell an entire year of hours for wages and then still
        spend a full year's worth of hours on projects in the same year -
        a free second year inside every year. There is one year, and one
        pair of hands.
        """
        workforce = self._world.workforce
        return hours_committed(workforce.teaching_hours_this_year,
                               workforce.relocation_hours_this_year,
                               (workforce.supervision_hours_this_year or 0.0) + self._world.director_overhead_hours(),
                               workforce.wage_hours_this_year)
