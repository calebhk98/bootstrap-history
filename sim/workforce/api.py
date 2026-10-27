"""The workforce package's only door: its commands, its rules and the state it saves."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import (AllocateFarmWorkforce, ApplyLandClearing, BuildHousing, CloseHoursYear, GrantStaff, NoteTradeSpread, NoteWageShock, PressLabour,
                       ReleaseStaff, ReportStaffReduction, TakeWageFallback,
                       ScaleDeputies, SetEmployed, SurviveStaff, UpdateWages)
from .commands_people import (BuySlaves, CommissionHours, FireStaff, FoundTradeSchool, HireStaff, Manumit, MoveBase, TrainStaff,
                              WorkForWages)
from .commands_hours import (AllocateHours, BleedStaff, CancelWork, DisperseDependants, DrawTradeHours, LoseCrew, OrderWork, ReleaseHours,
                             ResetTradeHours, SetReserve, SetWageHoursSold, SettleLivingCost, SpendDirectorHours, WatchStaff)
from .commands_bondage import AutoBuyPeople, AutoManumit, ChargeLivingCost, FadeMarketPressure
from .state import WorkforceSeat, WorkforceSociety
from . import rules
from .staff_loss_waves import wave_exposure
