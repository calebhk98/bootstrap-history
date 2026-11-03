"""The freight package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .constants import SEA_MODE
from .route import Leg, Route
from . import rules
