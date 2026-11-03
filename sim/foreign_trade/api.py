"""The foreign-trade package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import (ResetActorTradeTallies, CloseMarketsTo, NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg, RecordStockTaken,
                       SettleFlow, SettleTraderCargo)
from .constants import LANDING, OPENING_CARRIERS_PER_ROUTE, TAKING
from .state import ForeignTradeWorld
from . import rules
