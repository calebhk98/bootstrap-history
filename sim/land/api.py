"""The land package's only door: its commands, and the plain rules."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import AdvanceColonies, FoundColony, TransferTile
from .reference import install_reference_crop_technique
from . import rules

install_reference_crop_technique()
