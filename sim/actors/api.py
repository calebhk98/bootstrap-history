"""The actors package's only door. Only its commands exist here; the engine bridge applies them until the module moves."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import NoteTraderMargin, RecordConquestContact, RecordMigrantContact, ScaleStrata
