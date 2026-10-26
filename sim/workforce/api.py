"""The workforce package's only door. Only its commands and rules exist here; the engine bridge applies the commands until the module moves."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import (AllocateFarmWorkforce, ApplyLandClearing, BuildHousing, CloseHoursYear, NoteTradeSpread, NoteWageShock, PressLabour,
                       ReleaseStaff, ReportStaffReduction, TakeWageFallback,
                       ScaleDeputies, SetEmployed, SurviveStaff, UpdateWages)
from . import rules
from .staff_loss_waves import wave_exposure
