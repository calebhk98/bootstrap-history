"""Bridge entries the resources module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached."""
from sim.assembly.api import QUOTE

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





@bridge_view("automatic_policy", kind=QUOTE, seat_scoped=True)
def automatic_policy(sim, name):
	"""Whether the automatic policy `name` runs: what the acting seat set, else on for an automatic game and off for a manual one."""
	return sim.state.founder.policy.get(name, not sim.manual)
