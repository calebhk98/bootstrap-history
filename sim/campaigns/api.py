"""The campaigns package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import DisbandArmy, OrderArmy, RaiseArmy, RecallArmy
from . import rules
