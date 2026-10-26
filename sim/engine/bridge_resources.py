"""Bridge entries the resources module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached."""
from sim.assembly.api import KEYED, QUOTE

from . import purchase_rule
from .bridge import bridge_view


# ---- the game's data and the labour market ----

@bridge_view("start_year")
def start_year(sim):
	return sim.cfg["start_year"]


@bridge_view("labour_quote", kind=QUOTE)
def labour_quote(sim, trade, hours):
	"""Money one hour of a trade costs when `hours` of it are bought at once (the price rises with the hours)."""
	return sim.labour.labour_market.quote(trade, hours)


@bridge_view("mineral_scale", kind=KEYED)
def mineral_scale(sim, material):
	"""Fraction of a mineral's reference output the civilisation can draw on, from the tiles it holds."""
	return sim.geography.mineral_scale(material)


# ---- materials ----

@bridge_view("running_stamp")
def running_stamp(sim):
	"""(the projects record, the counts and versions of what is built, granted and operating, the tree): a table derived
	from what is running stays good while this is unchanged."""
	return sim._running_kept_stamp()


# ---- finance, polity and the seat's policy ----

@bridge_view("spending_power", kind=QUOTE)
def spending_power(sim, kind="buy"):
	return sim.spending_power(kind)


@bridge_view("purchase_budget", seat_scoped=True)
def purchase_budget(sim):
	"""Most the acting seat can spend on one outright purchase right now."""
	return purchase_rule.purchase_budget(sim)


@bridge_view("affordable_units", kind=QUOTE)
def affordable_units(sim, unit_cost, decimals=1):
	"""Units the purchase budget buys at `unit_cost`, rounded down so the figure is buyable."""
	return purchase_rule.affordable_units(sim, unit_cost, decimals=decimals)


@bridge_view("afford_means")
def afford_means(sim):
	return purchase_rule.afford_means()


@bridge_view("inspection_reach")
def inspection_reach(sim):
	"""The share of the home people whose claims and workings its employed inspectors check."""
	return sim.inspection_reach()


@bridge_view("forest_reach")
def forest_reach(sim):
	"""The share of the home people whose woodland tenure its employed foresters keep."""
	return sim.forest_reach()


@bridge_view("automatic_policy", kind=QUOTE, seat_scoped=True)
def automatic_policy(sim, name):
	"""Whether the automatic policy `name` runs: what the acting seat set, else on for an automatic game and off for a manual one."""
	return sim.state.founder.policy.get(name, not sim.manual)
