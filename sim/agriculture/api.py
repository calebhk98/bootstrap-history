"""The agriculture package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import InvestFarm, SellFarm
from .constants import FARM_LABOUR_HOURS_PER_HA, FARM_WEATHER_POOLED_CELL_CAP
from . import rules
