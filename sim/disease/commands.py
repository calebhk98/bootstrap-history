"""Commands to the owner of the nation's epidemics."""
from dataclasses import dataclass
from typing import Dict

from sim.assembly.api import Command


@dataclass(frozen=True)
class RunEpidemicYear(Command):
    """The year's epidemics run, once the farm year has set `food_kcal_per_day`. Answers {age band: deaths} for the
    population step; the same deaths by tile stay in the `epidemic_deaths_by_tile` view until the next run."""
    food_kcal_per_day: float
    year: int


@dataclass(frozen=True)
class HitSeatsWithEpidemic(Command):
    """Each playing seat's people and cash are cut by the working-age share `deaths_by_band` killed. Answers that share
    (zero when it is below the share a seat notices)."""
    deaths_by_band: Dict[str, float]
    year: int
