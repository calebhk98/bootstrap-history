"""The land package's only door: its commands, and the plain rules."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import AdvanceColonies, BuildWay, BuildWork, FinishWays, FoundColony, LoseWork, TransferTile
from .reference import install_reference_crop_technique
from . import action_results, rules, ways_rules, works_rules

install_reference_crop_technique()
