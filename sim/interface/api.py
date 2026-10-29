"""The interface package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/ or sim/ui/ at module level; the module asks sim.ui.api for code when it runs

from .command_data import CommandSpec, StatePathCheck, policy_defaults
from .commands import OpenInterface
from .declarations import CODE, MACRO, PATCH, POLICY, READ, SHIPPED, CommandDeclaration, Declared, FigureDeclaration
from .rules import SHIPPED_OWNER, declare, entry_fields
