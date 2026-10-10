"""How long the working day runs: the hours a person gives in a year, longer where light lets work go on after dark.

The convention is `HOURS_PER_PERSON_YEAR` (`sim/unit_conversions.py`: a ten-hour day over the working days of a year).
A work declares `mechanics.working_day = {"extra_hours_per_day": h}`: while it is open, `h` more hours of each working
day are lit, for the share of the people it covers if it declares `coverage`, else for everyone. Wage quotes, head counts
and hours ledgers all read the year through `working_hours_per_person_year`, so a longer day gives more hours for the
same people at the same hourly wage.
"""
from sim.constants import declare
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

BASE_WORKING_DAY_HOURS = declare(
    "BASE_WORKING_DAY_HOURS", 10.0, kind="engineering_estimate", unit="hours per working day",
    source="The ten-hour day behind HOURS_PER_PERSON_YEAR in sim/unit_conversions.py.", confidence="B",
    why="The day that extra lit hours are added to; the working year grows in the same proportion.")


class WorkingDayMixin:

    def extra_lit_hours_per_day(self):
        """Hours a day added by the open works that declare `working_day`, each for the people it covers."""
        total = 0.0
        for node_id in self.nodes_with_mechanic("working_day"):
            if not self.running(node_id):
                continue
            share = self.coverage_share(node_id) if node_id in self.coverage_nodes() else 1.0
            total += self.mechanic(node_id, "working_day")["extra_hours_per_day"] * share
        return total

    def working_hours_per_person_year(self):
        """Hours one person gives in a year: the convention, stretched by the lit hours added to the day."""
        if not self.nodes_with_mechanic("working_day"):
            return HOURS_PER_PERSON_YEAR
        return HOURS_PER_PERSON_YEAR * (1.0 + self.extra_lit_hours_per_day() / BASE_WORKING_DAY_HOURS)
