"""The workforce package's only door: its commands, its rules and the state it saves."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import (BuildHousing, CloseHoursYear, GrantStaff, NoteTradeSpread,
                       LoseStaff, NewcomersPlaced, NoteClearedWage, ReleaseStaff, TakeWageFallback, ClearingSettled,
                       SetEmployed, StaffArrived, HoursArrived, PostHoursOnce)
from .commands_people import (BuySlaves, CommissionHours, FireStaff, FoundTradeSchool, HireStaff, Manumit, MoveBase, TrainStaff,
                              WorkForWages)
from .commands_hours import (AllocateHours, BleedStaff, CancelWork, DisperseDependants, DrawTradeHours, LoseCrew, OrderWork, ReleaseHours,
                             ResetTradeHours, SetReserve, SpendDirectorHours, WatchStaff)
from .commands_bondage import AutoBuyPeople, AutoManumit, ChargeLivingCost, FadeMarketPressure, NoteBuyRefusal
from .state import ONCE_COMMISSION, ONCE_STOCK, TrainingRow, WorkforceSeat
from . import rules
from .wage_schedule import build_schedule
from .staff_loss_waves import wave_exposure
