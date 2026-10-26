"""Bridge entries the resources module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached."""
from sim.assembly.api import QUOTE

from . import purchase_rule
from .bridge import bridge_view


# ---- the game's data and the labour market ----

@bridge_view("start_year")
def start_year(sim):
	return sim.cfg["start_year"]


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


@bridge_view("automatic_policy", kind=QUOTE, seat_scoped=True)
def automatic_policy(sim, name):
	"""Whether the automatic policy `name` runs: what the acting seat set, else on for an automatic game and off for a manual one."""
	return sim.state.founder.policy.get(name, not sim.manual)
