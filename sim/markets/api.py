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


def rule_set_configuration(rule_set):
	"""The configuration entries that open a game's economy on `rule_set`; none for no name (the shipped set)."""
	from .port_setup import rule_set_configuration as configuration
	return configuration(rule_set)


def spin_up_trace(game, years):
	"""One row per year of the economy's hidden first stage run on the opening `game` saved."""
	from .port_trace import spin_up_trace as trace
	return trace(game, years)


def spin_up_stages(game, cash_factor=1.0):
	"""(watched goods, generator of one row per year) of the full-length hidden spin-up of the opening `game` saved,
	stage by stage as the run takes it; with a `cash_factor` other than one the households' cash is first scaled by it."""
	from .spin_up_stages import replay_opening
	return replay_opening(game.view("agent_opening_setup")(), cash_factor)


def spin_up_member_figures(rows):
	"""({quantity: end gap}, {quantity: trend}) of the rows `spin_up_stages` gave (spin_up_ensemble.trimmed_trends)."""
	from .spin_up_ensemble import trimmed_trends
	from .spin_up_stages import end_gaps
	return end_gaps(rows)["gaps"], trimmed_trends(rows)


def spin_up_cash_factor(member):
	"""The cash factor of ensemble member `member` (spin_up_ensemble.cash_factor)."""
	from .spin_up_ensemble import cash_factor
	return cash_factor(member)


def spin_up_summary(member_values):
	"""Median and spread by quantity across members (spin_up_ensemble.summarise_members)."""
	from .spin_up_ensemble import summarise_members
	return summarise_members(member_values)


def spin_up_end_gaps(rows):
	"""The settle gaps the opening ends with, from the rows `spin_up_stages` gave (spin_up_stages.end_gaps)."""
	from .spin_up_stages import end_gaps
	return end_gaps(rows)


def spin_up_by_good(rows):
	"""{watched good: its share, largest move, part of the "prices" gap, trend and saw} of the rows `spin_up_stages` gave
	(spin_up_by_good.by_good over the measured years)."""
	from .spin_up import SPIN_UP_MEASURED_YEARS
	from .spin_up_by_good import by_good
	return by_good(rows, int(SPIN_UP_MEASURED_YEARS))


def spin_up_median_by_good(tables):
	"""The members' `spin_up_by_good` tables as one of medians (spin_up_ensemble.median_by_good)."""
	from .spin_up_ensemble import median_by_good
	return median_by_good(tables)


def spin_up_mix_parts(rows, quantity, mix_name):
	"""[(good, its part of the change)] in the pair of measured years where `quantity` moved most (spin_up_by_good.mix_parts)."""
	from .spin_up import SPIN_UP_MEASURED_YEARS
	from .spin_up_by_good import mix_parts
	trimmed = [row for row in rows if row["stage"] == "trimmed"]
	return mix_parts(trimmed[-int(SPIN_UP_MEASURED_YEARS):], quantity, mix_name)


def spin_up_price_level_parts(rows):
	"""[(good, "moved", "entered" or "left", its effect)] on the price level in the pair of measured years where it moved
	most, as shares of the earlier level (spin_up_by_good.price_level_parts)."""
	from .spin_up import SPIN_UP_MEASURED_YEARS
	from .spin_up_by_good import price_level_parts
	trimmed = [row for row in rows if row["stage"] == "trimmed"]
	return price_level_parts(trimmed[-int(SPIN_UP_MEASURED_YEARS):])


def spin_up_mix_tables(rows, count):
	"""(labels, hours by trade, output by good, recipes whose share of a good moved) for the first year, the trough and the
	last year of the rows `spin_up_stages` gave (spin_up_mix_table.py); each table's rows hold one value per label."""
	from . import spin_up_mix_table as table
	marked = table.marked_rows(rows)
	mixes = [row["mix"] for _label, row in marked]
	return ([label for label, _row in marked], table.largest_first(mixes, "hours_by_trade", count, size=lambda hours: hours[0] + hours[1]),
	        table.largest_first(mixes, "output_by_good", count), table.recipes_that_moved(mixes, count))


def sensitivity_table(game, years, skip, variants=None):
	from .port_trace import sensitivity_table as table
	return table(game, years, skip, variants)


def coin_wear_per_year():
	from .port_trace import coin_wear_per_year as wear
	return wear()
