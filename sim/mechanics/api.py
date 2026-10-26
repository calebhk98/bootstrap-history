"""The mechanics package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the tree and what is running

from . import rules
from .rules import nodes_declaring, staff_capacity_sources
