"""The demography package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it what it still reads from the engine

from .commands import (AddCaptives, ChangeFarmland, CutPopulation, KillPeople, NotePopulationChange, OpenPopulation,
                       RecordFoodEaten, RefreshDemographicIndexes, SendSettlers, SetClearedFarmland, SetFarmHoursNeeded,
                       StepPopulation, TakeFromGranary)
from .constants import DEFAULT_POPULATION_100AD, POP_SCALE_FLOOR
from .people import People
from . import rules
