"""The workforce package's only door: its commands, its rules and the state it saves."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import (AllocateFarmWorkforce, ApplyLandClearing, BuildHousing, CloseHoursYear, GrantStaff, NoteTradeSpread, NoteWageShock, PressLabour,
                       ReleaseStaff, ReportStaffReduction, TakeWageFallback,
                       ScaleDeputies, SetEmployed, SurviveStaff, UpdateWages)
from .commands_hours import (AllocateHours, BleedStaff, CancelWork, DisperseDependants, DrawTradeHours, LoseCrew, OrderWork, ReleaseHours,
                             ResetTradeHours, SetReserve, SetWageHoursSold, SettleLivingCost, SpendDirectorHours, WatchStaff)
from .state import WorkforceSeat, WorkforceSociety
from . import rules
from .staff_loss_waves import wave_exposure
