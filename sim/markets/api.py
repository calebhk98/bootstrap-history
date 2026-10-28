"""The markets package's only door: its commands and the plain rules of the goods market."""

WALL = "two-way"  # nothing here imports sim/engine/

from .commands import (BuyMaterial, ForgetActorOrders, MarkMoneyPricedAtEconomy, NoteActorPurchase, NoteActorSale, NoteDraw, NotePurchase,
                       OpenMarketBook, RenameMarketSeat, RepriceOpeningMoney, ResetDraws, ResetMarketCaches,
                       SellMaterial)
from .constants import MEAN_INCOME_HOURS_PER_CAPITA
from .rules import HOME_SELLER
from .rules import tonnes_sold
from .spin_up import (SPIN_UP_MAXIMUM_YEARS, SPIN_UP_MEASURED_YEARS, SPIN_UP_TOLERANCE, SPIN_UP_TRIMMED_YEARS, SPIN_UP_YEARS_ENV,
                      spin_up_years)
from .port_key import SPIN_UP_SOURCE_MODULES, spin_up_key


# ---- the agent economy's opening, for the tools that run it on their own (the opening checks, the spin-up trace) ----

def build_setup(world, opening=None, production=None):
	"""The agent economy's setup for what `world` (the port's reads of a game) holds, or for `opening`."""
	from .port_setup import build_setup as build
	return build(world, opening, production)


def opening_setup(game):
	"""The setup of the opening `game` saved."""
	return build_setup(game.view("legacy_economy")().world, game.view("legacy_economy")().world.agent_record()["opening"])


def unit_mass_kg(material):
	"""Kilograms in one unit of a material, as the freight model reads it."""
	from .port_setup import unit_mass_kg as mass
	return mass(material)


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


def traded_staple(agent, stale):
	from .port_trace import traded_staple as staple
	return staple(agent, stale)
