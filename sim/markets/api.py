"""The markets package's only door: its commands and the plain rules of the goods market."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import (BuyMaterial, CancelMaterialOrders, FoundBankFromOutside, ForgetActorOrders, NoteActorPurchase, NoteActorSale,
                       MoveGoods, NoteDraw, RenameMarketSeat, RepriceOpeningMoney, ResetDraws,
                       SellMaterial)
from .spin_up import SPIN_UP_MAXIMUM_YEARS, SPIN_UP_TOLERANCE, SPIN_UP_YEARS_ENV
from .port_key import SPIN_UP_SOURCE_MODULES, spin_up_key
from .spin_up_trace_cache import TRACE_CACHE_DIRECTORY, trace_key_of_setup


# ---- the agent economy's opening, for the tools that run it on their own (the opening checks, the spin-up trace) ----

def opening_setup(game):
	"""The setup of the opening `game` saved."""
	return game.view("agent_opening_setup")()


def spin_up_trace(game, years):
	"""One row per year of the economy's hidden first stage run on the opening `game` saved."""
	from .port_trace import spin_up_trace as trace
	return trace(game, years)


def sensitivity_table(game, years, skip, variants=None):
	from .port_trace import sensitivity_table as table
	return table(game, years, skip, variants)


def coin_wear_per_year():
	from .port_trace import coin_wear_per_year as wear
	return wear()
