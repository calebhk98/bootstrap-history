"""The foreign-trade package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from .commands import (ClosePartnerBooks, CloseMarketsTo, NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg, RecordStockTaken,
                       SettleFlow, SettleTraderCargo)
from .constants import OPENING_CARRIERS_PER_ROUTE
from .state import ForeignTradeWorld
from . import country_trade_years, rules
